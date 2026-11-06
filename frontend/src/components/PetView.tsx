import { Center, OrbitControls, useGLTF } from '@react-three/drei';
import { Canvas, useFrame } from '@react-three/fiber';
import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { assetUrl, getCollection } from '../lib/api';
import type { CollectionItem } from '../types';

function PetModel({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  const object = useMemo(() => scene.clone(true), [scene]);
  const group = useRef<THREE.Group>(null);
  useFrame((_, delta) => {
    if (group.current) group.current.rotation.z += delta * 0.12;
  });
  return (
    <group ref={group} rotation={[0.08, -0.28, 0]}>
      <primitive object={object} />
    </group>
  );
}

export function PetView() {
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [selected, setSelected] = useState<CollectionItem | null>(null);
  const [error, setError] = useState('');
  const [drag, setDrag] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    document.body.classList.add('pet-body');
    document.documentElement.classList.add('pet-body');
    void getCollection()
      .then((r) => {
        setItems(r.items);
        setSelected(r.items.find((i) => i.model_path.toLowerCase().endsWith('.glb')) ?? r.items[0] ?? null);
      })
      .catch((e) => setError(String(e)));
    return () => { document.body.classList.remove('pet-body'); document.documentElement.classList.remove('pet-body'); };
  }, []);

  const url = selected?.model_path
    ? assetUrl(selected.model_path.startsWith('/') ? selected.model_path : `/${selected.model_path}`)
    : null;
  const isGlb = Boolean(url && url.toLowerCase().includes('.glb'));

  return (
    <div
      className="pet-shell"
      onPointerDown={(e) => setDrag({ x: e.clientX, y: e.clientY })}
      onPointerMove={(e) => {
        if (!drag) return;
        const dx = e.clientX - drag.x;
        const dy = e.clientY - drag.y;
        const w = window as unknown as { __TAURI__?: { window?: { startDragging?: () => void } }; __PV_PET_MOVE?: (dx: number, dy: number) => void };
        w.__PV_PET_MOVE?.(dx, dy);
        setDrag({ x: e.clientX, y: e.clientY });
      }}
      onPointerUp={() => setDrag(null)}
    >
      <div className="pet-stage" data-testid="pet-stage">
        {url && isGlb ? (
          <Canvas camera={{ position: [2.2, -2.6, 1.8], fov: 36 }} gl={{ alpha: true, antialias: true, preserveDrawingBuffer: true }} style={{ background: 'transparent' }}>
            <ambientLight intensity={1.8} />
            <directionalLight position={[3, -3, 5]} intensity={3.2} />
            <directionalLight position={[-4, 3, 2]} intensity={1.4} color="#a5d8ff" />
            <Suspense fallback={null}>
              <Center>
                <group scale={0.01}><PetModel url={url} /></group>
              </Center>
              <OrbitControls makeDefault enablePan={false} enableZoom />
            </Suspense>
          </Canvas>
        ) : (
          <div className="pet-empty">
            <b>{items.length ? '该作品没有彩色 GLB' : '还没有桌面宠物'}</b>
            <p>{items.length ? '请完成一次彩色图片转 3D 打印并收藏。' : '先完成一件作品，再把它放到桌面。'}</p>
          </div>
        )}
      </div>
      <div className="pet-bar">
        <span>桌面宠物</span>
        <select value={selected?.id ?? ''} onChange={(e) => setSelected(items.find((i) => String(i.id) === e.target.value) ?? null)}>
          {items.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
        </select>
        <span style={{ color: '#7e97a6', fontSize: 13 }}>拖动移动 · 滚轮缩放</span>
        <button className="ghost" onClick={() => window.close()}>关闭</button>
      </div>
      {error && <div className="error-box">{error}</div>}
    </div>
  );
}
