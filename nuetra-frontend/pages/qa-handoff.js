import { useEffect, useState } from 'react';

export default function QaHandoff() {
  const [failed,setFailed]=useState(false);
  useEffect(()=>{
    const params=new URLSearchParams(window.location.hash.slice(1));
    window.history.replaceState(null,'','/qa-handoff');
    const payload={code:params.get('code'),fixtureSetId:params.get('fixtureSetId'),role:params.get('role'),purpose:params.get('purpose')};
    params.delete('code');
    fetch('/api/qa/bootstrap',{method:'POST',credentials:'same-origin',headers:{'content-type':'application/json'},body:JSON.stringify(payload)})
      .then(async response=>response.ok?response.json():Promise.reject())
      .then(result=>window.location.replace(result.redirectTo))
      .catch(()=>setFailed(true));
  },[]);
  return <main className="flex min-h-screen items-center justify-center bg-[#0d0f12] text-white"><p>{failed?'The QA handoff is invalid or expired.':'Establishing governed QA session…'}</p></main>;
}
