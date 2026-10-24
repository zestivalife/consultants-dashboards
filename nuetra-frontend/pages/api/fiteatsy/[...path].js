import { readQaSession } from '../../../lib/qaServerSession';
const DEFAULT_UPSTREAM = 'https://fiteatsy-mobile-production.up.railway.app';
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
  'content-encoding',
]);

export const config = {
  api: {
    bodyParser: false,
    responseLimit: false,
  },
};

function getUpstreamBaseUrl() {
  return (process.env.NEXT_PUBLIC_FITEATSY_API_URL || DEFAULT_UPSTREAM).replace(/\/$/, '');
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
    if (HOP_BY_HOP_HEADERS.has(lowerKey) || lowerKey === 'origin' || lowerKey === 'cookie') {
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
  const qaToken = readQaSession(req);
  // The cookie is a fallback for cookie-only QA sessions. It must never
  // replace the bearer supplied by a legitimately signed-in user.
  if (qaToken && !headers.has('authorization')) headers.set('authorization', `Bearer ${qaToken}`);

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

export function validateExternalIntakePdfUpload(req, upstreamPath, bodyBuffer) {
  if (req.method !== 'POST' || !/^v1\/external\/intake\/[^/]+\/documents$/.test(upstreamPath)) return null;
  const contentType = String(req.headers['content-type'] || '').toLowerCase();
  if (!contentType.startsWith('multipart/form-data;') || !bodyBuffer?.length || bodyBuffer.length > 12 * 1024 * 1024 + 64 * 1024) return 'Choose a PDF no larger than 12 MB.';
  const body = bodyBuffer.toString('latin1');
  if (!/filename="[^"]+\.pdf"/i.test(body) || !/content-type:\s*application\/pdf/i.test(body) || !body.includes('%PDF-')) return 'Only valid PDF blood reports are supported.';
  return null;
}

export default async function handler(req, res) {
  const pathSegments = Array.isArray(req.query.path) ? req.query.path : [];
  const upstreamPath = pathSegments.join('/');
  const queryIndex = req.url.indexOf('?');
  const rawQuery = queryIndex >= 0 ? req.url.slice(queryIndex) : '';
  const upstreamUrl = `${getUpstreamBaseUrl()}/${upstreamPath}${rawQuery}`;

  const bodyBuffer =
    req.method === 'GET' || req.method === 'HEAD' ? null : await readRawBody(req);

  const uploadError = validateExternalIntakePdfUpload(req, upstreamPath, bodyBuffer);
  if (uploadError) return res.status(415).json({ success: false, safe_message: uploadError });

  try {
    const upstreamResponse = await fetch(upstreamUrl, {
      method: req.method,
      headers: buildForwardHeaders(req, bodyBuffer),
      body: bodyBuffer,
      redirect: 'manual',
    });

    copyResponseHeaders(upstreamResponse, res);
    res.status(upstreamResponse.status);

    const responseBody = Buffer.from(await upstreamResponse.arrayBuffer());
    res.send(responseBody);
  } catch (error) {
    console.error('[FITEATSY PROXY ERROR]', error);
    res.status(502).json({
      success: false,
      message: 'Fiteatsy proxy error',
      data: null,
      error: error instanceof Error ? error.message : 'Unknown proxy error',
    });
  }
}
