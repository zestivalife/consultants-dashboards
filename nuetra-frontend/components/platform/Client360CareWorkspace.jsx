import { useCallback, useEffect, useMemo, useState } from 'react';
import { CalendarDays, CheckCircle2, ClipboardList, Flag, NotebookPen, Plus, X } from 'lucide-react';
import {
  createFiteatsyClientOperation,
  listFiteatsyClientOperations,
  updateFiteatsyClientOperation,
} from '../../lib/fiteatsyConsultantsApi';

const TYPES = [
  ['CONSULTATION', 'Consultation', CalendarDays],
  ['TASK', 'Task', ClipboardList],
  ['FOLLOW_UP', 'Follow-up', Flag],
  ['GOAL', 'Goal', CheckCircle2],
  ['NOTE', 'Note', NotebookPen],
];

const emptyDraft = { operationType: 'TASK', title: '', detail: '', priority: 'NORMAL', dueAt: '' };

function toIso(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

export default function Client360CareWorkspace({ clientId, clientName }) {
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState(emptyDraft);

  const load = useCallback(async () => {
    if (!clientId) return;
    setLoading(true);
    setError(null);
    try {
      setOperations(await listFiteatsyClientOperations(clientId));
    } catch (nextError) {
      setError(nextError?.message || 'Care operations could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => { void load(); }, [load]);

  const grouped = useMemo(() => Object.fromEntries(TYPES.map(([key]) => [key, operations.filter((item) => item.operationType === key)])), [operations]);

  async function submit(event) {
    event.preventDefault();
    if (!draft.title.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const result = await createFiteatsyClientOperation(clientId, {
        operationType: draft.operationType,
        title: draft.title.trim(),
        detail: draft.detail.trim() || null,
        priority: draft.priority,
        dueAt: toIso(draft.dueAt),
        scheduledAt: draft.operationType === 'CONSULTATION' ? toIso(draft.dueAt) : null,
      }, `${clientId}:${draft.operationType}:${Date.now()}`);
      setOperations((current) => [result.operation, ...current.filter((item) => item.id !== result.operation.id)]);
      setDraft(emptyDraft);
      setPanelOpen(false);
    } catch (nextError) {
      setError(nextError?.message || 'The care operation could not be saved.');
    } finally {
      setSaving(false);
    }
  }

  async function complete(item) {
    setError(null);
    try {
      const result = await updateFiteatsyClientOperation(clientId, item.id, { status: 'COMPLETED', expectedVersion: item.version });
      setOperations((current) => current.map((candidate) => candidate.id === item.id ? result.operation : candidate));
    } catch (nextError) {
      setError(nextError?.status === 409 ? 'This item changed elsewhere. Refreshing the current version.' : nextError?.message || 'The item could not be updated.');
      await load();
    }
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[22px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-5 shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><h3 className="text-lg font-semibold">Care workspace</h3><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Backend-owned consultations, follow-ups, goals, tasks, and clinical notes for {clientName || 'this client'}.</p></div>
          <button type="button" onClick={() => setPanelOpen(true)} className="inline-flex min-h-10 items-center gap-2 rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-[var(--fluent-color-brand-foreground)]"><Plus size={16} />Add care item</button>
        </div>
        {error ? <div role="alert" className="mt-4 rounded-[14px] bg-[var(--fluent-color-status-danger-background)] px-4 py-3 text-sm text-[var(--fluent-color-status-danger-foreground)]">{error}</div> : null}
      </section>
      {loading ? <div className="rounded-[22px] bg-[var(--fluent-color-neutral-background-1)] p-6 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading the current care record…</div> : (
        <div className="grid gap-4 xl:grid-cols-2">
          {TYPES.map(([type, label, Icon]) => <section key={type} className="rounded-[22px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-5">
            <div className="flex items-center justify-between"><div className="flex items-center gap-2"><Icon size={18} /><h4 className="font-semibold">{label}s</h4></div><span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-2.5 py-1 text-xs">{grouped[type].length}</span></div>
            <div className="mt-4 space-y-2">{grouped[type].length ? grouped[type].map((item) => <article key={item.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{item.title}</p>{item.detail ? <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p> : null}<p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{item.status.replaceAll('_', ' ')} · {item.priority}</p></div>{!['COMPLETED','CANCELLED','ARCHIVED'].includes(item.status) ? <button type="button" onClick={() => void complete(item)} className="rounded-full border px-3 py-1.5 text-xs font-semibold">Complete</button> : null}</div></article>) : <p className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No {label.toLowerCase()} records yet.</p>}</div>
          </section>)}
        </div>
      )}
      {panelOpen ? <div className="fixed inset-0 z-[90] flex justify-end bg-black/25" onMouseDown={(event) => { if (event.target === event.currentTarget) setPanelOpen(false); }}><aside role="dialog" aria-modal="true" aria-labelledby="care-panel-title" className="h-full w-full max-w-[480px] overflow-y-auto bg-[var(--fluent-color-neutral-background-canvas)] p-5 shadow-[-12px_0_40px_rgba(15,23,42,0.18)]"><div className="flex items-start justify-between"><div><h3 id="care-panel-title" className="text-xl font-semibold">Add care item</h3><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Saved to the shared client record.</p></div><button type="button" aria-label="Close" onClick={() => setPanelOpen(false)} className="rounded-full border p-2"><X size={18} /></button></div><form onSubmit={submit} className="mt-6 space-y-4"><label className="block text-sm font-semibold">Type<select value={draft.operationType} onChange={(event) => setDraft((current) => ({ ...current, operationType: event.target.value }))} className="mt-2 w-full rounded-[14px] border bg-white px-3 py-3">{TYPES.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className="block text-sm font-semibold">Title<input value={draft.title} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} maxLength={180} required className="mt-2 w-full rounded-[14px] border px-3 py-3" /></label><label className="block text-sm font-semibold">Detail<textarea value={draft.detail} onChange={(event) => setDraft((current) => ({ ...current, detail: event.target.value }))} rows={5} maxLength={5000} className="mt-2 w-full rounded-[14px] border px-3 py-3" /></label><label className="block text-sm font-semibold">Due or scheduled time<input type="datetime-local" value={draft.dueAt} onChange={(event) => setDraft((current) => ({ ...current, dueAt: event.target.value }))} className="mt-2 w-full rounded-[14px] border px-3 py-3" /></label><button disabled={saving} className="w-full rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-3 font-semibold text-[var(--fluent-color-brand-foreground)] disabled:opacity-50">{saving ? 'Saving…' : 'Save care item'}</button></form></aside></div> : null}
    </div>
  );
}
