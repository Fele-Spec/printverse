import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  ContactShadows, Environment, Lightformer, OrbitControls, OrthographicCamera, PerspectiveCamera,
} from '@react-three/drei';
import { Suspense, useCallback, useEffect, useState } from 'react';
import * as THREE from 'three';
import type { PrintTick, Toolpath } from '../types';
import type { PanelMode, ViewPreset } from './SceneControls';
import { FinishedObject } from './FinishedObject';
import { PrintPaths } from './PrintPaths';
import { PrintSimulator } from './PrintSimulator';
import { VoronMachine } from './VoronMachine';
import { RealModules } from './RealModules';

const VIEW_CONFIG: Record<ViewPreset, { position: [number, number, number]; target: [number, number, number]; fov: number }> = {
  product: { position: [620, -1080, 680], target: [0, 0, 270], fov: 34 },
  engineering: { position: [760, -900, 760], target: [0, 0, 270], fov: 32 },
  interior: { position: [260, -540, 360], target: [0, 0, 300], fov: 38 },
  toolhead: { position: [205, -360, 405], target: [0, 0, 320], fov: 32 },
  top: { position: [0, -520, 1080], target: [0, 0, 270], fov: 34 },
  exploded: { position: [850, -1260, 900], target: [0, 0, 250], fov: 36 },
};

const CAD_VIEW_CONFIG: Record<ViewPreset, { position: [number, number, number]; target: [number, number, number]; fov: number }> = {
  product: { position: [620, -1080, 650], target: [0, 0, 225], fov: 34 },
  engineering: { position: [760, -900, 720], target: [0, 0, 225], fov: 32 },
  interior: { position: [260, -540, 350], target: [0, 0, 225], fov: 38 },
  toolhead: { position: [205, -330, 310], target: [0, 0, 158], fov: 30 },
  top: { position: [0, -520, 1030], target: [0, 0, 220], fov: 34 },
  exploded: { position: [850, -1260, 860], target: [0, 0, 215], fov: 36 },
};

function CameraRig({ view, orthographic, cadMode }: { view: ViewPreset; orthographic: boolean; cadMode: boolean }) {
  const { camera, controls, size } = useThree();
  useEffect(() => {
    const c = (cadMode ? CAD_VIEW_CONFIG : VIEW_CONFIG)[view];
    camera.up.set(0, 0, 1);
    camera.position.set(...c.position);
    camera.lookAt(...c.target);
    if ((camera as THREE.PerspectiveCamera).isPerspectiveCamera) {
      (camera as THREE.PerspectiveCamera).fov = c.fov;
      (camera as THREE.PerspectiveCamera).updateProjectionMatrix();
    }
    if ((camera as THREE.OrthographicCamera).isOrthographicCamera) {
      (camera as THREE.OrthographicCamera).zoom = orthographic ? 1.05 : 1;
      (camera as THREE.OrthographicCamera).updateProjectionMatrix();
    }
    const orbit = controls as unknown as { target?: THREE.Vector3; update?: () => void } | null;
    orbit?.target?.set(...c.target);
    orbit?.update?.();
  }, [view, orthographic, cadMode, camera, controls, size.width, size.height]);
  return null;
}

function FrameCounter() {
  useFrame(() => {
    const w = window as unknown as { __PV_FRAMES?: number };
    w.__PV_FRAMES = (w.__PV_FRAMES ?? 0) + 1;
  });
  return null;
}

function CameraBridge() {
  const { camera, controls } = useThree();
  useEffect(() => {
    (window as unknown as { __PV_VIEW?: (position: [number, number, number], target: [number, number, number]) => void }).__PV_VIEW = (position, target) => {
      camera.position.set(...position);
      camera.lookAt(...target);
      const orbit = controls as unknown as { target?: { set: (x: number, y: number, z: number) => void }; update?: () => void } | null;
      orbit?.target?.set(...target);
      orbit?.update?.();
    };
    return () => {
      delete (window as unknown as { __PV_VIEW?: unknown }).__PV_VIEW;
    };
  }, [camera, controls]);
  return null;
}

export function PrintScene({
  toolpath,
  modelUrl,
  colorUrl,
  status,
  playing,
  speed,
  showLabels,
  transformMode,
  detached,
  resetKey,
  viewPreset,
  orthographic,
  panelMode,
  explode,
  visibleModules,
  cadMode,
  showFasteners,
  selectedPartName,
  onPartSelect,
  onTick,
  onComplete,
}: {
  toolpath: Toolpath | null;
  modelUrl: string;
  colorUrl?: string | null;
  status: string;
  playing: boolean;
  speed: number;
  showLabels: boolean;
  transformMode: 'translate' | 'rotate' | 'scale';
  detached: boolean;
  resetKey: number;
  viewPreset: ViewPreset;
  orthographic: boolean;
  panelMode: PanelMode;
  explode: number;
  visibleModules: Record<string, boolean>;
  cadMode: boolean;
  showFasteners: boolean;
  selectedPartName?: string | null;
  onPartSelect?: (name: string, module: string) => void;
  onTick: (tick: PrintTick) => void;
  onComplete: () => void;
}) {
  const [tick, setTick] = useState<PrintTick>({
    time: 0, progress: 0, layer: 0, toolhead: { x: 0, y: 0 }, bedZ: 300, deposited: 0, mass_g: 0,
  });
  useEffect(() => {
    setTick({ time: 0, progress: 0, layer: 0, toolhead: { x: 0, y: 0 }, bedZ: 300, deposited: 0, mass_g: 0 });
  }, [resetKey]);
  const handleTick = useCallback((next: PrintTick) => {
    setTick(next);
    onTick(next);
  }, [onTick]);
  const showFinished = status === 'completed' || status === 'detached';
  const showPaths = Boolean(toolpath) && !showFinished;
  // Park the toolhead clear of the finished part; the bed remains at its final Z.
  const machineToolhead = showFinished ? { x: 0, y: 185 } : tick.toolhead;

  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      camera={{ position: [620, -1080, 680], fov: 34, near: 1, far: 4000, up: [0, 0, 1] }}
      gl={{ antialias: true, preserveDrawingBuffer: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.42, outputColorSpace: THREE.SRGBColorSpace }}
      data-testid="three-canvas"
    >
      <color attach="background" args={['#070b0d']} />
      <fog attach="fog" args={['#070b0d', 1100, 2300]} />
      <PerspectiveCamera makeDefault={!orthographic} position={[620, -1080, 680]} fov={34} near={1} far={4000} up={[0, 0, 1]} />
      <OrthographicCamera makeDefault={orthographic} position={[620, -1080, 680]} zoom={2.05} near={1} far={5000} up={[0, 0, 1]} />
      <CameraRig view={viewPreset} orthographic={orthographic} cadMode={cadMode} />
      <CameraBridge />
      <FrameCounter />

      <ambientLight intensity={0.78} />
      <hemisphereLight args={['#d6e8f0', '#0a1116', 0.55]} />
      <directionalLight
        position={[420, -420, 900]}
        intensity={3.4}
        color="#fff4e2"
        castShadow
        shadow-mapSize={[1024, 1024]}
        shadow-bias={-0.0003}
        shadow-camera-left={-620}
        shadow-camera-right={620}
        shadow-camera-top={620}
        shadow-camera-bottom={-620}
      />
      <directionalLight position={[-520, 280, 460]} intensity={1.15} color="#8bc7e4" />
      <directionalLight position={[260, 460, 250]} intensity={0.9} color="#ffbd82" />
      <spotLight position={[0, -260, 900]} angle={0.55} penumbra={0.8} intensity={55} color="#d8f1ff" />
      <Environment resolution={256} frames={1}>
        <Lightformer intensity={2.2} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 640]} scale={[10, 10, 1]} />
        <Lightformer intensity={1.1} rotation={[0, -Math.PI / 2, 0]} position={[-520, 0, 320]} scale={[8, 4, 1]} color="#9bc7df" />
        <Lightformer intensity={0.9} rotation={[0, Math.PI / 2, 0]} position={[520, 0, 280]} scale={[8, 4, 1]} color="#ffd1a0" />
        <Lightformer intensity={0.6} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, -120]} scale={[6, 6, 1]} color="#304b5a" />
      </Environment>

      <mesh position={[0, 0, -1.2]} receiveShadow>
        <planeGeometry args={[1200, 1200]} />
        <meshStandardMaterial color="#090f13" metalness={0.32} roughness={0.72} />
      </mesh>
      <gridHelper args={[760, 38, '#1d3542', '#0d1b23']} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0.2]} />
      <ContactShadows position={[0, 0, -0.5]} opacity={0.5} scale={920} blur={2.8} far={480} resolution={256} frames={1} color="#000000" />

      {cadMode ? (
        <Suspense fallback={null}>
          <RealModules
            visibleModules={visibleModules}
            panelMode={panelMode}
            explode={explode}
            highDetail={viewPreset === 'toolhead' || viewPreset === 'interior'}
            showFasteners={showFasteners}
            selectedPartId={selectedPartName}
            toolhead={machineToolhead}
            bedZ={tick.bedZ}
            onSelect={onPartSelect}
          />
          {showPaths && (
            <group position={[0, 0, tick.bedZ - 242]}>
              <PrintPaths toolpath={toolpath} deposited={tick.deposited} />
            </group>
          )}
        </Suspense>
      ) : (
        <VoronMachine
          toolhead={machineToolhead}
          bedZ={tick.bedZ}
          showLabels={showLabels}
          zRotation={tick.time * 0.2}
          panelMode={panelMode}
          explode={explode}
          visibleModules={visibleModules}
        >
          {showPaths && (
            <group position={[0, 0, tick.bedZ]}>
              <PrintPaths toolpath={toolpath} deposited={tick.deposited} />
            </group>
          )}
        </VoronMachine>
      )}

      {showFinished && (
        <Suspense fallback={null}>
          <FinishedObject
            modelUrl={modelUrl}
            colorUrl={colorUrl}
            bedZ={cadMode ? tick.bedZ - 242 : tick.bedZ}
            detached={detached}
            mode={transformMode}
            showLabel={showLabels}
          />
        </Suspense>
      )}

      <PrintSimulator
        toolpath={toolpath}
        playing={playing}
        speed={speed}
        resetKey={resetKey}
        onTick={handleTick}
        onComplete={onComplete}
      />
      <OrbitControls
        key={orthographic ? 'ortho' : 'persp'}
        makeDefault
        target={[0, 0, 270]}
        enableDamping
        dampingFactor={0.08}
        minDistance={180}
        maxDistance={1500}
        maxPolarAngle={Math.PI * 0.92}
      />
    </Canvas>
  );
}
