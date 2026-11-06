import { Html, TransformControls, useGLTF } from '@react-three/drei';
import { useLoader } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';

type FinishedProps = {
  modelUrl: string;
  colorUrl?: string | null;
  bedZ: number;
  detached: boolean;
  mode: 'translate' | 'rotate' | 'scale';
  showLabel?: boolean;
};

function StlContent({ geometry, center, minZ }: { geometry: THREE.BufferGeometry; center: THREE.Vector3; minZ: number }) {
  return (
    <mesh geometry={geometry} position={[-center.x, -center.y, -minZ]} castShadow receiveShadow>
      <meshStandardMaterial color="#79f2c0" metalness={0.15} roughness={0.48} />
    </mesh>
  );
}

function GlbContent({ colorUrl }: { colorUrl: string }) {
  const { scene } = useGLTF(colorUrl);
  const object = useMemo(() => scene.clone(true), [scene]);
  const placement = useMemo(() => {
    const box = new THREE.Box3().setFromObject(object);
    const center = new THREE.Vector3();
    box.getCenter(center);
    return { center, minZ: box.min.z };
  }, [object]);
  return <primitive object={object} position={[-placement.center.x, -placement.center.y, -placement.minZ]} />;
}

export function FinishedObject({ modelUrl, colorUrl, bedZ, detached, mode, showLabel = true }: FinishedProps) {
  const group = useRef<THREE.Group>(null);
  const [ready, setReady] = useState(false);
  const geometry = useLoader(STLLoader, modelUrl);
  const placement = useMemo(() => {
    const box = new THREE.Box3().setFromBufferAttribute(geometry.getAttribute('position') as THREE.BufferAttribute);
    const center = new THREE.Vector3();
    box.getCenter(center);
    return { center, minZ: box.min.z };
  }, [geometry]);
  useEffect(() => { setReady(Boolean(group.current)); }, []);

  if (colorUrl) {
    return (
      <>
        <group ref={group} position={[0, 0, bedZ]} name="PRINTED_OBJECT_COLOR">
          <GlbContent colorUrl={colorUrl} />
          {showLabel && (
            <Html position={[0, 0, 28]} center distanceFactor={520} zIndexRange={[2, 0]}>
              <div className="scene-label printed-label">彩色成品 · GLB</div>
            </Html>
          )}
        </group>
        {detached && ready && group.current && <TransformControls object={group.current} mode={mode} size={0.32} />}
      </>
    );
  }

  const content = (
    <group ref={group} position={[0, 0, bedZ]} name="PRINTED_OBJECT">
      <StlContent geometry={geometry} center={placement.center} minZ={placement.minZ} />
      {showLabel && (
        <Html position={[0, 0, 28]} center distanceFactor={520} zIndexRange={[2, 0]}>
          <div className="scene-label printed-label">打印成品</div>
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
