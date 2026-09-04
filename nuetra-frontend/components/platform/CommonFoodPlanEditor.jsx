import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { Check, ChevronRight, Lock, Search, Sparkles, Unlock, X } from 'lucide-react';
import {
  addFiteatsyCommonFoodComponent,
  autoBalanceFiteatsyCommonFoodOption,
  generateFiteatsyCommonFoodPlan,
  readFiteatsyCommonFoodOptions,
  removeFiteatsyCommonFoodComponent,
  replaceFiteatsyCommonFoodComponent,
  replaceFiteatsyCommonFoodSelection,
  searchFiteatsyCommonFoods,
  updateFiteatsyCommonFoodServing,
} from '../../lib/fiteatsyConsultantsApi';
import { isCommonFoodCombinationEngineEnabled } from '../../lib/dietFeatureFlags';
import { COMMON_FOOD_MEALS, commonFoodErrorMessage, commonFoodOptionType, formatNutrient, legacyOptionsForUnifiedPlan, optionSummary, optionTitle } from '../../lib/commonFoodUi.mjs';

const roles = [['', 'All food groups'], ['STARCH', 'Staples'], ['GRAIN', 'Grains'], ['BREAD', 'Indian breads'], ['PULSE', 'Dal & pulses'], ['PROTEIN', 'Protein foods'], ['VEGETABLE', 'Vegetables'], ['FRUIT', 'Fruits'], ['DAIRY', 'Dairy'], ['FAT', 'Fats'], ['NUT_SEED', 'Nuts & seeds'], ['BEVERAGE', 'Drinks'], ['ACCOMPANIMENT', 'Accompaniments']];
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

const componentRole = (component) => String(component.componentRole || component.role || component.roles?.[0] || 'Component').replaceAll('_', ' ').replace(/\b\w/g, (value) => value.toUpperCase());

function ComponentTable({ option, readOnly, onExplore, onRemove, onServing, locked, onLock }) {
  return <div className="mt-4 grid gap-2 sm:grid-cols-2" aria-label="Structured meal components">
    {(option.components || []).map((component) => {
      const isLocked = locked?.has(component.foodId);
      return <section key={component.componentId || component.foodId} className="rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-white p-3">
        <div className="flex items-start justify-between gap-3"><div><p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[var(--fluent-color-neutral-foreground-3)]">{componentRole(component)}</p><p className="mt-1 text-sm font-semibold">{component.foodDisplayNameSnapshot}</p><p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{component.label || `${component.multiplier} × ${component.servingDisplayNameSnapshot}`}</p></div>{isLocked ? <Lock size={15} aria-label="Serving locked" className="text-[var(--fluent-color-brand-foreground-link)]" /> : null}</div>
        <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{formatNutrient(component.nutrition?.kcal, 'kcal')} · {formatNutrient(component.nutrition?.protein, 'g protein')} · exact equivalent {formatNutrient(component.grams, 'g')}</p>
        {!readOnly ? <div className="mt-3 flex flex-wrap gap-x-3 gap-y-2 text-xs font-semibold"><button type="button" onClick={() => onExplore('replace', component)} className="text-[var(--fluent-color-brand-foreground-link)]">Change</button><button type="button" onClick={() => onServing(component)} className="text-[var(--fluent-color-brand-foreground-link)]">Adjust serving</button><button type="button" title="Keep this serving fixed during Auto-Balance" aria-pressed={isLocked} onClick={() => onLock(component.foodId)} className="inline-flex items-center gap-1 text-[var(--fluent-color-brand-foreground-link)]">{isLocked ? <Unlock size={13} /> : <Lock size={13} />}{isLocked ? 'Unlock' : 'Lock'}</button><button type="button" onClick={() => onRemove(component)} className="text-[var(--fluent-color-status-danger-foreground)]">Remove</button></div> : null}
      </section>;
    })}
  </div>;
}

function ClientPreview({ options, onClose }) {
  const selected = options.filter((option) => option.selected);
  return <div role="dialog" aria-modal="true" aria-label="Client Diet Plan preview" className="fixed inset-0 z-[95] overflow-y-auto bg-[rgba(15,23,42,0.55)] p-4 sm:p-8" onClick={onClose}><div className="mx-auto max-w-[760px] rounded-[24px] bg-white shadow-2xl" onClick={(event) => event.stopPropagation()}><header className="sticky top-0 z-10 flex items-center justify-between rounded-t-[24px] border-b bg-white px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--fluent-color-brand-foreground-link)]">Preview as Client</p><h3 className="mt-1 text-xl font-semibold">Your active Diet Plan</h3></div><button type="button" aria-label="Close Client Preview" onClick={onClose} className="flex h-10 w-10 items-center justify-center rounded-full border"><X size={18} /></button></header><div className="space-y-6 p-5"><p className="rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] p-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Choose any one option from each meal. This preview contains only the selected client-facing plan—never the candidate pool or internal audit data.</p>{COMMON_FOOD_MEALS.map(([head, label]) => <section key={head}><div className="flex items-center justify-between"><h4 className="text-lg font-semibold">{label}</h4><span className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">Choose any one</span></div><div className="mt-2 space-y-2">{selected.filter((option) => option.mealHead === head).map((option) => <article key={option.combinationId} className="rounded-[14px] border p-3"><p className="text-sm font-semibold">{optionTitle(option)}</p><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{optionSummary(option)}</p><p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{formatNutrient(option.nutrition?.kcal, 'kcal')} · {formatNutrient(option.nutrition?.protein, 'g protein')}</p></article>)}</div></section>)}</div></div></div>;
}

function FoodExplorer({ context, clientId, onClose, onSelect }) {
  const [filters, setFilters] = useState({ scope: 'RECOMMENDED', search: '', category: '', componentRole: '', dietClass: '', proteinMin: '', proteinMax: '', caloriesMin: '', caloriesMax: '', offset: 0 });
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
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-[var(--fluent-color-neutral-foreground-3)]">1 · Choose component</p><div className="mb-3 inline-flex rounded-full bg-white p-1 shadow-sm" aria-label="Catalogue scope">{[['RECOMMENDED', `Recommended for ${context.mealLabel}`], ['ALL', 'All eligible foods']].map(([value,label]) => <button key={value} type="button" aria-pressed={filters.scope === value} onClick={() => set('scope', value)} className={`rounded-full px-3 py-2 text-xs font-semibold ${filters.scope === value ? 'bg-[var(--fluent-color-brand-background)] text-white' : 'text-gray-600'}`}>{label}</button>)}</div><label className="relative block"><Search className="absolute left-3 top-3 text-gray-400" size={17} /><span className="sr-only">Search foods by dish, alias or common name</span><input ref={inputRef} value={filters.search} onChange={(event) => set('search', event.target.value)} placeholder="Search bhindi, okra, roti…" className="w-full rounded-[14px] border bg-white py-2.5 pl-10 pr-3 text-sm" /></label>
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          <input value={filters.category} onChange={(event) => set('category', event.target.value)} placeholder="Category" aria-label="Category filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm" />
          <select value={filters.componentRole} onChange={(event) => set('componentRole', event.target.value)} aria-label="Food group filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm">{roles.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select>
          <select value={filters.dietClass} onChange={(event) => set('dietClass', event.target.value)} aria-label="Diet classification filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm">{dietClasses.map((item) => <option key={item} value={item}>{item || 'All diet classes'}</option>)}</select>
          <input type="number" value={filters.proteinMin} onChange={(event) => set('proteinMin', event.target.value)} placeholder="Protein min" aria-label="Minimum protein per 100 grams" className="rounded-[12px] border bg-white px-3 py-2 text-sm" />
          <input type="number" value={filters.proteinMax} onChange={(event) => set('proteinMax', event.target.value)} placeholder="Protein max" aria-label="Maximum protein per 100 grams" className="rounded-[12px] border bg-white px-3 py-2 text-sm" />
          <div className="grid grid-cols-2 gap-2"><input type="number" value={filters.caloriesMin} onChange={(event) => set('caloriesMin', event.target.value)} placeholder="kcal min" aria-label="Minimum calories per 100 grams" className="min-w-0 rounded-[12px] border bg-white px-3 py-2 text-sm" /><input type="number" value={filters.caloriesMax} onChange={(event) => set('caloriesMax', event.target.value)} placeholder="kcal max" aria-label="Maximum calories per 100 grams" className="min-w-0 rounded-[12px] border bg-white px-3 py-2 text-sm" /></div>
        </div>
        {error ? <p role="alert" className="mt-3 rounded-[12px] bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <div className="mt-4 space-y-2">{loading ? <p className="py-6 text-sm">Searching foods…</p> : result.items?.length ? result.items.map((food) => <button type="button" key={food.catalogEntityId || food.id} onClick={() => choose(food)} className={`w-full rounded-[14px] border p-3 text-left ${selected?.id === food.id ? 'border-[var(--fluent-color-brand-stroke-1)] bg-blue-50' : 'bg-white'}`}><div className="flex justify-between gap-3"><div><p className="text-sm font-semibold">{food.displayName}</p><p className="mt-1 text-xs text-gray-500">{food.category} · {(food.roles || []).map((role) => roles.find(([value]) => value === role)?.[1] || role).join(', ')}</p><span className={`mt-2 inline-flex rounded-full px-2 py-1 text-[11px] font-semibold ${food.mealEligibility === 'ELIGIBLE' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-800'}`}>{food.mealEligibility === 'ELIGIBLE' ? `Suitable for ${context.mealLabel}` : `Not recommended for ${context.mealLabel}`}</span></div><p className="text-xs text-gray-500">{food.defaultServing?.label || 'Serving unavailable'}</p></div><div className="mt-2"><NutritionFields nutrition={food.defaultServing?.nutrition} prefix={`${food.defaultServing?.label || 'Serving'} · `} /></div></button>) : <p className="rounded-[14px] border border-dashed bg-white p-5 text-sm">No food matches these filters.</p>}</div>
        <div className="mt-4 flex items-center justify-between"><button type="button" disabled={filters.offset === 0} onClick={() => set('offset', Math.max(0, filters.offset - PAGE_SIZE))} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Previous</button><span className="text-xs">{result.total || 0} foods</span><button type="button" disabled={!result.hasMore} onClick={() => set('offset', filters.offset + PAGE_SIZE)} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Next</button></div>
        {selected ? <div className="mt-5 rounded-[16px] border bg-white p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-[var(--fluent-color-neutral-foreground-3)]">2 · Adjust serving</p><h4 className="mt-1 font-semibold">Nutrition & serving preview</h4><p className="mt-1 text-xs text-gray-500">Fiteatsy validates and recalculates authoritative totals after the change.</p><div className="mt-3 grid items-center gap-2 sm:grid-cols-2"><select value={servingId} onChange={(event) => { setServingId(event.target.value); const next = selected.servings.find((item) => item.id === event.target.value); setMultiplier(next?.allowedMultipliers?.includes(1) ? 1 : next?.allowedMultipliers?.[0]); }} aria-label="Serving" className="rounded-[12px] border px-3 py-2 text-sm">{selected.servings?.filter((item) => item.active).map((item) => <option key={item.id} value={item.id}>{item.label} · {item.grams} g</option>)}</select><div className="flex items-center justify-between rounded-[12px] border px-2 py-1"><button type="button" aria-label="Decrease serving" disabled={!serving || serving.allowedMultipliers.indexOf(multiplier) <= 0} onClick={() => { const values = serving.allowedMultipliers; setMultiplier(values[Math.max(0, values.indexOf(multiplier) - 1)]); }} className="h-8 w-8 rounded-full text-lg font-semibold disabled:opacity-30">−</button><span className="text-sm font-semibold">{multiplier} × {serving?.label || 'serving'}</span><button type="button" aria-label="Increase serving" disabled={!serving || serving.allowedMultipliers.indexOf(multiplier) >= serving.allowedMultipliers.length - 1} onClick={() => { const values = serving.allowedMultipliers; setMultiplier(values[Math.min(values.length - 1, values.indexOf(multiplier) + 1)]); }} className="h-8 w-8 rounded-full text-lg font-semibold disabled:opacity-30">+</button></div></div><button type="button" disabled={!servingId || multiplier == null || (context.mode === 'serving' && selected.id !== context.component.foodId)} onClick={() => onSelect({ foodId: selected.id, servingId, multiplier })} className="mt-4 rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">3 · {context.mode === 'replace' ? 'Replace component' : context.mode === 'serving' ? 'Update serving' : 'Add to meal'}</button>{context.mode === 'serving' && selected.id !== context.component.foodId ? <p className="mt-2 text-xs text-amber-700">Select {context.component.foodDisplayNameSnapshot} to change only its serving.</p> : null}</div> : null}
      </div>
    </aside>
  </div>;
}

function LegacyOptionDetails({ option }) {
  return <div className="mt-3 grid gap-2 border-t pt-3 text-xs text-gray-600 sm:grid-cols-2"><span>Serving: {option.servingLabel}</span><span>Verification: {option.verificationStatus || 'Legacy plan record'}</span>{option.prepNote ? <span className="sm:col-span-2">Preparation: {option.prepNote}</span> : null}</div>;
}

const CommonFoodPlanEditor = forwardRef(function CommonFoodPlanEditor({ clientId, dietPlanId, planVersionId, lifecycle, initialOptions = [], legacyMealPlan = {}, generationRequestId = 0, readOnly = false, onStale, onDirtyChange, onProgressChange }, ref) {
  const [meals, setMeals] = useState([]);
  const [options, setOptions] = useState(initialOptions);
  const [selectedIds, setSelectedIds] = useState(() => new Set(initialOptions.map((option) => option.combinationId)));
  const [persistedIds, setPersistedIds] = useState(() => new Set(initialOptions.map((option) => option.combinationId)));
  const [expanded, setExpanded] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [explorer, setExplorer] = useState(null);
  const [lockedServings, setLockedServings] = useState({});
  const [activeMealHead, setActiveMealHead] = useState(COMMON_FOOD_MEALS[0][0]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const handledGenerationRequest = useRef(0);

  const legacyOptions = useMemo(() => legacyOptionsForUnifiedPlan(legacyMealPlan), [legacyMealPlan]);
  const typedOptions = useMemo(() => options.map((option) => ({ ...option, sourceType: commonFoodOptionType(option) })), [options]);
  const unifiedOptions = useMemo(() => [...legacyOptions, ...typedOptions], [legacyOptions, typedOptions]);
  const byMeal = useMemo(() => Object.fromEntries(COMMON_FOOD_MEALS.map(([head]) => [head, typedOptions.filter((item) => item.mealHead === head)])), [typedOptions]);
  const legacyByMeal = useMemo(() => Object.fromEntries(COMMON_FOOD_MEALS.map(([head]) => [head, legacyOptions.filter((item) => item.mealHead === head)])), [legacyOptions]);
  const generate = useCallback(async () => {
    setLoading(true); setError(''); setMessage('');
    try {
      const response = await generateFiteatsyCommonFoodPlan(clientId, dietPlanId, COMMON_FOOD_MEALS.map(([head]) => head));
      if (response?.supported === false) { setOptions([]); setMeals([]); setError(commonFoodErrorMessage({ data: { error: response.code } })); return; }
      const generated = (response?.meals || []).flatMap((meal) => meal.options || []);
      setMeals(response?.meals || []);
      setOptions((current) => {
        const byId = new Map(current.map((option) => [option.combinationId, option]));
        generated.forEach((option) => { if (!byId.has(option.combinationId)) byId.set(option.combinationId, option); });
        return [...byId.values()];
      });
      setDirty(false); setMessage('Candidate options refreshed. Existing saved selections were preserved; select exactly five for every meal, then save before review.');
    } catch (nextError) { setError(commonFoodErrorMessage(nextError, 'Unable to generate Diet Plan options.')); }
    finally { setLoading(false); }
  }, [clientId, dietPlanId]);
  const reload = useCallback(async () => {
    if (!clientId || !dietPlanId) return;
    try {
      const response = await readFiteatsyCommonFoodOptions(clientId, dietPlanId);
      const savedOptions = response?.options || [];
      setOptions(savedOptions); setSelectedIds(new Set(savedOptions.map((option) => option.combinationId))); setPersistedIds(new Set(savedOptions.map((option) => option.combinationId))); setDirty(false);
      setMessage(savedOptions.length ? 'Saved Diet Plan reloaded.' : 'No saved Diet Plan options yet.');
      if (isCommonFoodCombinationEngineEnabled && savedOptions.length < 35 && ['draft', 'changes_requested'].includes(lifecycle) && !readOnly) await generate();
    } catch (nextError) { setError(commonFoodErrorMessage(nextError, 'Unable to reload Diet Plan options.')); }
  }, [clientId, dietPlanId, generate, lifecycle, readOnly]);
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
    const selected = options.filter((option) => selectedIds.has(option.combinationId));
    const incomplete = COMMON_FOOD_MEALS.filter(([head]) => selected.filter((option) => option.mealHead === head).length !== 5);
    if (incomplete.length) {
      const nextError = `Select exactly five options for every meal before saving. Incomplete: ${incomplete.map(([, label]) => label).join(', ')}.`;
      setError(nextError);
      throw new Error(nextError);
    }
    setSaving(true); setError('');
    try {
      const response = await replaceFiteatsyCommonFoodSelection(clientId, dietPlanId, { expectedPlanVersionId, options: selected.map((option) => ({ optionId: option.combinationId, mealHead: option.mealHead, components: option.components.map(({ foodId, servingId, multiplier }) => ({ foodId, servingId, multiplier })) })) });
      const persisted = response?.options || [];
      const nextIds = new Set(persisted.map((option) => option.combinationId));
      setOptions(persisted); setSelectedIds(nextIds); setPersistedIds(nextIds); setDirty(false); setMessage(`Saved ${persisted.length} selected, server-validated options.`);
    } catch (nextError) { if (nextError?.status === 409) onStale?.(); setError(commonFoodErrorMessage(nextError)); throw nextError; }
    finally { setSaving(false); }
  };
  useImperativeHandle(ref, () => ({ save: saveAll, reload: () => reload(), generate }), [generate, options, planVersionId, reload, selectedIds]);
  const mutate = async (action) => {
    setError('');
    try { const next = await action(); setOptions((current) => current.map((item) => item.combinationId === next.combinationId ? next : item)); setDirty(false); setExplorer(null); setMessage('Option updated and recalculated by Fiteatsy.'); }
    catch (nextError) { if (nextError?.status === 409) onStale?.(); setError(commonFoodErrorMessage(nextError)); }
  };
  const openExplorer = (mode, option, component, mealLabel) => setExplorer({ mode, option, component, mealHead: option.mealHead, mealLabel });
  const toggleSelection = (option) => {
    const id = option.combinationId;
    const selectedForMeal = options.filter((item) => item.mealHead === option.mealHead && selectedIds.has(item.combinationId));
    if (!selectedIds.has(id) && selectedForMeal.length >= 5) { setError('A meal can have at most five selected options. Unselect one before choosing another.'); return; }
    setSelectedIds((current) => { const next = new Set(current); if (next.has(id)) next.delete(id); else next.add(id); return next; });
    setDirty(true); setError(''); setMessage('Selection updated. Save the Diet Plan to persist it.');
  };
  const selectFood = (component) => { const draft = { mealHead: explorer.option.mealHead, components: explorer.option.components.map(({ foodId, servingId, multiplier }) => ({ foodId, servingId, multiplier })) }; return mutate(() => explorer.mode === 'replace'
    ? replaceFiteatsyCommonFoodComponent(clientId, dietPlanId, explorer.option.combinationId, explorer.component.foodId, { expectedPlanVersionId: planVersionId, draft, component })
    : explorer.mode === 'serving'
      ? updateFiteatsyCommonFoodServing(clientId, dietPlanId, explorer.option.combinationId, explorer.component.foodId, { expectedPlanVersionId: planVersionId, servingId: component.servingId, multiplier: component.multiplier })
      : addFiteatsyCommonFoodComponent(clientId, dietPlanId, explorer.option.combinationId, { expectedPlanVersionId: planVersionId, draft, component })); };
  const toggleServingLock = (optionId, foodId) => setLockedServings((current) => { const next = new Set(current[optionId] || []); if (next.has(foodId)) next.delete(foodId); else next.add(foodId); return { ...current, [optionId]: next }; });
  const autoBalance = (option) => mutate(() => autoBalanceFiteatsyCommonFoodOption(clientId, dietPlanId, option.combinationId, { expectedPlanVersionId: planVersionId, lockedFoodIds: [...(lockedServings[option.combinationId] || [])] }));

  const hasOptions = unifiedOptions.length > 0 || meals.length > 0;
  const selectedTotal = typedOptions.filter((option) => selectedIds.has(option.combinationId)).length;
  const remainingTotal = Math.max(0, 35 - selectedTotal);
  useEffect(() => { onProgressChange?.({ selected: selectedTotal, remaining: remainingTotal, ready: selectedTotal === 35, dirty }); }, [dirty, onProgressChange, remainingTotal, selectedTotal]);
  return <section aria-label="Diet Plan" className="space-y-4">
    <div className="sticky top-[72px] z-10 rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[rgba(255,255,255,0.96)] p-4 shadow-[0_8px_24px_rgba(15,23,42,0.06)] backdrop-blur"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex items-center gap-2"><h4 className="text-base font-semibold">{selectedTotal} / 35 selected</h4>{selectedTotal === 35 ? <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-[11px] font-semibold text-green-700"><Check size={12} /> Ready</span> : null}</div><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{remainingTotal ? `${remainingTotal} selections remaining` : 'All seven meals are complete and ready to save.'} · {dirty ? 'Unsaved changes' : saving ? 'Saving…' : 'Saved'}</p><div className="mt-3 h-1.5 w-full max-w-[360px] overflow-hidden rounded-full bg-[var(--fluent-color-neutral-background-3)]"><div className="h-full rounded-full bg-[var(--fluent-color-brand-background)] transition-all" style={{ width: `${Math.min(100, (selectedTotal / 35) * 100)}%` }} /></div></div><div className="flex flex-wrap gap-2"><button type="button" onClick={() => setPreviewOpen(true)} className="rounded-full border px-3 py-2 text-xs font-semibold">Preview as Client</button><button type="button" onClick={() => void generate()} disabled={loading || readOnly} className="inline-flex items-center gap-1 rounded-full border px-3 py-2 text-xs font-semibold disabled:opacity-40"><Sparkles size={14} /> Generate alternatives</button></div></div>{error ? <p role="alert" aria-live="assertive" className="mt-3 rounded-[12px] bg-red-50 p-3 text-sm text-red-700">{error}{error.includes('newer plan version') ? <button type="button" onClick={() => reload()} className="ml-2 underline">Reload latest</button> : null}</p> : null}{message ? <p role="status" className="mt-3 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{message}</p> : null}</div>
    {!hasOptions ? <div className="rounded-[18px] border border-dashed bg-[var(--fluent-color-neutral-background-2)] p-8 text-center text-sm text-[var(--fluent-color-neutral-foreground-2)]">{loading ? 'Generating personalised options for all seven meals…' : 'No suitable options are available for this meal yet. Generate alternatives or build a meal from eligible foods.'}</div> : <div className="grid items-start gap-4 xl:grid-cols-[220px_minmax(0,1fr)]"><nav className="sticky top-[198px] flex gap-2 overflow-x-auto rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-2 xl:block xl:space-y-2" aria-label="Meal navigator">{COMMON_FOOD_MEALS.map(([head,label])=>{const count=(byMeal[head]||[]).filter((option)=>selectedIds.has(option.combinationId)).length;return <button key={head} type="button" onClick={()=>setActiveMealHead(head)} className={`flex min-w-[150px] items-center justify-between gap-3 rounded-[12px] px-3 py-2.5 text-left text-xs xl:w-full ${activeMealHead===head?'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]':'bg-[var(--fluent-color-neutral-background-1)] text-[var(--fluent-color-neutral-foreground-2)]'}`}><span className="font-semibold">{label}</span><span className="shrink-0 font-semibold">{count}/5{count===5?' ✓':''}</span></button>})}</nav><div className="space-y-3">{COMMON_FOOD_MEALS.filter(([head])=>head===activeMealHead).map(([head, label]) => {
      const generatedMeal = meals.find((item) => item.mealHead === head);
      const mealOptions = byMeal[head] || [];
      const coverage = generatedMeal?.coverage || { state: mealOptions.length >= 5 ? 'COMPLETE' : 'SHORTAGE', available: mealOptions.length, required: 5, missing: Math.max(0, 5 - mealOptions.length) };
      const selectedCount = mealOptions.filter((option) => selectedIds.has(option.combinationId)).length;
      return <div key={head} className="rounded-[18px] border bg-white p-4"><div className="flex flex-wrap justify-between gap-3"><div><h5 className="text-lg font-semibold">{label}</h5><p className="mt-1 text-xs text-gray-500">Target {formatNutrient(generatedMeal?.target?.kcal, 'kcal')} · {formatNutrient(generatedMeal?.target?.protein, 'g protein')}</p></div><div className="flex flex-wrap items-center gap-2"><span className={`rounded-full px-3 py-1 text-xs font-semibold ${selectedCount === 5 ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-800'}`}>{selectedCount}/5 {selectedCount === 5 ? 'ready' : 'selected'}</span>{!readOnly && mealOptions[0] ? <button type="button" onClick={() => openExplorer('add', mealOptions[0], null, label)} className="rounded-full border px-3 py-1.5 text-xs font-semibold">+ Build Meal</button> : null}</div></div>
        <div className="mt-3 space-y-2">{mealOptions.map((option, index) => { const key = option.combinationId || `${head}-${index}`; const selected = selectedIds.has(option.combinationId); const state = persistedIds.has(option.combinationId) ? 'SAVED' : selected ? 'SELECTED' : 'AVAILABLE'; return <article key={key} data-option-type={option.sourceType} data-selection-state={state} className={`rounded-[14px] border p-3 ${selected ? 'border-[var(--fluent-color-brand-stroke-1)] bg-[var(--fluent-color-brand-background-2)]' : 'bg-[var(--fluent-color-neutral-background-2)]'}`}><div className="flex items-start justify-between gap-3"><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2">{!readOnly && ['draft', 'changes_requested'].includes(lifecycle) ? <input type="checkbox" checked={selected} onChange={() => toggleSelection(option)} aria-label={`${selected ? 'Unselect' : 'Select'} ${optionTitle(option)}`} className="h-4 w-4 accent-[var(--fluent-color-brand-background)]" /> : null}<p className="text-sm font-semibold">{optionTitle(option)}</p>{selected ? <span className="rounded-full bg-white px-2 py-1 text-[11px] font-semibold text-green-700">{state === 'SAVED' ? 'Saved' : 'Selected'}</span> : null}</div><p className="mt-1 text-sm text-gray-600">{optionSummary(option)}</p><p className="mt-2 text-xs font-medium text-gray-700">{formatNutrient(option.nutrition?.kcal, 'kcal')} · {formatNutrient(option.nutrition?.protein, 'g protein')}</p>{option.mealQuality ? <div className="mt-2 flex flex-wrap gap-2"><span className="rounded-full bg-green-50 px-2 py-1 text-[11px] font-medium text-green-700">{option.mealQuality.calories === 'GOOD_FIT' ? 'Good calorie fit' : 'Review calorie fit'}</span><span className="rounded-full bg-green-50 px-2 py-1 text-[11px] font-medium text-green-700">{option.mealQuality.protein === 'GOOD_FIT' ? 'Good protein fit' : 'Review protein fit'}</span></div> : null}</div><button type="button" aria-expanded={Boolean(expanded[key])} aria-label={`${expanded[key] ? 'Hide' : 'View'} ${optionTitle(option)} details`} onClick={() => setExpanded((current) => ({ ...current, [key]: !current[key] }))} className="rounded-full p-2 focus-visible:outline focus-visible:outline-2"><ChevronRight size={17} className={expanded[key] ? 'rotate-90' : ''} /></button></div>{expanded[key] ? <><div className="mt-3 border-t pt-3"><NutritionFields nutrition={option.nutrition} /></div><ComponentTable option={option} readOnly={readOnly || !['draft', 'changes_requested'].includes(lifecycle)} locked={lockedServings[option.combinationId]} onLock={(foodId) => toggleServingLock(option.combinationId, foodId)} onExplore={(mode, component) => openExplorer(mode, option, component, label)} onRemove={(component) => mutate(() => removeFiteatsyCommonFoodComponent(clientId, dietPlanId, option.combinationId, component.foodId, planVersionId))} onServing={(component) => openExplorer('serving', option, component, label)} />{!readOnly && ['draft', 'changes_requested'].includes(lifecycle) ? <div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => openExplorer('replace', option, option.components?.[0], label)} className="rounded-full border px-3 py-1.5 text-xs font-semibold">Edit Meal</button><button type="button" onClick={() => autoBalance(option)} className="rounded-full border px-3 py-1.5 text-xs font-semibold">Auto-Balance</button></div> : null}</> : null}</article>; })}{!mealOptions.length ? <p className="rounded-[12px] border border-dashed p-4 text-sm text-gray-500">{loading ? 'Generating personalised options…' : `Only ${coverage.available || 0} suitable options currently satisfy serving, nutrition and source-governance requirements.`}</p> : null}</div>
        {(legacyByMeal[head] || []).length ? <details className="mt-4 rounded-[14px] border border-dashed p-3"><summary className="cursor-pointer text-xs font-semibold">Legacy compatibility records · {(legacyByMeal[head] || []).length} preserved</summary><div className="mt-3 space-y-2">{legacyByMeal[head].map((option, index) => <article key={option.combinationId} data-option-type="LEGACY" data-selection-state="AVAILABLE" className="rounded-[12px] bg-[var(--fluent-color-neutral-background-2)] p-3"><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-semibold">{option.displayName}</p><span className="rounded-full bg-white px-2 py-1 text-[11px] font-semibold text-gray-600">Legacy option</span><span className="rounded-full bg-white px-2 py-1 text-[11px] font-semibold text-gray-600">REFERENCE</span></div><p className="mt-1 text-xs text-gray-600">{option.servingLabel}</p><div className="mt-2"><NutritionFields nutrition={option.nutrition} /></div><LegacyOptionDetails option={option} /></article>)}</div></details> : null}
      </div>;
    })}</div></div>}
    {explorer ? <FoodExplorer context={explorer} clientId={clientId} onClose={() => setExplorer(null)} onSelect={selectFood} /> : null}
    {previewOpen ? <ClientPreview options={typedOptions.map((option) => ({ ...option, selected: selectedIds.has(option.combinationId) }))} onClose={() => setPreviewOpen(false)} /> : null}
  </section>;
});

export default CommonFoodPlanEditor;
