const BASE='/api/gateway/api/v1/profession-intake';

async function request(token,path='',options={}){
  const response=await fetch(`${BASE}/${encodeURIComponent(token)}${path}`,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});
  const body=await response.json().catch(()=>null);
  if(!response.ok){const failure=new Error(body?.error?.safe_message||'This intake could not be loaded.');failure.code=body?.error?.code;throw failure;}
  return body?.data;
}

export function getProfessionIntake(token){return request(token);}
export function saveProfessionIntakeAnswers(token,answers){return request(token,'/answers',{method:'PATCH',body:JSON.stringify({answers})});}
export function submitProfessionIntake(token,consentVersion='profession-intake-v1'){return request(token,'/submit',{method:'POST',body:JSON.stringify({consent_accepted:true,consent_version:consentVersion})});}
