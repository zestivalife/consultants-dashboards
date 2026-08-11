import { getToken, refreshAccessToken } from './api';

const DEFAULT_FITEATSY_API_URL = 'https://fiteatsy-mobile-production.up.railway.app';

export function getFiteatsyApiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_FITEATSY_API_URL || DEFAULT_FITEATSY_API_URL;
  return configured.replace(/\/+$/, '');
}

function mapClient(record) {
  return {
    id: record.clientId,
    clientId: record.clientId,
    name: record.name || 'Unnamed client',
    age: record.age ?? null,
    gender: record.gender ?? null,
    profileCompleted: Boolean(record.profileCompleted),
    registeredAt: record.registeredAt || null,
    lastActiveAt: record.lastActiveAt || null,
  };
}

async function readJsonResponse(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

function buildAuthHeaders(token) {
  return {
    Accept: 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function requestFiteatsy(path) {
  const token = getToken();
  const url = `${getFiteatsyApiBaseUrl()}${path}`;
  let response = await fetch(url, {
    method: 'GET',
    headers: buildAuthHeaders(token),
  });
  let body = await readJsonResponse(response);

  if (response.status === 401) {
    const refreshedToken = await refreshAccessToken().catch(() => null);
    if (refreshedToken) {
      response = await fetch(url, {
        method: 'GET',
        headers: buildAuthHeaders(refreshedToken),
      });
      body = await readJsonResponse(response);
    }
  }

  if (!response.ok) {
    const error = new Error(body?.message || body?.error || `Fiteatsy request failed (${response.status})`);
    error.status = response.status;
    error.data = body;
    throw error;
  }

  return body;
}

export async function listFiteatsyConsultantClients() {
  const body = await requestFiteatsy('/v1/consultants/clients');

  return {
    clients: Array.isArray(body?.clients) ? body.clients.map(mapClient) : [],
  };
}
