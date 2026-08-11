import { getToken } from './api';

const DEFAULT_FITEATSY_API_URL = 'https://fiteatsy-mobile-production.up.railway.app';

export function getFiteatsyApiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_FITEATSY_API_URL || DEFAULT_FITEATSY_API_URL;
  return configured.replace(/\/+$/, '');
}

function mapHealthMetric(metric) {
  if (!metric || typeof metric !== 'object') return null;
  return {
    status: metric.status || 'NOT_AVAILABLE',
    value: metric.value ?? null,
    unit: metric.unit ?? null,
    category: metric.category ?? null,
    reason: metric.reason ?? null,
    formulaVersion: metric.formulaVersion ?? null,
    calculatedAt: metric.calculatedAt ?? null,
    values: metric.values && typeof metric.values === 'object' ? metric.values : {},
  };
}

function mapBiomarker(record) {
  return {
    biomarkerId: record.biomarkerId,
    name: record.name || 'Biomarker',
    value: typeof record.value === 'number' ? record.value : Number(record.value),
    unit: record.unit || '',
    status: record.status || 'VALIDATED',
    referenceRange: record.referenceRange ?? null,
    confidence: record.confidence ?? null,
    testDate: record.testDate ?? null,
    trend: record.trend ?? null,
    previousValue: record.previousValue ?? null,
    previousTestDate: record.previousTestDate ?? null,
  };
}

function mapClient(record) {
  return {
    id: record.clientId,
    clientId: record.clientId,
    name: record.name || 'Unnamed client',
    email: record.email ?? null,
    mobile: record.mobile ?? null,
    mobileNumberMasked: record.mobileNumberMasked ?? null,
    status: record.status ?? null,
    accountStatus: record.accountStatus ?? null,
    height: record.height ?? null,
    weight: record.weight ?? null,
    goal: record.goal ?? null,
    activityLevel: record.activityLevel ?? null,
    dietPreference: record.dietPreference ?? null,
    medicalConditions: Array.isArray(record.medicalConditions) ? record.medicalConditions : null,
    biomarkerStatus: record.biomarkerStatus ?? null,
    reportsCount: typeof record.reportsCount === 'number' ? record.reportsCount : 0,
    lastHealthUpdate: record.lastHealthUpdate ?? null,
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

export async function listFiteatsyConsultantClients() {
  const token = getToken();
  const response = await fetch(`${getFiteatsyApiBaseUrl()}/v1/consultants/clients`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await readJsonResponse(response);

  if (!response.ok) {
    const error = new Error(body?.message || body?.error || `Fiteatsy clients request failed (${response.status})`);
    error.status = response.status;
    error.data = body;
    throw error;
  }

  return {
    clients: Array.isArray(body?.clients) ? body.clients.map(mapClient) : [],
  };
}

export async function getFiteatsyConsultantClientProfile(clientId) {
  const token = getToken();
  const response = await fetch(`${getFiteatsyApiBaseUrl()}/v1/consultants/clients/${encodeURIComponent(clientId)}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await readJsonResponse(response);

  if (!response.ok) {
    const error = new Error(body?.message || body?.error || `Fiteatsy client profile request failed (${response.status})`);
    error.status = response.status;
    error.data = body;
    throw error;
  }

  return {
    client: body?.client || null,
    onboarding: body?.onboarding || null,
    healthProfile: body?.healthProfile || null,
    healthMetrics: body?.healthMetrics
      ? {
          bmi: mapHealthMetric(body.healthMetrics.bmi),
          bmr: mapHealthMetric(body.healthMetrics.bmr),
          tdee: mapHealthMetric(body.healthMetrics.tdee),
          targetHeartRate: mapHealthMetric(body.healthMetrics.targetHeartRate),
          bodyFat: mapHealthMetric(body.healthMetrics.bodyFat),
          oneRepMax: mapHealthMetric(body.healthMetrics.oneRepMax),
        }
      : null,
    biomarkers: Array.isArray(body?.biomarkers) ? body.biomarkers.map(mapBiomarker) : [],
  };
}
