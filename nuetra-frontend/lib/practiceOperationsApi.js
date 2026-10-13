const BASE='/api/gateway/api/v1/practice-operations';

async function request(path,options={}){
  const response=await fetch(`${BASE}${path}`,{credentials:'include',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});
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
