const DEFAULT_UPSTREAM = 'https://api.nuetra.in';
const DEFAULT_AUTH_UPSTREAM = 'https://auth-service-production-ef64.up.railway.app';
const AUTH_SERVICE_PREFIXES = [
  'api/v1/auth',
  'api/v1/owner/people-access',
  'api/v1/corporate-admin',
  'api/v1/team-lead',
  'api/v1/team-member',
  'api/v1/notifications',
];
const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
  'host',
  'content-length',
]);

export const config = {
  api: {
    bodyParser: false,
    responseLimit: false,
  },
};

function getUpstreamBaseUrl() {
  return (process.env.GATEWAY_UPSTREAM_URL || DEFAULT_UPSTREAM).replace(/\/$/, '');
}

function getAuthServiceBaseUrl() {
  return (process.env.AUTH_SERVICE_UPSTREAM_URL || DEFAULT_AUTH_UPSTREAM).replace(/\/$/, '');
}

function getBaseUrlForPath(upstreamPath) {
  if (AUTH_SERVICE_PREFIXES.some((prefix) => upstreamPath === prefix || upstreamPath.startsWith(`${prefix}/`))) {
    return getAuthServiceBaseUrl();
  }
  return getUpstreamBaseUrl();
}

async function readRawBody(req) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  return chunks.length ? Buffer.concat(chunks) : null;
}

function buildForwardHeaders(req, bodyBuffer) {
  const headers = new Headers();

  for (const [key, value] of Object.entries(req.headers)) {
    if (!value) continue;
    const lowerKey = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lowerKey) || lowerKey === 'origin') {
      continue;
    }
    if (Array.isArray(value)) {
      headers.set(key, value.join(', '));
    } else {
      headers.set(key, value);
    }
  }

  const forwardedFor = req.headers['x-forwarded-for'];
  if (typeof forwardedFor === 'string' && forwardedFor.trim()) {
    headers.set('x-forwarded-for', forwardedFor);
  } else if (req.socket?.remoteAddress) {
    headers.set('x-forwarded-for', req.socket.remoteAddress);
  }

  if (bodyBuffer) {
    headers.set('content-length', String(bodyBuffer.length));
  }

  return headers;
}

function copyResponseHeaders(upstreamResponse, res) {
  upstreamResponse.headers.forEach((value, key) => {
    if (HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      return;
    }
    res.setHeader(key, value);
  });
}

export default async function handler(req, res) {
  const pathSegments = Array.isArray(req.query.path) ? req.query.path : [];
  const upstreamPath = pathSegments.join('/');
  const queryIndex = req.url.indexOf('?');
  const rawQuery = queryIndex >= 0 ? req.url.slice(queryIndex) : '';
  const upstreamUrl = `${getBaseUrlForPath(upstreamPath)}/${upstreamPath}${rawQuery}`;

  const bodyBuffer =
    req.method === 'GET' || req.method === 'HEAD' ? null : await readRawBody(req);

  try {
    const upstreamResponse = await fetch(upstreamUrl, {
      method: req.method,
      headers: buildForwardHeaders(req, bodyBuffer),
      body: bodyBuffer,
      redirect: 'manual',
    });

    copyResponseHeaders(upstreamResponse, res);
    res.status(upstreamResponse.status);

    const responseBuffer = Buffer.from(await upstreamResponse.arrayBuffer());
    res.end(responseBuffer);
  } catch (error) {
    console.error('[API GATEWAY PROXY ERROR]', error);
    res.status(502).json({
      success: false,
      message: 'Gateway proxy error',
      data: null,
      error: error instanceof Error ? error.message : 'Unknown proxy error',
    });
  }
}
