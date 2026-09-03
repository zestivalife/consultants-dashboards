import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { ChevronRight, Search, X } from 'lucide-react';
import {
  addFiteatsyCommonFoodComponent,
  generateFiteatsyCommonFoodPlan,
  readFiteatsyCommonFoodOptions,
  removeFiteatsyCommonFoodComponent,
  replaceFiteatsyCommonFoodComponent,
  saveFiteatsyCommonFoodOption,
  searchFiteatsyCommonFoods,
  updateFiteatsyCommonFoodServing,
} from '../../lib/fiteatsyConsultantsApi';
import { COMMON_FOOD_MEALS, commonFoodErrorMessage, formatNutrient, optionSummary } from '../../lib/commonFoodUi.mjs';

const roles = ['', 'STARCH', 'GRAIN', 'BREAD', 'PULSE', 'PROTEIN', 'VEGETABLE', 'FRUIT', 'DAIRY', 'FAT', 'NUT_SEED', 'BEVERAGE', 'ACCOMPANIMENT'];
const dietClasses = ['', 'VEGAN', 'VEGETARIAN', 'EGG', 'NON_VEGETARIAN'];
const PAGE_SIZE = 20;

function NutritionFields({ nutrition, prefix = '' }) {
  return <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-5">
    <span>{prefix}Calories: {formatNutrient(nutrition?.kcal, 'kcal')}</span>
    <span>Protein: {formatNutrient(nutrition?.protein)}</span>
    <span>Carbs: {formatNutrient(nutrition?.carbohydrate)}</span>
    <span>Fat: {formatNutrient(nutrition?.fat)}</span>
    <span>Fibre: {formatNutrient(nutrition?.fibre)}</span>
  </div>;
}

function ComponentTable({ option, readOnly, onExplore, onRemove, onServing }) {
  return <div className="mt-3 overflow-x-auto">
    <table className="w-full min-w-[850px] text-left text-xs">
      <thead className="text-[var(--fluent-color-neutral-foreground-3)]"><tr>{['Component', 'Serving', 'Mass', 'Calories', 'Protein', 'Carbs', 'Fat', 'Fibre', 'Actions'].map((label) => <th key={label} className="pb-2 pr-3 font-medium">{label}</th>)}</tr></thead>
      <tbody className="divide-y divide-[var(--fluent-color-neutral-stroke-1)]">
        {(option.components || []).map((component) => <tr key={component.componentId || component.foodId}>
          <td className="py-2 pr-3 font-semibold">{component.foodDisplayNameSnapshot}</td>
          <td className="py-2 pr-3">{component.label || `${component.multiplier} × ${component.servingDisplayNameSnapshot}`}</td>
          <td className="py-2 pr-3">{formatNutrient(component.grams, 'g')}</td>
          <td className="py-2 pr-3">{formatNutrient(component.nutrition?.kcal, 'kcal')}</td>
          <td className="py-2 pr-3">{formatNutrient(component.nutrition?.protein)}</td>
          <td className="py-2 pr-3">{formatNutrient(component.nutrition?.carbohydrate)}</td>
          <td className="py-2 pr-3">{formatNutrient(component.nutrition?.fat)}</td>
          <td className="py-2 pr-3">{formatNutrient(component.nutrition?.fibre)}</td>
          <td className="py-2"><div className="flex gap-2">
            {!readOnly ? <><button type="button" onClick={() => onExplore('replace', component)} className="font-semibold text-[var(--fluent-color-brand-foreground-link)]">Replace</button><button type="button" onClick={() => onServing(component)} className="font-semibold text-[var(--fluent-color-brand-foreground-link)]">Serving</button><button type="button" onClick={() => onRemove(component)} className="font-semibold text-[var(--fluent-color-status-danger-foreground)]">Remove</button></> : <span>Snapshot</span>}
          </div></td>
        </tr>)}
      </tbody>
    </table>
  </div>;
}

function FoodExplorer({ context, clientId, onClose, onSelect }) {
  const [filters, setFilters] = useState({ search: '', category: '', componentRole: '', dietClass: '', proteinMin: '', proteinMax: '', caloriesMin: '', caloriesMax: '', offset: 0 });
  const [result, setResult] = useState({ items: [], total: 0, hasMore: false });
  const [selected, setSelected] = useState(null);
  const [servingId, setServingId] = useState('');
  const [multiplier, setMultiplier] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setLoading(true); setError('');
      try {
        const response = await searchFiteatsyCommonFoods(clientId, { ...filters, mealHead: context.mealHead, limit: PAGE_SIZE }, controller.signal);
        setResult(response || { items: [], total: 0, hasMore: false });
      } catch (nextError) { if (nextError?.name !== 'AbortError') setError(commonFoodErrorMessage(nextError, 'Food search failed.')); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    }, 300);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [clientId, context.mealHead, filters]);

  const choose = (food) => {
    const serving = food.servings?.find((item) => item.active && item.isDefault) || food.servings?.find((item) => item.active);
    setSelected(food); setServingId(serving?.id || ''); setMultiplier(serving?.allowedMultipliers?.includes(1) ? 1 : serving?.allowedMultipliers?.[0]);
  };
  const serving = selected?.servings?.find((item) => item.id === servingId);
  const set = (key, value) => setFilters((current) => ({ ...current, [key]: value, offset: key === 'offset' ? value : 0 }));
  return <div role="dialog" aria-modal="true" aria-label="Food Explorer" className="fixed inset-0 z-[90] bg-[rgba(15,23,42,0.3)]" onClick={onClose}>
    <aside className="absolute right-0 top-0 flex h-full w-full max-w-[760px] flex-col bg-[var(--fluent-color-neutral-background-canvas)] shadow-2xl" onClick={(event) => event.stopPropagation()}>
      <header className="flex items-center justify-between border-b border-[var(--fluent-color-neutral-stroke-1)] p-5"><div><h3 className="text-xl font-semibold">Food Explorer</h3><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{context.mode === 'replace' ? 'Replace component' : context.mode === 'serving' ? 'Change governed serving' : 'Add food'} · {context.mealLabel}</p></div><button type="button" aria-label="Close Food Explorer" onClick={onClose} className="flex h-10 w-10 items-center justify-center rounded-full border"><X size={18} /></button></header>
      <div className="overflow-y-auto p-5">
        <label className="relative block"><Search className="absolute left-3 top-3 text-gray-400" size={17} /><span className="sr-only">Search foods</span><input ref={inputRef} value={filters.search} onChange={(event) => set('search', event.target.value)} placeholder="Search governed foods" className="w-full rounded-[14px] border bg-white py-2.5 pl-10 pr-3 text-sm" /></label>
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          <input value={filters.category} onChange={(event) => set('category', event.target.value)} placeholder="Category" aria-label="Category filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm" />
          <select value={filters.componentRole} onChange={(event) => set('componentRole', event.target.value)} aria-label="Component role filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm">{roles.map((role) => <option key={role} value={role}>{role || 'All roles'}</option>)}</select>
          <select value={filters.dietClass} onChange={(event) => set('dietClass', event.target.value)} aria-label="Diet classification filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm">{dietClasses.map((item) => <option key={item} value={item}>{item || 'All diet classes'}</option>)}</select>
          <input type="number" value={filters.proteinMin} onChange={(event) => set('proteinMin', event.target.value)} placeholder="Protein min" aria-label="Minimum protein per 100 grams" className="rounded-[12px] border bg-white px-3 py-2 text-sm" />
          <input type="number" value={filters.proteinMax} onChange={(event) => set('proteinMax', event.target.value)} placeholder="Protein max" aria-label="Maximum protein per 100 grams" className="rounded-[12px] border bg-white px-3 py-2 text-sm" />
          <div className="grid grid-cols-2 gap-2"><input type="number" value={filters.caloriesMin} onChange={(event) => set('caloriesMin', event.target.value)} placeholder="kcal min" aria-label="Minimum calories per 100 grams" className="min-w-0 rounded-[12px] border bg-white px-3 py-2 text-sm" /><input type="number" value={filters.caloriesMax} onChange={(event) => set('caloriesMax', event.target.value)} placeholder="kcal max" aria-label="Maximum calories per 100 grams" className="min-w-0 rounded-[12px] border bg-white px-3 py-2 text-sm" /></div>
        </div>
        {error ? <p role="alert" className="mt-3 rounded-[12px] bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <div className="mt-4 space-y-2">{loading ? <p className="py-6 text-sm">Searching eligible foods…</p> : result.items?.length ? result.items.map((food) => <button type="button" key={food.id} onClick={() => choose(food)} className={`w-full rounded-[14px] border p-3 text-left ${selected?.id === food.id ? 'border-[var(--fluent-color-brand-stroke-1)] bg-blue-50' : 'bg-white'}`}><div className="flex justify-between gap-3"><div><p className="text-sm font-semibold">{food.displayName}</p><p className="mt-1 text-xs text-gray-500">{food.category} · {food.roles?.join(', ')}</p></div><p className="text-xs text-gray-500">Default: {food.servings?.find((item) => item.isDefault)?.label || 'Not set'}</p></div><div className="mt-2"><NutritionFields nutrition={food.nutritionPer100g} prefix="Per 100 g · " /></div></button>) : <p className="rounded-[14px] border border-dashed bg-white p-5 text-sm">No eligible food matches these filters.</p>}</div>
        <div className="mt-4 flex items-center justify-between"><button type="button" disabled={filters.offset === 0} onClick={() => set('offset', Math.max(0, filters.offset - PAGE_SIZE))} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Previous</button><span className="text-xs">{result.total || 0} eligible foods</span><button type="button" disabled={!result.hasMore} onClick={() => set('offset', filters.offset + PAGE_SIZE)} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Next</button></div>
        {selected ? <div className="mt-5 rounded-[16px] border bg-white p-4"><h4 className="font-semibold">Nutrition & serving preview</h4><p className="mt-1 text-xs text-gray-500">The backend validates and recalculates authoritative option totals after selection.</p><div className="mt-3 grid gap-2 sm:grid-cols-2"><select value={servingId} onChange={(event) => { setServingId(event.target.value); const next = selected.servings.find((item) => item.id === event.target.value); setMultiplier(next?.allowedMultipliers?.includes(1) ? 1 : next?.allowedMultipliers?.[0]); }} aria-label="Serving" className="rounded-[12px] border px-3 py-2 text-sm">{selected.servings?.filter((item) => item.active).map((item) => <option key={item.id} value={item.id}>{item.label} · {item.grams} g</option>)}</select><select value={multiplier} onChange={(event) => setMultiplier(Number(event.target.value))} aria-label="Serving multiplier" className="rounded-[12px] border px-3 py-2 text-sm">{serving?.allowedMultipliers?.map((value) => <option key={value} value={value}>{value}×</option>)}</select></div><button type="button" disabled={!servingId || multiplier == null || (context.mode === 'serving' && selected.id !== context.component.foodId)} onClick={() => onSelect({ foodId: selected.id, servingId, multiplier })} className="mt-4 rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">{context.mode === 'replace' ? 'Replace component' : context.mode === 'serving' ? 'Update serving' : 'Add food'}</button>{context.mode === 'serving' && selected.id !== context.component.foodId ? <p className="mt-2 text-xs text-amber-700">Select {context.component.foodDisplayNameSnapshot} to change only its serving.</p> : null}</div> : null}
      </div>
    </aside>
  </div>;
}

const CommonFoodPlanEditor = forwardRef(function CommonFoodPlanEditor({ clientId, dietPlanId, planVersionId, lifecycle, initialOptions = [], generationRequestId = 0, readOnly = false, onStale, onDirtyChange }, ref) {
  const [meals, setMeals] = useState([]);
  const [options, setOptions] = useState(initialOptions);
  const [expanded, setExpanded] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [explorer, setExplorer] = useState(null);
  const [activeMealHead, setActiveMealHead] = useState(COMMON_FOOD_MEALS[0][0]);
  const handledGenerationRequest = useRef(0);

  const byMeal = useMemo(() => Object.fromEntries(COMMON_FOOD_MEALS.map(([head]) => [head, options.filter((item) => item.mealHead === head)])), [options]);
  const generate = useCallback(async () => {
    setLoading(true); setError(''); setMessage('');
    try {
      const response = await generateFiteatsyCommonFoodPlan(clientId, dietPlanId, COMMON_FOOD_MEALS.map(([head]) => head));
      if (response?.supported === false) { setOptions([]); setMeals([]); setError(commonFoodErrorMessage({ data: { error: response.code } })); return; }
      setMeals(response?.meals || []); setOptions((response?.meals || []).flatMap((meal) => meal.options || [])); setDirty(true); setMessage('Your seven-meal Diet Plan is ready. Save the plan before submitting it for review.');
    } catch (nextError) { setError(commonFoodErrorMessage(nextError, 'Unable to generate Diet Plan options.')); }
    finally { setLoading(false); }
  }, [clientId, dietPlanId]);
  const reload = useCallback(async () => {
    if (!clientId || !dietPlanId) return;
    try {
      const response = await readFiteatsyCommonFoodOptions(clientId, dietPlanId);
      const savedOptions = response?.options || [];
      setOptions(savedOptions); setDirty(false);
      setMessage(savedOptions.length ? 'Saved Diet Plan reloaded.' : 'No saved Diet Plan options yet.');
    } catch (nextError) { setError(commonFoodErrorMessage(nextError, 'Unable to reload Diet Plan options.')); }
  }, [clientId, dietPlanId]);
  useEffect(() => {
    if (!dietPlanId) return;
    if (generationRequestId > handledGenerationRequest.current && ['draft', 'changes_requested'].includes(lifecycle) && !readOnly) {
      handledGenerationRequest.current = generationRequestId;
      void generate();
      return;
    }
    void reload();
  }, [dietPlanId, generate, generationRequestId, lifecycle, planVersionId, readOnly, reload]);
  useEffect(() => { onDirtyChange?.(dirty); }, [dirty, onDirtyChange]);
  useEffect(() => { const warn = (event) => { if (dirty) { event.preventDefault(); event.returnValue = ''; } }; window.addEventListener('beforeunload', warn); return () => window.removeEventListener('beforeunload', warn); }, [dirty]);

  const saveAll = async (expectedPlanVersionId = planVersionId) => {
    setSaving(true); setError('');
    try {
      const persisted = [];
      for (const option of options) persisted.push(await saveFiteatsyCommonFoodOption(clientId, dietPlanId, { optionId: option.combinationId, expectedPlanVersionId, mealHead: option.mealHead, components: option.components.map(({ foodId, servingId, multiplier }) => ({ foodId, servingId, multiplier })) }));
      setOptions(persisted); setDirty(false); setMessage(`Saved ${persisted.length} server-validated options.`);
    } catch (nextError) { if (nextError?.status === 409) onStale?.(); setError(commonFoodErrorMessage(nextError)); throw nextError; }
    finally { setSaving(false); }
  };
  useImperativeHandle(ref, () => ({ save: saveAll, reload: () => reload(), generate }), [generate, options, planVersionId, reload]);
  const mutate = async (action) => {
    setError('');
    try { const next = await action(); setOptions((current) => current.map((item) => item.combinationId === next.combinationId ? next : item)); setDirty(false); setExplorer(null); setMessage('Option updated and recalculated by Fiteatsy.'); }
    catch (nextError) { if (nextError?.status === 409) onStale?.(); setError(commonFoodErrorMessage(nextError)); }
  };
  const openExplorer = (mode, option, component, mealLabel) => setExplorer({ mode, option, component, mealHead: option.mealHead, mealLabel });
  const selectFood = (component) => mutate(() => explorer.mode === 'replace'
    ? replaceFiteatsyCommonFoodComponent(clientId, dietPlanId, explorer.option.combinationId, explorer.component.foodId, { expectedPlanVersionId: planVersionId, component })
    : explorer.mode === 'serving'
      ? updateFiteatsyCommonFoodServing(clientId, dietPlanId, explorer.option.combinationId, explorer.component.foodId, { expectedPlanVersionId: planVersionId, servingId: component.servingId, multiplier: component.multiplier })
      : addFiteatsyCommonFoodComponent(clientId, dietPlanId, explorer.option.combinationId, { expectedPlanVersionId: planVersionId, component }));

  const hasOptions = options.length > 0 || meals.length > 0;
  return <section aria-label="Diet Plan" className="space-y-4">
    <div><h4 className="text-base font-semibold">Diet Plan</h4><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Review five personalised options for each meal, then adjust foods and servings as needed.</p>{dirty ? <p className="mt-3 text-xs font-semibold text-amber-700">Unsaved Diet Plan changes</p> : null}{error ? <p role="alert" aria-live="assertive" className="mt-3 rounded-[12px] bg-red-50 p-3 text-sm text-red-700">{error}{error.includes('newer plan version') ? <button type="button" onClick={() => reload()} className="ml-2 underline">Reload latest</button> : null}</p> : null}{message ? <p role="status" className="mt-3 rounded-[12px] bg-green-50 p-3 text-sm text-green-700">{message}</p> : null}</div>
    {!hasOptions ? <div className="rounded-[18px] border border-dashed bg-[var(--fluent-color-neutral-background-2)] p-8 text-center text-sm text-[var(--fluent-color-neutral-foreground-2)]">{loading ? 'Generating personalised options for all seven meals…' : 'Generate a Diet Plan to create five personalised options for each meal.'}</div> : <div className="grid items-start gap-4 xl:grid-cols-[220px_minmax(0,1fr)]"><nav className="space-y-2 rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-2" aria-label="Meal navigator">{COMMON_FOOD_MEALS.map(([head,label],index)=>{const count=byMeal[head]?.length||0;return <button key={head} type="button" onClick={()=>setActiveMealHead(head)} className={`flex w-full items-center justify-between gap-3 rounded-[12px] px-3 py-2.5 text-left text-xs ${activeMealHead===head?'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]':'bg-[var(--fluent-color-neutral-background-1)] text-[var(--fluent-color-neutral-foreground-2)]'}`}><span><span className="font-semibold">{String(index+1).padStart(2,'0')}</span> {label}</span><span className="shrink-0 font-semibold">{count}/5</span></button>})}</nav><div className="space-y-3">{COMMON_FOOD_MEALS.filter(([head])=>head===activeMealHead).map(([head, label]) => {
      const generatedMeal = meals.find((item) => item.mealHead === head);
      const mealOptions = byMeal[head] || [];
      const coverage = generatedMeal?.coverage || { state: mealOptions.length >= 5 ? 'COMPLETE' : 'SHORTAGE', available: mealOptions.length, required: 5, missing: Math.max(0, 5 - mealOptions.length) };
      return <div key={head} className="rounded-[18px] border bg-white p-4"><div className="flex flex-wrap justify-between gap-3"><div><h5 className="font-semibold">{label}</h5><p className="mt-1 text-xs text-gray-500">Target: {formatNutrient(generatedMeal?.target?.kcal, 'kcal')} · {formatNutrient(generatedMeal?.target?.protein, 'g protein')}</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold ${coverage.state === 'COMPLETE' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-800'}`}>{coverage.state === 'COMPLETE' ? `${mealOptions.length} of 5 options` : `${coverage.available ?? mealOptions.length} of 5 valid options available`}</span></div>
        <div className="mt-3 space-y-2">{mealOptions.map((option, index) => { const key = option.combinationId || `${head}-${index}`; return <article key={key} className="rounded-[14px] border bg-[var(--fluent-color-neutral-background-2)] p-3"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">Option {index + 1}</p><p className="mt-1 text-sm text-gray-600">{optionSummary(option)}</p><div className="mt-2"><NutritionFields nutrition={option.nutrition} /></div></div><button type="button" aria-expanded={Boolean(expanded[key])} aria-label={`View ${label} option ${index + 1} details`} onClick={() => setExpanded((current) => ({ ...current, [key]: !current[key] }))} className="rounded-full p-2"><ChevronRight size={17} className={expanded[key] ? 'rotate-90' : ''} /></button></div>{expanded[key] ? <><ComponentTable option={option} readOnly={readOnly || !['draft', 'changes_requested'].includes(lifecycle)} onExplore={(mode, component) => openExplorer(mode, option, component, label)} onRemove={(component) => mutate(() => removeFiteatsyCommonFoodComponent(clientId, dietPlanId, option.combinationId, component.foodId, planVersionId))} onServing={(component) => openExplorer('serving', option, component, label)} />{!readOnly && ['draft', 'changes_requested'].includes(lifecycle) ? <button type="button" onClick={() => openExplorer('add', option, null, label)} className="mt-3 rounded-full border px-3 py-1.5 text-xs font-semibold">Add food</button> : null}</> : null}</article>; })}{!mealOptions.length ? <p className="rounded-[12px] border border-dashed p-4 text-sm text-gray-500">{loading ? 'Generating personalised options…' : 'No eligible options are available for this meal.'}</p> : null}</div>
      </div>;
    })}</div></div>}
    {explorer ? <FoodExplorer context={explorer} clientId={clientId} onClose={() => setExplorer(null)} onSelect={selectFood} /> : null}
  </section>;
});

export default CommonFoodPlanEditor;
