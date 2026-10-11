export default function handler(_request, response) {
  response.status(200).json({ service: 'unified-consultant-domain-router', status: 'ok' });
}
