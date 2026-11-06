import { Html, TransformControls } from '@react-three/drei';
import { useLoader } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';

export function FinishedObject({
  modelUrl,
  bedZ,
  detached,
  mode,
  showLabel = true,
}: {
  modelUrl: string;
  bedZ: number;
  detached: boolean;
  mode: 'translate' | 'rotate' | 'scale';
  showLabel?: boolean;
}) {
  const geometry = useLoader(STLLoader, modelUrl);
  const group = useRef<THREE.Group>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => { setReady(Boolean(group.current)); }, []);
  const placement = useMemo(() => {
    const g = geometry.clone();
    g.computeBoundingBox();
    const box = g.boundingBox ?? new THREE.Box3();
    const center = new THREE.Vector3();
    box.getCenter(center);
    return {
      geometry: g,
      center,
      minZ: box.min.z,
    };
  }, [geometry]);

  const content = (
    <group ref={group} position={[0, 0, bedZ]} name="PRINTED_OBJECT">
      <mesh
        geometry={placement.geometry}
        position={[-placement.center.x, -placement.center.y, -placement.minZ]}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial color="#79f2c0" metalness={0.15} roughness={0.48} />
      </mesh>
      {showLabel && (
        <Html position={[0, 0, 28]} center distanceFactor={520} zIndexRange={[2, 0]}>
          <div className="scene-label printed-label">PRINTED OBJECT</div>
        </Html>
      )}
    </group>
  );

  if (!detached || !ready || !group.current) return content;
  return (
    <>
      {content}
      <TransformControls object={group.current} mode={mode} size={0.32} />
    </>
  );
}
