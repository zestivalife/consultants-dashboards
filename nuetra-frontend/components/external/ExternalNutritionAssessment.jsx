import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  CircleAlert,
  ClipboardCopy,
  ClipboardList,
  History,
  Send,
} from "lucide-react";
import {
  createClientInformationRequest,
  getClientInformationCompleteness,
  getNutritionAssessment,
  listClientInformationRequests,
  reviewClientInformationRequest,
  revokeClientInformationRequest,
  saveNutritionAssessment,
} from "../../lib/practiceOperationsApi";
import { choices } from "../../lib/externalIntakeV2";
import {
  reconcileCompleteness,
  resolveNutritionAssessment,
} from "../../lib/nutritionAssessmentSync.mjs";

const EMPTY = {
  dietary_preference: "",
  allergies_intolerances: [],
  food_restrictions: [],
  meal_timing_frequency: "",
  typical_dietary_intake: "",
  appetite_eating_patterns: "",
  water_intake: "",
  food_dislikes_preferences: "",
  nutrition_medical_conditions: [],
  relevant_medications: [],
  relevant_supplements: [],
  weight_management_goals: [],
  recovery_disease_management_goals: [],
  consultant_notes: "",
};
const list = (value) =>
  Array.isArray(value) ? value.filter(Boolean) : value ? [value] : [];
const split = (value) =>
  String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
const label = (value) =>
  String(value || "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (letter) => letter.toUpperCase());
const fieldClass =
  "mt-2 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-100";

function buildSources(data, measurements, biomarkers) {
  const sections = data?.sections || {};
  const sources = [];
  const push = (
    source_type,
    source_id,
    data,
    status = "AVAILABLE",
    observed_at = null,
    provenance = { source: "CLIENT360" },
  ) => {
    if (data && Object.keys(data).length)
      sources.push({
        source_type,
        source_id,
        source_version: String(data.version || data.updatedAt || "current"),
        status,
        observed_at,
        data,
        provenance,
      });
  };
  push(
    "CLIENT_INTAKE",
    "client360-intake",
    {
      ...(sections.aboutYou || sections.personal || data?.overview || {}),
      conditionsSymptoms: sections.conditionsSymptoms || {},
      goals: sections.goals || {},
    },
  );
  push("DIETARY_PREFERENCES", "client360-nutrition", sections.nutrition || {});
  push(
    "ALLERGIES",
    "client360-allergies",
    sections.allergiesFamilyHistory || {},
  );
  push(
    "MEDICAL_HISTORY",
    "client360-medical-history",
    sections.medicalHistory || {},
  );
  push(
    "MEDICATIONS",
    "client360-medications",
    sections.medicationsSupplements || {},
  );
  push("LIFESTYLE", "client360-lifestyle", {
    ...(sections.lifestyle || {}),
    ...(sections.sleepStress || {}),
    ...(sections.activityHydration || {}),
  });
  const latest = measurements?.latest || {};
  if (Object.keys(latest).length) {
    const byType = (type) => latest[type]?.value;
    push(
      "MEASUREMENT",
      "client360-measurements",
      {
        height_cm: byType("HEIGHT_CM"),
        weight_kg: byType("WEIGHT_KG"),
        waist_cm: byType("WAIST_CM"),
        hip_cm: byType("HIP_CM"),
      },
      "AVAILABLE",
      Object.values(latest)[0]?.measured_at,
    );
  }
  (biomarkers || [])
    .filter(
      (item) =>
        item.reviewStatus === "CONFIRMED" || item.review_status === "CONFIRMED",
    )
    .forEach((item) =>
      push(
        "BIOMARKER",
        String(item.id || item.canonicalBiomarkerId),
        {
          canonical_biomarker_id:
            item.canonicalBiomarkerId || item.canonical_biomarker_id,
          value: item.value,
          unit: item.unit,
          source_report_reference:
            item.documentId ||
            item.sourceReportReference ||
            "TRANSIENT_ANALYSIS",
        },
        "CONFIRMED",
        item.observationDate,
        { source: "CONFIRMED_CLIENT_BIOMARKER" },
      ),
    );
  return sources;
}

function Readiness({ value }) {
  const checklist = value?.checklist || {};
  return (
    <section className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-700">
            Diet Plan readiness
          </p>
          <h3 className="mt-1 text-xl font-semibold">
            {label(value?.outcome || "NOT_STARTED")}
          </h3>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-bold ${value?.outcome === "READY" ? "bg-emerald-100 text-emerald-800" : value?.outcome === "BLOCKED" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}
        >
          {value?.outcome || "NOT_STARTED"}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-500">
        Operational readiness supports professional workflow. It is not a
        clinical safety guarantee.
      </p>
      <ul className="mt-5 space-y-2">
        {Object.entries(checklist).map(([key, ready]) => (
          <li key={key} className="flex items-center gap-2 text-sm">
            {ready ? (
              <CheckCircle2 size={17} className="text-emerald-600" />
            ) : (
              <CircleAlert size={17} className="text-amber-600" />
            )}
            <span>{label(key)}</span>
          </li>
        ))}
      </ul>
      {value?.outstanding_information?.length > 0 && (
        <div className="mt-5 rounded-xl bg-amber-50 p-3">
          <p className="text-xs font-bold text-amber-900">
            Outstanding information
          </p>
          <p className="mt-1 text-sm text-amber-800">
            {value.outstanding_information.map(label).join(" · ")}
          </p>
        </div>
      )}
    </section>
  );
}

function InformationCompleteness({ clientId, resolved, onError, onChanged }) {
  const [value, setValue] = useState(null);
  const [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false);
  const [link, setLink] = useState("");
  const [requests, setRequests] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const load = async () => {
    try {
      const [next, history] = await Promise.all([
        getClientInformationCompleteness(clientId),
        listClientInformationRequests(clientId),
      ]);
      setValue(reconcileCompleteness(next, resolved));
      setRequests(history.items || []);
      setSelected(
        next.fields
          .filter(
            (item) =>
              item.client_can_provide &&
              item.requirement_level === "REQUIRED" &&
              ["MISSING", "INVALID", "REQUIRES_CONFIRMATION"].includes(
                item.status,
              ),
          )
          .map((item) => item.field_id),
      );
    } catch (error) {
      onError(error.message);
    }
  };
  useEffect(() => {
    void load();
  }, [clientId, resolved]);
  const toggle = (id) =>
    setSelected((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : [...current, id],
    );
  const create = async () => {
    setBusy(true);
    try {
      const result = await createClientInformationRequest(clientId, {
        field_ids: selected,
        delivery_channel: "COPY_LINK",
        expires_in_hours: 168,
      });
      const url = `${window.location.origin}/client-information/${encodeURIComponent(result.token)}`;
      setLink(url);
      await navigator.clipboard?.writeText(url);
      await load();
      onChanged?.();
    } catch (error) {
      onError(error.message);
    } finally {
      setBusy(false);
    }
  };
  const review = async (item, decisions) => {
    setBusy(`review-${item.id}`);
    try {
      await reviewClientInformationRequest(item.id, {
        expected_version: item.version,
        decisions,
        notes: null,
      });
      await load();
      onChanged?.();
    } catch (error) {
      onError(error.message);
    } finally {
      setBusy(false);
    }
  };
  const revoke = async (item) => {
    setBusy(`revoke-${item.id}`);
    try {
      await revokeClientInformationRequest(item.id);
      await load();
    } catch (error) {
      onError(error.message);
    } finally {
      setBusy(false);
    }
  };
  if (!value)
    return (
      <section
        aria-live="polite"
        className="rounded-[24px] border border-slate-200 bg-white p-5 text-sm text-slate-500"
      >
        Checking client information completeness…
      </section>
    );
  const counts = value.counts || {};
  return (
    <section className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet-700">
        Assessment Link
      </p>
      <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-xl font-semibold">
          {value.total_relevant - (counts.MISSING || 0)} of{" "}
          {value.total_relevant} relevant fields available
        </h3>
        <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-bold text-violet-800">
          {selected.length ? "Information missing" : "Information received"}
        </span>
      </div>
      <p className="mt-2 text-sm text-slate-500">
        Existing client answers are already available. Use a secure link only when you want the client to provide specific missing details.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button type="button" onClick={()=>setExpanded((current)=>!current)} aria-expanded={expanded} className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold">
          {expanded ? "Hide information details" : `Choose missing fields (${selected.length})`}
        </button>
        <button
          type="button"
          disabled={!selected.length || busy}
          onClick={create}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-violet-700 px-4 text-sm font-semibold text-white disabled:opacity-40"
        >
          <Send size={16} />
          {busy ? "Creating…" : "Create Assessment Link"}
        </button>
      </div>
      {expanded&&<div className="mt-5 space-y-2">
        {value.fields
          .filter((item) => item.status !== "NOT_APPLICABLE")
          .map((item) => (
            <label
              key={item.field_id}
              className="flex min-h-11 items-start gap-3 rounded-xl border border-slate-200 p-3"
            >
              <input
                type="checkbox"
                className="mt-1 h-4 w-4"
                disabled={
                  !item.client_can_provide ||
                  !["MISSING", "INVALID", "REQUIRES_CONFIRMATION"].includes(
                    item.status,
                  )
                }
                checked={selected.includes(item.field_id)}
                onChange={() => toggle(item.field_id)}
              />
              <span className="min-w-0 flex-1">
                <span className="flex justify-between gap-2">
                  <strong className="text-sm">{item.label}</strong>
                  <span className="text-[11px] font-bold text-slate-500">
                    {label(item.status)}
                  </span>
                </span>
                <span className="mt-1 block text-xs text-slate-500">
                  {item.reason || item.source || "Existing client information"}
                </span>
              </span>
            </label>
          ))}
      </div>}
      <div className="mt-3 flex flex-wrap gap-3">
        {link && (
          <button
            type="button"
            onClick={() => navigator.clipboard?.writeText(link)}
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 px-4 text-sm font-semibold"
          >
            <ClipboardCopy size={16} />
            Copy secure link
          </button>
        )}
      </div>
      {link && (
        <div role="status" className="mt-3 rounded-xl bg-emerald-50 p-3 text-xs text-emerald-800"><p>Selective secure link copied. This is separate from the original 14-step Health Profile invitation.</p><a href={`https://wa.me/?text=${encodeURIComponent(`Please complete only the missing health information requested by your consultant: ${link}`)}`} target="_blank" rel="noreferrer" className="mt-2 inline-flex min-h-9 items-center rounded-lg border border-emerald-300 bg-white px-3 font-bold">Share through WhatsApp</a></div>
      )}
      {requests.some((item)=>["CREATED","SENT","OPENED","PARTIALLY_COMPLETED"].includes(item.status))&&<div className="mt-5 border-t border-slate-200 pt-4"><h4 className="font-semibold">Pending selective requests</h4>{requests.filter((item)=>["CREATED","SENT","OPENED","PARTIALLY_COMPLETED"].includes(item.status)).map((item)=><article key={item.id} className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-3 text-sm"><span><strong>{item.field_ids.length} requested field{item.field_ids.length===1?'':'s'}</strong><span className="block text-xs text-slate-500">{label(item.status)} · expires {new Date(item.expires_at).toLocaleString()}</span></span><button type="button" disabled={Boolean(busy)} onClick={()=>revoke(item)} className="min-h-10 rounded-lg border border-red-200 px-3 text-xs font-semibold text-red-700">Revoke request</button></article>)}</div>}
      {requests.some((item) => item.status === "SUBMITTED") && (
        <div className="mt-6 border-t border-slate-200 pt-5">
          <h4 className="font-semibold">Review newly submitted answers</h4>
          <div className="mt-3 space-y-3">
            {requests
              .filter((item) => item.status === "SUBMITTED")
              .map((item) => (
                <ReviewRequest key={item.id} item={item} busy={Boolean(busy)} onSubmit={(decisions)=>review(item,decisions)}/>
              ))}
          </div>
        </div>
      )}
    </section>
  );
}

function ReviewRequest({item,busy,onSubmit}){
  const answers=Object.entries(item.patch||{});const [decisions,setDecisions]=useState(Object.fromEntries(answers.map(([field])=>[field,'CONFIRM'])));
  return <article className="rounded-xl bg-slate-50 p-4"><div className="space-y-3">{answers.map(([field,answer])=><div key={field} className="rounded-xl bg-white p-3"><p className="text-xs text-slate-500">{label(field)}</p><p className="mt-1 font-medium">{Array.isArray(answer)?answer.map(label).join(', '):label(answer)}</p><div className="mt-3 flex flex-wrap gap-2">{['CONFIRM','REQUEST_CLARIFICATION'].map((decision)=><button key={decision} type="button" aria-pressed={decisions[field]===decision} onClick={()=>setDecisions((current)=>({...current,[field]:decision}))} className={`min-h-10 rounded-lg border px-3 text-xs font-semibold ${decisions[field]===decision?(decision==='CONFIRM'?'border-emerald-700 bg-emerald-700 text-white':'border-amber-500 bg-amber-50 text-amber-900'):'border-slate-300 bg-white'}`}>{decision==='CONFIRM'?'Confirm':'Request clarification'}</button>)}</div></div>)}</div><button type="button" disabled={busy||!answers.length} onClick={()=>onSubmit(decisions)} className="mt-4 min-h-11 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white disabled:opacity-40">Save field-level review</button></article>;
}

export default function ExternalNutritionAssessment({
  clientId,
  data,
  measurements,
  biomarkers,
  onError,
}) {
  const [state, setState] = useState({ loading: true, value: null });
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [fieldProvenance, setFieldProvenance] = useState({});
  const [editingClientFields, setEditingClientFields] = useState([]);
  const [openSection, setOpenSection] = useState("essentials");
  const [assessmentExpanded, setAssessmentExpanded] = useState(false);
  const sources = useMemo(
    () => buildSources(data, measurements, biomarkers),
    [data, measurements, biomarkers],
  );
  const completenessResolution = useMemo(
    () => ({ values: form, provenance: fieldProvenance }),
    [form, fieldProvenance],
  );
  const load = async () => {
    setState((current) => ({ ...current, loading: true }));
    try {
      const value = await getNutritionAssessment(clientId);
      const resolved = resolveNutritionAssessment(
        data?.sections || {},
        value.assessment_data || {},
        value.field_provenance || {},
      );
      setState({ loading: false, value });
      setForm({ ...EMPTY, ...resolved.values });
      setFieldProvenance(resolved.provenance);
    } catch (error) {
      setState({ loading: false, value: null });
      onError(error.message);
    }
  };
  useEffect(() => {
    void load();
  }, [clientId, data]);
  const set = (key, value) =>
    setForm((current) => ({ ...current, [key]: value }));
  const save = async (action) => {
    setBusy(action);
    setNotice("");
    try {
      await saveNutritionAssessment(clientId, {
        expected_version:
          state.value?.current_version ?? state.value?.version ?? 0,
        action,
        profile: form,
        sources,
        clinical_safety_findings: [],
      });
      await load();
      setNotice("Diet planning context saved.");
    } catch (error) {
      onError(error.message);
    } finally {
      setBusy("");
    }
  };
  if (state.loading)
    return (
      <section
        aria-live="polite"
        className="rounded-2xl bg-white p-8 text-center text-sm text-slate-500"
      >
        Loading Nutrition Assessment…
      </section>
    );
  const status = state.value?.status || "NOT_STARTED";
  const receivedFromClient = Object.values(fieldProvenance).some(
    (item) => item?.source === "CLIENT_SUBMITTED",
  );
  const availableFieldCount = Object.entries(form).filter(
    ([key, value]) => key !== "consultant_notes" && list(value).length > 0,
  ).length;
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-5">
        <InformationCompleteness
          clientId={clientId}
          resolved={completenessResolution}
          onError={onError}
          onChanged={load}
        />
        <section className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-700">
                Nutrition Assessment
              </p>
              <h2 className="mt-1 text-xl font-semibold">
                {receivedFromClient ? "Client information received" : "Diet planning context"}
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                {availableFieldCount} assessment field{availableFieldCount === 1 ? "" : "s"} available. Open only when you need to add or correct information.
              </p>
            </div>
            <button type="button" onClick={() => setAssessmentExpanded((current) => !current)} aria-expanded={assessmentExpanded} className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold">
              {assessmentExpanded ? "Close assessment" : "Edit assessment"}
            </button>
          </div>
        </section>
        {assessmentExpanded && <section className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-blue-700">
                <ClipboardList size={18} />
                <p className="text-xs font-bold uppercase tracking-[0.16em]">
                  Nutrition Assessment
                </p>
              </div>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Diet planning context
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Review source-backed client context and save the consultant's
                assessment.
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
              {label(status)}
            </span>
          </div>
          {notice && (
            <p
              role="status"
              className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-800"
            >
              {notice}
            </p>
          )}
          <div className="mt-5 grid grid-cols-3 gap-2 rounded-2xl bg-slate-100 p-1" role="tablist" aria-label="Assessment sections">
            {[['essentials','Essentials'],['patterns','Eating pattern'],['health','Health & goals']].map(([key,caption])=><button key={key} type="button" role="tab" aria-selected={openSection===key} onClick={()=>setOpenSection(key)} className={`min-h-11 rounded-xl px-3 text-sm font-semibold ${openSection===key?'bg-white text-slate-950 shadow-sm':'text-slate-500'}`}>{caption}</button>)}
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {openSection==='essentials'&&<>
            <AssessmentChoice field="dietary_preference" caption="Dietary preference" value={form.dietary_preference} options={["VEGETARIAN","EGG","NON_VEGETARIAN","VEGAN"]} provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("dietary_preference",value)} />
            <AssessmentChoice field="allergies_intolerances" caption="Allergies and intolerances" value={form.allergies_intolerances} options={["YES","NO","NOT_SURE","MILK_DAIRY","PEANUTS","TREE_NUTS","EGG","WHEAT","SOY","FISH","SHELLFISH","OTHER"]} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("allergies_intolerances",value)} />
            <AssessmentChoice field="food_restrictions" caption="Food restrictions" value={form.food_restrictions} options={[...choices.restrictions,"NO_DAIRY","GLUTEN_FREE","NO_ADDED_SUGAR","LOW_SODIUM"]} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("food_restrictions",value)} />
            <AssessmentChoice field="meal_timing_frequency" caption="Meals per day" value={form.meal_timing_frequency} options={choices.mealsPerDay} provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("meal_timing_frequency",value)} />
            </>}
            {openSection==='patterns'&&<>
            <AssessmentChoice wide field="typical_dietary_intake" caption="Typical dietary intake" value={form.typical_dietary_intake} options={["HOME_COOKED","MIXED_HOME_OUTSIDE","FREQUENT_RESTAURANT","REGULAR_SNACKING","IRREGULAR_SCHEDULE"]} provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("typical_dietary_intake",value)} />
            <AssessmentChoice field="appetite_eating_patterns" caption="Appetite and eating patterns" value={form.appetite_eating_patterns} options={["NORMAL_APPETITE","LOW_APPETITE","HIGH_APPETITE","IRREGULAR_HUNGER","SKIPS_MEALS","LATE_NIGHT_EATING","FREQUENT_SNACKING","EMOTIONAL_EATING","NONE","OTHER"]} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("appetite_eating_patterns",value)} />
            <AssessmentChoice field="water_intake" caption="Water intake" value={form.water_intake} options={Array.from({length:11},(_,index)=>`${1+index*.5} L/day`)} provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("water_intake",value)} />
            <AssessmentChoice wide field="food_dislikes_preferences" caption="Food dislikes and preferences" value={form.food_dislikes_preferences} options={[...choices.cravings,"NO_SPECIFIC_PREFERENCES"]} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("food_dislikes_preferences",value)} />
            </>}
            {openSection==='health'&&<>
            <AssessmentChoice field="nutrition_medical_conditions" caption="Nutrition-related medical conditions" value={form.nutrition_medical_conditions} options={choices.conditions} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("nutrition_medical_conditions",value)} />
            <AssessmentChoice field="relevant_medications" caption="Relevant medications" value={form.relevant_medications} options={[...(form.relevant_medications||[]),"NONE"]} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("relevant_medications",value)} />
            <AssessmentChoice field="relevant_supplements" caption="Relevant supplements" value={form.relevant_supplements} options={[...choices.supplementTypes,"NONE"]} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("relevant_supplements",value)} />
            <AssessmentChoice field="weight_management_goals" caption="Weight-management goals" value={form.weight_management_goals} options={["LOSE_WEIGHT","GAIN_WEIGHT","GAIN_MUSCLE","MAINTAIN_WEIGHT"]} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("weight_management_goals",value)} />
            <AssessmentChoice field="recovery_disease_management_goals" caption="Recovery and disease-management goals" value={form.recovery_disease_management_goals} options={choices.goals.filter((goal)=>!["LOSE_WEIGHT","GAIN_WEIGHT","GAIN_MUSCLE","MAINTAIN_WEIGHT"].includes(goal))} multiple provenance={fieldProvenance} editing={editingClientFields} setEditing={setEditingClientFields} onChange={(value)=>set("recovery_disease_management_goals",value)} />
            <Field wide label="Consultant notes">
              <textarea
                rows="4"
                value={form.consultant_notes || ""}
                onChange={(event) =>
                  set("consultant_notes", event.target.value)
                }
                className={fieldClass}
              />
            </Field>
            </>}
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              disabled={
                Boolean(busy) ||
                !["NOT_STARTED", "DRAFT", "CHANGES_REQUESTED"].includes(status)
              }
              onClick={() => save("SAVE_DRAFT")}
              className="min-h-11 rounded-xl border border-slate-300 px-4 text-sm font-semibold disabled:opacity-40"
            >
              {busy === "SAVE_DRAFT" ? "Saving…" : "Save assessment"}
            </button>
          </div>
        </section>}
        <SourceSummary
          data={data}
          measurements={measurements}
          biomarkers={biomarkers}
        />
        {state.value?.history?.length > 0 && (
          <section className="rounded-[24px] border border-slate-200 bg-white p-5">
            <div className="flex items-center gap-2">
              <History size={18} />
              <h3 className="font-semibold">Assessment history</h3>
            </div>
            <ol className="mt-4 space-y-3">
              {state.value.history.map((item, index) => (
                <li
                  key={`${item.created_at}-${index}`}
                  className="rounded-xl bg-slate-50 p-3 text-sm"
                >
                  <strong>{label(item.event_type)}</strong>
                  <span className="text-slate-500">
                    {" "}
                    · {label(item.from_status || "new")} →{" "}
                    {label(item.to_status)} · version {item.assessment_version}
                  </span>
                  <time className="mt-1 block text-xs text-slate-400">
                    {new Date(item.created_at).toLocaleString()}
                  </time>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>
      <Readiness value={state.value?.readiness} />
    </div>
  );
}

function Field({ label: caption, wide = false, children }) {
  return (
    <label
      className={`block text-sm font-semibold text-slate-800 ${wide ? "sm:col-span-2" : ""}`}
    >
      {caption}
      {children}
    </label>
  );
}
function AssessmentChoice({field,caption,value,options,multiple=false,wide=false,provenance,editing,setEditing,onChange}) {
  const source=provenance[field]?.source;
  const clientSupplied=source==="CLIENT_SUBMITTED";
  const locked=clientSupplied&&!editing.includes(field);
  const selected=multiple?list(value):(value?[value]:[]);
  const allOptions=[...new Set([...options,...selected])];
  const toggle=(option)=>{
    if(!multiple){onChange(option);return;}
    const exclusive=["NONE","NO","NOT_SURE","NO_SPECIFIC_PREFERENCES"];
    if(exclusive.includes(option)){onChange(selected.includes(option)?[]:[option]);return;}
    const clean=selected.filter((item)=>!exclusive.includes(item));
    onChange(clean.includes(option)?clean.filter((item)=>item!==option):[...clean,option]);
  };
  return <fieldset className={`${wide?"sm:col-span-2 ":""}rounded-2xl border border-slate-200 p-4`}>
    <div className="flex items-start justify-between gap-3"><div><legend className="text-sm font-semibold text-slate-800">{caption}</legend><SourceBadge source={source} confirmed={provenance[field]?.confirmed}/></div>{locked&&<button type="button" onClick={()=>setEditing((current)=>[...current,field])} className="min-h-9 rounded-lg border border-slate-300 px-3 text-xs font-semibold">Correct</button>}</div>
    {selected.length===0&&<p className="mt-3 text-sm text-slate-500">Not provided</p>}
    <div className="mt-3 flex flex-wrap gap-2">{allOptions.map((option)=>{const active=selected.includes(option);return <button key={option} type="button" role={multiple?"checkbox":"radio"} aria-checked={active} disabled={locked} onClick={()=>toggle(option)} className={`min-h-11 rounded-full border px-4 py-2 text-sm font-semibold disabled:cursor-default ${active?"border-emerald-700 bg-emerald-700 text-white":"border-slate-300 bg-white text-slate-700"}`}>{label(option)}</button>})}</div>
  </fieldset>;
}
function SourceBadge({source,confirmed}){
  const text=confirmed?"Consultant confirmed":source==="CLIENT_SUBMITTED"?"Client submitted":source==="CONSULTANT_ASSESSMENT"?"Consultant assessment":source?label(source):"Missing";
  return <span className={`mt-1 inline-flex rounded-full px-2 py-1 text-[11px] font-bold ${source?"bg-blue-50 text-blue-700":"bg-slate-100 text-slate-500"}`}>{text}</span>;
}
function ListField({ label: caption, value, onChange }) {
  return (
    <Field label={`${caption} (comma separated)`}>
      <input
        value={list(value).join(", ")}
        onChange={(event) => onChange(split(event.target.value))}
        className={fieldClass}
      />
    </Field>
  );
}
function SourceSummary({ data, measurements, biomarkers }) {
  const rows = [
    [
      "Current weight",
      measurements?.latest?.WEIGHT_KG?.value != null
        ? `${measurements.latest.WEIGHT_KG.value} kg`
        : "Not provided",
    ],
    [
      "BMI",
      measurements?.calculations?.bmi?.value ??
        data?.derived?.bmi?.value ??
        "Not provided",
    ],
    [
      "Medical conditions",
      list(data?.sections?.conditionsSymptoms?.conditions || data?.sections?.medicalHistory?.conditions).join(", ") ||
        "Not provided",
    ],
    [
      "Health goals",
      list(data?.sections?.goals?.goals || data?.sections?.goals?.selectedGoals).join(", ") || "Not provided",
    ],
    [
      "Confirmed biomarkers",
      String(
        (biomarkers || []).filter(
          (item) =>
            item.reviewStatus === "CONFIRMED" ||
            item.review_status === "CONFIRMED",
        ).length,
      ),
    ],
  ];
  return (
    <section className="rounded-[24px] border border-slate-200 bg-[#f8f7f2] p-5">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
        Existing client information
      </p>
      <h3 className="mt-1 text-lg font-semibold">Read-only health context</h3>
      <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rows.map(([caption, value]) => (
          <div key={caption} className="rounded-xl bg-white p-3">
            <dt className="text-xs text-slate-500">{caption}</dt>
            <dd className="mt-1 text-sm font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
