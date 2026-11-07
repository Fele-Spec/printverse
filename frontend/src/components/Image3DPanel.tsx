import { useEffect, useRef, useState } from 'react';
import { analyzeImage, assetUrl, createImage3DJob, createImage3DMultiJob, getImage3DJob, getImage3DProviders } from '../lib/api';
import type { Image3DJob, Image3DProvider } from '../types';
import { AssetPreview } from './AssetPreview';


const PROVIDER_ZH: Record<string, string> = {
  drawing_local: '工程图拉伸（本地）',
  mock_relief: 'Mock 浮雕（免费）',
  triposr_local: 'TripoSR 本地',
  stable_fast_3d: 'Stable Fast 3D（候选）',
  tripo_cloud: 'TokenHub Tripo 云端',
  hy3d_cloud: 'TokenHub HY-3D 3.1 云端',
  kimi_analysis: 'Kimi 图片理解',
};
const REASON_ZH: Record<string, string> = {
  drawing_local: '识别深色封闭轮廓并拉伸；不推断尺寸、约束或孔，不是参数化 CAD。',
  mock_relief: '并非真正的图片转三维；是用于测试打印链路的彩色高度场浮雕。',
  triposr_local: '本地 CPU 可用；生成后需检查修复。',
  stable_fast_3d: '尚未在 Windows 安装；权重与许可证需要审查。',
  tripo_cloud: '缺少 TokenHub Key 与账号端点；未产生费用。',
  hy3d_cloud: '缺少 TokenHub Key 与账号端点；未产生费用。',
  kimi_analysis: '账户余额不足（HTTP 429）；充值后启用分析。',
};
const zhProvider = (p: Image3DProvider) => PROVIDER_ZH[p.id] ?? p.label;
const zhReason = (p: Image3DProvider) => REASON_ZH[p.id] ?? p.reason;
const STATUS_ZH: Record<string, string> = { queued: '排队中', running: '生成中', completed: '已完成', failed: '失败', not_configured: '未配置', authorization_required: '需要授权' };
const COST_ZH: Record<string, string> = { free: '免费', low: '低成本', high: '高成本', unknown: '未知' };
const zhStatus = (s: string) => STATUS_ZH[s] ?? s;

type Props = { onClose: () => void; onUseModel?: (stlUrl: string, colorUrl: string) => void };

export function Image3DPanel({ onClose, onUseModel }: Props) {
  const [providers, setProviders] = useState<Image3DProvider[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [multiFiles, setMultiFiles] = useState<File[]>([]);
  const [preview, setPreview] = useState('');
  const [provider, setProvider] = useState('auto');
  const [prompt, setPrompt] = useState('一个轮廓清晰、适合打印的桌面摆件。');
  const [authorized, setAuthorized] = useState(false);
  const [budget, setBudget] = useState(0);
  const [widthMm, setWidthMm] = useState(80);
  const [heightMm, setHeightMm] = useState(3);
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [job, setJob] = useState<Image3DJob | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const outputUrl = job?.output_url ? assetUrl(job.output_url) : null;
  const stlPath = typeof job?.metadata?.stl_url === 'string' ? job.metadata.stl_url : null;
  const threeMfPath = typeof job?.metadata?.three_mf_url === 'string' ? job.metadata.three_mf_url : null;
  const stlUrl = stlPath ? assetUrl(stlPath) : null;
  const threeMfUrl = threeMfPath ? assetUrl(threeMfPath) : null;

  useEffect(() => {
    getImage3DProviders().then((r) => setProviders(r.providers)).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return;
    const timer = setInterval(async () => {
      try { setJob(await getImage3DJob(job.id)); } catch { /* keep polling */ }
    }, 1200);
    return () => clearInterval(timer);
  }, [job]);

  async function run() {
    if (!file) { setError('请先选择图片。'); return; }
    if ((provider === 'multiview_local' || multiFiles.length > 1) && multiFiles.length !== 3) {
      setError('多视角需要正面、侧面、顶面 3 张图片。');
      return;
    }
    setBusy(true); setError(''); setJob(null);
    try {
      const created = (provider === 'multiview_local' || multiFiles.length > 1)
        ? await createImage3DMultiJob(multiFiles, prompt)
        : await createImage3DJob(file, provider, prompt, authorized, budget, widthMm, heightMm);
      setJob(created);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Image-to-3D request failed');
    } finally { setBusy(false); }
  }

  async function analyze() {
    if (!file) return;
    setBusy(true); setError('');
    try { setAnalysis((await analyzeImage(file, prompt)).analysis ?? null); }
    catch (e) { setError(e instanceof Error ? e.message : 'Kimi analysis failed'); }
    finally { setBusy(false); }
  }

  return (
    <div className="image3d-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="image3d-panel" data-testid="image3d-panel">
        <header className="image3d-head">
          <div><span>PRINTVERSE · 图片 → 彩色 3D</span><h2>AI 三维创作</h2></div>
          <button onClick={onClose} aria-label="关闭图片转三维">×</button>
        </header>
        <div className="image3d-body">
          <div className="image3d-left">
            <label className={`image3d-drop ${preview ? 'has-image' : ''}`}>
              <input ref={fileRef} type="file" multiple accept="image/png,image/jpeg,image/webp" onChange={(e) => {
                const list = Array.from(e.target.files ?? []);
                setMultiFiles(list);
                setFile(list[0] ?? null);
              }} data-testid="image3d-file" />
              {preview ? <img src={preview} alt="输入图片预览" /> : <><b>选择图片</b><small>PNG / JPEG / WebP · 多视角请选正面/侧面/顶面 3 张</small></>}
              {multiFiles.length > 1 && <small>{multiFiles.length} 张 · 多视角轮廓重建</small>}
            </label>
            <label className="image3d-field"><span>生成引擎</span>
              <select value={provider} onChange={(e) => setProvider(e.target.value)} data-testid="image3d-provider">
                <option value="auto">自动 · 优先免费本地</option>
                {providers.map((p) => <option key={p.id} value={p.id} disabled={!p.available}>{zhProvider(p)}{p.available ? '' : ' · 不可用'}</option>)}
              </select>
            </label>
            <label className="image3d-field"><span>模型说明</span>
              <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={3} />
            </label>
            {provider === 'drawing_local' && (
              <div className="image3d-auth">
                <label>图纸宽度 mm <input type="number" min={20} max={300} step={1} value={widthMm} onChange={(e) => setWidthMm(Number(e.target.value))} /></label>
                <label>拉伸厚度 mm <input type="number" min={0.6} max={20} step={0.2} value={heightMm} onChange={(e) => setHeightMm(Number(e.target.value))} /></label>
              </div>
            )}
            <div className="image3d-auth">
              <label><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /> 授权云端付费调用</label>
              <label>预算 CNY <input type="number" min={0} step={0.01} value={budget} onChange={(e) => setBudget(Number(e.target.value))} /></label>
            </div>
            <div className="image3d-actions">
              <button className="primary" onClick={run} disabled={busy || !file} data-testid="image3d-run">{busy ? '生成中…' : '生成彩色 3D'}</button>
              <button className="ghost" onClick={analyze} disabled={busy || !file}>Kimi 理解图片</button>
            </div>
            {error && <div className="error-box">{error}</div>}
          </div>
          <div className="image3d-right">
            <h3>生成引擎</h3>
            <div className="provider-list">
              {providers.map((p) => (
                <div key={p.id} className={`provider-row ${p.available ? 'available' : ''}`}>
                  <i />
                  <div><b>{zhProvider(p)}</b><small>{p.model} · {COST_ZH[p.cost_class] ?? p.cost_class} · {p.available ? '就绪' : zhReason(p)}</small></div>
                </div>
              ))}
            </div>
            {analysis && <div className="image3d-analysis"><h3>Kimi 图片理解（不生成网格）</h3><pre>{JSON.stringify(analysis, null, 2)}</pre></div>}
            {job && (
              <div className="image3d-result" data-testid="image3d-result">
                <h3>生成结果</h3>
                {outputUrl && job.status === 'completed' && <AssetPreview url={outputUrl} />}
                <div className="image3d-result-grid">
                  <div><span>状态</span><b>{zhStatus(job.status)}</b></div>
                  <div><span>引擎</span><b>{job.provider}</b></div>
                  <div><span>模型</span><b>{job.model}</b></div>
                  <div><span>费用</span><b>{job.generation_cost == null ? '未知' : `${job.generation_cost.toFixed(4)} ${job.cost_currency ?? ''}`}</b></div>
                  <div><span>几何</span><b>{job.geometry_status ?? '—'}</b></div>
                  <div><span>颜色</span><b>{job.texture_status ?? '—'}</b></div>
                </div>
                {outputUrl && (
                  <div className="asset-downloads">
                    <a className="primary link-button" href={outputUrl} target="_blank" rel="noreferrer">下载彩色 GLB</a>
                    {stlUrl && <a className="ghost link-button" href={stlUrl} target="_blank" rel="noreferrer">STL</a>}
                    {threeMfUrl && <a className="ghost link-button" href={threeMfUrl} target="_blank" rel="noreferrer">3MF</a>}
                    {onUseModel && stlUrl && <button className="ghost" onClick={() => onUseModel(stlUrl, job.output_url ?? '')}>用于虚拟打印</button>}
                  </div>
                )}
                {job.error && <div className="error-box">{job.error}</div>}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
