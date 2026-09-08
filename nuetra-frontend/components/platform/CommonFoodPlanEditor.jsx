import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { Archive, Check, ChevronRight, Copy, Lock, Search, Sparkles, Unlock, X } from 'lucide-react';
import {
  addFiteatsyCommonFoodComponent,
  activateFiteatsyMealTemplate,
  applyFiteatsyMealTemplate,
  archiveFiteatsyMealTemplate,
  autoBalanceFiteatsyCommonFoodOption,
  createFiteatsyMealTemplate,
  generateFiteatsyCommonFoodPlan,
  listFiteatsyMealTemplates,
  readFiteatsyCommonFoodOptions,
  removeFiteatsyCommonFoodComponent,
  replaceFiteatsyCommonFoodComponent,
  replaceFiteatsyCommonFoodSelection,
  searchFiteatsyCommonFoods,
  updateFiteatsyCommonFoodServing,
} from '../../lib/fiteatsyConsultantsApi';
import { isCommonFoodCombinationEngineEnabled } from '../../lib/dietFeatureFlags';
import { COMMON_FOOD_MEALS, commonFoodErrorMessage, commonFoodOptionType, formatNutrient, legacyOptionsForUnifiedPlan, optionSummary, optionTitle } from '../../lib/commonFoodUi.mjs';
import { ConsultantFoodProposalPanel } from './FoodProposalUx';

const roles = [['', 'All food groups'], ['STARCH', 'Staples'], ['GRAIN', 'Grains'], ['BREAD', 'Indian breads'], ['PULSE', 'Dal & pulses'], ['PROTEIN', 'Protein foods'], ['VEGETABLE', 'Vegetables'], ['FRUIT', 'Fruits'], ['DAIRY', 'Dairy'], ['FAT', 'Fats'], ['NUT_SEED', 'Nuts & seeds'], ['BEVERAGE', 'Drinks'], ['ACCOMPANIMENT', 'Accompaniments']];
const dietClasses = ['', 'VEGAN', 'VEGETARIAN', 'EGG', 'NON_VEGETARIAN'];
const PAGE_SIZE = 20;
const BUILD_MEAL_ROLES = [['STARCH', 'Staple'], ['PULSE', 'Protein / Pulse'], ['VEGETABLE', 'Vegetable'], ['ACCOMPANIMENT', 'Accompaniment'], ['OPTIONAL_EXTRA', 'Optional Extra']];

export function mealCalorieStatus(optionKcal, targetKcal) {
  const current = Number(optionKcal);
  const target = Number(targetKcal);
  if (!Number.isFinite(current) || !Number.isFinite(target) || target <= 0) return null;
  const variancePercent = ((current - target) / target) * 100;
  return {
    current,
    target,
    minimum: target * 0.95,
    maximum: target * 1.05,
    remaining: target - current,
    variancePercent,
    state: variancePercent < -5 ? 'BELOW_TARGET' : variancePercent > 5 ? 'ABOVE_TARGET' : 'WITHIN_TARGET',
  };
}

function compactNutrition(nutrition) {
  return `${formatNutrient(nutrition?.kcal, 'kcal')} · P ${formatNutrient(nutrition?.protein, 'g')} · C ${formatNutrient(nutrition?.carbohydrate, 'g')} · F ${formatNutrient(nutrition?.fat, 'g')} · Fibre ${formatNutrient(nutrition?.fibre, 'g')}`;
}

function servingSummary(option) {
  const multipliers = (option.components || []).map((item) => Number(item.multiplier)).filter(Number.isFinite);
  const multiplier = multipliers.length && multipliers.every((value) => value === multipliers[0]) ? multipliers[0] : 1;
  return `Serving: ${multiplier} portion`;
}

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
  return <div className="mt-3 divide-y rounded-[12px] border bg-white px-3" aria-label="Meal composition">
    {(option.components || []).map((component) => {
      const isLocked = locked?.has(component.foodId);
      return <section key={component.componentId || component.foodId} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
        <div className="min-w-0"><p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--fluent-color-neutral-foreground-3)]">{componentRole(component)}</p><p className="truncate text-sm font-semibold">{component.foodDisplayNameSnapshot} <span className="font-normal text-gray-500">· {component.label || `${component.multiplier} × ${component.servingDisplayNameSnapshot}`}</span></p></div>
        {!readOnly ? <div className="flex flex-wrap gap-3 text-xs font-semibold"><button type="button" onClick={() => onExplore('replace', component)} className="text-[var(--fluent-color-brand-foreground-link)]">Replace</button><button type="button" onClick={() => onServing(component)} className="text-[var(--fluent-color-brand-foreground-link)]">Edit quantity</button><button type="button" aria-pressed={isLocked} onClick={() => onLock(component.foodId)} className="inline-flex items-center gap-1 text-gray-600">{isLocked ? <Unlock size={13} /> : <Lock size={13} />}{isLocked ? 'Unlock' : 'Lock'}</button><button type="button" onClick={() => onRemove(component)} className="text-[var(--fluent-color-status-danger-foreground)]">Remove</button></div> : <span className="text-xs text-gray-500">{formatNutrient(component.grams, 'g')}</span>}
      </section>;
    })}
  </div>;
}

function ClientPreview({ options, onClose }) {
  const selected = options.filter((option) => option.selected);
  return <div role="dialog" aria-modal="true" aria-label="Client Diet Plan preview" className="fixed inset-0 z-[95] overflow-y-auto bg-[rgba(15,23,42,0.55)] p-4 sm:p-8" onClick={onClose}><div className="mx-auto max-w-[760px] rounded-[24px] bg-white shadow-2xl" onClick={(event) => event.stopPropagation()}><header className="sticky top-0 z-10 flex items-center justify-between rounded-t-[24px] border-b bg-white px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--fluent-color-brand-foreground-link)]">Preview as Client</p><h3 className="mt-1 text-xl font-semibold">Your active Diet Plan</h3></div><button type="button" aria-label="Close Client Preview" onClick={onClose} className="flex h-10 w-10 items-center justify-center rounded-full border"><X size={18} /></button></header><div className="space-y-6 p-5"><p className="rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] p-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Choose any one option from each meal. This preview contains only the selected client-facing plan—never the candidate pool or internal audit data.</p>{COMMON_FOOD_MEALS.map(([head, label]) => <section key={head}><div className="flex items-center justify-between"><h4 className="text-lg font-semibold">{label}</h4><span className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">Choose any one</span></div><div className="mt-2 space-y-2">{selected.filter((option) => option.mealHead === head).map((option) => <article key={option.combinationId} className="rounded-[14px] border p-3"><p className="text-sm font-semibold">{optionTitle(option)}</p><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{optionSummary(option)}</p><p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{formatNutrient(option.nutrition?.kcal, 'kcal')} · {formatNutrient(option.nutrition?.protein, 'g protein')}</p></article>)}</div></section>)}</div></div></div>;
}

function TemplateLibrary({ clientId, dietPlanId, mealHead, initialVisibility = '', onApply, onClose }) {
  const [query,setQuery]=useState(''); const [visibility,setVisibility]=useState(initialVisibility); const [offset,setOffset]=useState(0); const [result,setResult]=useState({items:[],total:0}); const [error,setError]=useState(''); const [loading,setLoading]=useState(false);
  const load=useCallback(async()=>{setLoading(true);setError('');try{setResult(await listFiteatsyMealTemplates({search:query,mealHead,visibility,limit:PAGE_SIZE,offset}))}catch(e){setError(commonFoodErrorMessage(e,'Templates could not be loaded.'))}finally{setLoading(false)}},[mealHead,offset,query,visibility]);
  useEffect(()=>{const timer=window.setTimeout(()=>void load(),250);return()=>window.clearTimeout(timer)},[load]);
  const apply=async(template)=>{setLoading(true);setError('');try{const option=await applyFiteatsyMealTemplate(clientId,dietPlanId,template.id,template.revision.id);onApply(option);onClose()}catch(e){setError(commonFoodErrorMessage(e,'This template cannot be applied safely to this client.'))}finally{setLoading(false)}};
  return <div role="dialog" aria-modal="true" aria-label="Meal Template Library" className="fixed inset-0 z-[96] bg-[rgba(15,23,42,0.45)] p-4" onClick={onClose}><div className="mx-auto max-h-full max-w-[760px] overflow-y-auto rounded-[24px] bg-white p-5" onClick={(e)=>e.stopPropagation()}><header className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.1em] text-blue-700">Reusable meal structures</p><h3 className="text-xl font-semibold">Template Library</h3></div><button type="button" aria-label="Close Template Library" onClick={onClose} className="h-10 w-10 rounded-full border">×</button></header><div className="mt-4 grid gap-2 sm:grid-cols-[1fr_180px]"><input value={query} onChange={(e)=>{setQuery(e.target.value);setOffset(0)}} placeholder="Search templates or foods" className="rounded-[12px] border px-3 py-2"/><select value={visibility} onChange={(e)=>{setVisibility(e.target.value);setOffset(0)}} className="rounded-[12px] border px-3 py-2" aria-label="Template owner filter"><option value="">My and Team Templates</option><option value="PRIVATE">My Templates</option><option value="TEAM">Team Templates</option></select></div>{error?<p role="alert" className="mt-3 rounded-[12px] bg-red-50 p-3 text-sm text-red-700">{error}</p>:null}<div className="mt-4 space-y-3">{loading?<p className="text-sm">Loading templates…</p>:result.items?.map((template)=><article key={template.id} className="rounded-[16px] border p-4"><div className="flex items-start justify-between gap-3"><div><h4 className="font-semibold">{template.revision.name}</h4><p className="text-xs text-gray-500">{template.revision.mealHead.replaceAll('_',' ')} · Revision {template.revision.number} · {template.visibility==='TEAM'?'Team Template':'My Template'}</p><p className="mt-2 text-sm text-gray-600">{template.revision.components.map((item)=>item.catalogEntityId).join(' · ')}</p><p className="mt-2 text-xs text-gray-500">Nutrition is recalculated for each client.</p></div><button type="button" disabled={loading} onClick={()=>void apply(template)} className="rounded-full bg-blue-700 px-4 py-2 text-xs font-semibold text-white">Apply</button></div></article>)}</div>{!loading&&!result.items?.length?<p className="mt-4 rounded-[14px] border border-dashed p-5 text-sm">No active templates match this meal.</p>:null}<div className="mt-4 flex items-center justify-between"><button type="button" disabled={loading||offset===0} onClick={()=>setOffset(Math.max(0,offset-PAGE_SIZE))} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Previous</button><span className="text-xs">{result.total||0} templates</span><button type="button" disabled={loading||offset+PAGE_SIZE>=(result.total||0)} onClick={()=>setOffset(offset+PAGE_SIZE)} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Next</button></div></div></div>;
}

function SaveTemplateDialog({ option, locked, onClose, onSaved }) {
  const [name,setName]=useState(optionTitle(option));const [description,setDescription]=useState('');const [visibility,setVisibility]=useState('PRIVATE');const [teamId,setTeamId]=useState('');const [error,setError]=useState('');const [saving,setSaving]=useState(false);
  const save=async()=>{setSaving(true);setError('');try{const created=await createFiteatsyMealTemplate({name,description:description||undefined,mealHead:option.mealHead,mealStructure:{source:'CONSULTANT_CUSTOM_MEAL'},components:option.components.map((item,index)=>({semanticRole:item.componentRole||item.role,catalogEntityId:item.foodId,servingSelection:{servingId:item.servingId,multiplier:item.multiplier},servingLock:locked?.has(item.foodId)||false,order:index})),visibility,...(visibility==='TEAM'?{teamId}:{})});onSaved(created);onClose()}catch(e){setError(commonFoodErrorMessage(e,'Template could not be saved.'))}finally{setSaving(false)}};
  return <div role="dialog" aria-modal="true" aria-label="Save as Template" className="fixed inset-0 z-[97] bg-[rgba(15,23,42,0.45)] p-4" onClick={onClose}><form className="mx-auto mt-16 max-w-[520px] rounded-[24px] bg-white p-5" onClick={(e)=>e.stopPropagation()} onSubmit={(e)=>{e.preventDefault();void save()}}><div className="flex items-center justify-between"><h3 className="text-xl font-semibold">Save as Template</h3><button type="button" onClick={onClose} aria-label="Close Save as Template">×</button></div><label className="mt-4 block text-sm font-semibold">Template Name<input required maxLength={120} value={name} onChange={(e)=>setName(e.target.value)} className="mt-1 w-full rounded-[12px] border px-3 py-2 font-normal"/></label><label className="mt-3 block text-sm font-semibold">Description (optional)<textarea maxLength={600} value={description} onChange={(e)=>setDescription(e.target.value)} className="mt-1 w-full rounded-[12px] border px-3 py-2 font-normal"/></label><label className="mt-3 block text-sm font-semibold">Visibility<select value={visibility} onChange={(e)=>setVisibility(e.target.value)} className="mt-1 w-full rounded-[12px] border px-3 py-2 font-normal"><option value="PRIVATE">Only Me</option><option value="TEAM">My Team</option></select></label>{visibility==='TEAM'?<label className="mt-3 block text-sm font-semibold">Team<input required value={teamId} onChange={(e)=>setTeamId(e.target.value)} className="mt-1 w-full rounded-[12px] border px-3 py-2 font-normal"/></label>:null}{error?<p role="alert" className="mt-3 text-sm text-red-700">{error}</p>:null}<div className="mt-5 flex justify-end gap-2"><button type="button" onClick={onClose} className="rounded-full border px-4 py-2 text-sm">Cancel</button><button disabled={saving} className="rounded-full bg-blue-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{saving?'Saving…':'Save Template'}</button></div></form></div>;
}

function FoodExplorer({ context, clientId, onClose, onSelect, onOpenTemplates }) {
  const [panel, setPanel] = useState('library');
  const [filters, setFilters] = useState({ scope: 'RECOMMENDED', search: '', category: '', componentRole: context.targetRole || context.component?.componentRole || context.component?.role || '', referenceState: '', nutritionStatus: '', entityType: '', dietClass: '', proteinMin: '', proteinMax: '', caloriesMin: '', caloriesMax: '', offset: 0 });
  const [moreFilters, setMoreFilters] = useState(false);
  const [result, setResult] = useState({ items: [], total: 0, hasMore: false });
  const [selected, setSelected] = useState(null);
  const [servingId, setServingId] = useState('');
  const [multiplier, setMultiplier] = useState(1);
  const [applyScope, setApplyScope] = useState(context.defaultApplyScope || 'THIS_OPTION');
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
    setSelected(food); setError('');
    if (food.addToMealEligible === false) { setServingId(''); setMultiplier(1); return; }
    const serving = food.servings?.find((item) => item.active && item.isDefault) || food.servings?.find((item) => item.active);
    setSelected(food); setServingId(serving?.id || ''); setMultiplier(serving?.allowedMultipliers?.includes(1) ? 1 : serving?.allowedMultipliers?.[0]);
  };
  const serving = selected?.servings?.find((item) => item.id === servingId);
  const roleLabel = (value) => roles.find(([role]) => role === value)?.[1] || String(value || '').replaceAll('_', ' ');
  const stateLabel = (value) => String(value || 'As catalogued').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
  const unavailableReason = selected?.pendingReason || (selected?.mealEligibility === 'NOT_ELIGIBLE' ? `This food is not suitable for ${context.mealLabel} in the current meal structure.` : 'This food is not currently available for authoritative Diet calculation.');
  const set = (key, value) => setFilters((current) => ({ ...current, [key]: value, offset: key === 'offset' ? value : 0 }));
  return <div role="dialog" aria-modal="true" aria-label="Food Explorer" className="fixed inset-0 z-[90] bg-[rgba(15,23,42,0.3)]" onClick={onClose}>
    <aside className="absolute right-0 top-0 flex h-full w-full max-w-[760px] flex-col bg-[var(--fluent-color-neutral-background-canvas)] shadow-2xl" onClick={(event) => event.stopPropagation()}>
      <header className="border-b border-[var(--fluent-color-neutral-stroke-1)] p-5"><div className="flex items-center justify-between"><div><h3 className="text-xl font-semibold">{context.mode === 'replace' ? 'Replace Food' : 'Add Food'}</h3><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{context.mealLabel} · changes stay in this meal</p>{filters.componentRole?<p className="mt-1 text-xs font-semibold text-[var(--fluent-color-brand-foreground-link)]">Target role: {roleLabel(filters.componentRole)}</p>:null}</div><button type="button" aria-label="Close Food Library" onClick={onClose} className="flex h-10 w-10 items-center justify-center rounded-full border"><X size={18} /></button></div><div role="tablist" aria-label="Add food options" className="mt-4 flex gap-1 rounded-[12px] bg-gray-100 p-1"><button role="tab" aria-selected={panel==='library'} type="button" onClick={()=>setPanel('library')} className={`flex-1 rounded-[9px] px-3 py-2 text-sm font-semibold ${panel==='library'?'bg-white text-blue-700 shadow-sm':'text-gray-600'}`}>Food Library</button><button role="tab" aria-selected={panel==='proposal'} type="button" onClick={()=>setPanel('proposal')} className={`flex-1 rounded-[9px] px-3 py-2 text-sm font-semibold ${panel==='proposal'?'bg-white text-blue-700 shadow-sm':'text-gray-600'}`}>Propose New Food</button></div></header>
      {panel==='proposal'?<div className="min-h-0 flex-1 overflow-y-auto p-5"><ConsultantFoodProposalPanel onUseExisting={(item)=>{setPanel('library');set('search',item.canonicalName)}} /></div>:<div className="flex min-h-0 flex-1 flex-col p-5">
        <div className="shrink-0"><p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-[var(--fluent-color-neutral-foreground-3)]">Choose a food or reusable meal</p><div className="mb-3 flex flex-wrap gap-1 rounded-[14px] bg-white p-1 shadow-sm" aria-label="Food Explorer scope"><button type="button" aria-pressed={filters.scope === 'RECOMMENDED'} onClick={() => set('scope', 'RECOMMENDED')} className={`rounded-[10px] px-3 py-2 text-xs font-semibold ${filters.scope === 'RECOMMENDED' ? 'bg-[var(--fluent-color-brand-background)] text-white' : 'text-gray-600'}`}>Recommended</button><button type="button" onClick={() => onOpenTemplates('PRIVATE')} className="rounded-[10px] px-3 py-2 text-xs font-semibold text-gray-600">My Templates</button><button type="button" onClick={() => onOpenTemplates('TEAM')} className="rounded-[10px] px-3 py-2 text-xs font-semibold text-gray-600">Team Templates</button><button type="button" aria-pressed={filters.scope === 'ALL'} onClick={() => set('scope', 'ALL')} className={`rounded-[10px] px-3 py-2 text-xs font-semibold ${filters.scope === 'ALL' ? 'bg-[var(--fluent-color-brand-background)] text-white' : 'text-gray-600'}`}>All Foods &amp; Dishes · {result.totals?.catalogue ?? result.total ?? 0}</button></div><label className="relative block"><Search className="absolute left-3 top-3 text-gray-400" size={17} /><span className="sr-only">Search foods by dish, alias or common name</span><input ref={inputRef} value={filters.search} onChange={(event) => set('search', event.target.value)} placeholder="Search bhindi, okra, lauki, ragi…" className="w-full rounded-[14px] border bg-white py-2.5 pl-10 pr-3 text-sm" /></label>
        <div className="mt-3 grid gap-2 sm:grid-cols-4"><input value={filters.category} onChange={(event) => set('category', event.target.value)} placeholder="Food Type" aria-label="Food Type filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm" /><select value={filters.componentRole} onChange={(event) => set('componentRole', event.target.value)} aria-label="Role filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm">{roles.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select><select value={filters.referenceState} onChange={(event) => set('referenceState', event.target.value)} aria-label="Food State filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm"><option value="">All Food States</option>{(result.facets?.states || []).map(({ value, count }) => <option key={value} value={value}>{stateLabel(value)} · {count}</option>)}</select><select value={filters.nutritionStatus} onChange={(event) => set('nutritionStatus', event.target.value)} aria-label="Nutrition Status filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm"><option value="">All Nutrition Statuses</option><option value="NUTRITION_VERIFIED">Verified for Diet Use</option><option value="REFERENCE_ONLY">Reference Only</option><option value="NUTRITION_PENDING">Verification Pending</option></select></div><button type="button" aria-expanded={moreFilters} onClick={() => setMoreFilters((value) => !value)} className="mt-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground-link)]">{moreFilters ? 'Hide More Filters' : 'More Filters'}</button>{moreFilters ? <div className="mt-2 grid gap-2 sm:grid-cols-3"><select value={filters.entityType} onChange={(event) => set('entityType', event.target.value)} aria-label="Entity type filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm"><option value="">All Entity Types</option><option value="FOOD">Food</option><option value="READY_TO_EAT">Ready-to-Eat</option><option value="PREPARED_DISH">Prepared Dish</option><option value="INGREDIENT_ONLY">Ingredient Only</option><option value="CONDIMENT">Condiment</option><option value="TOPPING">Topping</option></select><select value={filters.dietClass} onChange={(event) => set('dietClass', event.target.value)} aria-label="Diet classification filter" className="rounded-[12px] border bg-white px-3 py-2 text-sm">{dietClasses.map((item) => <option key={item} value={item}>{item || 'All diet classes'}</option>)}</select><div className="grid grid-cols-2 gap-2"><input type="number" value={filters.proteinMin} onChange={(event) => set('proteinMin', event.target.value)} placeholder="Protein min" aria-label="Minimum protein" className="min-w-0 rounded-[12px] border bg-white px-3 py-2 text-sm" /><input type="number" value={filters.caloriesMax} onChange={(event) => set('caloriesMax', event.target.value)} placeholder="kcal max" aria-label="Maximum calories" className="min-w-0 rounded-[12px] border bg-white px-3 py-2 text-sm" /></div></div> : null}</div>
        {error ? <p role="alert" className="mt-3 rounded-[12px] bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {filters.scope === 'ALL' ? <details className="mt-3 rounded-[10px] bg-blue-50 px-3 py-2 text-xs text-blue-900"><summary className="cursor-pointer font-medium">ⓘ Reference-only foods are searchable but cannot be prescribed until nutrition verification is complete.</summary><p className="mt-2">They remain useful for alias discovery, preparation-state review and finding governed prepared alternatives.</p></details> : null}
        <div className="mt-3 min-h-0 flex-1 space-y-2 overflow-y-auto pb-3" role="listbox" aria-label="Food search results">{loading ? <p className="py-6 text-sm">Searching foods…</p> : result.items?.length ? result.items.map((food) => { const referenceOnly=food.nutritionDisplayMode !== 'AUTHORITATIVE_SERVING'; const foodNutrition=food.defaultServing?.nutrition; return <button type="button" role="option" aria-selected={selected?.id === food.id} key={food.catalogEntityId || food.id} onClick={() => choose(food)} className={`w-full rounded-[12px] border px-3 py-2 text-left ${selected?.id === food.id ? 'border-2 border-[var(--fluent-color-brand-stroke-1)] bg-blue-50' : 'bg-white'}`}><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="truncate text-sm font-semibold">{food.displayName}</p>{food.aliases?.length ? <p className="truncate text-xs text-gray-500">{food.aliases.slice(0,3).join(' · ')}</p> : null}<p className="mt-1 text-xs text-gray-600">{stateLabel(food.entityType)} · {stateLabel(food.foodState)}{food.roles?.length ? ` · ${food.roles.map(roleLabel).join(', ')}` : ''}</p></div><span className={`shrink-0 rounded-full px-2 py-1 text-[11px] font-semibold ${referenceOnly ? 'bg-amber-50 text-amber-800' : 'bg-green-50 text-green-700'}`}>{referenceOnly ? 'Reference catalogue · ' : ''}{food.displayStatus}</span></div>{referenceOnly ? <div className="mt-1.5 flex items-center justify-between gap-3 text-xs"><span className="text-amber-800">{food.servingDisplay || 'Serving profile pending'}</span><span className="font-semibold text-blue-700">{food.primaryAction}</span></div> : <div className="mt-1.5 flex items-center justify-between gap-3 text-xs"><span>{food.servingDisplay} · {formatNutrient(foodNutrition?.kcal, 'kcal')} · {formatNutrient(foodNutrition?.protein, 'g protein')}</span><span className={food.primaryActionEnabled ? 'font-semibold text-green-700' : 'text-amber-700'}>{food.primaryAction}</span></div>}</button>; }) : <p className="rounded-[14px] border border-dashed bg-white p-5 text-sm">No food matches these filters.</p>}</div>
        <div className="mt-4 flex items-center justify-between"><button type="button" disabled={filters.offset === 0} onClick={() => set('offset', Math.max(0, filters.offset - PAGE_SIZE))} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Previous</button><span className="text-xs">{result.total || 0} foods</span><button type="button" disabled={!result.hasMore} onClick={() => set('offset', filters.offset + PAGE_SIZE)} className="rounded-full border px-3 py-2 text-xs disabled:opacity-40">Next</button></div>
        {selected ? <div className="sticky bottom-0 mt-2 shrink-0 rounded-[16px] border bg-white p-3 shadow-[0_-8px_24px_rgba(15,23,42,0.12)]" aria-live="polite"><div className="flex items-start justify-between gap-3"><div><p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-gray-500">Selected</p><h4 className="font-semibold">{selected.displayName}</h4></div>{selected.primaryActionEnabled ? <p className="text-xs font-semibold text-green-700">{formatNutrient(selected.defaultServing?.nutrition?.kcal, 'kcal')} · {formatNutrient(selected.defaultServing?.nutrition?.protein, 'g protein')}</p> : null}</div>{selected.primaryActionEnabled ? <><div className="mt-2 grid items-center gap-2 sm:grid-cols-[1fr_1fr_auto]"><select value={servingId} onChange={(event) => { setServingId(event.target.value); const next = selected.servings.find((item) => item.id === event.target.value); setMultiplier(next?.allowedMultipliers?.includes(1) ? 1 : next?.allowedMultipliers?.[0]); }} aria-label="Serving" className="rounded-[12px] border px-3 py-2 text-sm">{selected.servings?.filter((item) => item.active).map((item) => <option key={item.id} value={item.id}>{item.label} · {item.grams} g</option>)}</select><div className="flex items-center justify-between rounded-[12px] border px-2 py-1"><button type="button" aria-label="Decrease serving" disabled={!serving || serving.allowedMultipliers.indexOf(multiplier) <= 0} onClick={() => { const values = serving.allowedMultipliers; setMultiplier(values[Math.max(0, values.indexOf(multiplier) - 1)]); }} className="h-8 w-8 rounded-full text-lg font-semibold disabled:opacity-30">−</button><span className="text-sm font-semibold">{multiplier} × {serving?.label}</span><button type="button" aria-label="Increase serving" disabled={!serving || serving.allowedMultipliers.indexOf(multiplier) >= serving.allowedMultipliers.length - 1} onClick={() => { const values = serving.allowedMultipliers; setMultiplier(values[Math.min(values.length - 1, values.indexOf(multiplier) + 1)]); }} className="h-8 w-8 rounded-full text-lg font-semibold disabled:opacity-30">+</button></div><button type="button" disabled={!servingId || multiplier == null || (context.mode === 'serving' && selected.id !== context.component.foodId)} onClick={() => onSelect({ foodId: selected.id, servingId, multiplier, applyScope })} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">{context.mode === 'replace' ? 'Replace Food' : context.mode === 'serving' ? 'Update serving' : 'Add to Meal'}</button></div>{context.mode === 'add' && context.optionIds?.length > 1 ? <fieldset className="mt-2"><legend className="text-xs font-semibold text-gray-600">Apply to</legend><div className="mt-1 flex flex-wrap gap-3">{[['THIS_OPTION','This option'],['SELECTED_OPTIONS','Selected options'],['ALL_FIVE','All 5 options']].map(([value,label])=><label key={value} className="flex items-center gap-1.5 text-xs"><input type="radio" name="apply-scope" value={value} checked={applyScope===value} onChange={()=>setApplyScope(value)} />{label}</label>)}</div></fieldset> : null}</> : <div className="mt-2"><p className="text-sm font-semibold text-amber-800">{selected.displayStatus}</p><p className="mt-1 text-xs text-gray-600">{unavailableReason}</p>{selected.relatedPreparedItems?.length ? <div className="mt-2 text-xs"><p className="font-semibold">Related prepared options</p>{selected.relatedPreparedItems.map((item) => <p key={item.id} className="mt-1 text-blue-700">{item.displayName}</p>)}</div> : <p className="mt-2 text-xs text-gray-600">No prepared {selected.displayName} dish is available yet.</p>}<button type="button" disabled className="mt-2 rounded-full bg-gray-100 px-4 py-2 text-sm font-semibold text-gray-600">{selected.primaryAction}</button></div>}</div> : null}
      </div>}
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
  const [templateLibrary, setTemplateLibrary] = useState(false);
  const [templateMeal, setTemplateMeal] = useState(null);
  const [generationSnapshot, setGenerationSnapshot] = useState(null);
  const [buildMealHead, setBuildMealHead] = useState('');
  const [buildOptionIds, setBuildOptionIds] = useState(new Set());
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
      setGenerationSnapshot(response?.generationSnapshot || null);
      setMeals(response?.meals || []);
      setOptions((current) => {
        const byId = new Map(current.map((option) => [option.combinationId, option]));
        generated.forEach((option) => { if (!byId.has(option.combinationId)) byId.set(option.combinationId, option); });
        const merged = [...byId.values()];
        setSelectedIds((currentSelected) => {
          const next = new Set();
          COMMON_FOOD_MEALS.forEach(([head]) => {
            const mealOptions = merged.filter((option) => option.mealHead === head);
            const retained = mealOptions.filter((option) => currentSelected.has(option.combinationId));
            [...retained, ...mealOptions.filter((option) => !currentSelected.has(option.combinationId))].slice(0, 5).forEach((option) => next.add(option.combinationId));
          });
          return next;
        });
        return merged;
      });
      setDirty(true); setMessage('Generated options are included by default. Review the five choices for each meal, then save.');
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
  const openExplorer = (mode, option, component, mealLabel, targetRole = '', extra = {}) => setExplorer({ mode, option, component, mealHead: option.mealHead, mealLabel, targetRole, ...extra });
  const toggleSelection = (option) => {
    const id = option.combinationId;
    const selectedForMeal = options.filter((item) => item.mealHead === option.mealHead && selectedIds.has(item.combinationId));
    if (!selectedIds.has(id) && selectedForMeal.length >= 5) { setError('A meal can have at most five selected options. Unselect one before choosing another.'); return; }
    setSelectedIds((current) => { const next = new Set(current); if (next.has(id)) next.delete(id); else next.add(id); return next; });
    setDirty(true); setError(''); setMessage('Selection updated. Save the Diet Plan to persist it.');
  };
  const setMealSelection = (mealHead, include) => {
    setSelectedIds((current) => { const next = new Set(current); options.filter((option) => option.mealHead === mealHead).forEach((option, index) => { if (include && index < 5) next.add(option.combinationId); else next.delete(option.combinationId); }); return next; });
    setDirty(true); setError(''); setMessage(include ? 'All five meal options included.' : 'Meal options cleared.');
  };
  const selectFood = async (component) => {
    const { applyScope: _applyScope, ...foodComponent } = component;
    if (explorer.mode === 'add' && explorer.optionIds?.length > 1 && component.applyScope !== 'THIS_OPTION') {
      const targets = component.applyScope === 'ALL_FIVE' ? explorer.optionIds : explorer.selectedOptionIds;
      setError('');
      try {
        const updated = [];
        for (const optionId of targets) {
          const option = options.find((item) => item.combinationId === optionId);
          if (!option) continue;
          const draft = { mealHead: option.mealHead, components: option.components.map(({ foodId, servingId, multiplier }) => ({ foodId, servingId, multiplier })) };
          updated.push(await addFiteatsyCommonFoodComponent(clientId, dietPlanId, optionId, { expectedPlanVersionId: planVersionId, draft, component: foodComponent }));
        }
        setOptions((current) => current.map((item) => updated.find((next) => next.combinationId === item.combinationId) || item));
        setDirty(false); setExplorer(null); setMessage(`Component added independently to ${updated.length} meal options.`);
      } catch (nextError) { if (nextError?.status === 409) onStale?.(); setError(commonFoodErrorMessage(nextError)); }
      return;
    }
    const draft = { mealHead: explorer.option.mealHead, components: explorer.option.components.map(({ foodId, servingId, multiplier }) => ({ foodId, servingId, multiplier })) }; return mutate(() => explorer.mode === 'replace'
    ? replaceFiteatsyCommonFoodComponent(clientId, dietPlanId, explorer.option.combinationId, explorer.component.foodId, { expectedPlanVersionId: planVersionId, draft, component: foodComponent })
    : explorer.mode === 'serving'
      ? updateFiteatsyCommonFoodServing(clientId, dietPlanId, explorer.option.combinationId, explorer.component.foodId, { expectedPlanVersionId: planVersionId, servingId: component.servingId, multiplier: component.multiplier })
      : addFiteatsyCommonFoodComponent(clientId, dietPlanId, explorer.option.combinationId, { expectedPlanVersionId: planVersionId, draft, component: foodComponent })); };
  const toggleServingLock = (optionId, foodId) => setLockedServings((current) => { const next = new Set(current[optionId] || []); if (next.has(foodId)) next.delete(foodId); else next.add(foodId); return { ...current, [optionId]: next }; });
  const autoBalance = (option) => mutate(() => autoBalanceFiteatsyCommonFoodOption(clientId, dietPlanId, option.combinationId, { expectedPlanVersionId: planVersionId, lockedFoodIds: [...(lockedServings[option.combinationId] || [])] }));
  const acceptAppliedTemplate = (option) => { setOptions((current) => [...current.filter((item) => item.combinationId !== option.combinationId), option]); setSelectedIds((current) => new Set([...current, option.combinationId])); setDirty(true); setMessage('Template revalidated for this client. Review it, then save the Diet Plan.'); };

  const hasOptions = unifiedOptions.length > 0 || meals.length > 0;
  const selectedTotal = typedOptions.filter((option) => selectedIds.has(option.combinationId)).length;
  const remainingTotal = Math.max(0, 35 - selectedTotal);
  useEffect(() => { onProgressChange?.({ selected: selectedTotal, remaining: remainingTotal, ready: selectedTotal === 35, dirty }); }, [dirty, onProgressChange, remainingTotal, selectedTotal]);
  return <section aria-label="Diet Plan" className="space-y-4">
    {!readOnly ? <div className="flex flex-wrap gap-2"><button type="button" onClick={() => setTemplateLibrary(true)} className="inline-flex items-center gap-1 rounded-full border px-3 py-2 text-xs font-semibold"><Copy size={14} /> Template Library</button><button type="button" disabled={dirty || !typedOptions.find((option) => selectedIds.has(option.combinationId))} title={dirty ? 'Save the Diet Plan before creating a reusable template.' : 'Save a complete selected meal as a reusable template.'} onClick={() => setTemplateMeal(typedOptions.find((option) => selectedIds.has(option.combinationId)))} className="rounded-full border px-3 py-2 text-xs font-semibold disabled:opacity-40">Save selected meal as Template</button></div> : null}
    {generationSnapshot?<details className="rounded-[14px] border bg-[var(--fluent-color-neutral-background-2)] px-4 py-3"><summary className="cursor-pointer text-sm font-semibold">Plan Context · Generated using current client profile, food preferences and available biomarkers</summary><div className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4"><div><p className="text-xs text-gray-500">Diet preference</p><p className="font-semibold">{generationSnapshot.dietPreference||'Not provided'}</p></div><div><p className="text-xs text-gray-500">Calorie target</p><p className="font-semibold">{generationSnapshot.dailyTargets?.calories!=null?`${generationSnapshot.dailyTargets.calories} kcal`:'Not calculated'}</p></div><div><p className="text-xs text-gray-500">Biomarkers available</p><p className="font-semibold">{generationSnapshot.biomarkers?.length||0}</p></div><div><p className="text-xs text-gray-500">Biomarkers affecting ranking</p><p className="font-semibold">{generationSnapshot.biomarkers?.filter((item)=>item.generationEffect==='RANKING').map((item)=>item.canonicalMarkerName).join(', ')||'No governed generation rule'}</p></div></div></details>:null}
    <div className="sticky top-[72px] z-10 rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[rgba(255,255,255,0.96)] p-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)] backdrop-blur"><div className="flex flex-wrap items-center justify-between gap-3"><div><div className="flex items-center gap-2"><h4 className="text-sm font-semibold">{selectedTotal} / 35 included</h4>{selectedTotal === 35 ? <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-[11px] font-semibold text-green-700"><Check size={12} /> Ready</span> : null}</div><p className="text-xs text-[var(--fluent-color-neutral-foreground-2)]">{remainingTotal ? `${remainingTotal} choices remaining` : 'All seven meals complete'} · {dirty ? 'Unsaved changes' : saving ? 'Saving…' : 'Saved'}</p></div><div className="flex flex-wrap gap-2"><button type="button" onClick={() => setPreviewOpen(true)} className="rounded-full border px-3 py-1.5 text-xs font-semibold">Preview as Client</button><button type="button" onClick={() => void generate()} disabled={loading || readOnly} className="inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-xs font-semibold disabled:opacity-40"><Sparkles size={14} /> Generate alternatives</button></div></div>{error ? <p role="alert" aria-live="assertive" className="mt-2 rounded-[12px] bg-red-50 p-2.5 text-sm text-red-700">{error}{error.includes('newer plan version') ? <button type="button" onClick={() => reload()} className="ml-2 underline">Reload latest</button> : null}</p> : null}{message ? <p role="status" className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{message}</p> : null}</div>
    {!hasOptions ? <div className="rounded-[18px] border border-dashed bg-[var(--fluent-color-neutral-background-2)] p-8 text-center text-sm text-[var(--fluent-color-neutral-foreground-2)]">{loading ? 'Generating personalised options for all seven meals…' : 'No suitable options are available for this meal yet. Generate alternatives or build a meal from eligible foods.'}</div> : <div className="grid items-start gap-4 xl:grid-cols-[220px_minmax(0,1fr)]"><nav className="sticky top-[198px] flex gap-2 overflow-x-auto rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-2 xl:block xl:space-y-2" aria-label="Meal navigator">{COMMON_FOOD_MEALS.map(([head,label])=>{const count=(byMeal[head]||[]).filter((option)=>selectedIds.has(option.combinationId)).length;return <button key={head} type="button" onClick={()=>setActiveMealHead(head)} className={`flex min-w-[150px] items-center justify-between gap-3 rounded-[12px] px-3 py-2.5 text-left text-xs xl:w-full ${activeMealHead===head?'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]':'bg-[var(--fluent-color-neutral-background-1)] text-[var(--fluent-color-neutral-foreground-2)]'}`}><span className="font-semibold">{label}</span><span className="shrink-0 font-semibold">{count}/5{count===5?' ✓':''}</span></button>})}</nav><div className="space-y-3">{COMMON_FOOD_MEALS.filter(([head])=>head===activeMealHead).map(([head, label]) => {
      const generatedMeal = meals.find((item) => item.mealHead === head);
      const mealOptions = byMeal[head] || [];
      const coverage = generatedMeal?.coverage || { state: mealOptions.length >= 5 ? 'COMPLETE' : 'SHORTAGE', available: mealOptions.length, required: 5, missing: Math.max(0, 5 - mealOptions.length) };
      const selectedCount = mealOptions.filter((option) => selectedIds.has(option.combinationId)).length;
      const mealTarget = generatedMeal?.target?.kcal;
      const targetStatus = mealCalorieStatus(mealTarget, mealTarget);
      return <div key={head} className="rounded-[18px] border bg-white p-4"><div className="flex flex-wrap justify-between gap-3"><div><h5 className="text-lg font-semibold">{label}</h5><p className="mt-1 text-xs text-gray-600">Target {formatNutrient(mealTarget, 'kcal')}{targetStatus ? ` · Acceptable range ${formatNutrient(targetStatus.minimum, 'kcal')}–${formatNutrient(targetStatus.maximum, 'kcal')}` : ''}</p></div><div className="flex flex-wrap items-center gap-2"><span className={`rounded-full px-3 py-1 text-xs font-semibold ${selectedCount === 5 ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-800'}`}>{selectedCount}/5 included</span>{!readOnly ? <><button type="button" onClick={()=>setMealSelection(head,true)} className="text-xs font-semibold text-blue-700">Select all</button><button type="button" onClick={()=>setMealSelection(head,false)} className="text-xs font-semibold text-gray-600">Clear</button><button type="button" onClick={()=>{setBuildMealHead(buildMealHead===head?'':head);setBuildOptionIds(new Set(mealOptions.filter((option)=>selectedIds.has(option.combinationId)).map((option)=>option.combinationId)))}} className="rounded-full border px-3 py-1.5 text-xs font-semibold">+ Build Meal</button></> : null}</div></div>
        {buildMealHead===head && mealOptions.length ? <section className="mt-3 rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] p-3" aria-label={`Build ${label} meal`}><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-semibold">Build Meal · choose options to update</p><button type="button" onClick={()=>setBuildMealHead('')} aria-label="Close Build Meal"><X size={16}/></button></div><div className="mt-2 flex flex-wrap gap-2">{mealOptions.slice(0,5).map((option,index)=><label key={option.combinationId} className="flex items-center gap-1 rounded-full border bg-white px-2.5 py-1.5 text-xs"><input type="checkbox" checked={buildOptionIds.has(option.combinationId)} onChange={()=>setBuildOptionIds((current)=>{const next=new Set(current);if(next.has(option.combinationId))next.delete(option.combinationId);else next.add(option.combinationId);return next})}/>Option {index+1}</label>)}</div><div className="mt-2 flex flex-wrap gap-2">{BUILD_MEAL_ROLES.map(([role,labelText])=><button key={role} type="button" disabled={!buildOptionIds.size} onClick={() => {const option=mealOptions.find((item)=>buildOptionIds.has(item.combinationId))||mealOptions[0];openExplorer('add',option,null,label,role,{optionIds:mealOptions.slice(0,5).map((item)=>item.combinationId),selectedOptionIds:[...buildOptionIds],defaultApplyScope:buildOptionIds.size>1?'SELECTED_OPTIONS':'THIS_OPTION'})}} className="rounded-full border bg-white px-3 py-1.5 text-xs font-semibold disabled:opacity-40">+ {labelText}</button>)}</div></section> : null}
        <div className="mt-3 space-y-2">{mealOptions.map((option, index) => { const key = option.combinationId || `${head}-${index}`; const selected = selectedIds.has(option.combinationId); const state = persistedIds.has(option.combinationId) ? 'SAVED' : selected ? 'SELECTED' : 'AVAILABLE'; const calorie=mealCalorieStatus(option.nutrition?.kcal,mealTarget); const calorieLabel=calorie?.state==='WITHIN_TARGET'?'Within target':calorie?.state==='BELOW_TARGET'?'Below target':'Above target'; return <article key={key} data-option-type={option.sourceType} data-selection-state={state} className={`rounded-[12px] border px-3 py-2.5 ${selected ? 'border-[var(--fluent-color-brand-stroke-1)] bg-[var(--fluent-color-brand-background-2)]' : 'bg-[var(--fluent-color-neutral-background-2)]'}`}><div className="flex items-start gap-3">{!readOnly && ['draft', 'changes_requested'].includes(lifecycle) ? <input type="checkbox" checked={selected} onChange={() => toggleSelection(option)} aria-label={`${selected ? 'Exclude' : 'Include'} ${optionTitle(option)}`} className="mt-1 h-4 w-4 accent-[var(--fluent-color-brand-background)]" /> : null}<div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><p className="truncate text-sm font-semibold">Option {index+1} · {optionTitle(option)}</p><span className={`text-[11px] font-semibold ${calorie?.state==='WITHIN_TARGET'?'text-green-700':'text-amber-800'}`}>{calorie ? `${calorie.variancePercent>=0?'+':''}${calorie.variancePercent.toFixed(1)}% · ${calorieLabel}${calorie.state==='WITHIN_TARGET'?' ✓':''}` : 'Calorie target unavailable'}</span></div><p className="mt-0.5 text-xs text-gray-600">{servingSummary(option)}</p><p className="mt-1 text-xs font-medium text-gray-700">{compactNutrition(option.nutrition)}</p><p className="mt-1 text-[11px] text-gray-500">Target {formatNutrient(mealTarget,'kcal')}{calorie ? ` · Current ${formatNutrient(calorie.current,'kcal')} · ${calorie.remaining>=0?'Remaining':'Over'} ${formatNutrient(Math.abs(calorie.remaining),'kcal')}` : ''}</p><div className="mt-2 flex flex-wrap gap-3 text-xs font-semibold">{!readOnly?<><button type="button" onClick={()=>setExpanded((current)=>({...current,[key]:true}))} className="text-blue-700">Edit</button><button type="button" onClick={()=>openExplorer('replace',option,option.components?.[0],label)} className="text-blue-700">Replace</button><button type="button" onClick={()=>{if(selected)toggleSelection(option)}} disabled={!selected} className="text-red-700 disabled:opacity-40">Remove</button></>:null}<button type="button" aria-expanded={Boolean(expanded[key])} onClick={()=>setExpanded((current)=>({...current,[key]:!current[key]}))} className="text-blue-700">{expanded[key]?'Hide composition':'Details'}</button></div>{expanded[key]?<><ComponentTable option={option} readOnly={readOnly || !['draft','changes_requested'].includes(lifecycle)} locked={lockedServings[option.combinationId]} onLock={(foodId)=>toggleServingLock(option.combinationId,foodId)} onExplore={(mode,component)=>openExplorer(mode,option,component,label)} onRemove={(component)=>mutate(()=>removeFiteatsyCommonFoodComponent(clientId,dietPlanId,option.combinationId,component.foodId,planVersionId))} onServing={(component)=>openExplorer('serving',option,component,label)}/>{!readOnly?<button type="button" onClick={()=>autoBalance(option)} className="mt-2 rounded-full border px-3 py-1.5 text-xs font-semibold">Balance to target</button>:null}</>:null}</div></div></article>; })}{!mealOptions.length ? <p className="rounded-[12px] border border-dashed p-4 text-sm text-gray-500">{loading ? 'Generating personalised options…' : `Only ${coverage.available || 0} suitable options are available for this meal.`}</p> : null}</div>
        {(legacyByMeal[head] || []).length ? <details className="mt-4 rounded-[14px] border border-dashed p-3"><summary className="cursor-pointer text-xs font-semibold">Previous plan choices · {(legacyByMeal[head] || []).length}</summary><div className="mt-3 space-y-2">{legacyByMeal[head].map((option) => <article key={option.combinationId} className="rounded-[12px] bg-[var(--fluent-color-neutral-background-2)] p-3"><p className="text-sm font-semibold">{option.displayName}</p><p className="mt-1 text-xs text-gray-600">{option.servingLabel} · {compactNutrition(option.nutrition)}</p><LegacyOptionDetails option={option} /></article>)}</div></details> : null}
      </div>;
    })}</div></div>}
    {explorer ? <FoodExplorer context={explorer} clientId={clientId} onClose={() => setExplorer(null)} onSelect={selectFood} onOpenTemplates={(visibility) => { setExplorer(null); setTemplateLibrary(visibility); }} /> : null}
    {templateLibrary ? <TemplateLibrary clientId={clientId} dietPlanId={dietPlanId} mealHead={activeMealHead} initialVisibility={typeof templateLibrary === 'string' ? templateLibrary : ''} onApply={acceptAppliedTemplate} onClose={() => setTemplateLibrary(false)} /> : null}
    {templateMeal ? <SaveTemplateDialog option={templateMeal} locked={lockedServings[templateMeal.combinationId]} onClose={() => setTemplateMeal(null)} onSaved={(template) => setMessage(`Template ${template.revision.name} saved as a draft. Activate it from the Template Library before reuse.`)} /> : null}
    {previewOpen ? <ClientPreview options={typedOptions.map((option) => ({ ...option, selected: selectedIds.has(option.combinationId) }))} onClose={() => setPreviewOpen(false)} /> : null}
  </section>;
});

export default CommonFoodPlanEditor;
