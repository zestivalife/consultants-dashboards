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
export function listSessionNotes(clientId){return request(`/clients/${encodeURIComponent(clientId)}/session-notes`);}
export function createSessionNote(payload){return request('/session-notes',{method:'POST',body:JSON.stringify(payload)});}
export function getSessionNote(noteId){return request(`/session-notes/${encodeURIComponent(noteId)}`);}
export function saveSessionNote(noteId,payload){return request(`/session-notes/${encodeURIComponent(noteId)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function finaliseSessionNote(noteId){return request(`/session-notes/${encodeURIComponent(noteId)}/finalise`,{method:'POST'});}
export function amendSessionNote(noteId,payload){return request(`/session-notes/${encodeURIComponent(noteId)}/amendments`,{method:'POST',body:JSON.stringify(payload)});}
export function listPrivateNotes(noteId){return request(`/session-notes/${encodeURIComponent(noteId)}/private`);}
export function createPrivateNote(noteId,payload){return request(`/session-notes/${encodeURIComponent(noteId)}/private`,{method:'POST',body:JSON.stringify(payload)});}
export function getClientProgress(clientId){return request(`/clients/${encodeURIComponent(clientId)}/progress`);}
export function createProgressMetric(payload){return request('/progress/metrics',{method:'POST',body:JSON.stringify(payload)});}
export function createProgressObservation(clientId,payload){return request(`/clients/${encodeURIComponent(clientId)}/progress/observations`,{method:'POST',body:JSON.stringify(payload)});}
export function createProgressTarget(clientId,payload){return request(`/clients/${encodeURIComponent(clientId)}/progress/targets`,{method:'POST',body:JSON.stringify(payload)});}
export function createProgressMilestone(clientId,payload){return request(`/clients/${encodeURIComponent(clientId)}/progress/milestones`,{method:'POST',body:JSON.stringify(payload)});}
export function getProfessionIntelligence(){return request('/intelligence/signals');}
export function listTemplates({scope,templateType}={}){const query=new URLSearchParams();if(scope)query.set('scope',scope);if(templateType)query.set('template_type',templateType);return request(`/templates?${query}`);}
export function getTemplate(templateId){return request(`/templates/${encodeURIComponent(templateId)}`);}
export function createTemplate(payload){return request('/templates',{method:'POST',body:JSON.stringify(payload)});}
export function updateTemplate(templateId,payload){return request(`/templates/${encodeURIComponent(templateId)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function duplicateTemplate(templateId){return request(`/templates/${encodeURIComponent(templateId)}/duplicate`,{method:'POST'});}
export function archiveTemplate(templateId){return request(`/templates/${encodeURIComponent(templateId)}/archive`,{method:'POST'});}
export function getSessionBriefing(clientId){return request(`/clients/${encodeURIComponent(clientId)}/session-briefing`);}
export function listSessionSuggestions(clientId){return request(`/clients/${encodeURIComponent(clientId)}/session-assistant/suggestions`);}
export function generateSessionSuggestions(sessionNoteId){return request('/session-assistant/suggestions',{method:'POST',body:JSON.stringify({session_note_id:sessionNoteId})});}
export function decideSessionSuggestion(suggestionId,payload){return request(`/session-assistant/suggestions/${encodeURIComponent(suggestionId)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function getClientEngagement(clientId){return request(`/clients/${encodeURIComponent(clientId)}/engagement`);}
export function getEngagementProjections(clientIds){return request('/engagement/projections',{method:'POST',body:JSON.stringify({client_ids:clientIds})});}
export function listServicePackages(includeInactive=false){return request(`/packages?include_inactive=${includeInactive?'true':'false'}`);}
export function createServicePackage(payload){return request('/packages',{method:'POST',body:JSON.stringify(payload)});}
export function updateServicePackage(packageId,payload){return request(`/packages/${encodeURIComponent(packageId)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function listClientPackages(clientId){const query=clientId?`?client_id=${encodeURIComponent(clientId)}`:'';return request(`/client-packages${query}`);}
export function assignClientPackage(payload){return request('/client-packages',{method:'POST',body:JSON.stringify(payload)});}
export function updateClientPackage(assignmentId,payload){return request(`/client-packages/${encodeURIComponent(assignmentId)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function recordPackageSession(assignmentId,payload){return request(`/client-packages/${encodeURIComponent(assignmentId)}/sessions`,{method:'POST',body:JSON.stringify(payload)});}
export function listRenewalSignals(){return request('/renewal-signals');}
export function listProfessionIntakeProjections(){return request('/profession-intake/projections');}
export function publishProfessionIntakeTemplate(payload){return request('/profession-intake/templates',{method:'POST',body:JSON.stringify(payload)});}
export function listPracticeCalendar({view='AGENDA',anchor,clientId}={}){const query=new URLSearchParams({view});if(anchor)query.set('anchor',anchor);if(clientId)query.set('client_id',clientId);return request(`/calendar/events?${query}`);}
export function listAppointmentTypes(includeInactive=false){return request(`/scheduling/appointment-types?include_inactive=${includeInactive?'true':'false'}`);}
export function createAppointmentType(payload){return request('/scheduling/appointment-types',{method:'POST',body:JSON.stringify(payload)});}
export function listSchedulingAvailability(){return request('/scheduling/availability');}
export function createSchedulingAvailability(payload){return request('/scheduling/availability',{method:'POST',body:JSON.stringify(payload)});}
export function listScheduledAppointments(clientId){const query=clientId?`?client_id=${encodeURIComponent(clientId)}`:'';return request(`/scheduling/appointments${query}`);}
export function createScheduledAppointment(payload){return request('/scheduling/appointments',{method:'POST',body:JSON.stringify(payload)});}
export function updateScheduledAppointment(id,payload){return request(`/scheduling/appointments/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function createBookingLink(payload){return request('/scheduling/booking-links',{method:'POST',body:JSON.stringify(payload)});}
export function createWaitlistEntry(payload){return request('/scheduling/waitlist',{method:'POST',body:JSON.stringify(payload)});}
export function listWaitlist(){return request('/scheduling/waitlist');}
export async function getPublicBooking(token){const response=await fetch(`${BASE}/public-booking/${encodeURIComponent(token)}`);const body=await response.json().catch(()=>null);if(!response.ok)throw new Error(body?.error?.safe_message||'Booking link is unavailable.');return body?.data;}
export async function submitPublicBooking(token,startsAt){const response=await fetch(`${BASE}/public-booking/${encodeURIComponent(token)}?starts_at=${encodeURIComponent(startsAt)}`,{method:'POST',headers:{'Content-Type':'application/json'}});const body=await response.json().catch(()=>null);if(!response.ok)throw new Error(body?.error?.safe_message||'Appointment could not be booked.');return body?.data;}
export async function openWhatsApp(payload){
  const result=await request('/communication/whatsapp-opened',{method:'POST',body:JSON.stringify(payload)});
  const url=`https://wa.me/${result.phone}?text=${encodeURIComponent(result.message)}`;
  window.open(url,'_blank','noopener,noreferrer');
  return result;
}
