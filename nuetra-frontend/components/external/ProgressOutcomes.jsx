import {useEffect,useMemo,useState} from 'react';
import {Activity,Flag,Loader2,Plus,RefreshCw,Target,TrendingUp} from 'lucide-react';
import {createProgressMetric,createProgressMilestone,createProgressObservation,getClientProgress} from '../../lib/practiceOperationsApi';

const displayValue=item=>item.numeric_value??item.text_value??'—';

export function ProgressTrendChart({observations=[]}){
  const points=observations.filter(item=>item.numeric_value!==null&&item.numeric_value!==undefined).slice().reverse().slice(-8);
  if(points.length<2)return <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">Add two numeric observations to show a trend.</div>;
  const values=points.map(item=>Number(item.numeric_value)),min=Math.min(...values),max=Math.max(...values),range=max-min||1;
  return <div aria-label="Progress trend chart" className="flex h-28 items-end gap-2 rounded-xl bg-slate-50 p-4">{points.map((point,index)=><div key={point.id} className="min-w-3 flex-1 rounded-t bg-blue-600" style={{height:`${20+((values[index]-min)/range)*80}%`}} title={`${point.label}: ${displayValue(point)} ${point.unit||''}`}/>)}</div>;
}

export function ProgressMetricCard({metric,observations=[]}){
  const history=observations.filter(item=>item.metric_definition_id===metric.id);const latest=history[0];
  return <article className="rounded-2xl border border-slate-200 bg-white p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-950">{metric.label}</p><p className="text-xs text-slate-500">{metric.source_type.replaceAll('_',' ').toLowerCase()}</p></div><TrendingUp aria-hidden="true" className="text-blue-700" size={20}/></div><p className="mt-4 text-2xl font-bold">{latest?displayValue(latest):'—'} <span className="text-sm font-medium text-slate-500">{metric.unit}</span></p><ProgressTrendChart observations={history}/></article>;
}

export function MilestoneTimeline({milestones=[]}){
  if(!milestones.length)return <div className="rounded-2xl border border-dashed bg-white p-6 text-center text-sm text-slate-500">No milestones recorded yet.</div>;
  return <ol aria-label="Milestone timeline" className="space-y-3">{milestones.map(item=><li key={item.id} className="flex gap-3 rounded-2xl border bg-white p-4"><Flag className="mt-0.5 text-emerald-700" size={18}/><span><strong className="block">{item.title}</strong><small className="text-slate-500">{item.status}{item.target_date?` · target ${item.target_date}`:''}</small></span></li>)}</ol>;
}

export function ProgressOutcomes({clientId}){
  const [data,setData]=useState(null),[state,setState]=useState('loading'),[error,setError]=useState('');
  const load=async()=>{setState('loading');setError('');try{setData(await getClientProgress(clientId));setState('ready')}catch(reason){setError(reason.message||'Progress and outcomes could not load.');setState('error')}};
  useEffect(()=>{void load()},[clientId]);
  const metrics=useMemo(()=>data?.metrics||[],[data]);
  const addMetric=async()=>{const label=window.prompt('Metric name');if(!label)return;try{await createProgressMetric({code:`custom_${Date.now()}`,label,value_type:'NUMBER',direction:'INCREASE',source_type:'MANUAL'});await load()}catch(reason){setError(reason.message);setState('error')}};
  const addObservation=async()=>{if(!metrics.length)return addMetric();const raw=window.prompt(`New value for ${metrics[0].label}`);if(raw===null||raw.trim()===''||!Number.isFinite(Number(raw)))return;try{await createProgressObservation(clientId,{metric_definition_id:metrics[0].id,numeric_value:Number(raw),source_type:'MANUAL',observed_at:new Date().toISOString()});await load()}catch(reason){setError(reason.message);setState('error')}};
  const addMilestone=async()=>{const title=window.prompt('Milestone title');if(!title)return;try{await createProgressMilestone(clientId,{title});await load()}catch(reason){setError(reason.message);setState('error')}};
  if(state==='loading')return <div role="status" className="grid min-h-40 place-items-center rounded-2xl bg-white"><Loader2 className="animate-spin"/><span className="sr-only">Loading progress and outcomes</span></div>;
  if(state==='error')return <div role="alert" className="rounded-2xl bg-red-50 p-5 text-red-800">{error}<button onClick={load} className="ml-3 min-h-11 px-3 font-bold"><RefreshCw className="inline"/> Retry</button></div>;
  return <section className="space-y-5" aria-labelledby="progress-title"><header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><p className="text-xs font-bold uppercase tracking-wider text-blue-700">Outcomes</p><h3 id="progress-title" className="text-xl font-bold">Progress & outcomes</h3><p className="text-sm text-slate-500">Profession-defined measures, targets, and milestones.</p></div><div className="flex flex-wrap gap-2"><button onClick={addMetric} className="min-h-11 rounded-xl border px-3 font-semibold"><Plus className="mr-1 inline" size={16}/>Metric</button><button onClick={addObservation} className="min-h-11 rounded-xl bg-blue-700 px-3 font-semibold text-white"><Activity className="mr-1 inline" size={16}/>Observation</button><button onClick={addMilestone} className="min-h-11 rounded-xl border px-3 font-semibold"><Target className="mr-1 inline" size={16}/>Milestone</button></div></header>{metrics.length?<div className="grid gap-4 lg:grid-cols-2">{metrics.map(metric=><ProgressMetricCard key={metric.id} metric={metric} observations={data.observations||[]}/>)}</div>:<div className="rounded-2xl border border-dashed bg-white p-8 text-center"><Activity className="mx-auto text-blue-700"/><h4 className="mt-3 font-semibold">No progress metrics yet.</h4><p className="mt-1 text-sm text-slate-500">Create a profession-relevant metric without changing shared clinical history.</p></div>}<div><h4 className="mb-3 font-semibold">Milestones</h4><MilestoneTimeline milestones={data.milestones||[]}/></div></section>;
}
