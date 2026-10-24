import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  searchExternalCommonFoods,
} from '../../lib/fiteatsyConsultantsApi';
import { bindDietPlanAssessment, createConsultantDietPlan, getConsultantDietPlan, getNutritionAssessment, listConsultantDietPlans, publishConsultantDietPlan, reviewConsultantDietPlan, saveConsultantDietPlan } from '../../lib/practiceOperationsApi';
import { COMMON_FOOD_MEALS } from '../../lib/commonFoodUi.mjs';
import CommonFoodPlanEditor from '../platform/CommonFoodPlanEditor';

const normalOption=(food,mealHead,index)=>({combinationId:`${mealHead}-${food.catalogEntityId||food.id}-${index}`,mealHead,selected:true,sourceType:'GOVERNED_CATALOGUE',nutrition:food.defaultServing?.nutrition||{},components:[{componentId:food.catalogEntityId||food.id,foodId:food.catalogEntityId||food.id,foodDisplayNameSnapshot:food.displayName,servingId:food.defaultServing?.id||food.servings?.[0]?.id,servingDisplayNameSnapshot:food.defaultServing?.label||food.servingDisplay||'Governed serving',multiplier:1,nutrition:food.defaultServing?.nutrition||{},provenance:{source:food.source||food.referenceSource||'FITEATSY_GOVERNED_CATALOGUE',nutritionStatus:food.nutritionStatus||food.displayStatus}}]});
const readPlan=async planId=>{const value=await getConsultantDietPlan(planId);return{value,options:value.options||[],planVersionId:value.current_version?.id}};
const persistOptions=async(planId,options)=>{const {value}=await readPlan(planId);return saveConsultantDietPlan(planId,{expected_version:value.plan.current_version,options})};
const editorVersionAliases = new Map();
const mergePersistedOptions=(currentOptions,requestedOptions)=>(requestedOptions||[]).map(requested=>{const current=currentOptions.find(option=>option.combinationId===requested.optionId);return{...(current||{}),combinationId:requested.optionId,mealHead:requested.mealHead,selected:true,components:(requested.components||[]).map(component=>{const prior=current?.components?.find(item=>item.foodId===component.foodId);return{...(prior||{}),...component,nutrition:prior?.nutrition||{},provenance:prior?.provenance||{source:'FITEATSY_GOVERNED_CATALOGUE'}}}),nutrition:current?.nutrition||{}}});
const authoringApi = {
  generate: async(clientId,_planId,mealHeads=COMMON_FOOD_MEALS.map(([head])=>head))=>{const meals=[];for(const mealHead of mealHeads){const response=await searchExternalCommonFoods(clientId,{scope:'RECOMMENDED',mealHead,limit:5});const foods=(response.items||response.foods||[]).filter(food=>food.primaryActionEnabled!==false).slice(0,5);meals.push({mealHead,options:foods.map((food,index)=>normalOption(food,mealHead,index))})}return{meals,generationSnapshot:{source:'FITEATSY_GOVERNED_CATALOGUE',readOnly:true}}},
  read: async(_clientId,planId)=>{const result=await readPlan(planId);return{options:result.options,planVersionId:editorVersionAliases.get(planId)||result.planVersionId}},
  replaceSelection: async(_clientId,planId,payload)=>{const result=await readPlan(planId);const options=mergePersistedOptions(result.options,payload.options);await persistOptions(planId,options);editorVersionAliases.set(planId,payload.expectedPlanVersionId);return{planVersionId:payload.expectedPlanVersionId}},
  replaceComponent: async()=>{throw new Error('Replace the complete governed meal option and save a new version.');},
  addComponent: async()=>{throw new Error('Create a governed meal option and save a new version.');},
  removeComponent: async()=>{throw new Error('Remove the complete meal option and save a new version.');},
  updateServing: async()=>{throw new Error('Serving changes are persisted with the complete plan version.');},
  search: searchExternalCommonFoods,
  saveOption: async(_clientId,planId,payload)=>{const result=await readPlan(planId);const option={combinationId:crypto.randomUUID(),mealHead:payload.mealHead,selected:true,sourceType:'MANUAL',components:payload.components,nutrition:payload.components.reduce((sum,item)=>({kcal:(sum.kcal||0)+Number(item.nutrition?.kcal||0),protein:(sum.protein||0)+Number(item.nutrition?.protein||0),carbohydrate:(sum.carbohydrate||0)+Number(item.nutrition?.carbohydrate||0),fat:(sum.fat||0)+Number(item.nutrition?.fat||0),fibre:(sum.fibre||0)+Number(item.nutrition?.fibre||0)}),{})};await persistOptions(planId,[...result.options,option]);return option},
  autoBalance: async () => { throw new Error('Use Edit quantity to select a governed serving.'); },
};

const initialForm = { name: '', dailyCalories: '', dailyProtein: '' };
const show = (value) => Array.isArray(value) ? value.join(', ') || 'Not provided' : value || 'Not provided';
const projectDetail=(detail)=>({id:detail.plan.id,name:detail.plan.title,status:detail.plan.status,updatedAt:detail.plan.updated_at,version:{id:detail.current_version?.id,number:detail.plan.current_version,plan:{dailyTargets:{calories:detail.plan.daily_calories_target,protein:Number(detail.plan.daily_protein_target_g)},meals:COMMON_FOOD_MEALS.map(([mealHead])=>({mealHead,options:(detail.options||[]).filter(item=>item.mealHead===mealHead)}))}},versions:detail.versions});

export default function ExternalMultiDietPlan({ clientId, context, onError }) {
  const [plans, setPlans] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const [loadError, setLoadError] = useState('');
  const [readiness, setReadiness] = useState({ outcome: 'LOADING' });
  const editorRef = useRef(null);
  const selected = useMemo(() => plans.find((plan) => plan.id === selectedId) || plans[0] || null, [plans, selectedId]);
  const valid = form.name.trim().length >= 2 && Number(form.dailyCalories) >= 800 && Number(form.dailyCalories) <= 6000 && Number(form.dailyProtein) >= 20 && Number(form.dailyProtein) <= 400;

  const load = useCallback(async (preferredId) => {
    setLoading(true); setLoadError('');
    try {
      const [plansResult,assessmentResult]=await Promise.allSettled([listConsultantDietPlans(clientId),getNutritionAssessment(clientId)]);
      if(plansResult.status==='rejected'){setPlans([]);setLoadError('Diet plans could not be loaded.');onError(plansResult.reason?.message||'Diet plans could not be loaded.');return;}
      if(assessmentResult.status==='fulfilled'){const assessment=assessmentResult.value;setReadiness({ outcome: assessment.readiness_status || assessment.readiness?.outcome || 'NOT_STARTED', assessmentId: assessment.id, assessmentVersion: assessment.current_version || assessment.version });}
      else{setReadiness({outcome:'UNAVAILABLE'});onError(assessmentResult.reason?.message||'Unable to load nutrition assessment.');}
      const details=await Promise.allSettled((plansResult.value.items||[]).map((item)=>getConsultantDietPlan(item.id).then(projectDetail)));
      const next=details.filter(item=>item.status==='fulfilled').map(item=>item.value);
      const failedDetails=details.length-next.length;
      if(failedDetails){setLoadError(`${failedDetails} Diet Plan ${failedDetails===1?'detail could':'details could'} not be loaded.`);onError('One or more Diet Plan details could not be loaded.');}
      next.forEach((plan) => editorVersionAliases.delete(plan.id));
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
    if (!valid || busy || readiness.outcome !== 'READY') return;
    setBusy('create'); setMessage(''); onError('');
    try {
      const result = await createConsultantDietPlan({ client_id: clientId, name: form.name.trim(), daily_calories_target: Number(form.dailyCalories), daily_protein_target_g: Number(form.dailyProtein), health_goals: context?.goals || [] });
      setForm(initialForm);
      await load(result.id);
      setMessage('A new independent Diet Plan draft was created and reloaded.');
    } catch (error) { onError(error.message || 'Unable to create Diet Plan.'); }
    finally { setBusy(''); }
  };

  const persist = async (action) => {
    if (!selected || busy) return;
    setBusy(action); setMessage(''); onError('');
    try {
      if (action === 'save') {
        await editorRef.current?.save();
        setMessage('Draft saved and reloaded from persistent storage.');
      } else {
        if (selected.status !== 'APPROVED') {
          await reviewConsultantDietPlan(selected.id, { action: 'SUBMIT', expected_version: selected.version.number });
          setMessage('Exact Diet Plan version submitted for Senior Consultant review.');
        } else {
          if (!window.confirm(`Publish approved “${selected.name}” to this client? Published history remains immutable.`)) return;
          try { await bindDietPlanAssessment(clientId, { external_plan_id: selected.id, external_plan_version: String(selected.version.number), assessment_id: readiness.assessmentId, assessment_version: readiness.assessmentVersion, plan_state: selected.status }); }
          catch (bindingError) { if (bindingError.code !== 'PLAN_ASSESSMENT_LINK_EXISTS') throw bindingError; }
          await publishConsultantDietPlan(selected.id);
          setMessage('Approved Diet Plan version published.');
        }
      }
      await load(selected.id);
    } catch (error) { onError(error.message || 'Unable to update Diet Plan.'); }
    finally { setBusy(''); }
  };

  const fields = [['Health & wellness goals', context?.goals], ['Diet preference', context?.dietPreference], ['Allergies', context?.allergies], ['Food restrictions', context?.restrictions], ['Weight', context?.weight], ['BMI', context?.bmi]];
  if (loading) return <div className="rounded-2xl bg-white p-12 text-center text-sm text-slate-500">Loading all Diet Plans…</div>;

  return <div className="space-y-4">
    {loadError&&<section role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-900"><p className="font-semibold">{loadError}</p><button type="button" onClick={()=>load(selectedId)} className="mt-3 min-h-11 rounded-xl border border-rose-300 bg-white px-4 font-semibold">Retry</button></section>}
    <section className={`rounded-2xl border p-5 ${readiness.outcome==='READY'?'border-emerald-200 bg-emerald-50':'border-amber-200 bg-amber-50'}`}>
      <p className="text-xs font-bold uppercase tracking-wider">Nutrition Assessment readiness</p>
      <h3 className="mt-1 text-lg font-semibold">{readiness.outcome.replaceAll('_',' ')}</h3>
      <p className="mt-1 text-sm">{readiness.outcome==='READY'?'The reviewed server-authoritative assessment permits Diet Plan authoring and publication.':'Complete and review the Nutrition Assessment before creating or publishing a Diet Plan. Existing drafts remain viewable.'}</p>
    </section>
    <section className="rounded-2xl border border-blue-200 bg-blue-50 p-5">
      <p className="text-xs font-bold uppercase tracking-wider text-blue-700">Read-only client context</p>
      <h3 className="mt-1 text-lg font-semibold text-blue-950">Confirmed context for professional review</h3>
      <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{fields.map(([label, value]) => <div key={label} className="rounded-xl bg-white p-3"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-sm font-semibold">{show(value)}</dd></div>)}</dl>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">All Diet Plans</p><h3 className="mt-1 text-xl font-semibold">{plans.length} independent {plans.length === 1 ? 'plan' : 'plans'}</h3></div>{plans.length > 0 && <label className="text-sm font-semibold">Selected plan<select aria-label="Selected Diet Plan" value={selected?.id || ''} onChange={(event) => setSelectedId(event.target.value)} className="ml-2 min-h-11 rounded-xl border border-slate-200 px-3">{plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {plan.status.replaceAll('_', ' ')}</option>)}</select></label>}</div>
      {plans.length===0&&!loadError&&<p className="mt-4 text-sm text-slate-500">No independent Diet Plans have been created for this client.</p>}
      {plans.length > 0 && <div className="mt-4 grid gap-3 md:grid-cols-2">{plans.map((plan) => <button key={plan.id} onClick={() => setSelectedId(plan.id)} className={`rounded-xl border p-4 text-left ${plan.id === selected?.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200'}`}><strong>{plan.name}</strong><p className="mt-1 text-xs text-slate-500">{plan.status.replaceAll('_', ' ')} · {plan.version.plan.dailyTargets.calories} kcal · {plan.version.plan.dailyTargets.protein} g protein</p><p className="mt-1 text-xs text-slate-400">Updated {new Date(plan.updatedAt).toLocaleString()}</p></button>)}</div>}
    </section>

    {selected && <><section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">{selected.status.replaceAll('_',' ')}</p><h3 className="mt-1 text-xl font-semibold">{selected.name} · Version {selected.version.number}</h3><p className="mt-1 text-sm text-slate-600">{selected.version.plan.dailyTargets.calories} kcal · {selected.version.plan.dailyTargets.protein} g protein</p></div><div className="flex flex-wrap gap-2">{['DRAFT','SAVED','CHANGES_REQUESTED'].includes(selected.status) && <button disabled={busy} onClick={() => persist('save')} className="min-h-11 rounded-xl border px-4 font-semibold disabled:opacity-40">{busy === 'save' ? 'Saving…' : 'Save Draft'}</button>}<button disabled={busy || readiness.outcome!=='READY' || ['SUBMITTED','UNDER_REVIEW','PUBLISHED'].includes(selected.status)} onClick={() => persist('publish')} className="min-h-11 rounded-xl bg-blue-600 px-4 font-semibold text-white disabled:opacity-40">{selected.status === 'PUBLISHED' ? 'Published' : readiness.outcome!=='READY'?'Assessment review required':selected.status === 'APPROVED' ? 'Publish approved version' : busy === 'publish' ? 'Submitting…' : 'Submit for review'}</button></div></div></section><section className="rounded-2xl border border-slate-200 bg-white p-5"><CommonFoodPlanEditor key={`${selected.id}:${selected.version.id}`} ref={editorRef} clientId={clientId} dietPlanId={selected.id} planVersionId={selected.version.id} generationRequestId={1} lifecycle={['DRAFT','SAVED','CHANGES_REQUESTED'].includes(selected.status) ? 'draft' : 'published'} initialOptions={selected.version.plan.meals.flatMap((meal) => meal.options)} legacyMealPlan={{}} readOnly={!['DRAFT','SAVED','CHANGES_REQUESTED'].includes(selected.status)} authoringApi={authoringApi} templatesEnabled={false} proposalsEnabled={false} autoBalanceEnabled={false} onStale={() => load(selected.id)} /></section><section className="rounded-2xl border bg-white p-5"><h4 className="font-semibold">Version history</h4><ul className="mt-2 space-y-1 text-sm">{selected.versions.map(version=><li key={version.id}>Version {version.version} · {version.status} · {version.nutrition_snapshot?.option_count||0}/35 options</li>)}</ul></section></>}

    <form onSubmit={create} className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="text-lg font-semibold">Create another Diet Plan</h3><p className="mt-1 text-sm text-slate-500">Each plan has its own name, targets, draft and publication history.</p><div className="mt-4 grid gap-3 md:grid-cols-3"><label className="text-sm font-semibold">Plan name<input required minLength={2} maxLength={120} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="mt-2 w-full rounded-xl border p-3" /></label><label className="text-sm font-semibold">Calories (800–6000)<input required type="number" min="800" max="6000" value={form.dailyCalories} onChange={(event) => setForm({ ...form, dailyCalories: event.target.value })} className="mt-2 w-full rounded-xl border p-3" /></label><label className="text-sm font-semibold">Protein (20–400 g)<input required type="number" min="20" max="400" step="0.1" value={form.dailyProtein} onChange={(event) => setForm({ ...form, dailyProtein: event.target.value })} className="mt-2 w-full rounded-xl border p-3" /></label></div><button disabled={!valid || busy || readiness.outcome!=='READY'} className="mt-4 min-h-11 rounded-xl bg-slate-950 px-5 font-semibold text-white disabled:opacity-40">{busy === 'create' ? 'Creating…' : readiness.outcome==='READY'?'Create independent plan':'Assessment review required'}</button></form>
    {message && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-800">{message}</p>}
  </div>;
}
