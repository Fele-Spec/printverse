import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { Toolpath } from '../types';
import { colorForType } from '../lib/palette';

const BED_BASE_Z = 300;

function buildGeometry(toolpath: Toolpath) {
  const positions: number[] = [];
  const colors: number[] = [];
  const depositTimes: number[] = [];
  const depositMass: number[] = [];
  let t = 0;
  let mass = 0;
  const area = Math.PI * (toolpath.meta.diameter_mm / 2) ** 2;
  for (const move of toolpath.moves) {
    const [x0, y0, x1, y1, z, de, dt, typeIndex, travel] = move;
    t += dt;
    if (!travel && de > 0) {
      const zz = Math.max(0, z) + 0.18;
      positions.push(x0 - 150, y0 - 150, zz, x1 - 150, y1 - 150, zz);
      const c = new THREE.Color(colorForType(toolpath.meta.types[typeIndex] ?? 'Unknown'));
      colors.push(c.r, c.g, c.b, c.r, c.g, c.b);
      depositTimes.push(t);
      mass += de * area * toolpath.meta.density_g_cm3 / 1000;
      depositMass.push(mass);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.computeBoundingSphere();
  return { geometry, depositTimes, depositMass, count: depositTimes.length };
}

export function PrintPaths({ toolpath, deposited }: { toolpath: Toolpath | null; deposited: number }) {
  const built = useMemo(() => (toolpath ? buildGeometry(toolpath) : null), [toolpath]);
  useEffect(() => {
    if (!built) return;
    built.geometry.setDrawRange(0, Math.max(0, Math.min(deposited, built.count)) * 2);
  }, [built, deposited]);
  if (!built) return null;
  return (
    <lineSegments geometry={built.geometry} frustumCulled={false} renderOrder={2}>
      <lineBasicMaterial vertexColors transparent opacity={0.95} depthWrite={false} />
    </lineSegments>
  );
}

export { BED_BASE_Z };
