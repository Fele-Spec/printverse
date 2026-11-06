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
import { SceneControls, type PanelMode, type ViewPreset } from './components/SceneControls';
import { PartInspector } from './components/PartInspector';
import { Image3DPanel } from './components/Image3DPanel';

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
    idle: '等待导入模型', slicing: '切片中', ready: '准备打印', printing: '打印中',
    paused: '已暂停', completed: '打印完成', detached: '已取下', error: '出错',
  } as Record<Status, string>)[status];
}

export default function App() {
  const [status, setStatus] = useState<Status>('idle');
  const [job, setJob] = useState<Job | null>(null);
  const [toolpath, setToolpath] = useState<Toolpath | null>(null);
  const [modelUrl, setModelUrl] = useState('/demo/cube.stl');
  const [colorUrl, setColorUrl] = useState<string | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [collection, setCollection] = useState<CollectionItem[]>([]);
  const [tick, setTick] = useState<PrintTick>(INITIAL_TICK);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(120);
  const [resetKey, setResetKey] = useState(0);
  const [showLabels, setShowLabels] = useState(false);
  const [viewPreset, setViewPreset] = useState<ViewPreset>('product');
  const [orthographic, setOrthographic] = useState(false);
  const [panelMode, setPanelMode] = useState<PanelMode>('glass');
  const [explode, setExplode] = useState(0);
  const [cadMode, setCadMode] = useState(() => !new URLSearchParams(window.location.search).has('sim'));
  const [showFasteners, setShowFasteners] = useState(false);
  const [selectedPart, setSelectedPart] = useState<{ name: string; module: string } | null>(null);
  const [visibleModules, setVisibleModules] = useState<Record<string, boolean>>({
    FRAME: true, ENCLOSURE: true, XY_GANTRY: true, Z_DRIVE: true,
    TOOLHEAD: true, BUILD_PLATFORM: true, ELECTRONICS: true, WIRING: true,
  });
  const [transformMode, setTransformMode] = useState<'translate' | 'rotate' | 'scale'>('translate');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const [collectionOpen, setCollectionOpen] = useState(false);
  const [image3DOpen, setImage3DOpen] = useState(false);
  const [advanced, setAdvanced] = useState(false);
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
        setColorUrl(null);
        setJob(DEMO_JOB);
        setStatus('ready');
        setTick(INITIAL_TICK);
      })
      .catch(() => setNotice('演示路径缺失；请导入 STL/3MF 开始。'));
  }, [refreshAccount]);

  const resetToReady = useCallback(() => {
    setPlaying(false);
    setStatus(toolpath ? 'ready' : 'idle');
    setTick(INITIAL_TICK);
    setResetKey((n) => n + 1);
    setError('');
    setNotice('');
  }, [toolpath]);

  const handleUpload = useCallback(async (file: File, sourceColorUrl?: string | null) => {
    if (!/\.(stl|3mf|obj|glb|gltf|step|stp|dxf)$/i.test(file.name)) {
      setError('请选择 STL / 3MF / OBJ / GLB / STEP / DXF 文件。');
      return;
    }
    setError('');
    setNotice('');
    setStatus('slicing');
    setPlaying(false);
    try {
      const result = await uploadStl(file, sourceColorUrl);
      const tp = await loadToolpath(result.toolpath_url);
      setJob(result);
      setToolpath(tp);
      setModelUrl(assetUrl(result.model_url));
      setColorUrl(result.color_url ? assetUrl(result.color_url) : sourceColorUrl ?? null);
      setWallet(result.wallet);
      setTick(INITIAL_TICK);
      setStatus('ready');
      setResetKey((n) => n + 1);
      setNotice(`切片完成 ${file.name}：${result.layers} 层，${result.mass_g.toFixed(3)} g`);
    } catch (e) {
      setStatus('error');
      setError(e instanceof Error ? e.message : '切片失败');
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
    setNotice('打印已取消，预扣耗材已退回。');
  }, [job, resetToReady]);

  const handleComplete = useCallback(async () => {
    setPlaying(false);
    setStatus('completed');
    setTick((t) => ({ ...t, progress: 1, deposited: 999999, mass_g: t.mass_g }));
    if (job && job.id !== 'demo') {
      try {
        const result = await completeJob(job.id);
        setWallet(result.wallet);
        setNotice(`打印完成：已结算 ${result.mass_g.toFixed(3)} g 虚拟耗材。`);
      } catch (e) {
        setError(e instanceof Error ? e.message : '无法结算打印任务');
      }
    } else {
      setNotice('演示打印完成。导入 STL 可使用虚拟耗材账本。');
    }
  }, [job]);

  const detach = useCallback(() => {
    setStatus('detached');
    setNotice('成品已从热床取下。拖动控制轴可移动、旋转或缩放。');
  }, []);

  const favorite = useCallback(async () => {
    if (!job) {
      setError('没有可收藏的打印成品。');
      return;
    }
    if (job.id === 'demo') {
      const local: CollectionItem = {
        id: Date.now(), user_id: 'demo', job_id: 'demo', name: job.name,
        mass_mg: Math.round(job.mass_g * 1000), model_path: '/demo/cube.stl',
        created_at: new Date().toISOString(),
      };
      setCollection((c) => [local, ...c.filter((i) => i.job_id !== 'demo')]);
      setNotice('演示立方体已加入本地收藏。');
      setCollectionOpen(true);
      return;
    }
    try {
      const result = await addToCollection(job.id);
      setWallet(result.wallet);
      const c = await getCollection();
      setCollection(c.items);
      setNotice('已加入 3D 收藏。');
      setCollectionOpen(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : '收藏失败');
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
      {image3DOpen && (
        <Image3DPanel
          onClose={() => setImage3DOpen(false)}
          onUseModel={async (stlUrl, generatedColorUrl) => {
            try {
              const res = await fetch(stlUrl);
              const blob = await res.blob();
              const file = new File([blob], 'image3d-generated.stl', { type: 'model/stl' });
              setImage3DOpen(false);
              await handleUpload(file, generatedColorUrl);
            } catch (e) {
              setError(e instanceof Error ? e.message : '生成的 STL 无法加载');
            }
          }}
        />
      )}
      <header className="topbar">
        <div className="brandblock">
          <div className="eyebrow">PRINTVERSE · 精密打印机数字孪生</div>
          <h1>Voron 2.4r2 <span>/ 300 mm</span></h1>
        </div>
        <div className="machine-facts">
          <div><b>300 × 300</b><span>X/Y 行程</span></div>
          <div><b>280 / 275</b><span>Z 行程 / 切片高度</span></div>
          <div className={`status-chip ${status}`} data-testid="print-status">
            <i /> {statusLabel(status)}
          </div>
        </div>
        <button className="image3d-launch" onClick={() => setImage3DOpen(true)} data-testid="open-image3d">图片 → 3D</button>
        <button className={advanced ? 'ghost active' : 'ghost'} onClick={() => setAdvanced((v) => !v)} data-testid="advanced-toggle">{advanced ? '退出高级' : '高级模式'}</button>
        <div className="wallet-pill" data-testid="wallet-balance">
          <span>虚拟耗材{wallet?.role === 'admin' ? ' · 所有者' : ''}</span>
          <b>{wallet ? `${wallet.balance_g.toFixed(2)} g` : '—'}</b>
          <em>{wallet?.role === 'admin' ? '所有者 · 无限额度' : wallet?.first_print_available ? '首件免费' : '首件已使用'}</em>
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
            colorUrl={colorUrl}
            status={status}
            playing={playing}
            speed={speed}
            showLabels={showLabels}
            transformMode={transformMode}
            detached={status === 'detached'}
            resetKey={resetKey}
            viewPreset={viewPreset}
            orthographic={orthographic}
            panelMode={panelMode}
            explode={explode}
            visibleModules={visibleModules}
            cadMode={cadMode}
            showFasteners={showFasteners}
            selectedPartName={selectedPart?.name ?? null}
            onPartSelect={(name, module) => setSelectedPart({ name, module })}
            onTick={setTick}
            onComplete={handleComplete}
          />

          {advanced && <SceneControls
            view={viewPreset}
            onView={setViewPreset}
            panelMode={panelMode}
            onPanelMode={setPanelMode}
            orthographic={orthographic}
            onOrthographic={setOrthographic}
            explode={explode}
            onExplode={setExplode}
            modules={visibleModules}
            onToggleModule={(id) => setVisibleModules((m) => ({ ...m, [id]: m[id] === false }))}
            cadMode={cadMode}
            onCadMode={setCadMode}
            showFasteners={showFasteners}
            onShowFasteners={setShowFasteners}
          />}

          {advanced && <div className="stage-top">
            <div className="hud-block">
              <span className="hud-label">设备</span>
              <b>V2.4r2 / 300</b>
              <small>CoreXY · 4-point Z</small>
            </div>
            <div className="hud-block right">
              <span className="hud-label">打印头</span>
              <b className="mono">
                X {tick.toolhead.x.toFixed(1)} · Y {tick.toolhead.y.toFixed(1)} · Z {(300 - tick.bedZ).toFixed(1)}
              </b>
              <small>bed Z {tick.bedZ.toFixed(1)} mm</small>
            </div>
          </div>}

          {selectedPart && (
            <PartInspector
              partId={selectedPart.name}
              module={selectedPart.module}
              onClose={() => setSelectedPart(null)}
              onHide={(module) => setVisibleModules((m) => ({ ...m, [module]: false }))}
              onFocus={(module) => {
                setViewPreset(module === 'TOOLHEAD' ? 'toolhead' : module === 'BUILD_PLATFORM' ? 'interior' : 'interior');
                setSelectedPart(null);
              }}
            />
          )}

          {advanced && <div className="stage-bottom">
            <div className="legend">
              <span><i className="swatch outer" /> 外墙</span>
              <span><i className="swatch inner" /> 内墙</span>
              <span><i className="swatch infill" /> 填充</span>
              <span><i className="swatch top" /> 顶面</span>
              <span><i className="swatch travel" /> 空驶</span>
            </div>
            <label className="toggle compact">
              <input type="checkbox" checked={showLabels} onChange={() => setShowLabels((v) => !v)} data-testid="labels-toggle" />
              <span>装配标签</span>
            </label>
          </div>}

          {dragging && <div className="drop-overlay">松开以切片 STL</div>}
        </section>

        <aside className="sidebar">
          <section className="card">
            <div className="card-head">
              <span className="step">01</span>
              <div><h2>导入模型</h2><p>使用真实 OrcaSlicer 切片，不使用假动画。</p></div>
            </div>
            <label className="dropzone" onDragOver={(e) => e.preventDefault()} onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files?.[0];
              if (f) void handleUpload(f);
            }}>
              <input
                ref={fileRef}
                type="file"
                accept=".stl,.3mf,.obj,.glb,.gltf,.step,.stp,.dxf"
                data-testid="upload-input"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) void handleUpload(f); }}
              />
              <span className="drop-icon">↥</span>
              <b>选择或拖入 .stl / .3mf / .obj / .glb</b>
              <small>首次运行建议使用 20 × 20 × 20 mm 立方体</small>
            </label>
            <div className="row gap">
              <button className="ghost" onClick={() => { void loadDemo().then(({ toolpath: tp, modelUrl: url }) => {
                setJob(DEMO_JOB); setToolpath(tp); setModelUrl(url); setStatus('ready'); setTick(INITIAL_TICK); setResetKey((n) => n + 1);
              }); }} data-testid="load-demo">载入演示立方体</button>
              <button className="ghost" onClick={() => fileRef.current?.click()}>浏览文件</button>
            </div>
            {status === 'slicing' && <div className="inline-progress"><i /> 正在用 OrcaSlicer 切片…</div>}
            {error && <div className="error-box" data-testid="error">{error}</div>}
            {notice && <div className="notice-box">{notice}</div>}
          </section>

          <section className="card print-card">
            <div className="card-head">
              <span className="step">02</span>
              <div><h2>虚拟打印</h2><p>{job?.name ?? '尚未载入任务'}</p></div>
            </div>
            <div className="progress-wrap">
              <div className="progress-labels">
                <span><b data-testid="current-layer">{layerNow}</b> / {layers} 层</span>
                <b data-testid="progress-percent">{progressPct}%</b>
              </div>
              <div className="progress-track" data-testid="progress"><i style={{ width: `${progressPct}%` }} /></div>
              <div className="progress-meta">
                <span>{humanTime(tick.time)} / {humanTime(toolpath?.meta.time_s ?? job?.time_s)}</span>
                <span>已沉积 {tick.mass_g.toFixed(3)} g</span>
              </div>
            </div>
            <div className="metric-grid">
              <div><span>模型质量</span><b>{modelMass.toFixed(3)} g</b></div>
              <div><span>层数</span><b>{layers}</b></div>
              <div><span>耗材长度</span><b>{((toolpath?.meta.filament_mm ?? 0) / 1000).toFixed(2)} m</b></div>
              <div><span>预计时间</span><b>{humanTime(toolpath?.meta.time_s ?? job?.time_s)}</b></div>
            </div>
            <div className="speed-row">
              <span>倍速</span>
              {[30, 60, 120, 300].map((s) => (
                <button key={s} className={speed === s ? 'active' : ''} onClick={() => setSpeed(s)} data-testid={`speed-${s}`}>{s}×</button>
              ))}
            </div>
            <div className="row actions">
              {!playing && status !== 'completed' && status !== 'detached' && (
                <button className="primary" onClick={start} disabled={!canStart} data-testid="start-print">
                  {status === 'paused' ? '继续打印' : '开始打印'}
                </button>
              )}
              {playing && <button className="primary" onClick={pause} data-testid="pause-print">暂停</button>}
              {(status === 'printing' || status === 'paused' || status === 'ready') && (
                <button className="ghost danger" onClick={() => void cancel()} data-testid="cancel-print">取消</button>
              )}
              {(status === 'completed' || status === 'detached') && (
                <button className="ghost" onClick={resetToReady} data-testid="reset-print">新打印</button>
              )}
            </div>
            {status === 'printing' && <div className="live-badge"><i /> G-code 实时驱动 · CoreXY / Z 同步</div>}
          </section>

          <section className="card finish-card">
            <div className="card-head">
              <span className="step">03</span>
              <div><h2>彩色成品</h2><p>从热床取下后收藏或放到桌面。</p></div>
            </div>
            <div className="row actions">
              <button className="primary" onClick={detach} disabled={status !== 'completed'} data-testid="detach-object">从热床取下</button>
              <button className="ghost" onClick={() => void favorite()} disabled={!isFinished} data-testid="favorite-print">☆ 加入收藏</button>
              <button className="ghost" onClick={() => window.open('/?pet=1', 'printverse-pet', 'width=620,height=760')} disabled={!isFinished} data-testid="send-to-desktop">放到桌面</button>
            </div>
            <div className="mode-row">
              <span>控制轴</span>
              {(['translate', 'rotate', 'scale'] as const).map((m) => (
                <button key={m} className={transformMode === m ? 'active' : ''} onClick={() => setTransformMode(m)} data-testid={`mode-${m}`}>{m === 'translate' ? '移动' : m === 'rotate' ? '旋转' : '缩放'}</button>
              ))}
            </div>
            {status === 'detached' && <div className="notice-box">拖动彩色控制轴；拖动时轨道旋转暂停。</div>}
          </section>

          <section className="card collection-card">
            <button className="collection-head" onClick={() => setCollectionOpen((v) => !v)}>
              <span className="step">04</span>
              <div><h2>3D 收藏</h2><p>{collection.length} 件作品</p></div>
              <span className="chev">{collectionOpen ? '−' : '+'}</span>
            </button>
            {collectionOpen && (
              <div className="collection-list" data-testid="collection-list">
                {collection.length === 0 && <div className="empty">还没有收藏。完成打印、取下成品后加入收藏。</div>}
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
            <div><span>虚拟钱包</span><b>{wallet ? `${wallet.balance_g.toFixed(2)} g` : 'offline'}</b></div>
            <div><span>首件</span><b>{wallet?.first_print_available ? 'FREE' : 'USED'}</b></div>
            <div><span>已预扣</span><b>{job ? `${job.reserved_g.toFixed(3)} g` : '—'}</b></div>
            <p>仅计量虚拟耗材额度；不扣真实材料、不发起支付。</p>
          </section>
        </aside>
      </main>
    </div>
  );
}
