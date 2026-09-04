import { QA_PURPOSE, sessionCookie } from '../../../lib/qaServerSession';

const BACKEND = (process.env.NEXT_PUBLIC_FITEATSY_API_URL || 'https://fiteatsy-mobile-production.up.railway.app').replace(/\/$/, '');
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store'); res.setHeader('Referrer-Policy', 'no-referrer');
  if (req.method !== 'POST') return res.status(405).end();
  const { code, fixtureSetId, role, purpose } = req.body || {};
  if (purpose !== QA_PURPOSE || !['consultant','senior_consultant'].includes(role) || typeof code !== 'string' || typeof fixtureSetId !== 'string') return res.status(400).end('Invalid handoff.');
  const response = await fetch(`${BACKEND}/v1/auth/qa-browser-handoff/exchange`, { method:'POST', headers:{'content-type':'application/json','x-qa-bootstrap-secret':process.env.QA_BROWSER_BOOTSTRAP_SHARED_SECRET || '','user-agent':req.headers['user-agent'] || 'qa-browser-bootstrap'}, body:JSON.stringify({code,fixtureSetId,role,purpose}) });
  const body = await response.json().catch(() => null);
  if (!response.ok || !body?.token || body?.qaSession === null) return res.status(response.status || 401).end('The QA handoff is invalid.');
  res.setHeader('Set-Cookie', sessionCookie(body.token));
  return res.status(200).json({ redirectTo: role === 'senior_consultant' ? '/dashboard/senior-consultant?view=command-center' : '/dashboard/consultant?view=clients' });
}
