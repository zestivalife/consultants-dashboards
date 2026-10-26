import crypto from 'node:crypto';

export const QA_SESSION_COOKIE = '__Host-fiteatsy_qa_session';
export const QA_PURPOSE = 'DIET_PARTIAL_PLAN_HYDRATION_E2E';
export const QA_BRANCH = 'codex/diet-builder-food-proposal-ux-v1';
export const qaServerSessionEnabled = (env = process.env) => {
  const backend = String(env.NEXT_PUBLIC_FITEATSY_API_URL || '').replace(/\/$/, '');
  return env.VERCEL_ENV === 'preview'
    && env.VERCEL_GIT_COMMIT_REF === QA_BRANCH
    && Boolean(env.QA_BROWSER_BOOTSTRAP_SHARED_SECRET)
    && /^https:\/\/[^/]*qa-diet-builder-acceptance[^/]*\.up\.railway\.app$/i.test(backend);
};
export const parseCookies = (header = '') => Object.fromEntries(header.split(';').map(x => x.trim()).filter(Boolean).map(x => {
  const at = x.indexOf('='); return [decodeURIComponent(x.slice(0, at)), decodeURIComponent(x.slice(at + 1))];
}));
export const readQaSession = req => parseCookies(req.headers.cookie || '')[QA_SESSION_COOKIE] || null;
export const sessionCookie = (token, maxAge = 1800) => `${QA_SESSION_COOKIE}=${encodeURIComponent(token)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
export const clearSessionCookie = () => `${QA_SESSION_COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;
export const safeEqual = (a, b) => Boolean(a && b && a.length === b.length && crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b)));
