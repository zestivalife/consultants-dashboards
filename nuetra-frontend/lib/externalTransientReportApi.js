import { getToken, refreshAccessToken } from './api';
import { getFiteatsyApiBaseUrl } from './fiteatsyConsultantsApi';

const readJson=async(response)=>{const text=await response.text();if(!text)return null;try{return JSON.parse(text);}catch{return null;}};
const fail=(response,body,fallback)=>{const error=new Error(body?.safe_message||body?.message||body?.error||fallback);error.status=response.status;error.data=body;throw error;};
const send=async(path,options,token)=>{const response=await fetch(`${getFiteatsyApiBaseUrl()}${path}`,{...options,headers:{Accept:'application/json',...(token?{Authorization:`Bearer ${token}`} : {}),...options.headers}});return{response,body:await readJson(response)}};
const authenticated=async(path,options={})=>{let{response,body}=await send(path,options,getToken());if(response.status===401){const refreshedToken=await refreshAccessToken().catch(()=>null);if(refreshedToken)({response,body}=await send(path,options,refreshedToken));}if(!response.ok)fail(response,body,'Report data is temporarily unavailable.');return body;};

export const analyzeExternalClientReport=async(clientId,file)=>{const data=new FormData();data.append('report',file);return authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/report-analyses`,{method:'POST',body:data});};
export const saveExternalReportBiomarkers=(clientId,analysisId,reviewToken,items)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/report-analyses/${encodeURIComponent(analysisId)}/save`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reviewToken,items})});
export const getPendingExternalReportAnalyses=(clientId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/report-analyses/pending`);
export const getExternalTransientBiomarkers=(clientId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/transient-biomarkers`);
export const getExternalTransientBiomarkerHistory=(clientId,biomarkerId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/transient-biomarkers/${encodeURIComponent(biomarkerId)}/history`);
export const listExternalHealthRecords=(clientId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/health-records`);
export const compareExternalHealthRecords=(clientId,previousRecordId,latestRecordId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/health-records/compare`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({previousRecordId,latestRecordId})});
export const getExternalHealthTrends=(clientId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/health-records/trends`);
export const removeExternalHealthRecord=(clientId,recordId,reason,detail)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/health-records/${encodeURIComponent(recordId)}/remove`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason,detail})});
export const listExternalProfileEvidenceReviews=(clientId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/profile-evidence-reviews`);
export const reviewExternalProfileEvidence=(clientId,reviewId,action,reason)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/profile-evidence-reviews/${encodeURIComponent(reviewId)}/review`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,reason})});
export const analyzeExternalClientIntakeReport=async(token,file)=>{const data=new FormData();data.append('report',file);const response=await fetch(`${getFiteatsyApiBaseUrl()}/v1/external/intake/${encodeURIComponent(token)}/report-analyses`,{method:'POST',body:data,headers:{Accept:'application/json'}});const body=await readJson(response);if(!response.ok)fail(response,body,'We could not read this report. Try a clearer PDF or image.');return body;};
