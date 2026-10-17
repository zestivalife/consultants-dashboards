import {getToken,refreshAccessToken} from './api';

const BASE='/api/gateway/api/v1/practice-operations';

async function request(path,options={}){
  const send=token=>fetch(`${BASE}${path}`,{credentials:'include',...options,headers:{'Content-Type':'application/json',...(token?{'X-Nuetra-Authorization':`Bearer ${token}`}:{}),...(options.headers||{})}});
  let response=await send(getToken());
  if(response.status===401){const refreshedToken=await refreshAccessToken().catch(()=>null);if(refreshedToken)response=await send(refreshedToken);}
  const body=await response.json().catch(()=>null);
  if(!response.ok){const error=new Error(body?.error?.safe_message||'Practice operation could not be completed.');error.code=body?.error?.code||'PRACTICE_OPERATION_FAILED';error.retryable=Boolean(body?.error?.retryable);error.correlationId=body?.error?.correlation_id;throw error;}
  return body?.data;
}

export function listPracticeResources(resource,{clientId,status,cursor,limit=25}={}){
  const query=new URLSearchParams({limit:String(limit)});if(clientId)query.set('client_id',clientId);if(status)query.set('status',status);if(cursor)query.set('cursor',cursor);
  return request(`/${resource}?${query}`);
}
export function createPracticeResource(resource,payload){return request(`/${resource}`,{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},body:JSON.stringify(payload)});}
export function updatePracticeResource(resource,id,payload){return request(`/${resource}/${id}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function getPracticeConfiguration(){return request('/configuration');}
export function updatePracticeConfiguration(payload){return request('/configuration',{method:'PUT',body:JSON.stringify(payload)});}
export function listCommunicationTemplates(){return request('/communication/templates');}
export function saveCommunicationTemplate(payload){return request('/communication/templates',{method:'POST',body:JSON.stringify(payload)});}
export function listCommunicationActivity(clientId){const query=clientId?`?client_id=${encodeURIComponent(clientId)}`:'';return request(`/communication/activity${query}`);}
export function listPracticeNotifications({unreadOnly=false}={}){return request(`/notifications?unread_only=${unreadOnly?'true':'false'}`);}
export function recordOnboardingCompleted(payload){return request('/events/onboarding-completed',{method:'POST',body:JSON.stringify(payload)});}
export function listClientTimeline(clientId){return request(`/clients/${encodeURIComponent(clientId)}/timeline`);}
export function createProfessionIntakeInvitation(clientId,payload={}){return request(`/clients/${encodeURIComponent(clientId)}/profession-intake-invitations`,{method:'POST',body:JSON.stringify(payload)});}
export function revokeProfessionIntakeInvitation(clientId){return request(`/clients/${encodeURIComponent(clientId)}/profession-intake-invitations/revoke`,{method:'POST'});}
export function getClientProfessionIntake(clientId){return request(`/clients/${encodeURIComponent(clientId)}/profession-intake`);}
export function getProfessionClient360(clientId){return request(`/clients/${encodeURIComponent(clientId)}/profession-view`);}
export function listProfessionPlans(clientId){return request(`/clients/${encodeURIComponent(clientId)}/profession-plans`);}
export function createProfessionPlan(payload){return request('/profession-plans',{method:'POST',body:JSON.stringify(payload)});}
export function getProfessionPlan(planId){return request(`/profession-plans/${encodeURIComponent(planId)}`);}
export function saveProfessionPlan(planId,payload){return request(`/profession-plans/${encodeURIComponent(planId)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function publishProfessionPlan(planId){return request(`/profession-plans/${encodeURIComponent(planId)}/publish`,{method:'POST'});}
export function listProfessionIntakeProjections(){return request('/profession-intake/projections');}
export function publishProfessionIntakeTemplate(payload){return request('/profession-intake/templates',{method:'POST',body:JSON.stringify(payload)});}
export function listPracticeCalendar({view='AGENDA',anchor,clientId}={}){const query=new URLSearchParams({view});if(anchor)query.set('anchor',anchor);if(clientId)query.set('client_id',clientId);return request(`/calendar/events?${query}`);}
export async function openWhatsApp(payload){
  const result=await request('/communication/whatsapp-opened',{method:'POST',body:JSON.stringify(payload)});
  const url=`https://wa.me/${result.phone}?text=${encodeURIComponent(result.message)}`;
  window.open(url,'_blank','noopener,noreferrer');
  return result;
}
