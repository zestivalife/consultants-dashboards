import { useState } from 'react';
import { Activity, BellRing, MessageCircle, UserRound } from 'lucide-react';
import s from '../../styles/AuthStoryPanel.module.css';

const stories={
  Client360:{icon:UserRound,title:'Everything about a client in one view',copy:'Profile, onboarding, consultations, plans, goals, health records and timeline.',metric:'91%',label:'Onboarding complete'},
  Priorities:{icon:BellRing,title:'Know what to do first',copy:'Incomplete onboarding, overdue follow-ups, tasks and new evidence are prioritised for you.',metric:'03',label:'Needs attention'},
  Progress:{icon:Activity,title:'Show clients how they are progressing',copy:'Track goals, measurements and longitudinal health evidence visually.',metric:'68%',label:'Goal progress'},
  Communication:{icon:MessageCircle,title:'Stay connected without losing context',copy:'Prepare onboarding, follow-up, plan and progress messages from the same workspace.',metric:'4',label:'Messages ready'},
};

export default function AuthStoryPanel({ mode='login' }){
  const[active,setActive]=useState(mode==='login'?'Priorities':'Client360');
  const item=stories[active],Icon=item.icon;
  return <section className={s.panel} aria-label="Zestiva Consultant product overview">
    <div><p className={s.eyebrow}>Zestiva Consultant</p><h1>{mode==='login'?'Your intelligent practice operating system.':'Build your practice workspace around the way you work.'}</h1><p className={s.intro}>{mode==='login'?'Manage clients, consultations, follow-ups, health records, plans, goals and communication from one connected workspace.':'Set up your Zestiva Consultant workspace and bring client management, consultations, follow-ups, progress and communication into one place.'}</p></div>
    <div className={s.tabs} role="tablist" aria-label="Product capabilities">{Object.keys(stories).map(name=><button key={name} role="tab" aria-selected={active===name} onClick={()=>setActive(name)}>{name}</button>)}</div>
    <div className={s.preview} aria-live="polite"><div className={s.previewIcon}><Icon/></div><div className={s.previewCopy}><small>{active}</small><h2>{item.title}</h2><p>{item.copy}</p></div><div className={s.metric}><strong>{item.metric}</strong><span>{item.label}</span><i><b style={{width:item.metric.includes('%')?item.metric:'72%'}}/></i></div></div>
  </section>;
}
