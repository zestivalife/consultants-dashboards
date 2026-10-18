const BASE='/api/gateway/api/v1/client-portal';

async function request(token,path='',options={}){
  const response=await fetch(`${BASE}/${encodeURIComponent(token)}${path}`,{
    ...options,
    headers:{'Content-Type':'application/json',...(options.headers||{})},
  });
  const body=await response.json().catch(()=>null);
  if(!response.ok){
    const failure=new Error(body?.error?.safe_message||'Your client portal could not be loaded.');
    failure.code=body?.error?.code;
    throw failure;
  }
  return body?.data;
}

export function getClientPortal(token){return request(token);}
export function completePortalTask(token,taskId){return request(token,`/tasks/${taskId}/complete`,{method:'POST'});}
export function submitPortalDocument(token,payload){return request(token,'/documents',{method:'POST',body:JSON.stringify(payload)});}
