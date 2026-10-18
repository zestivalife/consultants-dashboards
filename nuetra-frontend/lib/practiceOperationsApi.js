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
export function getBillingOverview(){return request('/billing/overview');}
export function listBillableServices(includeInactive=false){return request(`/billing/services?include_inactive=${includeInactive?'true':'false'}`);}
export function createBillableService(payload){return request('/billing/services',{method:'POST',body:JSON.stringify(payload)});}
export function updateBillableService(id,payload){return request(`/billing/services/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function listInvoices({status,clientId,search}={}){const query=new URLSearchParams();if(status)query.set('status',status);if(clientId)query.set('client_id',clientId);if(search)query.set('search',search);return request(`/billing/invoices?${query}`);}
export function createInvoice(payload){return request('/billing/invoices',{method:'POST',body:JSON.stringify(payload)});}
export function updateInvoice(id,payload){return request(`/billing/invoices/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function getInvoice(id){return request(`/billing/invoices/${encodeURIComponent(id)}`);}
export function issueInvoice(id){return request(`/billing/invoices/${encodeURIComponent(id)}/issue`,{method:'POST'});}
export function cancelInvoice(id){return request(`/billing/invoices/${encodeURIComponent(id)}/cancel`,{method:'POST'});}
export function recordInvoicePayment(id,payload){return request(`/billing/invoices/${encodeURIComponent(id)}/payments`,{method:'POST',body:JSON.stringify(payload)});}
export function listPayments(clientId){const query=clientId?`?client_id=${encodeURIComponent(clientId)}`:'';return request(`/billing/payments${query}`);}
export function getClientBilling(clientId){return request(`/billing/clients/${encodeURIComponent(clientId)}`);}
export function getReceipt(id){return request(`/billing/receipts/${encodeURIComponent(id)}`);}
export function listProfessionalResources(filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!=='')query.set(key,value)});return request(`/resources?${query}`);}
export function createProfessionalResource(payload){return request('/resources',{method:'POST',body:JSON.stringify(payload)});}
export function updateProfessionalResource(id,payload){return request(`/resources/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function archiveProfessionalResource(id){return request(`/resources/${encodeURIComponent(id)}/archive`,{method:'POST'});}
export function assignProfessionalResource(clientId,payload){return request(`/clients/${encodeURIComponent(clientId)}/resources`,{method:'POST',body:JSON.stringify(payload)});}
export function listClientHomework(clientId){return request(`/clients/${encodeURIComponent(clientId)}/homework`);}
export function createClientHomework(clientId,payload){return request(`/clients/${encodeURIComponent(clientId)}/homework`,{method:'POST',body:JSON.stringify(payload)});}
export function updateClientHomework(clientId,id,status){return request(`/clients/${encodeURIComponent(clientId)}/homework/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify({status})});}
export function getClientAdherence(clientId){return request(`/clients/${encodeURIComponent(clientId)}/adherence`);}
export function listAutomations(state){return request(`/automations${state?`?state=${encodeURIComponent(state)}`:''}`);}
export function listAutomationTemplates(){return request('/automations/templates');}
export function createAutomation(payload){return request('/automations',{method:'POST',body:JSON.stringify(payload)});}
export function updateAutomation(id,payload){return request(`/automations/${encodeURIComponent(id)}`,{method:'PUT',body:JSON.stringify(payload)});}
export function setAutomationEnabled(id,enabled){return request(`/automations/${encodeURIComponent(id)}/state`,{method:'PATCH',body:JSON.stringify({enabled})});}
export function dryRunAutomation(id,payload){return request(`/automations/${encodeURIComponent(id)}/dry-run`,{method:'POST',body:JSON.stringify(payload)});}
export function listAutomationHistory(){return request('/automations/executions/history');}
export function listPendingAutomationActions(){return request('/automations/actions/pending');}
export function decideAutomationAction(id,decision,configuration){return request(`/automations/actions/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify({decision,configuration})});}
export function getTeamAccess(){return request('/team/access');}
export function listTeamMembers(){return request('/team');}
export function listTeamRoles(){return request('/team/roles');}
export function listTeamInvitations(){return request('/team/invitations');}
export function inviteTeamMember(payload){return request('/team/invitations',{method:'POST',body:JSON.stringify(payload)});}
export function resendTeamInvitation(id){return request(`/team/invitations/${encodeURIComponent(id)}/resend`,{method:'POST'});}
export function updateTeamMember(id,payload){return request(`/team/members/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function suspendTeamMember(id){return request(`/team/members/${encodeURIComponent(id)}/suspend`,{method:'POST'});}
export function deactivateTeamMember(id){return request(`/team/members/${encodeURIComponent(id)}/deactivate`,{method:'POST'});}
export function listClientTeam(clientId){return request(`/clients/${encodeURIComponent(clientId)}/team`);}
export function listMyClientAssignments(){return request('/team/client-assignments');}
export function assignClientTeam(clientId,payload){return request(`/clients/${encodeURIComponent(clientId)}/team`,{method:'POST',body:JSON.stringify(payload)});}
export function updateClientTeamAssignment(clientId,id,payload){return request(`/clients/${encodeURIComponent(clientId)}/team/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function removeClientTeamAssignment(clientId,id){return request(`/clients/${encodeURIComponent(clientId)}/team/${encodeURIComponent(id)}`,{method:'DELETE'});}
export function getPracticeAnalytics(preset='30d'){return request(`/analytics/practice?preset=${encodeURIComponent(preset)}`);}
export function listReferrals(direction='outgoing',clientId=''){return request(`/referrals?direction=${encodeURIComponent(direction)}${clientId?`&client_id=${encodeURIComponent(clientId)}`:''}`);}
export function createReferral(payload){return request('/referrals',{method:'POST',body:JSON.stringify(payload)});}
export function actOnReferral(id,action,message){return request(`/referrals/${encodeURIComponent(id)}/actions`,{method:'POST',body:JSON.stringify({action,message})});}
export function getReferralSharedData(id){return request(`/referrals/${encodeURIComponent(id)}/shared-data`);}
export function listProgressReports(clientId=''){return request(`/progress-reports${clientId?`?client_id=${encodeURIComponent(clientId)}`:''}`);}
export function createProgressReport(payload){return request('/progress-reports',{method:'POST',body:JSON.stringify(payload)});}
export function previewProgressReport(id){return request(`/progress-reports/${encodeURIComponent(id)}/preview`);}
export function updateProgressReport(id,payload){return request(`/progress-reports/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(payload)});}
export function generateProgressReport(id){return request(`/progress-reports/${encodeURIComponent(id)}/generate`,{method:'POST'});}
export function shareProgressReport(id){return request(`/progress-reports/${encodeURIComponent(id)}/share`,{method:'POST'});}
export function revokeProgressReport(id){return request(`/progress-reports/${encodeURIComponent(id)}/revoke`,{method:'POST'});}
export function listForms(status=''){return request(`/forms${status?`?status=${encodeURIComponent(status)}`:''}`);}
export function getForm(id){return request(`/forms/${encodeURIComponent(id)}`);}
export function createForm(payload){return request('/forms',{method:'POST',body:JSON.stringify(payload)});}
export function updateForm(id,payload){return request(`/forms/${encodeURIComponent(id)}`,{method:'PUT',body:JSON.stringify(payload)});}
export function publishForm(id){return request(`/forms/${encodeURIComponent(id)}/publish`,{method:'POST'});}
export function assignForm(id,payload){return request(`/forms/${encodeURIComponent(id)}/assign`,{method:'POST',body:JSON.stringify(payload)});}
export function listFormAssignments(clientId=''){return request(`/form-assignments${clientId?`?client_id=${encodeURIComponent(clientId)}`:''}`);}
export function saveFormResponse(id,answers,submit=false){return request(`/form-assignments/${encodeURIComponent(id)}/response`,{method:'PUT',body:JSON.stringify({answers,submit})});}
export function listConsentTemplates(){return request('/consents/templates');}
export function createConsentTemplate(payload){return request('/consents/templates',{method:'POST',body:JSON.stringify(payload)});}
export function publishConsentTemplate(id){return request(`/consents/templates/${encodeURIComponent(id)}/publish`,{method:'POST'});}
export function assignConsent(id,client_id){return request(`/consents/templates/${encodeURIComponent(id)}/assign`,{method:'POST',body:JSON.stringify({client_id})});}
export function listConsents(clientId=''){return request(`/consents${clientId?`?client_id=${encodeURIComponent(clientId)}`:''}`);}
export function decideConsent(id,payload){return request(`/consents/${encodeURIComponent(id)}/decision`,{method:'POST',body:JSON.stringify(payload)});}
export function revokeConsent(id){return request(`/consents/${encodeURIComponent(id)}/revoke`,{method:'POST'});}
export function listVaultDocuments(filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!=='')query.set(key==='clientId'?'client_id':key,value)});return request(`/documents?${query}`);}
export async function uploadVaultDocument(payload,file){
  const pending=await request('/documents',{method:'POST',body:JSON.stringify({...payload,filename:file.name,content_type:file.type,size_bytes:file.size})});
  const response=await fetch(pending.upload.url,{method:'PUT',headers:{'Content-Type':file.type},body:file});
  if(!response.ok)throw new Error('Private storage upload failed. The pending record was not made available.');
  return request(`/documents/${encodeURIComponent(pending.id)}/finalise`,{method:'POST',body:JSON.stringify({version_id:pending.version_id})});
}
export async function uploadVaultDocumentVersion(documentId,file){
  const pending=await request(`/documents/${encodeURIComponent(documentId)}/versions`,{method:'POST',body:JSON.stringify({filename:file.name,content_type:file.type,size_bytes:file.size})});
  const response=await fetch(pending.upload.url,{method:'PUT',headers:{'Content-Type':file.type},body:file});
  if(!response.ok)throw new Error('Private storage upload failed. The existing document remains unchanged.');
  return request(`/documents/${encodeURIComponent(documentId)}/finalise`,{method:'POST',body:JSON.stringify({version_id:pending.version_id})});
}
export function changeVaultDocumentState(id,action){return request(`/documents/${encodeURIComponent(id)}/${encodeURIComponent(action)}`,{method:'POST'});}
export function listLeads({stage,search}={}){const query=new URLSearchParams();if(stage)query.set('stage',stage);if(search)query.set('search',search);return request(`/leads?${query}`);}
export function createLead(payload){return request('/leads',{method:'POST',body:JSON.stringify(payload)});}
export function updateLeadStage(id,stage,reason){return request(`/leads/${encodeURIComponent(id)}/stage`,{method:'POST',body:JSON.stringify({stage,reason})});}
export function createLeadFollowUp(id,payload){return request(`/leads/${encodeURIComponent(id)}/follow-ups`,{method:'POST',body:JSON.stringify(payload)});}
export function convertLead(id,clientId){return request(`/leads/${encodeURIComponent(id)}/convert`,{method:'POST',body:JSON.stringify({client_id:clientId})});}
export function getCommunicationCentre(clientId=''){return request(`/communication/centre${clientId?`?client_id=${encodeURIComponent(clientId)}`:''}`);}
export function prepareCommunication(payload){return request('/communication/centre',{method:'POST',body:JSON.stringify(payload)});}
export function createCommunicationReminder(payload){return request('/communication/reminders',{method:'POST',body:JSON.stringify(payload)});}
export function listPracticeLocations(includeInactive=false){return request(`/locations?include_inactive=${includeInactive?'true':'false'}`);}
export function createPracticeLocation(payload){return request('/locations',{method:'POST',body:JSON.stringify(payload)});}
export function assignLocationResource(id,payload){return request(`/locations/${encodeURIComponent(id)}/resources`,{method:'POST',body:JSON.stringify(payload)});}
export function getPaymentProviderStatus(){return request('/payments/provider');}
export function createPaymentOrder(payload){return request('/payments/orders',{method:'POST',body:JSON.stringify(payload)});}
export function verifyPaymentOrder(id,payload){return request(`/payments/orders/${encodeURIComponent(id)}/verify`,{method:'POST',body:JSON.stringify(payload)});}
export function lookupPaymentOrder(id){return request(`/payments/orders/${encodeURIComponent(id)}`);}
export function getAiCopilotStatus(){return request('/ai-copilot/status');}
export function createAiDraft(payload){return request('/ai-copilot/drafts',{method:'POST',body:JSON.stringify(payload)});}
export function listComplianceAudit(clientId=''){return request(`/compliance/audit${clientId?`?client_id=${encodeURIComponent(clientId)}`:''}`);}
export function exportClientData(clientId,sections){return request(`/compliance/exports/clients/${encodeURIComponent(clientId)}`,{method:'POST',body:JSON.stringify({sections})});}
export async function downloadVaultDocument(id){const result=await request(`/documents/${encodeURIComponent(id)}/download`,{method:'POST'});window.open(result.download_url,'_blank','noopener,noreferrer');return result;}
export async function downloadProgressReport(id,format){
  const send=token=>fetch(`${BASE}/progress-reports/${encodeURIComponent(id)}/artifacts/${encodeURIComponent(format)}`,{credentials:'include',headers:token?{'X-Nuetra-Authorization':`Bearer ${token}`}:{}});
  let response=await send(getToken());if(response.status===401){const refreshed=await refreshAccessToken().catch(()=>null);if(refreshed)response=await send(refreshed)}
  if(!response.ok)throw new Error('Report artifact could not be downloaded.');const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`progress-report.${format.toLowerCase()}`;link.click();URL.revokeObjectURL(url);
}
export async function getPublicBooking(token){const response=await fetch(`${BASE}/public-booking/${encodeURIComponent(token)}`);const body=await response.json().catch(()=>null);if(!response.ok)throw new Error(body?.error?.safe_message||'Booking link is unavailable.');return body?.data;}
export async function submitPublicBooking(token,startsAt){const response=await fetch(`${BASE}/public-booking/${encodeURIComponent(token)}?starts_at=${encodeURIComponent(startsAt)}`,{method:'POST',headers:{'Content-Type':'application/json'}});const body=await response.json().catch(()=>null);if(!response.ok)throw new Error(body?.error?.safe_message||'Appointment could not be booked.');return body?.data;}
export async function openWhatsApp(payload){
  const result=await request('/communication/whatsapp-opened',{method:'POST',body:JSON.stringify(payload)});
  const url=`https://wa.me/${result.phone}?text=${encodeURIComponent(result.message)}`;
  window.open(url,'_blank','noopener,noreferrer');
  return result;
}
