import { useEffect, useState } from "react";
import { BarChart3, Eye, RefreshCw, ShieldCheck } from "lucide-react";
import {
  decideMarketplaceProfile,
  decideMarketplaceQualification,
  decideMarketplaceReview,
  getAdminMarketplaceAnalytics,
  getAdminMarketplaceOperations,
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
const GOVERNANCE_CONTRACT = "Approval and publication are independent";
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
    try {
      await decideMarketplaceProfile(selected.id, action, reason);
      setSelected(null);
      setNotice(`${action.replaceAll("_", " ")} completed.`);
      load();
    } catch (error) {
      setNotice(error.message);
    }
  };
  return (
    <div className="space-y-5">
      <header className="rounded-3xl bg-slate-950 p-6 text-white">
        <p className="text-xs font-bold uppercase tracking-widest text-cyan-300">
          Super Admin authority
        </p>
        <h1 className="mt-2 text-3xl font-bold">Marketplace governance</h1>
        <p className="mt-2 text-sm text-slate-300">
          Approval, publication and Homepage Showcase are separate governed
          actions. Practice owners cannot access these controls.
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
      <ConsultantInventory data={inventory} />
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
          onClose={() => setSelected(null)}
          onAct={profileAction}
        />
      )}
    </div>
  );
}

function ConsultantInventory({data}){
  const [query,setQuery]=useState('');
  const [marketplaceStatus,setMarketplaceStatus]=useState('');
  if(!data)return <section aria-busy="true" className="rounded-2xl bg-white p-6">Loading All Consultants…</section>;
  const rows=(data.items||[]).filter(item=>(!marketplaceStatus||item.marketplace_status===marketplaceStatus)&&(!query||[item.name,item.email,item.profession,item.practice].some(value=>String(value||'').toLowerCase().includes(query.toLowerCase()))));
  const summary=data.summary||{};
  return <section className="rounded-2xl border bg-white p-5"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase text-blue-700">Master inventory</p><h2 className="text-xl font-bold">All Consultants</h2><p className="text-sm text-slate-500">Every governed consultant account, including profiles not started.</p></div><div className="flex flex-wrap gap-2"><input aria-label="Search consultants" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search name, email, profession or practice" className="min-h-11 rounded-xl border px-3"/><select aria-label="Marketplace status" value={marketplaceStatus} onChange={e=>setMarketplaceStatus(e.target.value)} className="min-h-11 rounded-xl border px-3"><option value="">All marketplace states</option>{['NOT_STARTED','DRAFT','SUBMITTED_FOR_REVIEW','UNDER_REVIEW','CHANGES_REQUIRED','APPROVED','PUBLISHED','UNPUBLISHED','REJECTED','SUSPENDED'].map(value=><option key={value}>{value}</option>)}</select></div></div><div className="mt-4 grid gap-2 sm:grid-cols-3 lg:grid-cols-5">{[['Total',summary.total],['Not started',summary.not_started],['Pending',summary.pending_review],['Published',summary.published],['Featured',summary.featured]].map(([label,value])=><div key={label} className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><strong>{value??'—'}</strong></div>)}</div>{data.state==='PARTIAL_DATA'?<p role="alert" className="mt-4 rounded-xl bg-amber-50 p-3">PARTIAL_DATA — consultant inventory is unavailable; marketplace queues remain independent.</p>:!rows.length?<p className="mt-4 rounded-xl border border-dashed p-6 text-center">CONFIRMED_EMPTY</p>:<div className="mt-4 overflow-x-auto"><table className="min-w-[1100px] w-full"><thead><tr>{['Consultant','Profession','Practice','Account','Marketplace','Completeness','Qualification','Eligibility','Website visibility','Featured','Action'].map(label=><th key={label} className="p-3 text-left text-xs uppercase text-slate-500">{label}</th>)}</tr></thead><tbody>{rows.map(item=><tr key={item.user_id} className="border-t"><td className="p-3"><strong>{item.name}</strong>{item.demo&&<span className="ml-2 rounded-full bg-violet-100 px-2 py-1 text-xs font-bold text-violet-800">DEMO</span>}<p className="text-xs text-slate-500">{item.email}</p></td><td className="p-3 text-sm">{item.profession?.replaceAll('_',' ')||'Not configured'}</td><td className="p-3 text-sm">{item.practice||'Independent'}</td><td className="p-3 text-sm">{item.account_status}</td><td className="p-3 text-sm">{item.marketplace_status.replaceAll('_',' ')}</td><td className="p-3">{item.profile_completeness}%</td><td className="p-3 text-sm">{item.qualification_status.replaceAll('_',' ')}</td><td className="p-3 text-sm"><strong>{item.eligibility.replaceAll('_',' ')}</strong>{item.eligibility_blockers?.length>0&&<p className="text-xs text-amber-700">{item.eligibility_blockers.join(', ').replaceAll('_',' ')}</p>}</td><td className="p-3 text-sm">{item.website_visibility.replaceAll('_',' ')}</td><td className="p-3">{item.homepage_featured?'Yes':'No'}</td><td className="p-3">{item.slug?<a className="font-bold text-blue-700" href={`/consultants/${item.slug}${item.published?'':'?preview=draft'}`} target="_blank" rel="noreferrer">{item.published?'Public profile':'Draft preview'}</a>:<span className="text-xs font-bold">Invite to complete profile</span>}</td></tr>)}</tbody></table></div>}</section>;
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
function ReviewDrawer({ item, onClose, onAct }) {
  const [reason, setReason] = useState("");
  const p = item.projection;
  const actions =
    item.status === "SUBMITTED_FOR_REVIEW"
      ? ["START_REVIEW"]
      : item.status === "UNDER_REVIEW"
        ? ["REQUEST_CHANGES", "APPROVE_PROFILE", "REJECT_PROFILE"]
        : item.status === "APPROVED"
          ? ["PUBLISH_PROFILE"]
          : item.status === "PUBLISHED"
            ? ["UNPUBLISH_PROFILE", "SUSPEND_PROFILE"]
            : item.status === "SUSPENDED"
              ? ["RESTORE_PROFILE"]
              : [];
  return (
    <div className="fixed inset-0 z-[100] bg-slate-950/50" onClick={onClose}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Marketplace profile review"
        onClick={(e) => e.stopPropagation()}
        className="ml-auto h-full w-[min(96vw,720px)] overflow-y-auto bg-white p-6"
      >
        <button onClick={onClose} className="min-h-11 rounded-xl border px-4">
          Close
        </button>
        <div className="mt-5 flex items-center gap-3">
          <ShieldCheck className="text-blue-700" />
          <div>
            <h2 className="text-2xl font-bold">{p.display_name}</h2>
            <p>
              {p.professional_title} · {p.profession_code}
            </p>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          {[['Profile',`${item.completeness}% complete`],['Credential','Review in Credentials queue'],['Review',item.status.replaceAll('_',' ')],['Website',item.public_visibility?'Visible':'Hidden']].map(([label,value])=><div key={label} className="rounded-xl border p-3"><p className="text-xs font-bold uppercase text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold">{value}</p></div>)}
        </div>
        {p.profile_photo_url&&<img src={p.profile_photo_url} alt={`${p.display_name} profile submission`} className="mt-5 aspect-[4/3] w-full rounded-2xl border bg-slate-100 object-cover sm:aspect-[3/1]"/>}
        <section className="mt-6 rounded-2xl bg-slate-50 p-5">
          <h3 className="font-bold">
            Proposed public version {item.working_version}
          </h3>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            {Object.entries(p)
              .filter(([key]) => key !== "profile_photo_url")
              .map(([key, value]) => (
                <div key={key}>
                  <dt className="text-xs font-bold uppercase text-slate-500">
                    {key.replaceAll("_", " ")}
                  </dt>
                  <dd className="mt-1 text-sm">
                    {Array.isArray(value)
                      ? value
                          .map((v) =>
                            typeof v === "object" ? JSON.stringify(v) : v,
                          )
                          .join(", ")
                      : String(value ?? "—")}
                  </dd>
                </div>
              ))}
          </dl>
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
        <label className="mt-5 block font-bold">
          Decision reason
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="mt-2 min-h-24 w-full rounded-xl border p-3"
          />
        </label>
        <div className="mt-5 flex flex-wrap gap-2">
          {actions.map((action) => (
            <button
              key={action}
              onClick={() => onAct(action, reason || null)}
              className="min-h-11 rounded-xl bg-slate-950 px-4 text-sm font-bold text-white"
            >
              {action.replaceAll("_", " ")}
            </button>
          ))}
        </div>
      </aside>
    </div>
  );
}
