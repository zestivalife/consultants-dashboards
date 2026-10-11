import { NextResponse } from 'next/server';
import { verifyRoutingState } from './lib/routing-state.mjs';

const ROUTING_COOKIE = '__Host-consultant-product-line';
const PUBLIC_ORIGIN_COOKIE = '__Host-consultant-public-origin';

function requiredOrigin(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required.`);
  return value.replace(/\/$/u, '');
}

function rewrite(request, origin) {
  const target = new URL(`${request.nextUrl.pathname}${request.nextUrl.search}`, origin);
  return NextResponse.rewrite(target);
}

function clearRoutingCookies(response) {
  response.cookies.delete(ROUTING_COOKIE);
  response.cookies.delete(PUBLIC_ORIGIN_COOKIE);
  return response;
}

export async function middleware(request) {
  const { pathname } = request.nextUrl;
  const inHouseOrigin = requiredOrigin('IN_HOUSE_ORIGIN');
  const externalOrigin = requiredOrigin('EXTERNAL_ORIGIN');

  if (
    pathname.startsWith('/__router') ||
    pathname === '/api/routing-state' ||
    pathname === '/api/logout-routing-state' ||
    pathname === '/api/health'
  ) return NextResponse.next();

  if (pathname === '/login' || pathname === '/') {
    return clearRoutingCookies(rewrite(request, inHouseOrigin));
  }

  if (pathname === '/signup') {
    const response = rewrite(request, externalOrigin);
    response.cookies.set(PUBLIC_ORIGIN_COOKIE, 'EXTERNAL', {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/',
      maxAge: 10 * 60,
    });
    response.cookies.delete(ROUTING_COOKIE);
    return response;
  }

  if (pathname.startsWith('/api/')) return rewrite(request, inHouseOrigin);

  const productLine = await verifyRoutingState(
    request.cookies.get(ROUTING_COOKIE)?.value,
    process.env.ROUTING_STATE_SECRET,
  );

  if (pathname.startsWith('/_next/') || pathname.includes('.')) {
    if (productLine === 'IN_HOUSE') return rewrite(request, inHouseOrigin);
    if (productLine === 'EXTERNAL') return rewrite(request, externalOrigin);
    if (request.cookies.get(PUBLIC_ORIGIN_COOKIE)?.value === 'EXTERNAL') return rewrite(request, externalOrigin);
    return rewrite(request, inHouseOrigin);
  }

  if (!productLine) {
    const resolver = request.nextUrl.clone();
    resolver.pathname = '/__router/resolve';
    resolver.searchParams.set('returnTo', `${pathname}${request.nextUrl.search}`);
    return NextResponse.rewrite(resolver);
  }

  return rewrite(request, productLine === 'IN_HOUSE' ? inHouseOrigin : externalOrigin);
}

export const config = {
  matcher: ['/((?!favicon.ico|robots.txt).*)'],
};
