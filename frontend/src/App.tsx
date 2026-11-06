import { Canvas, useFrame } from '@react-three/fiber';
import { Center, ContactShadows, Grid, OrbitControls, useGLTF } from '@react-three/drei';
import { Suspense, useCallback, useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import * as THREE from 'three';

type Background = { id: string; label: string; color: string; grid: string; accent: string };
const BACKGROUNDS: Background[] = [
  { id: 'dark', label: 'Dark studio', color: '#0b1016', grid: '#25313d', accent: '#79f2c0' },
  { id: 'light', label: 'Light studio', color: '#e9eef2', grid: '#b8c5ce', accent: '#0f766e' },
  { id: 'blueprint', label: 'Blueprint', color: '#071b33', grid: '#184a7a', accent: '#67c7ff' },
];

type ModelStats = { name: string; meshes: number; triangles: number; size: [number, number, number] };

function Model({ url, spin, onStats }: { url: string; spin: boolean; onStats: (s: ModelStats) => void }) {
  const gltf = useGLTF(url, true);
  const group = useRef<THREE.Group>(null);

  const stats = useMemo(() => {
    let meshes = 0;
    let triangles = 0;
    let meshName = '';
    gltf.scene.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        meshes += 1;
        if (!meshName) meshName = obj.name;
        const geometry = (obj as THREE.Mesh).geometry as THREE.BufferGeometry;
        triangles += geometry.index ? geometry.index.count / 3 : (geometry.attributes.position?.count ?? 0) / 3;
      }
    });
    // glTF is Y-up; the print domain is Z-up. Keep the source scene untouched on disk
    // but present it upright and report the original 60 x 34 x 2 mm envelope.
    gltf.scene.rotation.x = -Math.PI / 2;
    gltf.scene.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const size = new THREE.Vector3();
    box.getSize(size);
    return {
      name: meshName || (gltf.scene.name !== 'Scene' ? gltf.scene.name : '') || url.split('/').pop() || 'model',
      meshes,
      triangles: Math.round(triangles),
      size: [size.x, size.y, size.z] as [number, number, number],
    };
  }, [gltf.scene, url]);

  useEffect(() => onStats(stats), [stats, onStats]);
  useFrame((_, delta) => {
    if (spin && group.current) group.current.rotation.y += delta * 0.35;
  });

  return (
    <Center>
      <group ref={group}>
        <primitive object={gltf.scene} />
      </group>
    </Center>
  );
}

export default function App() {
  const [background, setBackground] = useState<Background>(BACKGROUNDS[0]);
  const [spin, setSpin] = useState(true);
  const [modelUrl, setModelUrl] = useState('/models/filament_card.glb');
  const [fileName, setFileName] = useState('filament_card.glb');
  const [stats, setStats] = useState<ModelStats | null>(null);
  const [dragging, setDragging] = useState(false);
  const [notice, setNotice] = useState('');

  const handleStats = useCallback((next: ModelStats) => setStats(next), []);

  const handleDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (!file) return;
    if (!/\.(glb|gltf)$/i.test(file.name)) {
      setNotice('Drop a .glb or .gltf file (STL drop is intentionally not enabled in this test).');
      return;
    }
    const next = URL.createObjectURL(file);
    setModelUrl(next);
    setFileName(file.name);
    setNotice(`Loaded ${file.name}`);
  };

  return (
    <div className="app" data-testid="printverse-app">
      <header className="topbar">
        <div>
          <div className="eyebrow">PRINTVERSE · DIGITAL TWIN BOOTSTRAP</div>
          <h1>Voron 2.4r2 · 300 mm</h1>
        </div>
        <div className="status">
          <span className="dot" />
          <span>LOCAL TEST SCENE</span>
        </div>
      </header>

      <main
        className={`viewport ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <Canvas
          shadows
          dpr={[1, 2]}
          camera={{ position: [78, 58, 82], fov: 42, near: 0.1, far: 2000 }}
          gl={{ antialias: true, preserveDrawingBuffer: true }}
          data-testid="three-canvas"
        >
          <color attach="background" args={[background.color]} />
          <fog attach="fog" args={[background.color, 220, 520]} />
          <ambientLight intensity={0.8} />
          <directionalLight position={[80, 120, 60]} intensity={2.2} castShadow shadow-mapSize={[1024, 1024]} />
          <directionalLight position={[-90, 40, -50]} intensity={0.7} color="#9bd7ff" />
          <Suspense fallback={null}>
            <Model url={modelUrl} spin={spin} onStats={handleStats} />
          </Suspense>
          <Grid
            position={[0, -1.2, 0]}
            args={[220, 220]}
            cellSize={10}
            cellThickness={0.6}
            cellColor={background.grid}
            sectionSize={50}
            sectionThickness={1.1}
            sectionColor={background.accent}
            fadeDistance={300}
            fadeStrength={1}
            infiniteGrid
          />
          <ContactShadows position={[0, -1.1, 0]} opacity={0.45} scale={140} blur={2.6} far={80} />
          <OrbitControls makeDefault enablePan enableZoom enableRotate rotateSpeed={0.8} zoomSpeed={0.9} />
        </Canvas>

        <aside className="panel">
          <div className="panel-label">OBJECT</div>
          <div className="object-name" data-testid="object-name">{stats?.name || fileName}</div>
          <div className="mono small">{fileName}</div>
          <div className="metrics">
            <div><span>Meshes</span><b>{stats?.meshes ?? '—'}</b></div>
            <div><span>Triangles</span><b>{stats?.triangles.toLocaleString() ?? '—'}</b></div>
            <div><span>Size (mm)</span><b>{stats ? stats.size.map((n) => n.toFixed(1)).join(' × ') : '—'}</b></div>
          </div>
          <div className="panel-label">BACKGROUND</div>
          <div className="row">
            {BACKGROUNDS.map((item) => (
              <button
                key={item.id}
                className={background.id === item.id ? 'active' : ''}
                onClick={() => setBackground(item)}
                data-testid={`bg-${item.id}`}
              >
                {item.label}
              </button>
            ))}
          </div>
          <label className="toggle">
            <input type="checkbox" checked={spin} onChange={() => setSpin((v) => !v)} data-testid="spin-toggle" />
            <span>Auto-rotate</span>
          </label>
          <div className="hint">Drag to orbit · wheel to zoom · right-drag to pan · drop a GLB to replace</div>
          {notice && <div className="notice">{notice}</div>}
        </aside>

        <div className="legend">
          <span>BOOTSTRAP VERIFICATION</span>
          <span>Three.js · React Three Fiber · Drei</span>
        </div>
      </main>
    </div>
  );
}
