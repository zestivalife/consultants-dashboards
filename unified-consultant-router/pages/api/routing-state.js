import { issueRoutingState, resolveProductLine } from '../../lib/routing-state.mjs';

const COOKIE_NAME = '__Host-consultant-product-line';

function appendCookie(response, value) {
  response.setHeader('Set-Cookie', `${COOKIE_NAME}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=900`);
}

export default async function handler(request, response) {
  response.setHeader('Cache-Control', 'no-store');
  if (request.method !== 'POST') return response.status(405).json({ error: 'METHOD_NOT_ALLOWED' });
  const authorization = request.headers.authorization;
  if (!authorization?.startsWith('Bearer ')) return response.status(401).json({ error: 'AUTH_REQUIRED' });
  if (!process.env.CANONICAL_AUTH_ME_URL || !process.env.ROUTING_STATE_SECRET) {
    return response.status(503).json({ error: 'ROUTER_CONFIGURATION_REQUIRED' });
  }

  try {
    const upstream = await fetch(process.env.CANONICAL_AUTH_ME_URL, {
      headers: { Authorization: authorization, Accept: 'application/json' },
      cache: 'no-store',
    });
    const body = await upstream.json().catch(() => null);
    if (!upstream.ok) return response.status(upstream.status === 401 ? 401 : 403).json({ error: 'AUTHORITY_RESOLUTION_DENIED' });
    const productLine = resolveProductLine(body);
    if (!productLine) return response.status(403).json({ error: 'TENANT_CONTEXT_REQUIRED' });
    appendCookie(response, await issueRoutingState(productLine, process.env.ROUTING_STATE_SECRET));
    return response.status(200).json({ routed: true });
  } catch {
    return response.status(503).json({ error: 'AUTHORITY_SERVICE_UNAVAILABLE' });
  }
}
