import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  addExternalCommonFoodComponent,
  createExternalCommonFoodOption,
  createExternalDietPlan,
  downloadExternalDietPlanVersion,
  generateExternalCommonFoodCandidates,
  listExternalDietPlans,
  publishExternalDietPlanById,
  readExternalCommonFoodOptions,
  removeExternalCommonFoodComponent,
  replaceExternalCommonFoodComponent,
  replaceExternalCommonFoodSelection,
  saveExternalDietPlanById,
  searchExternalCommonFoods,
  updateExternalCommonFoodServing,
} from '../../lib/fiteatsyConsultantsApi';
import CommonFoodPlanEditor from '../platform/CommonFoodPlanEditor';
import ExternalDietPlanHistory from './ExternalDietPlanHistory';

const authoringApi = {
  generate: generateExternalCommonFoodCandidates,
  read: readExternalCommonFoodOptions,
  replaceSelection: replaceExternalCommonFoodSelection,
  replaceComponent: replaceExternalCommonFoodComponent,
  addComponent: addExternalCommonFoodComponent,
  removeComponent: removeExternalCommonFoodComponent,
  updateServing: updateExternalCommonFoodServing,
  search: searchExternalCommonFoods,
  saveOption: createExternalCommonFoodOption,
  autoBalance: async () => { throw new Error('Use Edit quantity to select a governed serving.'); },
};

const initialForm = { name: '', dailyCalories: '', dailyProtein: '' };
const show = (value) => Array.isArray(value) ? value.join(', ') || 'Not provided' : value || 'Not provided';

export default function ExternalMultiDietPlan({ clientId, context, onError }) {
  const [plans, setPlans] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const editorRef = useRef(null);
  const selected = useMemo(() => plans.find((plan) => plan.id === selectedId) || plans[0] || null, [plans, selectedId]);
  const valid = form.name.trim().length >= 2 && Number(form.dailyCalories) >= 800 && Number(form.dailyCalories) <= 6000 && Number(form.dailyProtein) >= 20 && Number(form.dailyProtein) <= 400;

  const load = useCallback(async (preferredId) => {
    setLoading(true);
    try {
      const result = await listExternalDietPlans(clientId);
      const next = result.plans || [];
      setPlans(next);
      setSelectedId((current) => preferredId || (next.some((plan) => plan.id === current) ? current : next[0]?.id || ''));
    } catch (error) {
      onError(error.message || 'Unable to load Diet Plans.');
    } finally {
      setLoading(false);
    }
  }, [clientId, onError]);

  useEffect(() => { load(); }, [load]);

  const create = async (event) => {
    event.preventDefault();
    if (!valid || busy) return;
    setBusy('create'); setMessage(''); onError('');
    try {
      const result = await createExternalDietPlan(clientId, { name: form.name.trim(), dailyCalories: Number(form.dailyCalories), dailyProtein: Number(form.dailyProtein) });
      setForm(initialForm);
      await load(result.plan.id);
      setMessage('A new independent Diet Plan draft was created and reloaded.');
    } catch (error) { onError(error.message || 'Unable to create Diet Plan.'); }
    finally { setBusy(''); }
  };

  const persist = async (action) => {
    if (!selected || busy) return;
    setBusy(action); setMessage(''); onError('');
    try {
      if (action === 'save') {
        const options = selected.version.plan.meals.flatMap((meal) => meal.options);
        await saveExternalDietPlanById(clientId, selected.id, options);
        setMessage('Draft saved and reloaded from persistent storage.');
      } else {
        if (!window.confirm(`Publish “${selected.name}” to this client? Published history remains immutable.`)) return;
        await publishExternalDietPlanById(clientId, selected.id);
        setMessage('Diet Plan published. Its published version is now immutable.');
      }
      await load(selected.id);
    } catch (error) { onError(error.message || 'Unable to update Diet Plan.'); }
    finally { setBusy(''); }
  };

  const download = async () => {
    if (!selected || busy) return;
    setBusy('download'); onError('');
    try {
      const { blob, filename } = await downloadExternalDietPlanVersion(clientId, selected.version.id);
      const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
      anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
    } catch (error) { onError(error.message || 'Unable to export this Diet Plan version.'); }
    finally { setBusy(''); }
  };

  const fields = [['Primary goal', context?.goal], ['Diet preference', context?.dietPreference], ['Allergies', context?.allergies], ['Food restrictions', context?.restrictions], ['Weight', context?.weight], ['BMI', context?.bmi]];
  if (loading) return <div className="rounded-2xl bg-white p-12 text-center text-sm text-slate-500">Loading all Diet Plans…</div>;

  return <div className="space-y-4">
    <section className="rounded-2xl border border-blue-200 bg-blue-50 p-5">
      <p className="text-xs font-bold uppercase tracking-wider text-blue-700">Read-only client context</p>
      <h3 className="mt-1 text-lg font-semibold text-blue-950">Confirmed context for professional review</h3>
      <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{fields.map(([label, value]) => <div key={label} className="rounded-xl bg-white p-3"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-sm font-semibold">{show(value)}</dd></div>)}</dl>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">All Diet Plans</p><h3 className="mt-1 text-xl font-semibold">{plans.length} independent {plans.length === 1 ? 'plan' : 'plans'}</h3></div>{plans.length > 0 && <label className="text-sm font-semibold">Selected plan<select aria-label="Selected Diet Plan" value={selected?.id || ''} onChange={(event) => setSelectedId(event.target.value)} className="ml-2 min-h-11 rounded-xl border border-slate-200 px-3">{plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {plan.status.replaceAll('_', ' ')}</option>)}</select></label>}</div>
      {plans.length > 0 && <div className="mt-4 grid gap-3 md:grid-cols-2">{plans.map((plan) => <button key={plan.id} onClick={() => setSelectedId(plan.id)} className={`rounded-xl border p-4 text-left ${plan.id === selected?.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200'}`}><strong>{plan.name}</strong><p className="mt-1 text-xs text-slate-500">{plan.status.replaceAll('_', ' ')} · {plan.version.plan.dailyTargets.calories} kcal · {plan.version.plan.dailyTargets.protein} g protein</p><p className="mt-1 text-xs text-slate-400">Updated {new Date(plan.updatedAt).toLocaleString()}</p></button>)}</div>}
    </section>

    {selected && <><section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">{selected.status === 'PUBLISHED' ? 'Published Plan' : 'Draft Plan'}</p><h3 className="mt-1 text-xl font-semibold">{selected.name} · Version {selected.version.number}</h3></div><div className="flex flex-wrap gap-2"><button disabled={busy} onClick={download} className="min-h-11 rounded-xl border px-4 font-semibold disabled:opacity-40">{busy === 'download' ? 'Preparing DOCX…' : 'Download DOCX'}</button>{selected.status === 'DRAFT' && <button disabled={busy} onClick={() => persist('save')} className="min-h-11 rounded-xl border px-4 font-semibold disabled:opacity-40">{busy === 'save' ? 'Saving…' : 'Save Draft'}</button>}<button disabled={busy || selected.status === 'PUBLISHED'} onClick={() => persist('publish')} className="min-h-11 rounded-xl bg-blue-600 px-4 font-semibold text-white disabled:opacity-40">{selected.status === 'PUBLISHED' ? 'Published' : busy === 'publish' ? 'Publishing…' : 'Publish to Client'}</button></div></div></section><section className="rounded-2xl border border-slate-200 bg-white p-5"><CommonFoodPlanEditor key={`${selected.id}:${selected.version.id}`} ref={editorRef} clientId={clientId} dietPlanId={selected.id} planVersionId={selected.version.id} generationRequestId={1} lifecycle={selected.status === 'DRAFT' ? 'draft' : 'published'} initialOptions={selected.version.plan.meals.flatMap((meal) => meal.options)} legacyMealPlan={{}} readOnly={selected.status !== 'DRAFT'} authoringApi={authoringApi} templatesEnabled={false} proposalsEnabled={false} autoBalanceEnabled={false} onStale={() => load(selected.id)} /></section><ExternalDietPlanHistory key={selected.id} clientId={clientId} planId={selected.id} onDraftCreated={() => load(selected.id)} onError={onError}/></>}

    <form onSubmit={create} className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="text-lg font-semibold">Create another Diet Plan</h3><p className="mt-1 text-sm text-slate-500">Each plan has its own name, targets, draft and publication history.</p><div className="mt-4 grid gap-3 md:grid-cols-3"><label className="text-sm font-semibold">Plan name<input required minLength={2} maxLength={120} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="mt-2 w-full rounded-xl border p-3" /></label><label className="text-sm font-semibold">Calories (800–6000)<input required type="number" min="800" max="6000" value={form.dailyCalories} onChange={(event) => setForm({ ...form, dailyCalories: event.target.value })} className="mt-2 w-full rounded-xl border p-3" /></label><label className="text-sm font-semibold">Protein (20–400 g)<input required type="number" min="20" max="400" step="0.1" value={form.dailyProtein} onChange={(event) => setForm({ ...form, dailyProtein: event.target.value })} className="mt-2 w-full rounded-xl border p-3" /></label></div><button disabled={!valid || busy} className="mt-4 min-h-11 rounded-xl bg-slate-950 px-5 font-semibold text-white disabled:opacity-40">{busy === 'create' ? 'Creating…' : 'Create independent plan'}</button></form>
    {message && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-800">{message}</p>}
  </div>;
}
