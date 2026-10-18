const BASE='/api/gateway/api/v1/public/consultants';
async function publicRequest(path='',options={}){const response=await fetch(`${BASE}${path}`,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});const body=await response.json().catch(()=>null);if(!response.ok){const problem=new Error(body?.error?.safe_message||'Marketplace request failed');problem.code=body?.error?.code;throw problem}return body?.data}
export function listPublicConsultants(filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==''&&value!=null)query.set(key,String(value))});return publicRequest(`?${query}`)}
export function getPublicConsultant(slug){return publicRequest(`/${encodeURIComponent(slug)}`)}
export function getPublicAvailability(slug){return publicRequest(`/${encodeURIComponent(slug)}/availability`)}
export function createPublicEnrolment(slug,payload){return publicRequest(`/${encodeURIComponent(slug)}/enrolments`,{method:'POST',body:JSON.stringify(payload)})}
