import { getToken } from './api';
import { getFiteatsyApiBaseUrl } from './fiteatsyConsultantsApi';

const readJson=async(response)=>{const text=await response.text();if(!text)return null;try{return JSON.parse(text);}catch{return null;}};
const fail=(response,body,fallback)=>{const error=new Error(body?.safe_message||body?.message||fallback);error.status=response.status;error.data=body;throw error;};
const authenticated=async(path,options={})=>{const response=await fetch(`${getFiteatsyApiBaseUrl()}${path}`,{...options,headers:{Accept:'application/json',Authorization:`Bearer ${getToken()}`,...options.headers}});const body=await readJson(response);if(!response.ok)fail(response,body,'External report operation failed.');return body;};

export const analyzeExternalClientReport=async(clientId,file)=>{const data=new FormData();data.append('report',file);return authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/report-analyses`,{method:'POST',body:data});};
export const saveExternalReportBiomarkers=(clientId,analysisId,reviewToken,items)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/report-analyses/${encodeURIComponent(analysisId)}/save`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reviewToken,items})});
export const getPendingExternalReportAnalyses=(clientId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/report-analyses/pending`);
export const getExternalTransientBiomarkers=(clientId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/transient-biomarkers`);
export const getExternalTransientBiomarkerHistory=(clientId,biomarkerId)=>authenticated(`/v1/external/clients/${encodeURIComponent(clientId)}/transient-biomarkers/${encodeURIComponent(biomarkerId)}/history`);
export const analyzeExternalClientIntakeReport=async(token,file)=>{const data=new FormData();data.append('report',file);const response=await fetch(`${getFiteatsyApiBaseUrl()}/v1/external/intake/${encodeURIComponent(token)}/report-analyses`,{method:'POST',body:data,headers:{Accept:'application/json'}});const body=await readJson(response);if(!response.ok)fail(response,body,'We could not read this report. Try a clearer PDF or image.');return body;};
