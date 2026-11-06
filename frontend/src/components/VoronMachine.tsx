import { Html, Line } from '@react-three/drei';
import { useLoader } from '@react-three/fiber';
import { Suspense, useMemo, type ReactNode } from 'react';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';

const FRAME = { x: 460, y: 460, z: 480, extrusion: 20 };
const BED_BASE_Z = 300;
const RAIL_Z = 350;

type PartProps = {
  size: [number, number, number];
  position: [number, number, number];
  color?: string;
  metalness?: number;
  roughness?: number;
  transparent?: boolean;
  opacity?: number;
  depthWrite?: boolean;
};

function Part({ size, position, color = '#43515d', metalness = 0.55, roughness = 0.38, transparent = false, opacity = 1, depthWrite = true }: PartProps) {
  return (
    <mesh position={position} castShadow={!transparent} receiveShadow>
      <boxGeometry args={size} />
      <meshStandardMaterial color={color} metalness={metalness} roughness={roughness} transparent={transparent} opacity={opacity} depthWrite={depthWrite} />
    </mesh>
  );
}

function Screw({ x, y, height, z, color = '#95a6b4' }: { x: number; y: number; height: number; z: number; color?: string }) {
  return (
    <mesh position={[x, y, z]} rotation={[Math.PI / 2, 0, 0]} castShadow>
      <cylinderGeometry args={[3.2, 3.2, height, 12]} />
      <meshStandardMaterial color={color} metalness={0.85} roughness={0.22} />
    </mesh>
  );
}

function Label({ position, children }: { position: [number, number, number]; children: ReactNode }) {
  return (
    <Html position={position} center distanceFactor={520} zIndexRange={[1, 0]}>
      <div className="scene-label">{children}</div>
    </Html>
  );
}

function BedMesh() {
  const geometry = useLoader(STLLoader, '/models/voron_300_bed.stl');
  const placement = useMemo(() => {
    const g = geometry.clone();
    g.computeBoundingBox();
    const box = g.boundingBox ?? new THREE.Box3();
    const center = new THREE.Vector3();
    box.getCenter(center);
    return { geometry: g, center, maxZ: box.max.z };
  }, [geometry]);
  return (
    <mesh
      geometry={placement.geometry}
      position={[-placement.center.x, -placement.center.y, -placement.maxZ]}
      castShadow
      receiveShadow
    >
      <meshStandardMaterial color="#aebfc3" metalness={0.3} roughness={0.58} />
    </mesh>
  );
}

export function VoronMachine({
  toolhead,
  bedZ,
  showLabels,
  zRotation,
  panelMode = 'glass',
  explode = 0,
  visibleModules = {},
  children,
}: {
  toolhead: { x: number; y: number };
  bedZ: number;
  showLabels: boolean;
  zRotation: number;
  panelMode?: 'glass' | 'clear' | 'hidden';
  explode?: number;
  visibleModules?: Record<string, boolean>;
  children?: ReactNode;
}) {
  const show = (id: string) => visibleModules[id] !== false;
  const panelOpacity = panelMode === 'hidden' ? 0 : panelMode === 'clear' ? 0.055 : 0.16;
  const panelVisible = panelMode !== 'hidden';
  const gantryY = Math.max(-155, Math.min(155, toolhead.y));
  const gantryX = Math.max(-160, Math.min(160, toolhead.x));
  const frame = useMemo(() => {
    const v = FRAME.extrusion;
    const half = FRAME.x / 2 - v / 2;
    const parts: Array<{ size: [number, number, number]; pos: [number, number, number]; key: string }> = [];
    for (const x of [-half, half]) {
      for (const y of [-half, half]) {
        parts.push({ key: `v${x}${y}`, size: [v, v, FRAME.z], pos: [x, y, FRAME.z / 2] });
      }
    }
    for (const z of [v / 2, FRAME.z - v / 2]) {
      for (const y of [-half, half]) {
        parts.push({ key: `bx${z}${y}`, size: [FRAME.x - 2 * v, v, v], pos: [0, y, z] });
      }
      for (const x of [-half, half]) {
        parts.push({ key: `by${z}${x}`, size: [v, FRAME.y - 2 * v, v], pos: [x, 0, z] });
      }
    }
    // Rear upper cross brace from the 290 mm BOM extrusion.
    parts.push({ key: 'brace', size: [290, v, v], pos: [0, half, FRAME.z - 70] });
    return parts;
  }, []);

  const belts = useMemo<Array<{ key: string; points: [number, number, number][]; color: string }>>(() => {
    const rearLeft: [number, number, number] = [-150, -205, 52];
    const rearRight: [number, number, number] = [150, -205, 52];
    const frontLeft: [number, number, number] = [-190, 205, RAIL_Z];
    const frontRight: [number, number, number] = [190, 205, RAIL_Z];
    return [
      { key: 'a-rear', points: [rearLeft, [-190, gantryY, RAIL_Z]], color: '#f3a35c' },
      { key: 'a-front', points: [[-190, gantryY, RAIL_Z], frontLeft], color: '#f3a35c' },
      { key: 'b-rear', points: [rearRight, [190, gantryY, RAIL_Z]], color: '#6fd6ff' },
      { key: 'b-front', points: [[190, gantryY, RAIL_Z], frontRight], color: '#6fd6ff' },
    ];
  }, [gantryY]);

  return (
    <group name="VORON_V2_4R2_300">
      <group name="FRAME" visible={show('FRAME')}>
        {frame.map((p) => (
          <Part key={p.key} size={p.size} position={p.pos} color={p.key === 'brace' ? '#53616d' : '#3b4853'} />
        ))}
        {panelVisible && (
          <group name="ENCLOSURE">
            <Part size={[FRAME.x - 14, 3, FRAME.z - 30]} position={[0, 232, FRAME.z / 2]} color="#154258" transparent opacity={panelOpacity} metalness={0.1} roughness={0.12} depthWrite={false} />
            <Part size={[3, FRAME.y - 14, FRAME.z - 30]} position={[-232, 0, FRAME.z / 2]} color="#154258" transparent opacity={panelOpacity} metalness={0.1} roughness={0.12} depthWrite={false} />
            <Part size={[3, FRAME.y - 14, FRAME.z - 30]} position={[232, 0, FRAME.z / 2]} color="#154258" transparent opacity={panelOpacity} metalness={0.1} roughness={0.12} depthWrite={false} />
            <Part size={[FRAME.x - 14, 3, FRAME.z - 30]} position={[0, -232, FRAME.z / 2]} color="#154258" transparent opacity={panelOpacity * 0.65} metalness={0.1} roughness={0.12} depthWrite={false} />
          </group>
        )}
        {showLabels && <Label position={[0, 232, 490]}>FRAME 460 × 460 × 480</Label>}
      </group>

      <group name="CORE_XY_GANTRY" visible={show('XY_GANTRY')} position={[0, 0, explode * 34]}>
        <Part size={[12, 410, 12]} position={[-190, 0, RAIL_Z - 14]} color="#9aa8b3" metalness={0.9} roughness={0.2} />
        <Part size={[12, 410, 12]} position={[190, 0, RAIL_Z - 14]} color="#9aa8b3" metalness={0.9} roughness={0.2} />
        <Part size={[380, 20, 20]} position={[0, gantryY, RAIL_Z]} color="#7a93a3" transparent opacity={0.5} depthWrite={false} />
        <Part size={[350, 9, 9]} position={[0, gantryY, RAIL_Z - 22]} color="#c1ced8" metalness={0.9} roughness={0.16} transparent opacity={0.72} depthWrite={false} />
        <Part size={[42, 32, 30]} position={[-190, gantryY, RAIL_Z - 10]} color="#1f2a32" />
        <Part size={[42, 32, 30]} position={[190, gantryY, RAIL_Z - 10]} color="#1f2a32" />
        <Part size={[46, 36, 30]} position={[gantryX, gantryY, RAIL_Z - 26]} color="#1f2a32" />
        {showLabels && <Label position={[0, gantryY + 12, RAIL_Z + 32]}>CORE-XY GANTRY</Label>}
      </group>

      <group name="TOOLHEAD" visible={show('TOOLHEAD')} position={[0, 0, explode * 80]}>
        <group position={[gantryX, gantryY, 0]}>
          <Part size={[62, 52, 64]} position={[0, 0, 356]} color="#27343d" />
          <Part size={[38, 34, 16]} position={[0, -7, 322]} color="#53616d" />
          <mesh position={[0, 0, 312]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <cylinderGeometry args={[8, 8, 24, 18]} />
            <meshStandardMaterial color="#d8b56a" metalness={0.8} roughness={0.25} />
          </mesh>
          <mesh position={[0, 0, 302]} rotation={[Math.PI, 0, 0]} castShadow>
            <coneGeometry args={[3.2, 8, 16]} />
            <meshStandardMaterial color="#ffb45f" emissive="#8d4d16" emissiveIntensity={0.7} metalness={0.7} roughness={0.2} />
          </mesh>
          <Part size={[5, 5, 3]} position={[0, 0, 297]} color="#ffcf7d" metalness={0.1} roughness={0.4} />
          {showLabels && <Label position={[0, 0, 390]}>TOOLHEAD · nozzle Z0</Label>}
        </group>
      </group>

      {belts.map((belt) => (
        <Line key={belt.key} points={belt.points} color={belt.color} lineWidth={2.2} transparent opacity={0.85} />
      ))}
      <mesh position={[-150, -205, 46]} castShadow>
        <cylinderGeometry args={[14, 14, 18, 24]} />
        <meshStandardMaterial color="#2b3a44" metalness={0.7} roughness={0.3} />
      </mesh>
      <mesh position={[150, -205, 46]} castShadow>
        <cylinderGeometry args={[14, 14, 18, 24]} />
        <meshStandardMaterial color="#2b3a44" metalness={0.7} roughness={0.3} />
      </mesh>
      {showLabels && <Label position={[0, -215, 100]}>A / B DRIVES · CoreXY</Label>}

      <group name="Z_AXIS" visible={show('Z_DRIVE')}>
        {[-145, 145].map((x) =>
          [-145, 145].map((y) => (
            <group key={`${x}${y}`}>
              <Screw x={x} y={y} height={300} z={165} />
              <mesh position={[x, y, 22]} rotation={[Math.PI / 2, 0, 0]} castShadow>
                <cylinderGeometry args={[10, 10, 30, 18]} />
                <meshStandardMaterial color="#2b3a44" metalness={0.7} roughness={0.3} />
              </mesh>
            </group>
          )),
        )}
        <mesh position={[0, 0, 44]} rotation={[0, 0, zRotation]} castShadow>
          <boxGeometry args={[310, 310, 8]} />
          <meshStandardMaterial color="#26343e" metalness={0.6} roughness={0.35} />
        </mesh>
        {showLabels && <Label position={[0, 175, 80]}>4-POINT Z · lead screws</Label>}
      </group>

      <group name="Z_BED" visible={show('BUILD_PLATFORM')} position={[0, 0, bedZ - explode * 26]}>
        <Part size={[305, 305, 6]} position={[0, 0, -13]} color="#53656d" metalness={0.3} roughness={0.6} />
        <Suspense fallback={<Part size={[305, 305, 8]} position={[0, 0, -4]} color="#94a6ab" metalness={0.25} roughness={0.7} />}>
          <BedMesh />
        </Suspense>
        <Part size={[250, 250, 3]} position={[0, 0, -10]} color="#9a552e" metalness={0.2} roughness={0.6} />
        <Part size={[318, 318, 9]} position={[0, 0, -18]} color="#202b33" metalness={0.4} roughness={0.4} />
        {[-145, 145].map((x) =>
          [-145, 145].map((y) => (
            <mesh key={`${x}${y}`} position={[x, y, -8]} rotation={[Math.PI / 2, 0, 0]} castShadow>
              <cylinderGeometry args={[8, 8, 6, 16]} />
              <meshStandardMaterial color="#d2a15d" metalness={0.7} roughness={0.3} />
            </mesh>
          )),
        )}
        {children}
        {showLabels && <Label position={[0, 0, 24]}>Z BED · 305 × 305</Label>}
      </group>
    </group>
  );
}

export { BED_BASE_Z };
