import { getToken, refreshAccessToken } from './api';

const DEFAULT_FITEATSY_API_URL = 'https://fiteatsy-mobile-production.up.railway.app';

export function getFiteatsyApiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_FITEATSY_API_URL || DEFAULT_FITEATSY_API_URL;
  return configured.replace(/\/+$/, '');
}

function mapClient(record) {
  const onboarding = record.onboarding && typeof record.onboarding === 'object' ? record.onboarding : {};
  const healthProfile = record.healthProfile && typeof record.healthProfile === 'object' ? record.healthProfile : {};
  return {
    id: record.clientId,
    clientId: record.clientId,
    name: record.name || 'Unnamed client',
    email: record.email ?? null,
    mobile: record.mobile ?? null,
    mobileNumberMasked: record.mobileNumberMasked ?? null,
    status: record.status ?? null,
    accountStatus: record.accountStatus ?? null,
    age: record.age ?? null,
    gender: record.gender ?? null,
    height: record.height ?? onboarding.height ?? null,
    weight: record.weight ?? onboarding.weight ?? null,
    goal: record.goal ?? onboarding.goal ?? null,
    activityLevel: record.activityLevel ?? onboarding.activityLevel ?? null,
    dietPreference: record.dietPreference ?? onboarding.dietPreference ?? null,
    medicalConditions: Array.isArray(record.medicalConditions)
      ? record.medicalConditions
      : Array.isArray(onboarding.medicalConditions)
        ? onboarding.medicalConditions
        : null,
    biomarkerStatus: record.biomarkerStatus ?? healthProfile.biomarkerStatus ?? null,
    reportsCount: typeof record.reportsCount === 'number' ? record.reportsCount : Number(healthProfile.reportsCount ?? 0),
    lastHealthUpdate: record.lastHealthUpdate ?? healthProfile.lastHealthUpdate ?? null,
    profileCompleted: Boolean(record.profileCompleted ?? healthProfile.profileCompleted),
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

export async function getFiteatsyConsultantClientProfile(clientId) {
  if (!clientId) {
    const error = new Error('Client ID is required');
    error.status = 400;
    throw error;
  }

  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/workspace`);
}
