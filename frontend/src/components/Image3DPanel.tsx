import { useEffect, useRef, useState } from 'react';
import { analyzeImage, assetUrl, createImage3DJob, getImage3DJob, getImage3DProviders } from '../lib/api';
import type { Image3DJob, Image3DProvider } from '../types';

type Props = { onClose: () => void; onUseStl?: (url: string) => void };

export function Image3DPanel({ onClose, onUseStl }: Props) {
  const [providers, setProviders] = useState<Image3DProvider[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [provider, setProvider] = useState('auto');
  const [prompt, setPrompt] = useState('A compact printable desk figurine with a clear silhouette.');
  const [authorized, setAuthorized] = useState(false);
  const [budget, setBudget] = useState(0);
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [job, setJob] = useState<Image3DJob | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const outputUrl = job?.output_url ? assetUrl(job.output_url) : null;

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
    if (!file) { setError('Choose an image first.'); return; }
    setBusy(true); setError(''); setJob(null);
    try {
      const created = await createImage3DJob(file, provider, prompt, authorized, budget);
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
          <div><span>PRINTVERSE · IMAGE → 3D</span><h2>Multi-provider generation</h2></div>
          <button onClick={onClose} aria-label="Close Image to 3D">×</button>
        </header>
        <div className="image3d-body">
          <div className="image3d-left">
            <label className={`image3d-drop ${preview ? 'has-image' : ''}`}>
              <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setFile(e.target.files?.[0] ?? null)} data-testid="image3d-file" />
              {preview ? <img src={preview} alt="input preview" /> : <><b>Choose an image</b><small>PNG / JPEG / WebP · one clear object</small></>}
            </label>
            <label className="image3d-field"><span>PROVIDER</span>
              <select value={provider} onChange={(e) => setProvider(e.target.value)} data-testid="image3d-provider">
                <option value="auto">Auto · free local first</option>
                {providers.map((p) => <option key={p.id} value={p.id} disabled={!p.available}>{p.label}{p.available ? '' : ' · unavailable'}</option>)}
              </select>
            </label>
            <label className="image3d-field"><span>BRIEF</span>
              <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={3} />
            </label>
            <div className="image3d-auth">
              <label><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /> Authorize paid API</label>
              <label>budget CNY <input type="number" min={0} step={0.01} value={budget} onChange={(e) => setBudget(Number(e.target.value))} /></label>
            </div>
            <div className="image3d-actions">
              <button className="primary" onClick={run} disabled={busy || !file} data-testid="image3d-run">{busy ? 'Working…' : 'Generate 3D'}</button>
              <button className="ghost" onClick={analyze} disabled={busy || !file}>Kimi analyze</button>
            </div>
            {error && <div className="error-box">{error}</div>}
          </div>
          <div className="image3d-right">
            <h3>Providers</h3>
            <div className="provider-list">
              {providers.map((p) => (
                <div key={p.id} className={`provider-row ${p.available ? 'available' : ''}`}>
                  <i />
                  <div><b>{p.label}</b><small>{p.model} · {p.cost_class} · {p.available ? 'ready' : p.reason}</small></div>
                </div>
              ))}
            </div>
            {analysis && <div className="image3d-analysis"><h3>Kimi analysis (not a mesh)</h3><pre>{JSON.stringify(analysis, null, 2)}</pre></div>}
            {job && (
              <div className="image3d-result" data-testid="image3d-result">
                <h3>Generation result</h3>
                <div className="image3d-result-grid">
                  <div><span>STATUS</span><b>{job.status}</b></div>
                  <div><span>PROVIDER</span><b>{job.provider}</b></div>
                  <div><span>MODEL</span><b>{job.model}</b></div>
                  <div><span>COST</span><b>{job.generation_cost == null ? 'unknown' : `${job.generation_cost.toFixed(4)} ${job.cost_currency ?? ''}`}</b></div>
                  <div><span>GEOMETRY</span><b>{job.geometry_status ?? '—'}</b></div>
                  <div><span>TEXTURE</span><b>{job.texture_status ?? '—'}</b></div>
                </div>
                {outputUrl && <div className="row gap"><a className="primary link-button" href={outputUrl} target="_blank" rel="noreferrer">Download {job.output_format?.toUpperCase()}</a>{onUseStl && job.output_format === 'stl' && <button className="ghost" onClick={() => onUseStl(outputUrl)}>Use in print flow</button>}</div>}
                {job.error && <div className="error-box">{job.error}</div>}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
