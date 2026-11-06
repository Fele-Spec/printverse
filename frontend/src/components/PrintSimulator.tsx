import { useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import type { PrintTick, Toolpath } from '../types';
import { BED_BASE_Z } from './VoronMachine';

type TimedMove = {
  x0: number; y0: number; x1: number; y1: number; z: number;
  dt: number; t0: number; t1: number; layer: number;
};

function upperBound(times: number[], value: number): number {
  let lo = 0;
  let hi = times.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (times[mid] <= value) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

export function PrintSimulator({
  toolpath,
  playing,
  speed,
  resetKey,
  onTick,
  onComplete,
}: {
  toolpath: Toolpath | null;
  playing: boolean;
  speed: number;
  resetKey: number;
  onTick: (tick: PrintTick) => void;
  onComplete: () => void;
}) {
  const timeRef = useRef(0);
  const doneRef = useRef(false);
  const lastEmit = useRef(0);
  const tickRef = useRef(onTick);
  const completeRef = useRef(onComplete);
  tickRef.current = onTick;
  completeRef.current = onComplete;

  const data = useMemo(() => {
    if (!toolpath || toolpath.moves.length === 0) return null;
    let t = 0;
    const timeline: TimedMove[] = [];
    const depositTimes: number[] = [];
    const depositMass: number[] = [];
    const area = Math.PI * (toolpath.meta.diameter_mm / 2) ** 2;
    let mass = 0;
    for (const m of toolpath.moves) {
      const [x0, y0, x1, y1, z, de, dt, , travel, layer] = m;
      const t0 = t;
      t += dt;
      timeline.push({ x0, y0, x1, y1, z, dt, t0, t1: t, layer });
      if (!travel && de > 0) {
        depositTimes.push(t);
        mass += de * area * toolpath.meta.density_g_cm3 / 1000;
        depositMass.push(mass);
      }
    }
    return {
      timeline,
      moveEndTimes: timeline.map((m) => m.t1),
      depositTimes,
      depositMass,
      total: t,
      layers: toolpath.meta.layers,
    };
  }, [toolpath]);

  useEffect(() => {
    timeRef.current = 0;
    doneRef.current = false;
    lastEmit.current = 0;
  }, [resetKey, toolpath]);

  useFrame((_, delta) => {
    if (!data || !playing || doneRef.current) return;
    timeRef.current = Math.min(data.total, timeRef.current + delta * speed);
    const time = timeRef.current;
    const idx = Math.min(data.timeline.length - 1, upperBound(data.moveEndTimes, time));
    const m = data.timeline[idx];
    const frac = m.dt > 0 ? Math.min(1, Math.max(0, (time - m.t0) / m.dt)) : 1;
    const deposited = upperBound(data.depositTimes, time);
    const tick: PrintTick = {
      time,
      progress: data.total > 0 ? time / data.total : 0,
      layer: m.layer,
      toolhead: {
        x: m.x0 + (m.x1 - m.x0) * frac - 150,
        y: m.y0 + (m.y1 - m.y0) * frac - 150,
      },
      bedZ: BED_BASE_Z - Math.max(0, m.z),
      deposited,
      mass_g: deposited > 0 ? data.depositMass[deposited - 1] : 0,
    };
    const now = performance.now();
    if (now - lastEmit.current > 45 || time >= data.total) {
      tickRef.current(tick);
      lastEmit.current = now;
    }
    if (time >= data.total && !doneRef.current) {
      doneRef.current = true;
      completeRef.current();
    }
  });

  return null;
}
