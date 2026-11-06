import { useCallback, useEffect, useRef, useState } from 'react';
import type { CollectionItem, Job, PrintTick, Toolpath, Wallet } from './types';
import {
  addToCollection,
  assetUrl,
  cancelJob,
  completeJob,
  getCollection,
  getWallet,
  loadDemo,
  loadToolpath,
  uploadStl,
} from './lib/api';
import { PrintScene } from './components/PrintScene';

type Status = 'idle' | 'slicing' | 'ready' | 'printing' | 'paused' | 'completed' | 'detached' | 'error';
const INITIAL_TICK: PrintTick = {
  time: 0, progress: 0, layer: 0, toolhead: { x: 0, y: 0 }, bedZ: 300, deposited: 0, mass_g: 0,
};
const DEMO_JOB: Job = {
  id: 'demo', name: 'cube.stl', status: 'ready', mass_g: 3.978, layers: 100,
  time_s: 1192, free_print: true, reserved_g: 0, warnings: null,
  toolpath_url: '/demo/cube.toolpath.json', model_url: '/demo/cube.stl', gcode_url: '/demo/cube.gcode',
};

function humanTime(seconds: number | null | undefined): string {
  if (!seconds) return '—';
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return m ? `${m}m ${s}s` : `${s}s`;
}

function statusLabel(status: Status): string {
  return ({
    idle: 'AWAITING STL', slicing: 'SLICING', ready: 'READY', printing: 'PRINTING',
    paused: 'PAUSED', completed: 'COMPLETE', detached: 'DETACHED', error: 'ERROR',
  } as Record<Status, string>)[status];
}

export default function App() {
  const [status, setStatus] = useState<Status>('idle');
  const [job, setJob] = useState<Job | null>(null);
  const [toolpath, setToolpath] = useState<Toolpath | null>(null);
  const [modelUrl, setModelUrl] = useState('/demo/cube.stl');
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [collection, setCollection] = useState<CollectionItem[]>([]);
  const [tick, setTick] = useState<PrintTick>(INITIAL_TICK);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(120);
  const [resetKey, setResetKey] = useState(0);
  const [showLabels, setShowLabels] = useState(false);
  const [transformMode, setTransformMode] = useState<'translate' | 'rotate' | 'scale'>('translate');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const [collectionOpen, setCollectionOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const refreshAccount = useCallback(async () => {
    try {
      const w = await getWallet();
      setWallet(w);
      const c = await getCollection();
      setCollection(c.items);
    } catch {
      /* demo can run while API is offline; upload/collection require it */
    }
  }, []);

  useEffect(() => {
    void refreshAccount();
    void loadDemo()
      .then(({ toolpath: tp, modelUrl: url }) => {
        setToolpath(tp);
        setModelUrl(url);
        setJob(DEMO_JOB);
        setStatus('ready');
        setTick(INITIAL_TICK);
      })
      .catch(() => setNotice('Demo toolpath missing; upload an STL to begin.'));
  }, [refreshAccount]);

  const resetToReady = useCallback(() => {
    setPlaying(false);
    setStatus(toolpath ? 'ready' : 'idle');
    setTick(INITIAL_TICK);
    setResetKey((n) => n + 1);
    setError('');
    setNotice('');
  }, [toolpath]);

  const handleUpload = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.stl')) {
      setError('Please choose a .stl file.');
      return;
    }
    setError('');
    setNotice('');
    setStatus('slicing');
    setPlaying(false);
    try {
      const result = await uploadStl(file);
      const tp = await loadToolpath(result.toolpath_url);
      setJob(result);
      setToolpath(tp);
      setModelUrl(assetUrl(result.model_url));
      setWallet(result.wallet);
      setTick(INITIAL_TICK);
      setStatus('ready');
      setResetKey((n) => n + 1);
      setNotice(`Sliced ${file.name}: ${result.layers} layers, ${result.mass_g.toFixed(3)} g`);
    } catch (e) {
      setStatus('error');
      setError(e instanceof Error ? e.message : 'Slicing failed');
    }
  }, []);

  const start = useCallback(() => {
    if (!toolpath) return;
    if (status === 'completed' || status === 'detached') {
      setTick(INITIAL_TICK);
      setResetKey((n) => n + 1);
    }
    setError('');
    setStatus('printing');
    setPlaying(true);
  }, [status, toolpath]);

  const pause = useCallback(() => {
    setPlaying(false);
    setStatus('paused');
  }, []);

  const cancel = useCallback(async () => {
    setPlaying(false);
    if (job && job.id !== 'demo') {
      try {
        const result = await cancelJob(job.id);
        setWallet(result.wallet);
      } catch {
        /* keep UI responsive */
      }
    }
    resetToReady();
    setNotice('Print cancelled; reservation released.');
  }, [job, resetToReady]);

  const handleComplete = useCallback(async () => {
    setPlaying(false);
    setStatus('completed');
    setTick((t) => ({ ...t, progress: 1, deposited: 999999, mass_g: t.mass_g }));
    if (job && job.id !== 'demo') {
      try {
        const result = await completeJob(job.id);
        setWallet(result.wallet);
        setNotice(`Print complete: ${result.mass_g.toFixed(3)} g committed.`);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Could not commit job');
      }
    } else {
      setNotice('Demo print complete. Upload an STL to use the virtual ledger.');
    }
  }, [job]);

  const detach = useCallback(() => {
    setStatus('detached');
    setNotice('Object released from the bed. Drag the gizmo to move / rotate / scale.');
  }, []);

  const favorite = useCallback(async () => {
    if (!job) {
      setError('No print to collect.');
      return;
    }
    if (job.id === 'demo') {
      const local: CollectionItem = {
        id: Date.now(), user_id: 'demo', job_id: 'demo', name: job.name,
        mass_mg: Math.round(job.mass_g * 1000), model_path: '/demo/cube.stl',
        created_at: new Date().toISOString(),
      };
      setCollection((c) => [local, ...c.filter((i) => i.job_id !== 'demo')]);
      setNotice('Demo cube added to local collection.');
      setCollectionOpen(true);
      return;
    }
    try {
      const result = await addToCollection(job.id);
      setWallet(result.wallet);
      const c = await getCollection();
      setCollection(c.items);
      setNotice('Added to your 3D collection.');
      setCollectionOpen(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Collection failed');
    }
  }, [job]);

  const layers = toolpath?.meta.layers ?? job?.layers ?? 0;
  const modelMass = job?.mass_g ?? toolpath?.meta.mass_g ?? 0;
  const progressPct = Math.round(tick.progress * 100);
  const layerNow = Math.max(0, Math.min(layers, tick.layer));
  const canStart = Boolean(toolpath) && status !== 'slicing' && status !== 'printing';
  const isFinished = status === 'completed' || status === 'detached';

  return (
    <div className="app" data-testid="printverse-app">
      <header className="topbar">
        <div className="brandblock">
          <div className="eyebrow">PRINTVERSE · PHASE 02 · VIRTUAL PRINT LOOP</div>
          <h1>Voron 2.4r2 <span>/ 300 mm</span></h1>
        </div>
        <div className="machine-facts">
          <div><b>300 × 300</b><span>X/Y travel</span></div>
          <div><b>280 / 275</b><span>Z travel / slicer</span></div>
          <div className={`status-chip ${status}`} data-testid="print-status">
            <i /> {statusLabel(status)}
          </div>
        </div>
        <div className="wallet-pill" data-testid="wallet-balance">
          <span>VIRTUAL FILAMENT</span>
          <b>{wallet ? `${wallet.balance_g.toFixed(2)} g` : '—'}</b>
          <em>{wallet?.first_print_available ? 'first print free' : 'first print used'}</em>
        </div>
      </header>

      <main className="workspace">
        <section
          className={`stage ${dragging ? 'dragging' : ''}`}
          data-testid="scene-wrap"
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files?.[0];
            if (file) void handleUpload(file);
          }}
        >
          <PrintScene
            toolpath={toolpath}
            modelUrl={modelUrl}
            status={status}
            playing={playing}
            speed={speed}
            showLabels={showLabels}
            transformMode={transformMode}
            detached={status === 'detached'}
            resetKey={resetKey}
            onTick={setTick}
            onComplete={handleComplete}
          />

          <div className="stage-top">
            <div className="hud-block">
              <span className="hud-label">MACHINE</span>
              <b>V2.4r2 / 300</b>
              <small>CoreXY · 4-point Z</small>
            </div>
            <div className="hud-block right">
              <span className="hud-label">TOOLHEAD</span>
              <b className="mono">
                X {tick.toolhead.x.toFixed(1)} · Y {tick.toolhead.y.toFixed(1)} · Z {(300 - tick.bedZ).toFixed(1)}
              </b>
              <small>bed Z {tick.bedZ.toFixed(1)} mm</small>
            </div>
          </div>

          <div className="stage-bottom">
            <div className="legend">
              <span><i className="swatch outer" /> outer wall</span>
              <span><i className="swatch inner" /> inner wall</span>
              <span><i className="swatch infill" /> infill</span>
              <span><i className="swatch top" /> top surface</span>
              <span><i className="swatch travel" /> travel</span>
            </div>
            <label className="toggle compact">
              <input type="checkbox" checked={showLabels} onChange={() => setShowLabels((v) => !v)} data-testid="labels-toggle" />
              <span>Assembly labels</span>
            </label>
          </div>

          {dragging && <div className="drop-overlay">DROP STL TO SLICE</div>}
        </section>

        <aside className="sidebar">
          <section className="card">
            <div className="card-head">
              <span className="step">01</span>
              <div><h2>Input STL</h2><p>Real OrcaSlicer slice, not a fake animation.</p></div>
            </div>
            <label className="dropzone" onDragOver={(e) => e.preventDefault()} onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files?.[0];
              if (f) void handleUpload(f);
            }}>
              <input
                ref={fileRef}
                type="file"
                accept=".stl"
                data-testid="upload-input"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) void handleUpload(f); }}
              />
              <span className="drop-icon">↥</span>
              <b>Choose or drop .stl</b>
              <small>20 × 20 × 20 mm cube recommended for the first run</small>
            </label>
            <div className="row gap">
              <button className="ghost" onClick={() => { void loadDemo().then(({ toolpath: tp, modelUrl: url }) => {
                setJob(DEMO_JOB); setToolpath(tp); setModelUrl(url); setStatus('ready'); setTick(INITIAL_TICK); setResetKey((n) => n + 1);
              }); }} data-testid="load-demo">Load demo cube</button>
              <button className="ghost" onClick={() => fileRef.current?.click()}>Browse files</button>
            </div>
            {status === 'slicing' && <div className="inline-progress"><i /> Slicing with OrcaSlicer…</div>}
            {error && <div className="error-box" data-testid="error">{error}</div>}
            {notice && <div className="notice-box">{notice}</div>}
          </section>

          <section className="card print-card">
            <div className="card-head">
              <span className="step">02</span>
              <div><h2>Print simulation</h2><p>{job?.name ?? 'No job loaded'}</p></div>
            </div>
            <div className="progress-wrap">
              <div className="progress-labels">
                <span><b data-testid="current-layer">{layerNow}</b> / {layers} layers</span>
                <b data-testid="progress-percent">{progressPct}%</b>
              </div>
              <div className="progress-track" data-testid="progress"><i style={{ width: `${progressPct}%` }} /></div>
              <div className="progress-meta">
                <span>{humanTime(tick.time)} / {humanTime(toolpath?.meta.time_s ?? job?.time_s)}</span>
                <span>{tick.mass_g.toFixed(3)} g deposited</span>
              </div>
            </div>
            <div className="metric-grid">
              <div><span>MODEL MASS</span><b>{modelMass.toFixed(3)} g</b></div>
              <div><span>LAYERS</span><b>{layers}</b></div>
              <div><span>FILAMENT</span><b>{((toolpath?.meta.filament_mm ?? 0) / 1000).toFixed(2)} m</b></div>
              <div><span>EST. TIME</span><b>{humanTime(toolpath?.meta.time_s ?? job?.time_s)}</b></div>
            </div>
            <div className="speed-row">
              <span>SPEED</span>
              {[30, 60, 120, 300].map((s) => (
                <button key={s} className={speed === s ? 'active' : ''} onClick={() => setSpeed(s)} data-testid={`speed-${s}`}>{s}×</button>
              ))}
            </div>
            <div className="row actions">
              {!playing && status !== 'completed' && status !== 'detached' && (
                <button className="primary" onClick={start} disabled={!canStart} data-testid="start-print">
                  {status === 'paused' ? 'Resume print' : 'Start print'}
                </button>
              )}
              {playing && <button className="primary" onClick={pause} data-testid="pause-print">Pause</button>}
              {(status === 'printing' || status === 'paused' || status === 'ready') && (
                <button className="ghost danger" onClick={() => void cancel()} data-testid="cancel-print">Cancel</button>
              )}
              {(status === 'completed' || status === 'detached') && (
                <button className="ghost" onClick={resetToReady} data-testid="reset-print">New print</button>
              )}
            </div>
            {status === 'printing' && <div className="live-badge"><i /> G-CODE STREAM · CoreXY / Z synchronized</div>}
          </section>

          <section className="card finish-card">
            <div className="card-head">
              <span className="step">03</span>
              <div><h2>Finished object</h2><p>Release from the bed, then collect it.</p></div>
            </div>
            <div className="row actions">
              <button className="primary" onClick={detach} disabled={status !== 'completed'} data-testid="detach-object">Detach from bed</button>
              <button className="ghost" onClick={() => void favorite()} disabled={!isFinished} data-testid="favorite-print">☆ Add to collection</button>
            </div>
            <div className="mode-row">
              <span>GIZMO</span>
              {(['translate', 'rotate', 'scale'] as const).map((m) => (
                <button key={m} className={transformMode === m ? 'active' : ''} onClick={() => setTransformMode(m)} data-testid={`mode-${m}`}>{m}</button>
              ))}
            </div>
            {status === 'detached' && <div className="notice-box">Drag the colored gizmo. Orbit is disabled while dragging.</div>}
          </section>

          <section className="card collection-card">
            <button className="collection-head" onClick={() => setCollectionOpen((v) => !v)}>
              <span className="step">04</span>
              <div><h2>3D collection</h2><p>{collection.length} object{collection.length === 1 ? '' : 's'}</p></div>
              <span className="chev">{collectionOpen ? '−' : '+'}</span>
            </button>
            {collectionOpen && (
              <div className="collection-list" data-testid="collection-list">
                {collection.length === 0 && <div className="empty">No saved prints yet. Finish, detach, and add one.</div>}
                {collection.map((item) => (
                  <div className="collection-item" key={`${item.id}-${item.job_id}`} data-testid="collection-item">
                    <div className="mini-cube">◈</div>
                    <div><b>{item.name}</b><small>{(item.mass_mg / 1000).toFixed(3)} g · {new Date(item.created_at).toLocaleDateString()}</small></div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="ledger-card">
            <div><span>VIRTUAL WALLET</span><b>{wallet ? `${wallet.balance_g.toFixed(2)} g` : 'offline'}</b></div>
            <div><span>FIRST PRINT</span><b>{wallet?.first_print_available ? 'FREE' : 'USED'}</b></div>
            <div><span>RESERVED</span><b>{job ? `${job.reserved_g.toFixed(3)} g` : '—'}</b></div>
            <p>Virtual-only accounting. No payment or real spool is touched.</p>
          </section>
        </aside>
      </main>
    </div>
  );
}
