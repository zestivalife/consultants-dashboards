import { useEffect, useState } from "react";
import { BarChart3, Eye, RefreshCw, ShieldCheck } from "lucide-react";
import {
  decideMarketplaceProfile,
  decideMarketplaceQualification,
  decideMarketplaceReview,
  getAdminMarketplaceAnalytics,
  getAdminMarketplaceOperations,
  getAdminMarketplaceQualificationEvidence,
  getAdminMarketplaceFinance,
  getAdminFinderConfig,
  updateAdminFinderConfig,
  listAdminMarketplace,
  listAdminMarketplaceConsultants,
  setMarketplaceHomepageFeature,
} from "../../lib/practiceOperationsApi";

const VIEWS = [
  "",
  "SUBMITTED_FOR_REVIEW",
  "UNDER_REVIEW",
  "CHANGES_REQUIRED",
  "APPROVED",
  "PUBLISHED",
  "REJECTED",
  "SUSPENDED",
];
const GOVERNANCE_CONTRACT = "Super Admin publication makes the reviewed profile visible";
export default function MarketplaceGovernanceModule() {
  const [state, setState] = useState("loading");
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [operations, setOperations] = useState(null);
  const [notice, setNotice] = useState("");
  const [finder, setFinder] = useState(null);
  const [finance, setFinance] = useState(null);
  const [inventory, setInventory] = useState(null);
  const load = () => {
    setState("loading");
    Promise.allSettled([
      listAdminMarketplace(status),
      getAdminMarketplaceAnalytics(),
      getAdminMarketplaceOperations(),
      getAdminFinderConfig(),
      getAdminMarketplaceFinance(),
      listAdminMarketplaceConsultants(),
    ])
      .then((results) => {
        const [profiles,metrics,ops,finderConfig,financeData,consultants]=results;
        if(profiles.status==='fulfilled'){setItems(profiles.value.items||[]);setState(profiles.value.state||'READY');}else{setState('FAILED_TO_LOAD');}
        setAnalytics(metrics.status==='fulfilled'?metrics.value:null);
        setOperations(ops.status==='fulfilled'?ops.value:null);
        setFinder(finderConfig.status==='fulfilled'?finderConfig.value.config:null);
        setFinance(financeData.status==='fulfilled'?financeData.value:null);
        setInventory(consultants.status==='fulfilled'?consultants.value:{state:'PARTIAL_DATA',items:[],summary:null});
        const failed=results.filter(result=>result.status==='rejected');
        setNotice(failed.length?`${failed.length} marketplace section${failed.length===1?' is':'s are'} unavailable. Available sections remain usable.`:'');
      });
  };
  useEffect(load, [status]);
  const profileAction = async (action, reason) => {
    await decideMarketplaceProfile(selected.id, action, reason);
    setSelected(null);
    setNotice(`${action.replaceAll("_", " ")} completed.`);
    load();
  };
  const qualificationAction = async (id, action, reason) => {
    await decideMarketplaceQualification(id, action, reason);
    setNotice(`${action.replaceAll("_", " ")} completed.`);
    load();
  };
  return (
    <div className="space-y-5">
      <header className="rounded-3xl bg-slate-950 p-6 text-white">
        <p className="text-xs font-bold uppercase tracking-widest text-cyan-300">
          Super Admin authority
        </p>
        <h1 className="mt-2 text-3xl font-bold">Marketplace governance</h1>
        <p className="mt-2 text-sm text-slate-300">
          Review and publish consultant submissions to the public directory.
          Homepage Showcase remains a separate governed action. Practice owners
          cannot access these controls.
        </p>
      </header>
      {notice && (
        <p role="status" className="rounded-xl bg-blue-50 p-3 text-sm">
          {notice}
        </p>
      )}
      <Metrics analytics={analytics} />
      <MarketplaceFinance data={finance} />
      <HomepageShowcase items={items} onNotice={setNotice} onDone={load} />
      <FinderConfiguration config={finder} onChange={setFinder} onNotice={setNotice} />
      <ConsultantInventory
        data={inventory}
        profiles={items}
        onReview={setSelected}
      />
      <nav
        className="flex gap-2 overflow-x-auto"
        aria-label="Marketplace review states"
      >
        {VIEWS.map((value) => (
          <button
            key={value || "ALL"}
            onClick={() => setStatus(value)}
            className={`min-h-11 shrink-0 rounded-xl px-3 text-xs font-bold ${status === value ? "bg-blue-700 text-white" : "border bg-white"}`}
          >
            {value?.replaceAll("_", " ") || "All"}
          </button>
        ))}
      </nav>
      {state === "loading" ? (
        <p aria-busy="true" className="rounded-2xl bg-white p-8">
          Loading marketplace governance…
        </p>
      ) : state === "FAILED_TO_LOAD" ? (
        <div
          role="alert"
          className="rounded-2xl border border-red-200 bg-red-50 p-6"
        >
          <strong>Marketplace data unavailable</strong>
          <p>No empty queue or zero analytics are inferred.</p>
          <button onClick={load} className="mt-4 min-h-11">
            <RefreshCw className="inline" /> Retry
          </button>
        </div>
      ) : state === "CONFIRMED_EMPTY" ? (
        <div className="rounded-2xl border border-dashed bg-white p-8 text-center">
          No profiles are confirmed in this state.
        </div>
      ) : (
        <ProfileTable items={items} onSelect={setSelected} />
      )}
      <Operations data={operations} onNotice={setNotice} onDone={load} />
      {selected && (
        <ReviewDrawer
          item={selected}
          qualifications={(operations?.qualifications || []).filter(
            (qualification) => String(qualification.profile_id) === String(selected.id),
          )}
          onClose={() => setSelected(null)}
          onAct={profileAction}
          onQualificationAct={qualificationAction}
        />
      )}
    </div>
  );
}

function ConsultantInventory({data,profiles,onReview}){
  const [query,setQuery]=useState('');
  const [marketplaceStatus,setMarketplaceStatus]=useState('');
  if(!data)return <section aria-busy="true" className="rounded-2xl bg-white p-6">Loading All Consultants…</section>;
  const rows=(data.items||[]).filter(item=>(!marketplaceStatus||item.marketplace_status===marketplaceStatus)&&(!query||[item.name,item.email,item.profession,item.practice].some(value=>String(value||'').toLowerCase().includes(query.toLowerCase()))));
  const summary=data.summary||{};
  const openReview=(item)=>{
    const profile=(profiles||[]).find(candidate=>String(candidate.id)===String(item.profile_id));
    if(profile)onReview(profile);
  };
  return <section className="rounded-2xl border bg-white p-5"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase text-blue-700">Master inventory</p><h2 className="text-xl font-bold">All Consultants</h2><p className="text-sm text-slate-500">Every governed consultant account, including profiles not started.</p></div><div className="flex flex-wrap gap-2"><input aria-label="Search consultants" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search name, email, profession or practice" className="min-h-11 rounded-xl border px-3"/><select aria-label="Marketplace status" value={marketplaceStatus} onChange={e=>setMarketplaceStatus(e.target.value)} className="min-h-11 rounded-xl border px-3"><option value="">All marketplace states</option>{['NOT_STARTED','DRAFT','SUBMITTED_FOR_REVIEW','UNDER_REVIEW','CHANGES_REQUIRED','APPROVED','PUBLISHED','UNPUBLISHED','REJECTED','SUSPENDED'].map(value=><option key={value}>{value}</option>)}</select></div></div><div className="mt-4 grid gap-2 sm:grid-cols-3 lg:grid-cols-5">{[['Total',summary.total],['Not started',summary.not_started],['Pending',summary.pending_review],['Published',summary.published],['Featured',summary.featured]].map(([label,value])=><div key={label} className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><strong>{value??'—'}</strong></div>)}</div>{data.state==='PARTIAL_DATA'?<p role="alert" className="mt-4 rounded-xl bg-amber-50 p-3">PARTIAL_DATA — consultant inventory is unavailable; marketplace queues remain independent.</p>:!rows.length?<p className="mt-4 rounded-xl border border-dashed p-6 text-center">CONFIRMED_EMPTY</p>:<div className="mt-4 overflow-x-auto"><table className="min-w-[1100px] w-full"><thead><tr>{['Consultant','Profession','Practice','Account','Marketplace','Completeness','Qualification','Eligibility','Website visibility','Featured','Action'].map(label=><th key={label} className="p-3 text-left text-xs uppercase text-slate-500">{label}</th>)}</tr></thead><tbody>{rows.map(item=><tr key={item.user_id} className="border-t"><td className="p-3"><strong>{item.name}</strong>{item.demo&&<span className="ml-2 rounded-full bg-violet-100 px-2 py-1 text-xs font-bold text-violet-800">DEMO</span>}<p className="text-xs text-slate-500">{item.email}</p></td><td className="p-3 text-sm">{item.profession?.replaceAll('_',' ')||'Not configured'}</td><td className="p-3 text-sm">{item.practice||'Independent'}</td><td className="p-3 text-sm">{item.account_status}</td><td className="p-3 text-sm">{item.marketplace_status.replaceAll('_',' ')}</td><td className="p-3">{item.profile_completeness}%</td><td className="p-3 text-sm">{item.qualification_status.replaceAll('_',' ')}</td><td className="p-3 text-sm"><strong>{item.eligibility.replaceAll('_',' ')}</strong>{item.eligibility_blockers?.length>0&&<p className="text-xs text-amber-700">{item.eligibility_blockers.join(', ').replaceAll('_',' ')}</p>}</td><td className="p-3 text-sm">{item.website_visibility.replaceAll('_',' ')}</td><td className="p-3">{item.homepage_featured?'Yes':'No'}</td><td className="p-3">{item.published?<a className="font-bold text-blue-700" href={`/consultants/${item.slug}`} target="_blank" rel="noreferrer">Public profile</a>:item.profile_id?<button type="button" onClick={()=>openReview(item)} className="min-h-11 rounded-xl border px-3 font-bold text-blue-700"><Eye className="inline"/> Review profile</button>:<span className="text-xs font-bold">Invite to complete profile</span>}</td></tr>)}</tbody></table></div>}</section>;
}

function MarketplaceFinance({data}){return <section className="rounded-2xl border bg-white p-5"><h2 className="text-xl font-bold">Marketplace Finance</h2>{!data?<p role="status" className="mt-3 text-sm">Finance data unavailable; no zero values are inferred.</p>:<div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{[['GMV',data.gmv_minor],['Platform revenue',data.platform_revenue_minor],['Consultant payable',data.consultant_payable_minor],['Pending settlement',data.pending_settlement_minor],['Refunds',data.refunds_minor]].map(([label,value])=><div key={label} className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><strong className="mt-1 block">{data.state==='CONFIRMED_EMPTY'?'No recorded activity':value}</strong></div>)}</div>}<p className="mt-3 text-xs text-slate-500">Revenue recognition: recorded transactions only. No payment movement is inferred.</p></section>}

function FinderConfiguration({ config, onChange, onNotice }) {
  if (!config) return <section role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-5"><b>CONFIGURATION_UNAVAILABLE</b><p>No empty configuration is inferred.</p></section>;
  const areas = Object.entries(config.support_areas || {});
  const questions = config.questions || [];
  const save = async () => { try { await updateAdminFinderConfig(config); onNotice("Consultant Finder configuration saved."); } catch (error) { onNotice(error.message); } };
  const toggleQuestion = code => onChange({...config,questions:questions.includes(code)?questions.filter(x=>x!==code):[...questions,code]});
  const registry=["DIETITIAN","NUTRITIONIST","DIABETES_EDUCATOR","PSYCHOLOGIST","WELLNESS_CONSULTANT","HEALTH_COACH","BEHAVIOURAL_THERAPIST","OCCUPATIONAL_THERAPIST","PHYSIOTHERAPIST","MENTAL_WELLNESS_THERAPIST"];
  const allQuestions=["support_area","mode","location","languages","availability","budget","experience"],ordered=[...questions,...allQuestions.filter(x=>!questions.includes(x))];
  const mapProfession=(code,profession)=>{const area=config.support_areas[code],current=area.professions||[];const professions=current.includes(profession)?current.filter(x=>x!==profession):[...current,profession];onChange({...config,support_areas:{...config.support_areas,[code]:{...area,professions}}})};
  const move=(code,direction)=>{const index=questions.indexOf(code),target=index+direction;if(index<0||target<0||target>=questions.length||code==='support_area')return;const next=[...questions];[next[index],next[target]]=[next[target],next[index]];if(next[0]!=='support_area')return;onChange({...config,questions:next})};
  return <section className="rounded-2xl border bg-white p-5"><div className="flex flex-wrap justify-between gap-3"><div><p className="text-xs font-bold uppercase text-blue-700">Consultant Finder</p><h2 className="text-xl font-bold">Finder Configuration</h2></div><a href="/consultants/finder?preview=1" target="_blank" rel="noreferrer" className="min-h-11 rounded-xl border px-4 py-3 font-bold">Preview Finder</a></div><h3 className="mt-5 font-bold">Support Areas &amp; Profession Mapping</h3><div className="mt-3 grid gap-3 lg:grid-cols-2">{areas.map(([code,area])=><article key={code} className="rounded-xl border p-4"><strong>{area.label}</strong><p className="text-xs text-slate-500">{code}</p><fieldset className="mt-3"><legend className="text-xs font-bold">Mapped professions</legend><div className="mt-2 grid gap-1 sm:grid-cols-2">{registry.map(profession=><label key={profession} className="flex min-h-11 items-center gap-2 text-xs"><input type="checkbox" checked={(area.professions||[]).includes(profession)} onChange={()=>mapProfession(code,profession)}/>{profession.replaceAll('_',' ')}</label>)}</div></fieldset><label className="mt-3 flex min-h-11 items-center gap-2"><input type="checkbox" checked={area.active!==false} onChange={e=>onChange({...config,support_areas:{...config.support_areas,[code]:{...area,active:e.target.checked}}})}/> Enabled</label></article>)}</div><h3 className="mt-5 font-bold">Questions</h3><div className="mt-3 space-y-2">{ordered.map(code=>{const enabled=questions.includes(code),index=questions.indexOf(code);return <div key={code} className="flex flex-wrap items-center gap-2 rounded-xl border p-2"><label className="flex min-h-11 flex-1 items-center gap-2"><input type="checkbox" disabled={code==='support_area'} checked={enabled} onChange={()=>toggleQuestion(code)}/>{code.replaceAll('_',' ')} {code==='support_area'?'(required)':'(optional)'}</label><button aria-label={`Move ${code} up`} disabled={!enabled||index<=1} onClick={()=>move(code,-1)} className="min-h-11 rounded-lg border px-3 font-bold disabled:opacity-30">Move Up</button><button aria-label={`Move ${code} down`} disabled={!enabled||index===questions.length-1||code==='support_area'} onClick={()=>move(code,1)} className="min-h-11 rounded-lg border px-3 font-bold disabled:opacity-30">Move Down</button></div>})}</div><button onClick={save} className="mt-5 min-h-11 rounded-xl bg-slate-950 px-5 font-bold text-white">Save Finder Configuration</button></section>;
}

function Metrics({ analytics }) {
  if (!analytics) return null;
  return (
    <>
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          ["Published consultants", analytics.summary.published_consultants],
          ["Pending approvals", analytics.summary.pending_approvals],
          ["Accepting clients", analytics.summary.accepting_clients],
        ].map(([label, value]) => (
          <section key={label} className="rounded-2xl border bg-white p-4">
            <BarChart3 />
            <p className="mt-3 text-sm text-slate-500">{label}</p>
            <strong className="text-2xl">{value}</strong>
          </section>
        ))}
      </div>
      <section className="rounded-2xl border bg-white p-5">
        <h2 className="font-bold">Homepage marketplace analytics</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {[
            ["Impressions", "HOMEPAGE_CONSULTANT_IMPRESSION"],
            ["Profile clicks", "HOMEPAGE_CONSULTANT_VIEW_CLICK"],
            ["Enrol clicks", "HOMEPAGE_ENROL_CLICK"],
            ["Directory clicks", "HOMEPAGE_DIRECTORY_CLICK"],
            ["Profession discovery", "HOMEPAGE_PROFESSION_CLICK"],
          ].map(([label, key]) => {
            const value = (analytics.homepage_events || []).find(
              (item) => item.event_type === key,
            )?.count;
            return (
              <div key={key}>
                <p className="text-xs text-slate-500">{label}</p>
                <strong className="text-xl">{value ?? "—"}</strong>
              </div>
            );
          })}
        </div>
      </section>
    </>
  );
}
function HomepageShowcase({ items, onNotice, onDone }) {
  const published = items.filter((item) => item.status === "PUBLISHED");
  const change = async (item) => {
    try {
      const enabling = !item.featured_on_homepage;
      await setMarketplaceHomepageFeature(item.id, {
        featured_on_homepage: enabling,
        featured_rank: enabling
          ? item.featured_rank ||
            published.filter((x) => x.featured_on_homepage).length + 1
          : null,
        featured_from: null,
        featured_until: null,
      });
      onNotice(
        enabling
          ? "Consultant added to Homepage Showcase."
          : "Consultant removed from Homepage Showcase.",
      );
      onDone();
    } catch (error) {
      onNotice(error.message);
    }
  };
  return (
    <section className="rounded-2xl border bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-bold uppercase text-blue-700">
            Homepage Showcase
          </p>
          <h2 className="text-xl font-bold">Featured consultants</h2>
        </div>
        <span className="text-xs text-slate-500">
          Super Admin controlled · deterministic rank · optional feature window
        </span>
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {published.map((item) => (
          <article key={item.id} className="rounded-xl border p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <strong>{item.projection.display_name}</strong>
                <p className="text-xs text-slate-500">
                  {item.featured_on_homepage
                    ? `Featured rank ${item.featured_rank}`
                    : "Not featured"}{" "}
                  ·{" "}
                  {item.accepting_new_clients
                    ? "Accepting clients"
                    : "View profile only"}
                </p>
              </div>
              <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs text-emerald-800">
                Published
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="min-h-11 rounded-xl bg-slate-950 px-3 text-xs font-bold text-white"
                onClick={() => change(item)}
              >
                {item.featured_on_homepage
                  ? "Remove from Homepage"
                  : "Feature Consultant"}
              </button>
              <a
                className="min-h-11 rounded-xl border px-3 py-3 text-xs font-bold"
                href={`/consultants/${item.slug}`}
                target="_blank"
                rel="noreferrer"
              >
                Preview Homepage Card
              </a>
            </div>
          </article>
        ))}
      </div>
      {!published.length && (
        <p className="mt-4 text-sm text-slate-500">
          No published profiles are eligible. Approved-not-published, suspended
          and unpublished profiles cannot be featured.
        </p>
      )}
    </section>
  );
}
function ProfileTable({ items, onSelect }) {
  return (
    <div className="overflow-x-auto rounded-2xl border bg-white">
      <table className="min-w-[760px] w-full">
        <thead>
          <tr>
            {[
              "Consultant",
              "Tenant",
              "Status",
              "Completeness",
              "Version",
              "Action",
            ].map((x) => (
              <th
                className="p-4 text-left text-xs uppercase text-slate-500"
                key={x}
              >
                {x}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr className="border-t" key={item.id}>
              <td className="p-4 font-bold">{item.projection.display_name}</td>
              <td className="p-4 text-sm">{item.tenant_id}</td>
              <td className="p-4 text-sm">
                {item.status.replaceAll("_", " ")}
              </td>
              <td className="p-4">{item.completeness}%</td>
              <td className="p-4">v{item.working_version}</td>
              <td className="p-4">
                <button
                  onClick={() => onSelect(item)}
                  className="min-h-11 rounded-xl border px-3 font-bold"
                >
                  <Eye className="inline" /> Review
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function Operations({ data, onNotice, onDone }) {
  if (!data) return null;
  const act = async (kind, id, action) => {
    const reason = [
      "VERIFY_QUALIFICATION",
      "PUBLISH_REVIEW",
      "RESTORE_REVIEW",
    ].includes(action)
      ? null
      : window.prompt("Decision reason");
    if (
      !["VERIFY_QUALIFICATION", "PUBLISH_REVIEW", "RESTORE_REVIEW"].includes(
        action,
      ) &&
      !reason
    )
      return;
    try {
      await (kind === "credential"
        ? decideMarketplaceQualification(id, action, reason)
        : decideMarketplaceReview(id, action, reason));
      onNotice(`${action.replaceAll("_", " ")} completed.`);
      onDone();
    } catch (error) {
      onNotice(error.message);
    }
  };
  return (
    <div className="grid gap-5 xl:grid-cols-3">
      <Queue
        title="Credentials"
        empty="No credential evidence awaiting operations"
      >
        {data.qualifications.map((item) => (
          <article className="border-t py-3" key={item.id}>
            <strong>{item.title}</strong>
            <p className="text-xs text-slate-500">
              {item.institution} · {item.verification_status} · evidence{" "}
              {item.credential_document_status || "not attached"}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {[
                ["Verify", "VERIFY_QUALIFICATION"],
                ["Reject", "REJECT_QUALIFICATION"],
                ["Expire", "EXPIRE_QUALIFICATION"],
              ].map(([label, action]) => (
                <button
                  className="min-h-11 rounded-xl border px-3 text-xs font-bold"
                  onClick={() => act("credential", item.id, action)}
                  key={action}
                >
                  {label}
                </button>
              ))}
            </div>
          </article>
        ))}
      </Queue>
      <Queue title="Reviews" empty="No reviews in moderation">
        {data.reviews.map((item) => (
          <article className="border-t py-3" key={item.id}>
            <strong>
              {item.overall_rating}/5 · {item.status}
            </strong>
            <p className="mt-1 text-xs text-slate-500">
              {item.review_text || "No written review"}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {[
                ["Publish", "PUBLISH_REVIEW"],
                ["Reject", "REJECT_REVIEW"],
                ["Hide", "HIDE_REVIEW"],
                ["Restore", "RESTORE_REVIEW"],
              ].map(([label, action]) => (
                <button
                  className="min-h-11 rounded-xl border px-3 text-xs font-bold"
                  onClick={() => act("review", item.id, action)}
                  key={action}
                >
                  {label}
                </button>
              ))}
            </div>
          </article>
        ))}
      </Queue>
      <Queue title="Enrolments" empty="No enrolments">
        {data.enrolments.map((item) => (
          <article className="border-t py-3" key={item.id}>
            <strong>{item.full_name}</strong>
            <p className="text-xs text-slate-500">
              {item.status} · {item.consultation_mode || "mode not selected"} ·
              lead {item.lead_id}
            </p>
          </article>
        ))}
      </Queue>
    </div>
  );
}
function Queue({ title, empty, children }) {
  return (
    <section className="rounded-2xl border bg-white p-5">
      <h2 className="text-lg font-bold">{title}</h2>
      {Array.isArray(children) && !children.length ? (
        <p className="mt-3 text-sm text-slate-500">{empty}</p>
      ) : (
        <div className="mt-3">{children}</div>
      )}
    </section>
  );
}
function ReviewDrawer({ item, qualifications, onClose, onAct, onQualificationAct }) {
  const [reason, setReason] = useState("");
  const [photoFailed, setPhotoFailed] = useState(false);
  const [actionError, setActionError] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const p = item.projection;
  const actions =
    item.status === "SUBMITTED_FOR_REVIEW"
      ? ["PUBLISH_SUBMISSION", "REQUEST_CHANGES"]
      : item.status === "UNDER_REVIEW"
        ? ["REQUEST_CHANGES", "APPROVE_PROFILE", "REJECT_PROFILE"]
        : item.status === "APPROVED"
          ? ["PUBLISH_PROFILE"]
          : item.status === "PUBLISHED"
            ? ["UNPUBLISH_PROFILE", "SUSPEND_PROFILE"]
            : item.status === "SUSPENDED"
              ? ["RESTORE_PROFILE"]
              : [];
  const reasonActions = new Set(["REQUEST_CHANGES", "REJECT_PROFILE", "UNPUBLISH_PROFILE", "SUSPEND_PROFILE"]);
  const requiresReason = actions.some((action) => reasonActions.has(action));
  const act = async (action) => {
    if (reasonActions.has(action) && !reason.trim()) {
      setActionError("Enter a clear decision reason before requesting changes.");
      return;
    }
    setActionError("");
    setBusyAction(action);
    try {
      await onAct(action, reason.trim() || null);
    } catch (error) {
      setActionError(error?.message || "The marketplace action could not be completed.");
    } finally {
      setBusyAction("");
    }
  };
  const qualificationAct = async (qualification, action, reason = null) => {
    if (action === "VERIFY_QUALIFICATION" && !qualification.credential_document_id) {
      setActionError("Attach qualification evidence before verification.");
      return;
    }
    setActionError("");
    setBusyAction(`${action}:${qualification.id}`);
    try {
      await onQualificationAct(qualification.id, action, reason);
    } catch (error) {
      setActionError(error?.message || "The qualification decision could not be completed.");
    } finally {
      setBusyAction("");
    }
  };
  const list = (value) => (Array.isArray(value) ? value : []).filter(Boolean);
  const initials = String(p.display_name || "Consultant")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
  const chips = (values) =>
    list(values).length ? (
      <div className="flex flex-wrap gap-2">
        {list(values).map((value) => (
          <span key={String(value)} className="rounded-full bg-white px-3 py-1 text-sm font-semibold shadow-sm">
            {String(value).replaceAll("_", " ")}
          </span>
        ))}
      </div>
    ) : (
      <span className="text-sm text-slate-500">Not provided</span>
    );
  return (
    <div className="fixed inset-0 z-[100] bg-slate-950/50" onClick={onClose}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Marketplace profile review"
        onClick={(e) => e.stopPropagation()}
        className="ml-auto flex h-full w-[min(100vw,840px)] flex-col bg-slate-50"
      >
        <header className="border-b bg-white p-5 sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex min-w-0 items-center gap-4">
              <div className="h-20 w-20 shrink-0 overflow-hidden rounded-2xl border bg-slate-100">
                {p.profile_photo_url && !photoFailed ? (
                  <img src={p.profile_photo_url} alt={`${p.display_name} profile submission`} onError={() => setPhotoFailed(true)} className="h-full w-full object-cover" />
                ) : (
                  <div className="grid h-full place-items-center text-xl font-bold text-slate-500">{initials}</div>
                )}
              </div>
              <div className="min-w-0">
                <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-blue-700"><ShieldCheck size={16}/> Marketplace review</p>
                <h2 className="mt-1 truncate text-2xl font-bold">{p.display_name}</h2>
                <p className="text-sm text-slate-600">{p.professional_title} · {String(p.profession_code || "Not configured").replaceAll("_", " ")}</p>
              </div>
            </div>
            <button onClick={onClose} className="min-h-11 shrink-0 rounded-xl border bg-white px-4 font-semibold">Close</button>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-5 sm:p-6">
        <div className="grid gap-3 sm:grid-cols-4">
          {[['Profile',`${item.completeness}% complete`],['Credential','Review in Credentials queue'],['Review',item.status.replaceAll('_',' ')],['Website',item.public_visibility?'Visible':'Hidden']].map(([label,value])=><div key={label} className="rounded-xl border p-3"><p className="text-xs font-bold uppercase text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold">{value}</p></div>)}
        </div>
        <section className="mt-5 rounded-2xl border bg-white p-5">
          <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-lg font-bold">Proposed public profile</h3><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">Version {item.working_version}</span></div>
          <p className="mt-3 leading-7 text-slate-700">{p.bio || "Biography not provided."}</p>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <ProfileReviewField label="Specialisations">{chips(p.specialisations)}</ProfileReviewField>
            <ProfileReviewField label="Areas of focus">{chips(p.areas_of_focus)}</ProfileReviewField>
            <ProfileReviewField label="Languages">{chips(p.languages)}</ProfileReviewField>
            <ProfileReviewField label="Consultation modes">{chips(p.consultation_modes)}</ProfileReviewField>
            <ProfileReviewField label="Previous workplaces">{chips(p.previous_workplaces)}</ProfileReviewField>
            <ProfileReviewField label="Session and experience"><p className="text-sm font-semibold">{p.session_duration ? `${p.session_duration} minutes` : "Duration not provided"} · {p.experience_years ?? "—"} years’ experience</p></ProfileReviewField>
          </div>
        </section>
        <section className="mt-5 grid gap-4 sm:grid-cols-2">
          <ReviewCollection title="Services" items={p.services} empty="No services configured" />
          <ReviewCollection title="Programmes" items={p.programmes} empty="No programmes configured" />
          <ReviewCollection title="Public locations" items={p.public_locations} empty="No public locations configured" />
          <article className="rounded-2xl border bg-white p-5"><h3 className="font-bold">Marketplace settings</h3><dl className="mt-3 space-y-2 text-sm"><div className="flex justify-between gap-4"><dt className="text-slate-500">Accepting new clients</dt><dd className="font-semibold">{p.accepting_new_clients ? "Yes" : "No"}</dd></div><div className="flex justify-between gap-4"><dt className="text-slate-500">Public fee</dt><dd className="text-right font-semibold">{p.public_fee_currency ? `${p.public_fee_currency} ${p.public_fee_from ?? "—"}` : "Currency not configured"}</dd></div></dl></article>
        </section>
        <section className="mt-5 rounded-2xl border bg-white p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">Credential review</p><h3 className="mt-1 text-lg font-bold">Qualifications</h3><p className="mt-1 text-sm text-slate-600">Verify only genuine qualifications supported by attached evidence.</p></div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold">{qualifications.length} submitted</span>
          </div>
          {!qualifications.length ? <p className="mt-4 rounded-xl border border-dashed p-4 text-sm text-slate-600">No qualifications have been submitted for this profile.</p> : <div className="mt-4 space-y-3">{qualifications.map((qualification) => <QualificationReviewCard key={qualification.id} qualification={qualification} busyAction={busyAction} onDecision={qualificationAct} />)}</div>}
        </section>
        {item.current_published_version &&
          item.current_published_version !== item.working_version && (
            <section className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <h3 className="font-bold">Diff review</h3>
              <p className="mt-2 text-sm">
                Current public version {item.current_published_version} remains
                live. Proposed version {item.working_version} stays hidden until
                separately approved and published.
              </p>
            </section>
          )}
        {item.status === "DRAFT" && (
          <section className="mt-5 rounded-2xl border border-blue-200 bg-blue-50 p-5">
            <h3 className="font-bold">Draft available for inspection</h3>
            <p className="mt-2 text-sm">
              The consultant must submit this draft before a governed review can
              begin. Review actions will appear here after submission; the draft
              remains hidden from the public directory.
            </p>
          </section>
        )}
        </div>
        <footer className="sticky bottom-0 border-t bg-white p-5 shadow-[0_-8px_24px_rgba(15,23,42,0.08)] sm:p-6">
        {actionError ? <p role="alert" className="mb-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">{actionError}</p> : null}
        {requiresReason ? <label className="block font-bold">Decision reason <span className="font-normal text-slate-500">(required when requesting changes or rejecting)</span><textarea value={reason} onChange={(e) => setReason(e.target.value)} className="mt-2 min-h-20 w-full rounded-xl border p-3" /></label> : actions.length ? <p className="text-sm text-slate-600">Publishing makes this exact submitted version visible in the consultant directory. A verified qualification is required.</p> : <p className="text-sm text-slate-600">No governance action is available for the current state.</p>}
        <div className="mt-3 flex flex-wrap gap-2">
          {actions.map((action) => (
            <button
              key={action}
              onClick={() => void act(action)}
              disabled={Boolean(busyAction) || (reasonActions.has(action) && !reason.trim())}
              className="min-h-11 rounded-xl bg-slate-950 px-4 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busyAction === action ? "Working…" : action === "PUBLISH_SUBMISSION" ? "Publish" : action.replaceAll("_", " ")}
            </button>
          ))}
        </div>
        </footer>
      </aside>
    </div>
  );
}

function QualificationReviewCard({ qualification, busyAction, onDecision }) {
  const [reason, setReason] = useState("");
  const [evidence, setEvidence] = useState(null);
  const [evidenceState, setEvidenceState] = useState("idle");
  const [evidenceError, setEvidenceError] = useState("");
  const evidenceAttached = Boolean(qualification.credential_document_id);
  const verificationStatus = qualification.verification_status || "PENDING";
  const pending = verificationStatus === "PENDING";
  const working = busyAction.endsWith(`:${qualification.id}`);
  return <section className="rounded-xl border bg-slate-50 p-4" aria-label={`${qualification.title} qualification`}>
    <div className="flex flex-wrap items-start justify-between gap-3"><div><strong className="text-base">{qualification.title}</strong><p className="text-sm text-slate-600">{qualification.institution || "Institution not provided"}{qualification.award_year ? ` · ${qualification.award_year}` : ""}</p><p className="mt-1 text-xs text-slate-500">{[qualification.country, qualification.issuing_body, qualification.registration_number].filter(Boolean).join(" · ") || "No additional credential metadata"}</p></div><span className={`rounded-full px-3 py-1 text-xs font-bold ${verificationStatus === "VERIFIED" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{verificationStatus.replaceAll("_", " ")}</span></div>
    <div className={`mt-3 rounded-lg p-3 text-sm ${evidenceAttached ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-900"}`}><strong>{evidenceAttached ? "Certificate attached" : "Certificate not attached"}</strong><p className="mt-1 text-xs">{evidenceAttached ? qualification.credential_document_title || "Private certificate image" : "The consultant must upload a JPEG certificate before verification."}</p>{evidenceAttached ? <button type="button" disabled={evidenceState==="loading"} onClick={async()=>{setEvidenceState("loading");setEvidenceError("");try{const result=await getAdminMarketplaceQualificationEvidence(qualification.id);setEvidence(result);setEvidenceState("ready");}catch(error){setEvidenceError(error.message||"Certificate could not be loaded.");setEvidenceState("error");}}} className="mt-3 min-h-11 rounded-xl border border-emerald-700 bg-white px-4 text-sm font-bold text-emerald-800">{evidenceState==="loading"?"Loading certificate…":"View certificate"}</button> : null}</div>
    {evidenceError ? <p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-700">{evidenceError}</p> : null}
    {evidence?.view_url ? <figure className="mt-3 overflow-hidden rounded-xl border bg-white p-3"><img src={evidence.view_url} alt={`${qualification.title} certificate submitted for verification`} loading="lazy" decoding="async" className="max-h-[32rem] w-full rounded-lg object-contain"/><figcaption className="mt-2 text-xs text-slate-500">Private reviewer preview · link expires in 5 minutes</figcaption></figure> : null}
    {pending ? <><label className="mt-3 block text-sm font-bold">Rejection reason <span className="font-normal text-slate-500">(required only when rejecting)</span><textarea value={reason} onChange={(event) => setReason(event.target.value)} className="mt-2 min-h-16 w-full rounded-lg border bg-white p-3" /></label><div className="mt-3 flex flex-wrap gap-2"><button type="button" disabled={!evidenceAttached || evidenceState!=="ready" || working} onClick={() => void onDecision(qualification, "VERIFY_QUALIFICATION")} className="min-h-11 rounded-xl bg-emerald-700 px-4 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50">{working ? "Working…" : "Verify qualification"}</button><button type="button" disabled={!reason.trim() || working} onClick={() => void onDecision(qualification, "REJECT_QUALIFICATION", reason.trim())} className="min-h-11 rounded-xl border border-red-300 px-4 text-sm font-bold text-red-700 disabled:cursor-not-allowed disabled:opacity-50">Reject qualification</button></div>{evidenceAttached && evidenceState!=="ready" ? <p className="mt-2 text-xs text-slate-500">Open the certificate before verifying this qualification.</p> : null}</> : null}
  </section>;
}

function ProfileReviewField({ label, children }) {
  return <div><p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>{children}</div>;
}

function ReviewCollection({ title, items, empty }) {
  const values = Array.isArray(items) ? items : [];
  return <article className="rounded-2xl border bg-white p-5"><h3 className="font-bold">{title}</h3>{values.length ? <div className="mt-3 space-y-3">{values.map((value,index)=><div key={value.id||`${title}-${index}`} className="rounded-xl bg-slate-50 p-3"><p className="font-semibold">{value.name||value.title||`Item ${index+1}`}</p><p className="mt-1 text-xs text-slate-600">{[value.mode?.replaceAll?.('_',' '),value.duration?`${value.duration} minutes`:null,value.description].filter(Boolean).join(' · ')||'Configured'}</p></div>)}</div>:<p className="mt-3 text-sm text-slate-500">{empty}</p>}</article>;
}
