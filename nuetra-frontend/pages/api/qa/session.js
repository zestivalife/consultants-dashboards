import { clearSessionCookie, QA_PURPOSE, readQaSession } from '../../../lib/qaServerSession';
const BACKEND = (process.env.NEXT_PUBLIC_FITEATSY_API_URL || 'https://fiteatsy-mobile-production.up.railway.app').replace(/\/$/, '');
export default async function handler(req,res) {
  res.setHeader('Cache-Control','no-store'); const token=readQaSession(req);
  if (!token) return res.status(401).json({error:'QA_SESSION_REQUIRED'});
  if (req.method === 'DELETE') {
    await fetch(`${BACKEND}/v1/auth/logout`,{method:'POST',headers:{authorization:`Bearer ${token}`}}).catch(()=>null);
    res.setHeader('Set-Cookie',clearSessionCookie()); return res.status(204).end();
  }
  if (req.method !== 'GET') return res.status(405).end();
  const upstream=await fetch(`${BACKEND}/v1/auth/me`,{headers:{authorization:`Bearer ${token}`}}); const body=await upstream.json().catch(()=>null);
  if (!upstream.ok || body?.user?.accountPurpose!=='QA_TEST' || body?.qaSession?.purpose!==QA_PURPOSE) { res.setHeader('Set-Cookie',clearSessionCookie()); return res.status(401).json({error:'INVALID_QA_SESSION'}); }
  return res.status(200).json({user:body.user,qaSession:body.qaSession,expiresAtISO:body.sessionExpiresAtISO});
}
