const COOKIES = ['__Host-consultant-product-line', '__Host-consultant-public-origin'];

export default function handler(request, response) {
  response.setHeader('Cache-Control', 'no-store');
  if (request.method !== 'POST' && request.method !== 'DELETE') {
    return response.status(405).json({ error: 'METHOD_NOT_ALLOWED' });
  }
  response.setHeader('Set-Cookie', COOKIES.map((name) => `${name}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`));
  return response.status(204).end();
}
