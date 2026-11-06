import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Suspense, useCallback, useEffect, useState } from 'react';
import type { PrintTick, Toolpath } from '../types';
import { FinishedObject } from './FinishedObject';
import { PrintPaths } from './PrintPaths';
import { PrintSimulator } from './PrintSimulator';
import { VoronMachine } from './VoronMachine';

export function PrintScene({
  toolpath,
  modelUrl,
  status,
  playing,
  speed,
  showLabels,
  transformMode,
  detached,
  resetKey,
  onTick,
  onComplete,
}: {
  toolpath: Toolpath | null;
  modelUrl: string;
  status: string;
  playing: boolean;
  speed: number;
  showLabels: boolean;
  transformMode: 'translate' | 'rotate' | 'scale';
  detached: boolean;
  resetKey: number;
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
      camera={{ position: [620, -1080, 680], fov: 34, near: 1, far: 3000, up: [0, 0, 1] }}
      gl={{ antialias: true, preserveDrawingBuffer: true }}
      data-testid="three-canvas"
    >
      <color attach="background" args={['#081017']} />
      <fog attach="fog" args={['#081017', 1000, 1900]} />
      <ambientLight intensity={1.05} />
      <hemisphereLight args={['#d8f7ff', '#0a151d', 0.55]} />
      <directionalLight
        position={[350, -380, 760]}
        intensity={2.4}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-500}
        shadow-camera-right={500}
        shadow-camera-top={500}
        shadow-camera-bottom={-500}
      />
      <directionalLight position={[-420, 220, 360]} intensity={0.8} color="#6fc8ff" />
      <pointLight position={[0, 0, 330]} intensity={40} color="#79f2c0" distance={500} />

      <mesh position={[0, 0, -1]} receiveShadow>
        <planeGeometry args={[900, 900]} />
        <meshStandardMaterial color="#0a151d" metalness={0.2} roughness={0.85} />
      </mesh>
      <gridHelper args={[760, 38, '#264b5c', '#122631']} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0.2]} />

      <VoronMachine toolhead={machineToolhead} bedZ={tick.bedZ} showLabels={showLabels} zRotation={tick.time * 0.2}>
        {showPaths && <PrintPaths toolpath={toolpath} deposited={tick.deposited} />}
      </VoronMachine>

      {showFinished && (
        <Suspense fallback={null}>
          <FinishedObject
            modelUrl={modelUrl}
            bedZ={tick.bedZ}
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
