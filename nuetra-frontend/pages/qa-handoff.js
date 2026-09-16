import { QA_PURPOSE, sessionCookie } from '../lib/qaServerSession';

const QA_BRANCH = 'codex/diet-builder-food-proposal-ux-v1';
const ALLOWED_ROLES = new Set(['consultant', 'senior_consultant']);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const qaBackend = () => (process.env.NEXT_PUBLIC_FITEATSY_API_URL || '').replace(/\/$/, '');

const qaServerBootstrapEnabled = () => {
  const backend = qaBackend();
  return process.env.VERCEL_ENV === 'preview'
    && process.env.VERCEL_GIT_COMMIT_REF === QA_BRANCH
    && Boolean(process.env.QA_BROWSER_BOOTSTRAP_SHARED_SECRET)
    && /^https:\/\/[^/]*qa-diet-builder-acceptance[^/]*\.up\.railway\.app$/i.test(backend);
};

export async function getServerSideProps({ query, req, res }) {
  res.setHeader('Cache-Control', 'no-store, max-age=0');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('X-Robots-Tag', 'noindex, nofollow, noarchive');
  if (!qaServerBootstrapEnabled()) return { notFound: true };

  const code = typeof query.code === 'string' ? query.code : '';
  const fixtureSetId = typeof query.fixtureSetId === 'string' ? query.fixtureSetId : '';
  const role = typeof query.role === 'string' ? query.role : '';
  const purpose = typeof query.purpose === 'string' ? query.purpose : '';
  if (code.length < 32 || !UUID.test(fixtureSetId) || !ALLOWED_ROLES.has(role) || purpose !== QA_PURPOSE) {
    return { props: { failed: true } };
  }

  try {
    const response = await fetch(`${qaBackend()}/v1/auth/qa-browser-handoff/exchange`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-qa-bootstrap-secret': process.env.QA_BROWSER_BOOTSTRAP_SHARED_SECRET,
        'user-agent': req.headers['user-agent'] || 'qa-server-bootstrap',
      },
      body: JSON.stringify({ code, fixtureSetId, role, purpose }),
    });
    const body = await response.json().catch(() => null);
    const authenticatedRole = body?.qaSession?.role;
    const validSession = response.ok
      && typeof body?.token === 'string'
      && body.token.length > 0
      && body?.user?.accountPurpose === 'QA_TEST'
      && body?.qaSession?.fixtureSetId === fixtureSetId
      && body?.qaSession?.purpose === QA_PURPOSE
      && ALLOWED_ROLES.has(authenticatedRole);
    if (!validSession) return { props: { failed: true } };

    res.setHeader('Set-Cookie', sessionCookie(body.token));
    return {
      redirect: {
        destination: authenticatedRole === 'senior_consultant'
          ? '/dashboard/senior-consultant?view=command-center'
          : '/dashboard/consultant?view=clients',
        permanent: false,
      },
    };
  } catch {
    return { props: { failed: true } };
  }
}

export default function QaHandoff({ failed }) {
  return <main className="flex min-h-screen items-center justify-center bg-[#0d0f12] px-6 text-center text-white"><p>{failed ? 'The QA handoff is invalid or expired.' : 'The QA session could not be established.'}</p></main>;
}
