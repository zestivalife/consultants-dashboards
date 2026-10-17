import {useEffect,useState} from 'react';
import {Activity,ClipboardCheck,FileText,RefreshCw} from 'lucide-react';
import {getProfessionClient360} from '../../lib/practiceOperationsApi';

const readable=value=>String(value||'').replaceAll('_',' ').toLowerCase().replace(/^./,letter=>letter.toUpperCase());

export function ProfessionCapabilityNavigation({sections,active,onChange}){
  return <nav aria-label="Profession Client 360 sections" className="flex gap-2 overflow-x-auto pb-1">{sections.map(section=><button key={section.label} onClick={()=>onChange(section.label)} aria-current={active===section.label?'page':undefined} className={`min-h-11 shrink-0 rounded-full px-4 text-sm font-semibold ${active===section.label?'bg-slate-950 text-white':'border border-slate-200 bg-white text-slate-700'}`}>{section.label}</button>)}</nav>;
}

function SectionRecord({item}){
  return <article className="rounded-2xl border border-slate-200 bg-white p-4"><div className="flex flex-wrap items-center justify-between gap-2"><strong>{item.title||readable(item.type)||'Recorded activity'}</strong><span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700">{readable(item.status)||'Recorded'}</span></div><p className="mt-2 text-xs text-slate-500">{item.occurred_at?new Date(item.occurred_at).toLocaleString():'Date unavailable'}</p>{item.due_at&&<p className="mt-1 text-xs text-slate-500">Due {new Date(item.due_at).toLocaleString()}</p>}</article>;
}

export function ProfessionClient360({clientId,biomarkers=[]}){
  const [state,setState]=useState('loading');const [error,setError]=useState('');const [projection,setProjection]=useState(null);const [active,setActive]=useState('');
  const load=async()=>{setState('loading');setError('');try{const value=await getProfessionClient360(clientId);setProjection(value);setActive(current=>current||value.sections?.[0]?.label||'');setState('ready')}catch(reason){setError(reason.message||'Profession workspace could not load.');setState('error')}};
  useEffect(()=>{setActive('');void load()},[clientId]);
  if(state==='loading')return <div role="status" className="grid min-h-48 place-items-center rounded-2xl border bg-white text-sm text-slate-500">Loading profession workspace…</div>;
  if(state==='error')return <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800">{error}<button onClick={load} className="ml-3 min-h-11 rounded-xl px-3 font-bold"><RefreshCw className="mr-1 inline" size={16}/>Retry</button></div>;
  if(!projection?.sections?.length)return <section className="rounded-2xl border border-dashed bg-white p-8 text-center"><Activity className="mx-auto text-blue-700"/><h3 className="mt-3 font-semibold">Standard Client 360</h3><p className="mt-2 text-sm text-slate-500">This practice uses the established Client 360 experience.</p></section>;
  const section=projection.sections.find(item=>item.label===active)||projection.sections[0];
  const items=section.source==='biomarkers'?biomarkers:section.items||[];
  return <div className="space-y-5"><header className="rounded-3xl bg-gradient-to-br from-slate-950 to-blue-950 p-6 text-white"><p className="text-xs font-bold uppercase tracking-[.18em] text-blue-200">{readable(projection.profession)} workspace</p><h3 className="mt-2 text-2xl font-bold">Profession Client 360</h3><p className="mt-2 text-sm text-blue-100">Capability-driven client context from governed, tenant-scoped records.</p></header><ProfessionCapabilityNavigation sections={projection.sections} active={section.label} onChange={setActive}/>{section.state==='UNAVAILABLE'?<div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">This section is unavailable because its practice capability is not enabled.</div>:items.length?<div className="grid gap-3 md:grid-cols-2">{items.map(item=><SectionRecord key={item.id||`${item.canonicalBiomarkerId}-${item.observationDate}`} item={item}/>)}</div>:<section className="rounded-2xl border border-dashed bg-white p-8 text-center"><ClipboardCheck className="mx-auto text-blue-700"/><h4 className="mt-3 font-semibold">No {section.label.toLowerCase()} recorded yet.</h4><p className="mt-2 text-sm text-slate-500">This is a confirmed empty state from the {section.source.replaceAll('-',' ')} source.</p></section>}<footer className="flex items-center gap-2 text-xs text-slate-500"><FileText size={14}/>Source: {section.source.replaceAll('-',' ')} · tenant scoped</footer></div>;
}
