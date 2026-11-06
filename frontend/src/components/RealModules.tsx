import { useGLTF } from '@react-three/drei';
import type { ThreeEvent } from '@react-three/fiber';
import { useEffect, useMemo, useState } from 'react';
import * as THREE from 'three';

export const MODULE_URLS: Record<string, string> = {
  FRAME: '/models/voron/modules/FRAME.lod.glb',
  ENCLOSURE: '/models/voron/modules/ENCLOSURE.lod.glb',
  XY_GANTRY: '/models/voron/modules/XY_GANTRY.lod.glb',
  Z_DRIVE: '/models/voron/modules/Z_DRIVE.lod.glb',
  TOOLHEAD: '/models/voron/modules/TOOLHEAD.lod.glb',
  BUILD_PLATFORM: '/models/voron/modules/BUILD_PLATFORM.lod.glb',
  ELECTRONICS: '/models/voron/modules/ELECTRONICS.lod.glb',
  WIRING: '/models/voron/modules/WIRING.lod.glb',
};

export const MODULE_URLS_HIGH: Record<string, string> = Object.fromEntries(
  Object.keys(MODULE_URLS).map((id) => [id, `/models/voron/modules/${id}.glb`]),
);

type PartRange = { placement_id: string; part_name: string; start: number; count: number };
type PartRecord = { bbox?: number[] | null };

function rangeFor(ranges: PartRange[], faceIndex: number | null | undefined): PartRange | null {
  if (faceIndex == null) return null;
  let lo = 0;
  let hi = ranges.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const r = ranges[mid];
    if (faceIndex < r.start) hi = mid - 1;
    else if (faceIndex >= r.start + r.count) lo = mid + 1;
    else return r;
  }
  return null;
}

const MODULE_MATERIAL: Record<string, { color: string; metalness: number; roughness: number }> = {
  FRAME: { color: '#1b2023', metalness: 0.82, roughness: 0.38 },
  ENCLOSURE: { color: '#91afbb', metalness: 0.02, roughness: 0.12 },
  XY_GANTRY: { color: '#39454c', metalness: 0.88, roughness: 0.28 },
  Z_DRIVE: { color: '#303a40', metalness: 0.8, roughness: 0.34 },
  TOOLHEAD: { color: '#252b2f', metalness: 0.58, roughness: 0.42 },
  BUILD_PLATFORM: { color: '#a9a396', metalness: 0.12, roughness: 0.68 },
  ELECTRONICS: { color: '#232a2e', metalness: 0.35, roughness: 0.56 },
  WIRING: { color: '#111416', metalness: 0.02, roughness: 0.78 },
};

function Module({ id, url, visible, panelMode, ranges, onSelect }: {
  id: string; url: string; visible: boolean; panelMode: 'glass' | 'clear' | 'hidden';
  ranges: PartRange[];
  onSelect?: (name: string, module: string) => void;
}) {
  const { scene } = useGLTF(url);
  const cloned = useMemo(() => {
    const root = scene.clone(true);
    const spec = MODULE_MATERIAL[id] ?? MODULE_MATERIAL.FRAME;
    const isPanel = id === 'ENCLOSURE';
    const material = new THREE.MeshStandardMaterial({
      color: spec.color, metalness: spec.metalness, roughness: spec.roughness,
      transparent: isPanel, opacity: isPanel ? (panelMode === 'clear' ? 0.055 : 0.21) : 1,
      depthWrite: !isPanel, side: THREE.DoubleSide,
    });
    root.traverse((child) => {
      const mesh = child as THREE.Mesh;
      if (!mesh.isMesh) return;
      mesh.userData.module = id;
      mesh.userData.partId = mesh.name;
      mesh.userData.partName = mesh.name;
      mesh.castShadow = false;
      mesh.receiveShadow = true;
      mesh.material = material;
    });
    return root;
  }, [scene, id, panelMode]);

  return (
    <primitive
      object={cloned}
      visible={visible && !(id === 'ENCLOSURE' && panelMode === 'hidden')}
      onClick={(event: ThreeEvent<MouseEvent>) => {
        event.stopPropagation();
        const hit = rangeFor(ranges, event.faceIndex);
        onSelect?.(hit?.placement_id ?? id, id);
      }}
    />
  );
}

export function RealModules({
  visibleModules, panelMode, onSelect, zOffset = 0, explode = 0, highDetail = false, selectedPartId,
  toolhead, bedZ,
}: {
  visibleModules: Record<string, boolean>;
  panelMode: 'glass' | 'clear' | 'hidden';
  onSelect?: (name: string, module: string) => void;
  zOffset?: number;
  explode?: number;
  highDetail?: boolean;
  selectedPartId?: string | null;
  toolhead?: { x: number; y: number };
  bedZ?: number;
}) {
  const [ranges, setRanges] = useState<Record<string, PartRange[]>>({});
  const [selected, setSelected] = useState<PartRecord | null>(null);
  useEffect(() => {
    fetch(highDetail ? '/models/voron/module-face-ranges.json' : '/models/voron/module-face-ranges-lod.json')
      .then((r) => r.json())
      .then(setRanges)
      .catch(() => setRanges({}));
  }, [highDetail]);
  useEffect(() => {
    if (!selectedPartId) { setSelected(null); return; }
    fetch('/models/voron/parts-index.json')
      .then((r) => r.json())
      .then((index) => setSelected(index[selectedPartId] ?? null))
      .catch(() => setSelected(null));
  }, [selectedPartId]);
  const edges = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)), []);
  const box = selected?.bbox;
  const selection = box ? {
    center: [(box[0] + box[3]) / 2 / 1000, (box[1] + box[4]) / 2 / 1000, (box[2] + box[5]) / 2 / 1000] as [number, number, number],
    size: [Math.max((box[3] - box[0]) / 1000, 0.002), Math.max((box[4] - box[1]) / 1000, 0.002), Math.max((box[5] - box[2]) / 1000, 0.002)] as [number, number, number],
  } : null;
  return (
    <group position={[-127, -127, 58 + zOffset]} scale={1000}>
      {Object.keys(MODULE_URLS).map((id) => {
        const motion: [number, number, number] = id === 'TOOLHEAD' && toolhead
          ? [(toolhead.x - 6) / 1000, (toolhead.y - 15.5) / 1000, 0]
          : id === 'BUILD_PLATFORM' && bedZ != null
            ? [0, 0, (bedZ - 300) / 1000]
            : [0, 0, 0];
        const explodeZ = explode * (id === 'TOOLHEAD' ? 0.25 : id === 'XY_GANTRY' ? 0.11 : id === 'Z_DRIVE' ? 0.055 : id === 'BUILD_PLATFORM' ? -0.08 : id === 'ELECTRONICS' ? 0.03 : 0);
        return (
          <group key={id} position={[motion[0], motion[1], motion[2] + explodeZ]}>
            <Module id={id} url={(highDetail ? MODULE_URLS_HIGH : MODULE_URLS)[id]} visible={visibleModules[id] !== false} panelMode={panelMode} ranges={ranges[id] ?? []} onSelect={onSelect} />
          </group>
        );
      })}
      {selection && (
        <lineSegments geometry={edges} position={selection.center} scale={selection.size}>
          <lineBasicMaterial color="#79f2c0" transparent opacity={0.95} depthTest={false} />
        </lineSegments>
      )}
    </group>
  );
}
