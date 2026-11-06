import type { CollectionItem, Image3DJob, Image3DProvider, Job, Toolpath, Wallet } from '../types';

const API_BASE = (import.meta as ImportMeta & { env?: { VITE_API_BASE?: string } }).env?.VITE_API_BASE ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* keep status */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function assetUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith('/runtime/')) return `${API_BASE}${path}`;
  return path;
}

export async function getWallet(): Promise<Wallet> {
  return request<Wallet>('/api/wallet');
}

export async function getCollection(): Promise<{ items: CollectionItem[]; wallet: Wallet }> {
  return request('/api/collection');
}

export async function uploadStl(file: File, colorUrl?: string | null): Promise<Job & { wallet: Wallet }> {
  const form = new FormData();
  form.append('file', file, file.name);
  if (colorUrl) form.append('color_url', colorUrl);
  return request('/api/jobs', { method: 'POST', body: form });
}

export async function completeJob(jobId: string): Promise<Job & { wallet: Wallet }> {
  return request(`/api/jobs/${jobId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 'demo' }),
  });
}

export async function cancelJob(jobId: string): Promise<Job & { wallet: Wallet }> {
  return request(`/api/jobs/${jobId}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 'demo' }),
  });
}

export async function addToCollection(jobId: string): Promise<{ item: CollectionItem; wallet: Wallet }> {
  return request('/api/collection', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, user_id: 'demo' }),
  });
}

export async function loadToolpath(path: string): Promise<Toolpath> {
  const res = await fetch(assetUrl(path));
  if (!res.ok) throw new Error(`toolpath ${res.status}`);
  return res.json() as Promise<Toolpath>;
}

export async function getImage3DProviders(): Promise<{ providers: Image3DProvider[] }> {
  return request('/api/image3d/providers');
}

export async function createImage3DJob(file: File, provider: string, prompt: string, authorized: boolean, budget: number): Promise<Image3DJob> {
  const form = new FormData();
  form.append('file', file, file.name);
  form.append('provider', provider);
  form.append('prompt', prompt);
  form.append('authorized', String(authorized));
  form.append('budget_cny', String(budget));
  return request('/api/image3d/jobs', { method: 'POST', body: form });
}

export async function getImage3DJob(id: string): Promise<Image3DJob> {
  return request(`/api/image3d/jobs/${id}`);
}

export async function analyzeImage(file: File, prompt: string): Promise<{ analysis?: Record<string, unknown>; raw?: string }> {
  const form = new FormData();
  form.append('file', file, file.name);
  form.append('prompt', prompt);
  return request('/api/image3d/analyze', { method: 'POST', body: form });
}

export async function loadDemo(): Promise<{ toolpath: Toolpath; modelUrl: string }> {
  const toolpath = await loadToolpath('/demo/cube.toolpath.json');
  return { toolpath, modelUrl: '/demo/cube.stl' };
}
