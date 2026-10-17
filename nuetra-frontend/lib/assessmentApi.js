import {getToken,refreshAccessToken} from './api';
const BASE='/api/gateway/api/v1/practice-operations';
async function request(path,options={}){const send=token=>fetch(`${BASE}${path}`,{credentials:'include',...options,headers:{'Content-Type':'application/json',...(token?{'X-Nuetra-Authorization':`Bearer ${token}`}:{}),...(options.headers||{})}});let response=await send(getToken());if(response.status===401){const token=await refreshAccessToken().catch(()=>null);if(token)response=await send(token)}const body=await response.json().catch(()=>null);if(!response.ok)throw new Error(body?.error?.safe_message||'Assessment request failed.');return body?.data;}
export const listAssessmentDefinitions=()=>request('/assessments/definitions');
export const assignAssessment=(clientId,payload)=>request(`/clients/${encodeURIComponent(clientId)}/assessments`,{method:'POST',body:JSON.stringify(payload)});
export const listClientAssessments=clientId=>request(`/clients/${encodeURIComponent(clientId)}/assessments`);
export const getAssessment=id=>request(`/assessments/${encodeURIComponent(id)}`);
export const saveAssessment=(id,answers)=>request(`/assessments/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify({answers})});
export const completeAssessment=(id,answers,reviewNotes='')=>request(`/assessments/${encodeURIComponent(id)}/complete`,{method:'POST',body:JSON.stringify({answers,review_notes:reviewNotes||null})});
