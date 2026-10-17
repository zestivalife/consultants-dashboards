import {useEffect,useMemo,useState} from 'react';
import {useRouter} from 'next/router';
import {CheckCircle2,Loader2,ShieldCheck} from 'lucide-react';
import {getProfessionIntake,saveProfessionIntakeAnswers,submitProfessionIntake} from '../../lib/professionIntakeApi';
import {resolveProfessionExperience} from '../../lib/professionExperience';

function Question({question,value,onChange}){
  const common={id:question.question_key,required:question.required,value:value??'',onChange:event=>onChange(question.question_key,event.target.type==='checkbox'?event.target.checked:event.target.value),className:'mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 py-2'};
  if(question.question_type==='BOOLEAN')return <input {...common} type="checkbox" checked={Boolean(value)} value="" className="mt-3 h-5 w-5"/>;
  if(question.question_type==='TEXTAREA')return <textarea {...common} rows={4}/>;
  if(question.question_type==='SINGLE_SELECT')return <select {...common}><option value="">Select</option>{question.options.map(option=><option key={option}>{option}</option>)}</select>;
  return <input {...common} type={question.question_type==='NUMBER'?'number':question.question_type==='DATE'?'date':'text'}/>;
}

export default function ProfessionIntakePage(){
  const router=useRouter();const token=typeof router.query.token==='string'?router.query.token:'';
  const [data,setData]=useState(null);const [answers,setAnswers]=useState({});const [state,setState]=useState('loading');const [error,setError]=useState('');
  useEffect(()=>{if(!token)return;getProfessionIntake(token).then(value=>{setData(value);setAnswers(Object.fromEntries(value.sections.flatMap(section=>section.questions.filter(q=>q.answer!==null).map(q=>[q.question_key,q.answer]))));setState(value.instance.status==='COMPLETED'?'complete':'ready');}).catch(reason=>{setError(reason.message);setState('error');});},[token]);
  const percent=useMemo(()=>data?.instance?.completionPercent||0,[data]);
  const experience=useMemo(()=>resolveProfessionExperience(data?.instance?.professionCode),[data]);
  const change=(key,value)=>setAnswers(current=>({...current,[key]:value}));
  const save=async()=>{setState('saving');setError('');try{const result=await saveProfessionIntakeAnswers(token,answers);setData(current=>({...current,instance:{...current.instance,completionPercent:result.completionPercent}}));setState('ready');}catch(reason){setError(reason.message);setState('ready');}};
  const submit=async()=>{setState('submitting');setError('');try{await saveProfessionIntakeAnswers(token,answers);await submitProfessionIntake(token);setState('complete');}catch(reason){setError(reason.message);setState('ready');}};
  if(state==='loading')return <main className="grid min-h-screen place-items-center bg-slate-50"><Loader2 className="animate-spin"/><span className="sr-only">Loading secure intake</span></main>;
  if(state==='error')return <main className="grid min-h-screen place-items-center bg-slate-50 px-5"><section className="max-w-md rounded-3xl bg-white p-8 text-center shadow-sm"><ShieldCheck className="mx-auto text-slate-500"/><h1 className="mt-4 text-2xl font-semibold">Link unavailable</h1><p className="mt-2 text-slate-600">{error}</p></section></main>;
  if(state==='complete')return <main className="grid min-h-screen place-items-center bg-slate-50 px-5"><section className="max-w-md rounded-3xl bg-white p-8 text-center shadow-sm"><CheckCircle2 className="mx-auto text-emerald-600" size={40}/><h1 className="mt-4 text-2xl font-semibold">Intake submitted</h1><p className="mt-2 text-slate-600">Your practitioner can now review your responses.</p></section></main>;
  return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-3xl"><header className="rounded-3xl bg-slate-950 p-6 text-white"><div className="flex items-center gap-3"><ShieldCheck/><p className="text-sm font-semibold uppercase tracking-wider">Secure profession intake</p></div><h1 className="mt-4 text-3xl font-semibold">Your health and care profile</h1><p className="mt-2 text-slate-300">{data.instance.professionCode.replaceAll('_',' ').toLowerCase()} · {percent}% complete</p></header>{error&&<p role="alert" className="mt-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}<div className="mt-6 space-y-5">{data.sections.map(section=><section key={section.section_key} className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-7"><h2 className="text-xl font-semibold">{section.title}</h2>{section.description&&<p className="mt-1 text-sm text-slate-600">{section.description}</p>}<div className="mt-6 space-y-5">{section.questions.map(question=><label key={question.question_key} htmlFor={question.question_key} className="block text-sm font-semibold text-slate-800">{question.prompt}{question.required&&<span className="text-red-600"> *</span>}<Question question={question} value={answers[question.question_key]} onChange={change}/></label>)}</div></section>)}</div><div className="sticky bottom-0 mt-6 flex gap-3 border-t bg-slate-50/95 py-4 backdrop-blur"><button disabled={state!=='ready'} onClick={save} className="min-h-12 flex-1 rounded-xl border border-slate-300 bg-white font-semibold">Save progress</button><button disabled={state!=='ready'} onClick={submit} className="min-h-12 flex-1 rounded-xl bg-slate-950 font-semibold text-white">Submit intake</button></div></div></main>;
}
