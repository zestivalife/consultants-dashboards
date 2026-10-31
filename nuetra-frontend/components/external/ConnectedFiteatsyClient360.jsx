import {useCallback,useEffect,useMemo,useState} from 'react';
import {ArrowLeft,Download,FileText,HeartPulse,RefreshCw,ShieldCheck,UserRound} from 'lucide-react';
import {downloadFiteatsyConnectionReport,getFiteatsyConnectionHealthContext} from '../../lib/practiceOperationsApi';

const present=value=>value!==null&&value!==undefined&&value!=='';
const title=value=>String(value||'').replaceAll('_',' ').toLowerCase().replace(/^./,letter=>letter.toUpperCase());
const display=value=>Array.isArray(value)?value.map(item=>typeof item==='object'?JSON.stringify(item):String(item)).join(', '):typeof value==='object'&&value!==null?JSON.stringify(value):present(value)?String(value):'Not shared';

function SummaryGrid({value}){
  const entries=Object.entries(value||{}).filter(([,item])=>present(item)).slice(0,12);
  if(!entries.length)return <p className="mt-3 text-sm text-slate-500">No records were shared in this category.</p>;
  return <dl className="mt-4 grid gap-3 sm:grid-cols-2">{entries.map(([key,item])=><div key={key} className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs font-bold uppercase tracking-wider text-slate-500">{title(key)}</dt><dd className="mt-2 break-words text-sm font-semibold text-slate-900">{display(item)}</dd></div>)}</dl>;
}

export function ConnectedFiteatsyClient360({client,onBack}){
  const [state,setState]=useState({loading:true,data:null,error:''});
  const connectionId=client?.connectionId;
  const load=useCallback(async()=>{
    if(!connectionId){setState({loading:false,data:null,error:'This client has no active consented connection. Health data remains unavailable.'});return;}
    setState({loading:true,data:null,error:''});
    try{setState({loading:false,data:await getFiteatsyConnectionHealthContext(connectionId),error:''});}
    catch(error){setState({loading:false,data:null,error:error.message||'The consented Fiteatsy health context could not be loaded.'});}
  },[connectionId]);
  useEffect(()=>{load();},[load]);
  const profile=state.data?.profile?.client||{};
  const onboarding=state.data?.profile?.onboarding||{};
  const healthProfile=state.data?.profile?.healthProfile||{};
  const healthSummary={...healthProfile,...(state.data?.wearables||{})};
  const name=profile.name||client?.displayName||'Connected Fiteatsy client';
  const connectedRecently=useMemo(()=>client?.connectedAt&&Date.now()-new Date(client.connectedAt).getTime()<7*24*60*60*1000,[client?.connectedAt]);
  const download=async report=>{try{const file=await downloadFiteatsyConnectionReport(connectionId,report.id);const url=URL.createObjectURL(file.blob);const link=document.createElement('a');link.href=url;link.download=file.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){setState(current=>({...current,error:error.message||'The report could not be downloaded.'}));}};
  return <section>
    <button type="button" onClick={onBack} className="mb-5 inline-flex min-h-11 items-center gap-2 rounded-xl px-2 text-sm font-bold text-slate-600 hover:bg-slate-100"><ArrowLeft size={17}/>Back to clients</button>
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <header className="bg-gradient-to-br from-slate-950 via-blue-950 to-cyan-900 p-6 text-white sm:p-8"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-300">Client 360 · consent controlled</p><h2 className="mt-2 text-3xl font-bold">{name}</h2><p className="mt-2 text-sm text-blue-100">Live, connection-scoped Fiteatsy context</p></div><span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/30 bg-emerald-400/15 px-3 py-2 text-xs font-bold text-emerald-100"><ShieldCheck size={16}/>{connectedRecently?'Newly connected':'Connected'}</span></div></header>
      {state.loading?<div className="p-12 text-center text-sm text-slate-500">Loading authorised client data…</div>:state.error?<div className="m-6 rounded-2xl border border-red-200 bg-red-50 p-5" role="alert"><p className="font-bold text-red-900">Client data unavailable</p><p className="mt-2 text-sm text-red-800">{state.error}</p><button type="button" onClick={load} className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl bg-red-900 px-4 text-sm font-bold text-white"><RefreshCw size={16}/>Retry</button></div>:<div className="space-y-6 p-6 sm:p-8">
        <section><div className="flex items-center gap-2"><UserRound className="text-blue-700" size={20}/><h3 className="text-lg font-bold">Profile</h3></div><SummaryGrid value={profile}/></section>
        <section><div className="flex items-center gap-2"><HeartPulse className="text-rose-600" size={20}/><h3 className="text-lg font-bold">Health summary</h3></div><SummaryGrid value={healthSummary}/></section>
        <section className="rounded-2xl border p-5"><h3 className="font-bold">Onboarding context</h3><SummaryGrid value={onboarding}/></section>
        <div className="grid gap-6 lg:grid-cols-2"><section className="rounded-2xl border p-5"><h3 className="font-bold">Measurements</h3><SummaryGrid value={state.data?.measurements}/></section><section className="rounded-2xl border p-5"><h3 className="font-bold">Biomarkers</h3><p className="mt-3 text-3xl font-bold">{state.data?.biomarkers?.length||0}</p><p className="text-sm text-slate-500">consented records</p></section></div>
        <section><div className="flex items-center gap-2"><FileText className="text-violet-700" size={20}/><h3 className="text-lg font-bold">Health reports</h3></div>{(state.data?.reports||[]).length?<div className="mt-4 grid gap-3">{state.data.reports.map(report=><button key={report.id} type="button" onClick={()=>download(report)} className="flex min-h-12 items-center justify-between rounded-2xl border px-4 text-left text-sm font-semibold hover:bg-slate-50"><span>{report.fileName||report.file_name||report.reportType||'Health report'}</span><Download size={17}/></button>)}</div>:<p className="mt-3 text-sm text-slate-500">No reports were shared.</p>}</section>
        <p className="text-xs text-slate-500">Only scopes approved by this client are shown. Revoking consent immediately removes access.</p>
      </div>}
    </div>
  </section>;
}
