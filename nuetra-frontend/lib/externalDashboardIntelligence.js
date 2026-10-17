export const PRIORITY_RULES=Object.freeze({
  HIGH_PRIORITY_FOLLOW_UP_OVERDUE:40,
  FOLLOW_UP_OVERDUE:30,
  HIGH_PRIORITY_TASK_OVERDUE:30,
  TASK_OVERDUE:20,
  ONBOARDING_COMPLETED_NEEDS_REVIEW:20,
  ONBOARDING_INCOMPLETE:10,
  GOAL_NEEDS_ATTENTION:20,
  APPOINTMENT_TODAY:10,
});

export const PRIORITY_THRESHOLDS=Object.freeze([
  {minimum:70,level:'P1_CRITICAL',label:'Critical'},
  {minimum:40,level:'P2_HIGH',label:'High'},
  {minimum:20,level:'P3_MEDIUM',label:'Medium'},
  {minimum:0,level:'P4_LOW',label:'Low'},
]);

const day=value=>value?new Date(value).toISOString().slice(0,10):null;
const priorityFor=score=>PRIORITY_THRESHOLDS.find(item=>score>=item.minimum);
const ageLabel=(value,now)=>{if(!value)return'Time unavailable';const hours=Math.max(0,Math.floor((now-new Date(value))/36e5));if(hours<1)return'Less than an hour ago';if(hours<24)return`${hours}h ago`;return`${Math.floor(hours/24)}d ago`;};

export function deriveOnboardingState(client={}){
  const intakeState=typeof client.intakeState==='string'?client.intakeState.toUpperCase():null;
  const hasPercent=client.intakeCompletionPercent!==null&&client.intakeCompletionPercent!==undefined&&client.intakeCompletionPercent!=='';
  const completionPercent=hasPercent&&Number.isFinite(Number(client.intakeCompletionPercent))?Math.max(0,Math.min(100,Number(client.intakeCompletionPercent))):null;
  if(intakeState==='COMPLETED')return{state:'COMPLETED',completionPercent};
  if(intakeState==='NOT_STARTED')return{state:'NOT_STARTED',completionPercent};
  if(intakeState==='IN_PROGRESS')return{state:'IN_PROGRESS',completionPercent};
  if(completionPercent===100)return{state:'COMPLETED',completionPercent};
  if(completionPercent===0)return{state:'NOT_STARTED',completionPercent};
  if(completionPercent!==null)return{state:'IN_PROGRESS',completionPercent};
  return{state:'UNKNOWN',completionPercent:null};
}

export function buildDashboardIntelligence({clients=[],resources={},notifications=[],professionSignals=[],now=new Date()}={}){
  const clientById=new Map(clients.map(client=>[client.id,client]));
  const today=day(now);const month=today?.slice(0,7);
  const consultations=resources.consultations||[];const followups=resources.followups||[];const tasks=resources.tasks||[];const goals=resources.goals||[];
  const activeClients=clients.filter(client=>client.status!=='INACTIVE');
  const items=[];const add=(sourceId,clientId,signal,score,reason,occurredAt,action,target,source={})=>{const key=`${signal}:${sourceId||clientId}`;if(items.some(item=>item.key===key))return;const priority=priorityFor(score);const client=clientById.get(clientId);items.push({key,client,clientId,clientName:client?.displayName,signal,score,reason,occurredAt,age:ageLabel(occurredAt,now),action,directAction:action,target,priorityLevel:priority.level,...source,...priority});};
  for(const item of followups){const overdue=item.due_at&&new Date(item.due_at)<now&&!['COMPLETED','CANCELLED'].includes(item.status);if(overdue)add(item.id,item.client_id,'FOLLOW_UP_OVERDUE',item.payload?.priority==='HIGH'?40:30,item.title||'Follow-up is overdue',item.due_at,'Review follow-up','followups');}
  for(const item of tasks){const overdue=item.due_at&&new Date(item.due_at)<now&&!['COMPLETED','CANCELLED'].includes(item.status);if(overdue)add(item.id,item.client_id,'TASK_OVERDUE',item.payload?.priority==='HIGH'?30:20,item.title||'Task is overdue',item.due_at,'Review task','tasks');}
  for(const item of goals){if(item.status==='NEEDS_ATTENTION')add(item.id,item.client_id,'GOAL_NEEDS_ATTENTION',20,item.title||'Goal needs attention',item.updated_at||item.created_at,'Review goal','goals');}
  for(const item of notifications){if(item.event_type==='ONBOARDING_COMPLETED'&&!item.read_at)add(item.id,item.client_id,'ONBOARDING_COMPLETED_NEEDS_REVIEW',20,item.title,item.created_at,'View client','client');}
  for(const item of professionSignals){const priority={P2_HIGH:40,P3_MEDIUM:20,P4_LOW:10}[item.priority]||10;add(item.source_record_id,item.client_id,item.signal_code,priority,item.reason,item.due_at||item.occurred_at,item.cta?.label||'Review',item.cta?.target||'client',{sourceDomain:item.source_domain,provenance:item.provenance,resolutionState:item.resolution_state,professionCode:item.profession_code});}
  const onboarding=clients.map(client=>({client,...deriveOnboardingState(client)}));
  for(const item of onboarding){if(['IN_PROGRESS','NOT_STARTED'].includes(item.state)){const detail=item.completionPercent===null?item.state.replaceAll('_',' ').toLowerCase():`${item.completionPercent}% complete`;add(item.client.id,item.client.id,'ONBOARDING_INCOMPLETE',PRIORITY_RULES.ONBOARDING_INCOMPLETE,`Onboarding is incomplete (${detail})`,item.client.updatedAt||item.client.createdAt,'View onboarding','client',{completionPercent:item.completionPercent,intakeState:item.client.intakeState||item.state});}}
  items.sort((a,b)=>b.score-a.score||new Date(a.occurredAt||0)-new Date(b.occurredAt||0));
  const completedFollowups=followups.filter(item=>item.status==='COMPLETED').length;
  const scheduledConsultations=consultations.filter(item=>item.due_at&&day(item.due_at)>=today&&!['COMPLETED','CANCELLED'].includes(item.status));
  return{
    kpis:{activeClients:activeClients.length,newClientsThisMonth:clients.filter(client=>String(client.createdAt||'').slice(0,7)===month).length,consultationsThisWeek:consultations.filter(item=>item.due_at&&Math.abs(new Date(item.due_at)-now)<=7*864e5).length,followupsDueToday:followups.filter(item=>day(item.due_at)===today&&!['COMPLETED','CANCELLED'].includes(item.status)).length,overdueFollowups:followups.filter(item=>item.due_at&&new Date(item.due_at)<now&&!['COMPLETED','CANCELLED'].includes(item.status)).length,overdueTasks:tasks.filter(item=>item.due_at&&new Date(item.due_at)<now&&!['COMPLETED','CANCELLED'].includes(item.status)).length,onboardingCompleted:onboarding.some(item=>item.state==='UNKNOWN')?null:onboarding.filter(item=>item.state==='COMPLETED').length,clientsNeedingReview:new Set(items.map(item=>item.clientId).filter(Boolean)).size},
    availability:{onboarding:!onboarding.some(item=>item.state==='UNKNOWN')},
    items,upcoming:scheduledConsultations.slice(0,5),recent:notifications.slice(0,5),
    charts:{followups:{completed:completedFollowups,open:Math.max(0,followups.length-completedFollowups)},goals:goals.reduce((result,item)=>({...result,[item.status]:(result[item.status]||0)+1}),{})},
  };
}
