import { Center, OrbitControls, useGLTF } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';

function Model({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene.clone(true)} />;
}

export function AssetPreview({ url, label = '彩色 GLB 预览' }: { url: string; label?: string }) {
  return (
    <div className="asset-preview">
      <Canvas camera={{ position: [2.4, -2.8, 2.1], fov: 38, near: 0.01, far: 100 }} gl={{ antialias: true, preserveDrawingBuffer: true }}>
        <color attach="background" args={['#071018']} />
        <ambientLight intensity={1.4} />
        <directionalLight position={[3, -3, 5]} intensity={3} />
        <directionalLight position={[-4, 3, 2]} intensity={1.5} color="#9bd6ff" />
        <Suspense fallback={null}>
          <Center>
            <group scale={0.01}><Model url={url} /></group>
          </Center>
          <OrbitControls makeDefault enableDamping />
        </Suspense>
      </Canvas>
      <span>{label}</span>
    </div>
  );
}
