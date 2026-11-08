import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  searchExternalCommonFoods,
} from '../../lib/fiteatsyConsultantsApi';
import { bindDietPlanAssessment, createClientInformationRequest, createConsultantDietPlan, downloadConsultantDietPlan, getClientInformationCompleteness, getConsultantDietPlan, getDietPlanHealthContext, getNutritionAssessment, listConsultantDietPlans, openWhatsApp, publishConsultantDietPlan, reviewConsultantDietPlan, saveConsultantDietPlan, updateConsultantDietPlanOption } from '../../lib/practiceOperationsApi';
import { canPublishExternalDietVersion, createdDraftPresentation, externalDietEditorState, loadDietPlanWorkspace } from '../../lib/dietPlanWorkspaceState.mjs';
import { COMMON_FOOD_MEALS } from '../../lib/commonFoodUi.mjs';
import CommonFoodPlanEditor from '../platform/CommonFoodPlanEditor';

const normalOption=(food,mealHead,index)=>({combinationId:`${mealHead}-${food.catalogEntityId||food.id}-${index}`,mealHead,selected:true,sourceType:'GOVERNED_CATALOGUE',nutrition:food.defaultServing?.nutrition||{},components:[{componentId:food.catalogEntityId||food.id,foodId:food.catalogEntityId||food.id,foodDisplayNameSnapshot:food.displayName,servingId:food.defaultServing?.id||food.servings?.[0]?.id,servingDisplayNameSnapshot:food.defaultServing?.label||food.servingDisplay||'Governed serving',multiplier:1,nutrition:food.defaultServing?.nutrition||{},provenance:{source:food.source||food.referenceSource||'FITEATSY_GOVERNED_CATALOGUE',nutritionStatus:food.nutritionStatus||food.displayStatus}}]});
const readPlan=async planId=>{const value=await getConsultantDietPlan(planId);return{value,options:value.options||[],planVersionId:value.current_version?.id}};
const persistOptions=async(planId,options)=>{const {value}=await readPlan(planId);return saveConsultantDietPlan(planId,{expected_version:value.plan.current_version,options})};
const generatedOptionsByPlan=new Map();
const editorVersionAliases = new Map();
const governedOptionOperationKeys=new Map();
const mergePersistedOptions=(currentOptions,requestedOptions,candidates=[])=>{
  const available=[...(currentOptions||[]),...(candidates||[])];
  return(requestedOptions||[]).map(requested=>{const current=available.find(option=>option.combinationId===requested.optionId);return{...(current||{}),combinationId:requested.optionId,mealHead:requested.mealHead,selected:true,components:(requested.components||[]).map(component=>{const prior=current?.components?.find(item=>item.foodId===component.foodId);return{...(prior||{}),...component,nutrition:prior?.nutrition||{},provenance:prior?.provenance||{source:'FITEATSY_GOVERNED_CATALOGUE'}}}),nutrition:current?.nutrition||{}}});
};
const authoringApi = {
  generate: async(clientId,planId,mealHeads=COMMON_FOOD_MEALS.map(([head])=>head))=>{const meals=[];for(const mealHead of mealHeads){const response=await searchExternalCommonFoods(clientId,{scope:'RECOMMENDED',mealHead,limit:5});const foods=(response.items||response.foods||[]).filter(food=>food.primaryActionEnabled!==false).slice(0,5);meals.push({mealHead,options:foods.map((food,index)=>normalOption(food,mealHead,index))})}generatedOptionsByPlan.set(planId,meals.flatMap(meal=>meal.options));return{meals,generationSnapshot:{source:'FITEATSY_GOVERNED_CATALOGUE',readOnly:true}}},
  read: async(_clientId,planId)=>{const result=await readPlan(planId);return{options:result.options,planVersionId:editorVersionAliases.get(planId)||result.planVersionId}},
  replaceSelection: async(_clientId,planId,payload)=>{const result=await readPlan(planId);const options=mergePersistedOptions(result.options,payload.options,generatedOptionsByPlan.get(planId));await persistOptions(planId,options);generatedOptionsByPlan.set(planId,options);editorVersionAliases.set(planId,payload.expectedPlanVersionId);return{planVersionId:payload.expectedPlanVersionId}},
  replaceComponent: async(_clientId,planId,optionId,componentId,payload)=>mutateGovernedOption(planId,optionId,option=>({...option,components:payload.draft.components.map(component=>component.foodId===componentId?payload.component:component)})),
  addComponent: async(_clientId,planId,optionId,payload)=>mutateGovernedOption(planId,optionId,option=>({...option,components:[...payload.draft.components,payload.component]})),
  removeComponent: async(_clientId,planId,optionId,componentId)=>mutateGovernedOption(planId,optionId,option=>({...option,components:option.components.filter(component=>component.foodId!==componentId)})),
  updateServing: async(_clientId,planId,optionId,componentId,payload)=>mutateGovernedOption(planId,optionId,option=>({...option,components:option.components.map(component=>component.foodId===componentId?{...component,servingId:payload.servingId,multiplier:payload.multiplier}:component)})),
  search: searchExternalCommonFoods,
  saveOption: async(_clientId,planId,payload)=>mutateGovernedOption(planId,crypto.randomUUID(),()=>({mealHead:payload.mealHead,components:payload.components})),
  autoBalance: async () => { throw new Error('Use Edit quantity to select a governed serving.'); },
};

async function mutateGovernedOption(planId,optionId,mutator){
  const current=await getConsultantDietPlan(planId);
  const existing=(current.options||[]).find(option=>option.combinationId===optionId)||{mealHead:null,components:[]};
  const desired=mutator(existing);
  if(!desired.mealHead||!desired.components?.length)throw new Error('A governed meal option must contain at least one component.');
  const payload={expected_version:current.plan.current_version,meal_head:desired.mealHead,components:desired.components.map(({foodId,servingId,multiplier})=>({food_id:foodId,serving_id:servingId,multiplier:Number(multiplier)}))};
  const fingerprint=JSON.stringify({planId,optionId,payload});
  const key=governedOptionOperationKeys.get(fingerprint)||crypto.randomUUID();
  governedOptionOperationKeys.set(fingerprint,key);
  const result=await updateConsultantDietPlanOption(planId,optionId,payload,key);
  editorVersionAliases.set(planId,result.plan_version_id);
  return result.option;
}

const initialForm = { name: '', dailyCalories: '', dailyProtein: '' };
const displayValue = (value) => {
  if (value == null || value === '') return '';
  if (typeof value !== 'object') return String(value);
  return displayValue(value.name ?? value.code ?? value.value ?? value.label ?? value.id ?? '');
};
const valueList = (value) => (Array.isArray(value) ? value : value == null ? [] : [value]).map(displayValue).filter(Boolean);
const show = (value) => valueList(value).join(', ') || 'Not provided';
const projectDetail=(detail)=>({id:detail.plan.id,name:detail.plan.title,status:detail.plan.status,updatedAt:detail.plan.updated_at,version:{id:detail.current_version?.id,number:detail.plan.current_version,plan:{dailyTargets:{calories:detail.plan.daily_calories_target,protein:Number(detail.plan.daily_protein_target_g)},meals:COMMON_FOOD_MEALS.map(([mealHead])=>({mealHead,options:(detail.options||[]).filter(item=>item.mealHead===mealHead)}))}},versions:detail.versions});

export default function ExternalMultiDietPlan({ clientId, clientName='Client', clientPhone='', clientCountryIso2='IN', context, onError, onReviewMeasurements }) {
  const [plans, setPlans] = useState([]);
  const [plansStatus, setPlansStatus] = useState('loading');
  const [selectedId, setSelectedId] = useState('');
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const [creationState, setCreationState] = useState({ state: 'idle', createdId: '' });
  const [loadError, setLoadError] = useState('');
  const [readiness, setReadiness] = useState({ outcome: 'LOADING' });
  const [healthContext, setHealthContext] = useState(null);
  const [requirementsOpen, setRequirementsOpen] = useState(false);
  const [completeness, setCompleteness] = useState(null);
  const [requestedFields, setRequestedFields] = useState([]);
  const [questionnaireLink, setQuestionnaireLink] = useState('');
  const [editorDirty, setEditorDirty] = useState(false);
  const editorRef = useRef(null);
  const selectedIdRef = useRef('');
  const creationKeyRef = useRef('');
  const generateButtonRef = useRef(null);
  const firstFieldRef = useRef(null);
  const selected = useMemo(() => plans.find((plan) => plan.id === selectedId) || plans[0] || null, [plans, selectedId]);
  const editorState = useMemo(() => externalDietEditorState(selected?.status), [selected?.status]);
  const publishReady = canPublishExternalDietVersion({ status: selected?.status, dirty: editorDirty });
  const valid = form.name.trim().length >= 2 && Number(form.dailyCalories) >= 1 && Number(form.dailyProtein) >= 0;

  const load = useCallback(async (preferredId) => {
    setLoading(true); setLoadError('');
    try {
      const result=await loadDietPlanWorkspace({clientId,preferredId,currentId:selectedIdRef.current,projectDetail,api:{list:listConsultantDietPlans,assessment:getNutritionAssessment,context:getDietPlanHealthContext,detail:getConsultantDietPlan}});
      setReadiness(result.readiness);setHealthContext(result.healthContext);setLoadError(result.loadError);setPlansStatus(result.plansStatus);
      if(result.plans!==null){result.plans.forEach((plan)=>editorVersionAliases.delete(plan.id));setPlans(result.plans);selectedIdRef.current=result.selectedId;setSelectedId(result.selectedId);}
      if(result.errors.length)onError(result.errors[0]?.message||result.loadError||'One or more Diet Plan requests failed.');
      return result;
    } catch (error) {
      setPlansStatus('error');setLoadError('Diet plans could not be loaded.');setReadiness({outcome:'ERROR'});
      onError(error.message || 'Unable to load Diet Plans.');
      return {plansStatus:'error',plans:null,selectedId:selectedIdRef.current,preferredLoaded:false,loadError:'Diet plans could not be loaded.',readiness:{outcome:'ERROR'},healthContext:null,errors:[error]};
    } finally {
      setLoading(false);
    }
  }, [clientId, onError]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!requirementsOpen) return undefined;
    firstFieldRef.current?.focus();
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') {
        setRequirementsOpen(false);
        requestAnimationFrame(() => generateButtonRef.current?.focus());
      }
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [requirementsOpen]);

  const openRequirements = async () => {
    setRequirementsOpen(true);
    setQuestionnaireLink('');
    try {
      const value = await getClientInformationCompleteness(clientId);
      setCompleteness(value);
      setRequestedFields((value.fields || []).filter((item) => item.client_can_provide && ['MISSING','INVALID','REQUIRES_CONFIRMATION'].includes(item.status)).map((item) => item.field_id));
    } catch (error) {
      setCompleteness(null);
      onError(error.message || 'Client information completeness could not be loaded.');
    }
  };

  const requestMissingInformation = async () => {
    if (!requestedFields.length || busy) return;
    setBusy('questionnaire');
    try {
      const result = await createClientInformationRequest(clientId, { field_ids: requestedFields, delivery_channel: 'COPY_LINK', expires_in_hours: 168 });
      const url = `${window.location.origin}/client-information/${encodeURIComponent(result.token)}`;
      setQuestionnaireLink(url);
      await navigator.clipboard?.writeText(url);
    } catch (error) {
      onError(error.message || 'The secure questionnaire link could not be created.');
    } finally {
      setBusy('');
    }
  };

  const create = async (event) => {
    event.preventDefault();
    if (!valid || busy) return;
    setBusy('create'); setMessage(''); setCreationState({state:'creating',createdId:''}); onError('');
    try {
      const idempotencyKey=creationKeyRef.current||globalThis.crypto.randomUUID();creationKeyRef.current=idempotencyKey;
      const result = await createConsultantDietPlan({ client_id: clientId, name: form.name.trim(), daily_calories_target: Number(form.dailyCalories), daily_protein_target_g: Number(form.dailyProtein), health_goals: valueList(context?.goals).slice(0, 3) },idempotencyKey);
      creationKeyRef.current='';
      setForm(initialForm);
      setRequirementsOpen(false);
      const loaded=await load(result.id);const presentation=createdDraftPresentation(result.id,loaded);setCreationState(presentation);setMessage(presentation.message);
    } catch (error) { setCreationState({state:'failed',createdId:''});onError(error.message || 'Unable to create Diet Plan.'); }
    finally { setBusy(''); }
  };

  const persist = async (action) => {
    if (!selected || busy) return;
    setBusy(action); setMessage(''); onError('');
    try {
      if (action === 'save') {
        await editorRef.current?.save();
        setMessage('A new immutable Diet Plan version was saved.');
      } else if (action === 'publish') {
        if (editorDirty) throw new Error('Save the current Diet Plan changes before publishing to the client app.');
        const refreshed = await getConsultantDietPlan(selected.id);
        const currentPlan = refreshed?.plan;
        const currentOptions = refreshed?.options || [];
        if (!currentPlan || currentOptions.length < 1) throw new Error('Add and save at least one governed meal option before publishing.');
        if (currentPlan.status !== 'APPROVED') throw new Error('Approve the exact saved Diet Plan version before publishing to the client app.');
        if (!window.confirm(`Publish “${selected.name}” version ${currentPlan.current_version} to ${clientName}'s Fiteatsy Nutrition screen?`)) return;
        if(readiness.assessmentId&&readiness.assessmentVersion){
          try { await bindDietPlanAssessment(clientId, { external_plan_id: selected.id, external_plan_version: String(currentPlan.current_version), assessment_id: readiness.assessmentId, assessment_version: readiness.assessmentVersion, plan_state: currentPlan.status }); }
          catch (bindingError) { if (bindingError.code !== 'PLAN_ASSESSMENT_LINK_EXISTS') throw bindingError; }
        }
        const publication = await publishConsultantDietPlan(selected.id);
        setMessage(`Version ${publication.version} was published to ${clientName}'s Fiteatsy Nutrition screen${publication.publication_id ? ` (publication ${publication.publication_id})` : ''}.`);
      } else {
        if(action==='submit') await editorRef.current?.save();
        const refreshed=await getConsultantDietPlan(selected.id);
        const actionMap={submit:'SUBMIT',startReview:'START_REVIEW',approve:'APPROVE',requestChanges:'REQUEST_CHANGES'};
        await reviewConsultantDietPlan(selected.id,{action:actionMap[action],expected_version:refreshed.plan.current_version,reason:action==='requestChanges'?'Changes requested by reviewer':undefined});
        setMessage(action==='approve'?'This exact Diet Plan version was approved and is ready to publish.':action==='submit'?'Diet Plan submitted for review.':action==='requestChanges'?'Changes were requested for this version.':'Review started.');
      }
      await load(selected.id);
    } catch (error) { onError(error.message || 'Unable to update Diet Plan.'); }
    finally { setBusy(''); }
  };
  const download=async(format='DOCX')=>{if(!selected||busy)return;setBusy(`download-${format}`);try{const file=await downloadConsultantDietPlan(selected.id,format);const href=URL.createObjectURL(file.blob);const anchor=document.createElement('a');anchor.href=href;anchor.download=file.filename;anchor.click();URL.revokeObjectURL(href);}catch(error){onError(error.message||'Unable to download Diet Plan.');}finally{setBusy('');}};
  const sharePublishedPlan=async()=>{if(!selected||selected.status!=='PUBLISHED'||busy)return;setBusy('share');try{await openWhatsApp({client_id:clientId,intent:'SHARE_PUBLISHED_PLAN',purpose:'Share published Diet Plan availability',phone:clientPhone,country_iso2:clientCountryIso2,message:`Your consultant has published “${selected.name}” version ${selected.version.number}. Sign in to Fiteatsy and open Nutrition to view the secure plan.`,shareable_type:'PUBLISHED_DIET_PLAN',shareable_id:selected.id});setMessage('WhatsApp opened with a secure availability notice. You must press Send yourself.');}catch(error){onError(error.message||'WhatsApp could not be opened.');}finally{setBusy('');}};

  const resolved=healthContext?.measurement_context||{};const latest=resolved.latest||{};const calculations=resolved.calculations||{};
  const fields = [['Health & wellness goals', healthContext?.profile?.weight_management_goals?.length?healthContext.profile.weight_management_goals:context?.goals], ['Diet preference', healthContext?.profile?.dietary_preference||context?.dietPreference], ['Allergies', healthContext?.profile?.allergies_intolerances?.length?healthContext.profile.allergies_intolerances:context?.allergies], ['Food restrictions', healthContext?.profile?.food_restrictions?.length?healthContext.profile.food_restrictions:context?.restrictions], ['Current weight', latest.WEIGHT_KG?`${latest.WEIGHT_KG.value} ${latest.WEIGHT_KG.unit}`:'Not provided'], ['Current height', latest.HEIGHT_CM?`${latest.HEIGHT_CM.value} ${latest.HEIGHT_CM.unit}`:'Not provided'], ['BMI', calculations.bmi?.value??'Not available']];
  const nutritionContext = [['Health goals', healthContext?.profile?.weight_management_goals?.length?healthContext.profile.weight_management_goals:context?.goals],['Diet preference',healthContext?.profile?.dietary_preference||context?.dietPreference],['Allergies',healthContext?.profile?.allergies_intolerances?.length?healthContext.profile.allergies_intolerances:context?.allergies],['Food restrictions',healthContext?.profile?.food_restrictions?.length?healthContext.profile.food_restrictions:context?.restrictions],['Meals per day',healthContext?.profile?.meal_timing_frequency],['Typical food intake',healthContext?.profile?.typical_dietary_intake],['Appetite and eating patterns',healthContext?.profile?.appetite_eating_patterns],['Hydration',healthContext?.profile?.water_intake],['Medical conditions',healthContext?.profile?.nutrition_medical_conditions||context?.conditions],['Medications',healthContext?.profile?.relevant_medications||context?.medications],['Supplements',healthContext?.profile?.relevant_supplements]];
  const confirmedBiomarkers=(context?.biomarkers||[]).filter(item=>!item.reviewStatus||item.reviewStatus==='CONFIRMED'||item.review_status==='CONFIRMED');
  if (loading) return <div className="rounded-2xl bg-white p-12 text-center text-sm text-slate-500">Loading all Diet Plans…</div>;

  return <div className="space-y-4">
    {loadError&&<section role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-900"><p className="font-semibold">{loadError}</p><button type="button" onClick={()=>load(selectedId)} className="mt-3 min-h-11 rounded-xl border border-rose-300 bg-white px-4 font-semibold">Retry</button></section>}
    <section className={`rounded-2xl border p-5 ${readiness.outcome==='READY'?'border-emerald-200 bg-emerald-50':readiness.outcome==='ERROR'?'border-rose-200 bg-rose-50':'border-amber-200 bg-amber-50'}`}>
      <p className="text-xs font-bold uppercase tracking-wider">Nutrition Assessment readiness</p>
      <h3 className="mt-1 text-lg font-semibold">{String(readiness.outcome || 'NOT_STARTED').replaceAll('_',' ')}</h3>
      <p className="mt-1 text-sm">{readiness.outcome==='READY'?'Available client information can support Diet Chart authoring.':'Some nutrition information is unavailable or incomplete. You may use professional judgement and consultant-entered values; review missing information before publication.'}</p>
    </section>
    <section className="rounded-2xl border border-blue-200 bg-blue-50 p-5">
      <p className="text-xs font-bold uppercase tracking-wider text-blue-700">Health Context for Diet Planning</p>
      <h3 className="mt-1 text-lg font-semibold text-blue-950">Server-authoritative context is ready for review</h3>
      <p className="mt-2 text-sm text-blue-900">Open Diet Requirements to review nutrition, measurements and confirmed evidence without duplicating Client 360 data.</p>
      {(resolved.requires_professional_confirmation||healthContext?.assessment?.measurement_context_changed)&&<div role="status" className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">{healthContext?.assessment?.measurement_context_changed?'Measurements changed after the current assessment. Review them when applying professional judgement.':'Legacy self-reported measurements are advisory and should be professionally reviewed before use.'}</div>}
      <button type="button" onClick={onReviewMeasurements} className="mt-4 min-h-11 rounded-xl border border-blue-300 bg-white px-4 text-sm font-semibold text-blue-900">Review measurements in Client360</button>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">All Diet Plans</p><h3 className="mt-1 text-xl font-semibold">{plansStatus==='error'?'Plan count unavailable':plansStatus==='partial'?`${plans.length} loaded ${plans.length===1?'plan':'plans'} · some unavailable`:`${plans.length} independent ${plans.length===1?'plan':'plans'}`}</h3></div>{plans.length > 0 && <label className="text-sm font-semibold">Selected plan<select aria-label="Selected Diet Plan" value={selected?.id || ''} onChange={(event) => {selectedIdRef.current=event.target.value;setSelectedId(event.target.value);}} className="ml-2 min-h-11 rounded-xl border border-slate-200 px-3">{plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {plan.status.replaceAll('_', ' ')}</option>)}</select></label>}</div>
      {plans.length===0&&!loadError&&<p className="mt-4 text-sm text-slate-500">No independent Diet Plans have been created for this client.</p>}
      {plans.length > 0 && <div className="mt-4 grid gap-3 md:grid-cols-2">{plans.map((plan) => <button key={plan.id} onClick={() => {selectedIdRef.current=plan.id;setSelectedId(plan.id);}} className={`rounded-xl border p-4 text-left ${plan.id === selected?.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200'}`}><strong>{plan.name}</strong><p className="mt-1 text-xs text-slate-500">{plan.status.replaceAll('_', ' ')} · {plan.version.plan.dailyTargets.calories} kcal · {plan.version.plan.dailyTargets.protein} g protein</p><p className="mt-1 text-xs text-slate-400">Updated {new Date(plan.updatedAt).toLocaleString()}</p></button>)}</div>}
    </section>

    {selected && <>
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-blue-700">{selected.status.replaceAll('_',' ')}</p>
            <h3 className="mt-1 text-xl font-semibold">{selected.name} · Version {selected.version.number}</h3>
            <p className="mt-1 text-sm text-slate-600">{selected.version.plan.dailyTargets.calories} kcal · {selected.version.plan.dailyTargets.protein} g protein</p>
            <p className="mt-1 text-xs text-slate-500">Published versions are immutable. Editing a published plan and saving creates the next version.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button disabled={busy} onClick={()=>download('DOCX')} className="min-h-11 rounded-xl border px-4 font-semibold disabled:opacity-40">{busy==='download-DOCX'?'Preparing…':'Download DOCX'}</button>
            {['APPROVED','PUBLISHED'].includes(selected.status)&&<button disabled={busy} onClick={()=>download('PDF')} className="min-h-11 rounded-xl border px-4 font-semibold disabled:opacity-40">{busy==='download-PDF'?'Preparing…':'Download PDF'}</button>}
            {selected.status==='PUBLISHED'&&<button disabled={busy||!clientPhone} onClick={sharePublishedPlan} className="min-h-11 rounded-xl bg-emerald-700 px-4 font-semibold text-white disabled:opacity-40">{busy==='share'?'Opening…':'Share via WhatsApp'}</button>}
            {!['APPROVED','PUBLISHED','ARCHIVED'].includes(selected.status) && <button disabled={busy} onClick={() => persist('save')} className="min-h-11 rounded-xl border px-4 font-semibold disabled:opacity-40">{busy === 'save' ? 'Saving…' : 'Save version'}</button>}
            {['DRAFT','SAVED','CHANGES_REQUESTED','SUBMITTED','UNDER_REVIEW'].includes(selected.status)&&<button disabled={busy} onClick={()=>persist('approve')} className="min-h-11 rounded-xl bg-emerald-700 px-4 font-semibold text-white disabled:opacity-40">{busy==='approve'?'Approving…':'Approve exact version'}</button>}
            {selected.status!=='PUBLISHED'&&selected.status!=='ARCHIVED'&&<button aria-describedby="publish-client-app-requirement" disabled={Boolean(busy)||!publishReady} onClick={() => persist('publish')} title={editorDirty?'Save the current changes before publishing.':selected.status!=='APPROVED'?'Approve the exact saved version before publishing.':'Publish this exact approved version to the assigned client app.'} className="min-h-11 rounded-xl bg-blue-700 px-5 font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-40">{busy==='publish'?'Publishing…':'Publish to Client App'}</button>}
          </div>
          {selected.status!=='PUBLISHED'&&selected.status!=='ARCHIVED'&&<p id="publish-client-app-requirement" className={`mt-2 text-xs ${editorDirty?'font-semibold text-amber-700':'text-slate-500'}`}>{editorDirty?'Unsaved changes must be saved before publication.':selected.status==='APPROVED'?'The backend will verify the active Fiteatsy connection and Diet Plan publication consent.':'Save and approve the exact version before publishing it to the client app.'}</p>}
        </div>
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <CommonFoodPlanEditor key={`${selected.id}:${selected.version.id}`} ref={editorRef} clientId={clientId} dietPlanId={selected.id} planVersionId={selected.version.id} generationRequestId={editorState.generationRequestId} generateMissingOnLoad={false} lifecycle={editorState.lifecycle} initialOptions={selected.version.plan.meals.flatMap((meal) => meal.options)} legacyMealPlan={{}} readOnly={editorState.readOnly} authoringApi={authoringApi} templatesEnabled={false} proposalsEnabled={false} autoBalanceEnabled={false} onDirtyChange={setEditorDirty} onStale={() => load(selected.id)} />
      </section>
      <section className="rounded-2xl border bg-white p-5">
        <h4 className="font-semibold">Version history</h4>
        <p className="mt-1 text-xs text-slate-500">Every saved and published version remains available for audit and comparison.</p>
        <ul className="mt-2 space-y-1 text-sm">{selected.versions.map(version=><li key={version.id}>Version {version.version} · {version.status} · {version.nutrition_snapshot?.option_count||0}/35 options</li>)}</ul>
      </section>
    </>}

    <section className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="text-lg font-semibold">Generate Diet Chart</h3><p className="mt-1 text-sm text-slate-500">Review existing information and confirm professional plan targets.</p><button ref={generateButtonRef} type="button" onClick={openRequirements} className="mt-4 min-h-11 rounded-xl bg-slate-950 px-5 font-semibold text-white">Open Diet Requirements</button></section>
    {requirementsOpen&&<div className="fixed inset-0 z-[80] overflow-y-auto bg-slate-950/60 p-3 sm:p-6" role="presentation" onMouseDown={(event)=>{if(event.target===event.currentTarget){setRequirementsOpen(false);requestAnimationFrame(()=>generateButtonRef.current?.focus());}}}><section role="dialog" aria-modal="true" aria-labelledby="diet-requirements-title" className="mx-auto w-full max-w-5xl rounded-3xl bg-slate-50 p-5 shadow-2xl sm:p-7"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">Diet planning</p><h2 id="diet-requirements-title" className="mt-1 text-2xl font-semibold">Diet Requirements</h2><p className="mt-1 text-sm text-slate-600">Existing information remains governed by Nutrition Assessment and Client 360.</p></div><button type="button" aria-label="Close Diet Requirements" onClick={()=>{setRequirementsOpen(false);requestAnimationFrame(()=>generateButtonRef.current?.focus());}} className="grid min-h-11 min-w-11 place-items-center rounded-xl border bg-white text-xl">×</button></div>
      <section className={`mt-5 rounded-2xl border p-4 ${readiness.outcome==='READY'?'border-emerald-200 bg-emerald-50':'border-amber-200 bg-amber-50'}`}><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-xs font-bold uppercase tracking-wider">Planning information</p><p className="mt-1 font-semibold">{String(readiness.outcome||'NOT_STARTED').replaceAll('_',' ')}</p></div><span className="rounded-full bg-white px-3 py-1 text-xs font-bold">Authoring permitted</span></div><p className="mt-2 text-sm">{readiness.outcome==='READY'?'The current assessment is available as planning context.':'Missing information is advisory. Enter appropriate targets using professional judgement, and request optional client information when useful.'}</p>{(resolved.requires_professional_confirmation||healthContext?.assessment?.measurement_context_changed)&&<p role="status" className="mt-2 text-sm font-semibold">{healthContext?.assessment?.measurement_context_changed?'Measurements changed after the current assessment; review them when relevant.':'One or more legacy measurements may benefit from professional confirmation.'}</p>}</section>
      <form onSubmit={create} className="mt-5 rounded-2xl border border-slate-200 bg-white p-4"><h3 className="font-semibold">Professional plan inputs</h3><p className="mt-1 text-xs text-slate-500"><strong>Target methodology:</strong> consultant-entered targets use professional judgement and are not prescribed automatically from BMI or assessment completeness.</p><div className="mt-4 grid gap-3 md:grid-cols-3"><label className="text-sm font-semibold">Plan name<input ref={firstFieldRef} required minLength={2} maxLength={120} value={form.name} onChange={(event)=>setForm({...form,name:event.target.value})} className="mt-2 w-full rounded-xl border p-3"/></label><label className="text-sm font-semibold">Calories<input required type="number" min="1" value={form.dailyCalories} onChange={(event)=>setForm({...form,dailyCalories:event.target.value})} className="mt-2 w-full rounded-xl border p-3"/></label><label className="text-sm font-semibold">Protein (g)<input required type="number" min="0" step="0.1" value={form.dailyProtein} onChange={(event)=>setForm({...form,dailyProtein:event.target.value})} className="mt-2 w-full rounded-xl border p-3"/></label></div><button disabled={!valid||busy} className="mt-4 min-h-11 rounded-xl bg-slate-950 px-5 font-semibold text-white disabled:opacity-40">{busy==='create'?'Generating…':'Generate Diet Chart'}</button></form>
      <details className="mt-5 rounded-2xl border border-slate-200 bg-white p-4"><summary className="cursor-pointer font-semibold">Client nutrition context</summary><p className="mt-2 text-xs text-slate-500">Use Nutrition Assessment to edit or confirm these values.</p><dl className="mt-4 grid gap-3 sm:grid-cols-2">{nutritionContext.map(([label,value])=><div key={label} className="rounded-xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-sm font-semibold">{show(value)}</dd></div>)}</dl></details>
      <details className="mt-4 rounded-2xl border border-slate-200 bg-white p-4"><summary className="cursor-pointer font-semibold">Measurements and evidence</summary><p className="mt-2 text-xs text-slate-500">Read-only values remain governed by Client 360.</p><dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{fields.map(([label,value])=><div key={label} className="rounded-xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-sm font-semibold">{show(value)}</dd></div>)}</dl><p className="mt-3 text-xs text-slate-500">Confirmed biomarkers for consultant review</p><p className="mt-1 text-sm font-semibold">{confirmedBiomarkers.length?`${confirmedBiomarkers.length} confirmed biomarker result${confirmedBiomarkers.length===1?'':'s'} available`:'No confirmed biomarkers available'}</p><p className="mt-1 text-xs text-slate-500">These results remain evidence for professional review. They do not automatically diagnose conditions and do not silently prescribe foods or targets.</p><button type="button" onClick={onReviewMeasurements} className="mt-4 min-h-11 rounded-xl border px-4 text-sm font-semibold">Review measurements in Client 360</button></details>
      <section className="mt-4 rounded-2xl border border-slate-200 bg-white p-4"><h3 className="font-semibold">Missing information</h3>{completeness?<><p className="mt-2 text-sm text-slate-600">{requestedFields.length?`${requestedFields.length} missing or confirmation-required field${requestedFields.length===1?'':'s'} can be requested securely.`:'No requestable missing information was reported.'}</p>{(completeness.fields||[]).filter((item)=>item.client_can_provide&&['MISSING','INVALID','REQUIRES_CONFIRMATION'].includes(item.status)).map((item)=><label key={item.field_id} className="mt-2 flex min-h-11 items-start gap-3 rounded-xl bg-slate-50 p-3"><input type="checkbox" className="mt-1" checked={requestedFields.includes(item.field_id)} onChange={()=>setRequestedFields((current)=>current.includes(item.field_id)?current.filter((id)=>id!==item.field_id):[...current,item.field_id])}/><span><strong className="text-sm">{item.label}</strong><span className="block text-xs text-slate-500">{String(item.status).replaceAll('_',' ')} · {item.reason||item.source||'Client information'}</span></span></label>)}<button type="button" disabled={!requestedFields.length||busy} onClick={requestMissingInformation} className="mt-4 min-h-11 rounded-xl bg-violet-700 px-4 text-sm font-semibold text-white disabled:opacity-40">{busy==='questionnaire'?'Creating secure link…':'Request Missing Information'}</button>{questionnaireLink&&<div role="status" className="mt-3 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800"><p>The scoped link is ready and expires automatically.</p><button type="button" onClick={()=>navigator.clipboard?.writeText(questionnaireLink)} className="mt-2 min-h-10 rounded-lg border border-emerald-300 bg-white px-3 font-semibold">Copy secure link</button></div>}</>:<p className="mt-2 text-sm text-slate-500">Completeness is unavailable. No empty state has been inferred.</p>}</section>
    </section></div>}
    {message && <p role="status" className={`rounded-xl p-3 text-sm font-semibold ${creationState.state==='reload_failed'?'border border-amber-300 bg-amber-50 text-amber-900':'bg-emerald-50 text-emerald-800'}`}>{message}</p>}
  </div>;
}
