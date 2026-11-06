export type ViewPreset = 'product' | 'engineering' | 'interior' | 'toolhead' | 'top' | 'exploded';
export type PanelMode = 'glass' | 'clear' | 'hidden';

const VIEWS: Array<{ id: ViewPreset; label: string; hint: string }> = [
  { id: 'product', label: 'PRODUCT', hint: '外观三分之四' },
  { id: 'engineering', label: 'ENGINEERING', hint: '整机结构' },
  { id: 'interior', label: 'INTERIOR', hint: '内部机械' },
  { id: 'toolhead', label: 'TOOLHEAD', hint: '喷头细节' },
  { id: 'top', label: 'TOP', hint: '顶部龙门' },
  { id: 'exploded', label: 'EXPLODED', hint: '模块拆解' },
];

const MODULES = [
  ['FRAME', '机架'],
  ['ENCLOSURE', '机舱'],
  ['XY_GANTRY', 'XY 龙门'],
  ['Z_DRIVE', 'Z 驱动'],
  ['TOOLHEAD', '打印头'],
  ['BUILD_PLATFORM', '打印平台'],
  ['ELECTRONICS', '电控'],
  ['WIRING', '线缆'],
] as const;

export function SceneControls({
  view, onView, panelMode, onPanelMode, orthographic, onOrthographic,
  explode, onExplode, modules, onToggleModule, cadMode, onCadMode,
}: {
  view: ViewPreset;
  onView: (v: ViewPreset) => void;
  panelMode: PanelMode;
  onPanelMode: (m: PanelMode) => void;
  orthographic: boolean;
  onOrthographic: (v: boolean) => void;
  explode: number;
  onExplode: (v: number) => void;
  modules: Record<string, boolean>;
  onToggleModule: (m: string) => void;
  cadMode: boolean;
  onCadMode: (v: boolean) => void;
}) {
  return (
    <div className="scene-dock" data-testid="scene-controls">
      <div className="dock-head">
        <span>VIEW</span>
        <div className="dock-head-actions">
          <button className={`ortho-toggle ${cadMode ? 'cad-on' : ''}`} onClick={() => onCadMode(!cadMode)} data-testid="cad-toggle">
            {cadMode ? 'CAD' : 'SIM'}
          </button>
          <button className="ortho-toggle" onClick={() => onOrthographic(!orthographic)} data-testid="ortho-toggle">
            {orthographic ? 'ORTHO' : 'PERSP'}
          </button>
        </div>
      </div>
      <div className="view-grid">
        {VIEWS.map((v) => (
          <button key={v.id} className={view === v.id ? 'active' : ''} onClick={() => { onView(v.id); if (v.id === 'exploded') onExplode(0.65); }} title={v.hint} data-testid={`view-${v.id}`}>
            {v.label}
          </button>
        ))}
      </div>
      <div className="dock-sep" />
      <div className="dock-head"><span>ENCLOSURE</span></div>
      <div className="segmented">
        {(['glass', 'clear', 'hidden'] as PanelMode[]).map((m) => (
          <button key={m} className={panelMode === m ? 'active' : ''} onClick={() => onPanelMode(m)} data-testid={`panel-${m}`}>
            {m === 'glass' ? '烟玻' : m === 'clear' ? '透明' : '隐藏'}
          </button>
        ))}
      </div>
      <div className="dock-sep" />
      <div className="dock-head"><span>MODULES</span><em>{Object.values(modules).filter(Boolean).length}/8</em></div>
      <div className="module-grid">
        {MODULES.map(([id, label]) => (
          <button key={id} className={modules[id] ? 'on' : ''} onClick={() => onToggleModule(id)} title={label} data-testid={`module-${id}`}>
            <i />{label}
          </button>
        ))}
      </div>
      <div className="dock-sep" />
      <label className="explode-row">
        <span>EXPLODE</span>
        <input type="range" min={0} max={1} step={0.01} value={explode} onChange={(e) => onExplode(Number(e.target.value))} />
        <b>{Math.round(explode * 100)}%</b>
      </label>
    </div>
  );
}
