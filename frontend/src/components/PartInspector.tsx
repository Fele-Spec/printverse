import { useEffect, useState } from 'react';

type PartRecord = { name: string; module: string; dims: number[]; material: string; parent: string | null; path: string };

export function PartInspector({ partId, module, onClose, onHide, onFocus }: {
  partId: string; module: string; onClose: () => void;
  onHide: (module: string) => void; onFocus: (module: string) => void;
}) {
  const [record, setRecord] = useState<PartRecord | null>(null);
  useEffect(() => {
    let alive = true;
    fetch('/models/voron/parts-index.json')
      .then((r) => r.json())
      .then((index) => { if (alive) setRecord(index[partId] ?? null); })
      .catch(() => { if (alive) setRecord(null); });
    return () => { alive = false; };
  }, [partId]);

  return (
    <div className="part-inspector" data-testid="part-inspector">
      <button className="inspector-close" onClick={onClose} aria-label="Close part inspector">×</button>
      <span className="inspector-kicker">SELECTED CAD PART</span>
      <b>{record?.name ?? partId}</b>
      <div className="inspector-grid">
        <div><span>MODULE</span><strong>{record?.module ?? module}</strong></div>
        <div><span>MATERIAL</span><strong>{record?.material ?? 'UNASSIGNED'}</strong></div>
        <div><span>DIMENSIONS</span><strong>{record?.dims?.length ? record.dims.map((v) => v.toFixed(1)).join(' × ') + ' mm' : '—'}</strong></div>
        <div><span>PLACEMENT</span><strong>{partId}</strong></div>
      </div>
      <small className="inspector-path">{record?.path ?? 'VORON2.4_Assembly.step'}</small>
      <div className="inspector-actions">
        <button onClick={() => onHide(record?.module ?? module)}>Hide module</button>
        <button onClick={() => onFocus(record?.module ?? module)}>Focus</button>
      </div>
    </div>
  );
}
