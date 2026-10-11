const IN_HOUSE_TENANT_TYPES = new Set(['ZESTIVA_INTERNAL']);
const EXTERNAL_TENANT_TYPES = new Set(['INDEPENDENT_CONSULTANT', 'PRACTICE', 'CLINIC']);
const ACTIVE_MEMBERSHIP_STATUSES = new Set(['ACTIVE']);

function base64UrlEncode(input) {
  const bytes = typeof input === 'string' ? new TextEncoder().encode(input) : input;
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/u, '');
}

function base64UrlDecode(input) {
  const normalized = input.replaceAll('-', '+').replaceAll('_', '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  const binary = atob(padded);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function constantTimeEqual(left, right) {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) difference |= left[index] ^ right[index];
  return difference === 0;
}

async function hmac(value, secret) {
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  return new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(value)));
}

export function resolveProductLine(authPayload) {
  const principal = authPayload?.data ?? authPayload;
  const tenant = principal?.currentTenant ?? principal?.current_tenant ?? null;
  const tenantType = String(tenant?.tenantType ?? tenant?.tenant_type ?? '').trim().toUpperCase();
  const membershipStatus = String(
    tenant?.membershipStatus ?? tenant?.membership_status ?? tenant?.currentMembershipStatus ?? '',
  ).trim().toUpperCase();

  if (!tenant || !tenantType || !ACTIVE_MEMBERSHIP_STATUSES.has(membershipStatus)) return null;
  if (IN_HOUSE_TENANT_TYPES.has(tenantType)) return 'IN_HOUSE';
  if (EXTERNAL_TENANT_TYPES.has(tenantType)) return 'EXTERNAL';
  return null;
}

export async function issueRoutingState(productLine, secret, now = Date.now()) {
  if (!['IN_HOUSE', 'EXTERNAL'].includes(productLine)) throw new Error('Unsupported product line.');
  if (!secret || secret.length < 32) throw new Error('Routing secret must contain at least 32 characters.');
  const payload = base64UrlEncode(JSON.stringify({ line: productLine, exp: now + 15 * 60 * 1000 }));
  const signature = base64UrlEncode(await hmac(payload, secret));
  return `${payload}.${signature}`;
}

export async function verifyRoutingState(value, secret, now = Date.now()) {
  if (!value || !secret) return null;
  const [payload, signature, extra] = value.split('.');
  if (!payload || !signature || extra) return null;
  try {
    const actual = base64UrlDecode(signature);
    const expected = await hmac(payload, secret);
    if (!constantTimeEqual(actual, expected)) return null;
    const parsed = JSON.parse(new TextDecoder().decode(base64UrlDecode(payload)));
    if (!['IN_HOUSE', 'EXTERNAL'].includes(parsed?.line)) return null;
    if (!Number.isFinite(parsed?.exp) || parsed.exp <= now) return null;
    return parsed.line;
  } catch {
    return null;
  }
}
