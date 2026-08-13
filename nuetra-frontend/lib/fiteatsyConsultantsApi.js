import { getToken, refreshAccessToken } from './api';

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
    age: record.age ?? onboarding.age ?? null,
    gender: record.gender ?? onboarding.gender ?? null,
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

async function requestFiteatsyJson(path) {
  return requestFiteatsy(path, { method: 'GET' });
}

async function requestFiteatsy(path, options = {}) {
  const token = getToken();
  const url = `${getFiteatsyApiBaseUrl()}${path}`;
  const response = await fetch(url, {
    method: options.method || 'GET',
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...(options.body ? { body: JSON.stringify(options.body) } : {}),
  });
  let body = await readJsonResponse(response);

  if (response.status === 401) {
    const refreshedToken = await refreshAccessToken().catch(() => null);
    if (refreshedToken) {
      const retryResponse = await fetch(url, {
        method: options.method || 'GET',
        headers: {
          Accept: 'application/json',
          ...(options.body ? { 'Content-Type': 'application/json' } : {}),
          Authorization: `Bearer ${refreshedToken}`,
          ...(options.headers || {}),
        },
        ...(options.body ? { body: JSON.stringify(options.body) } : {}),
      });
      body = await readJsonResponse(retryResponse);
      if (retryResponse.ok) return body;

      const retryError = new Error(
        body?.message || body?.error || `Fiteatsy request failed (${retryResponse.status})`
      );
      retryError.status = retryResponse.status;
      retryError.data = body;
      throw retryError;
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
  const body = await requestFiteatsyJson('/v1/consultants/clients');

  return {
    clients: Array.isArray(body?.clients) ? body.clients.map(mapClient) : [],
  };
}

export async function getFiteatsyConsultantClientProfile(clientId) {
  const body = await requestFiteatsyJson(`/v1/consultants/clients/${encodeURIComponent(clientId)}/workspace`);

  return {
    contract: body?.contract || null,
    access: body?.access || null,
    client: body?.client || null,
    profile: body?.profile || null,
    onboarding: body?.onboarding || null,
    healthProfile: body?.healthProfile || null,
    bodyMetrics: body?.bodyMetrics || null,
    nutritionProtocol: body?.nutritionProtocol || null,
    nutritionIntelligence: body?.nutritionIntelligence || null,
    nutritionSnapshot: body?.nutritionSnapshot || null,
    dietPlan: body?.dietPlan || null,
    planWorkflow: body?.planWorkflow || null,
    wearableSummary: body?.wearableSummary || null,
    reports: Array.isArray(body?.reports) ? body.reports : [],
    recommendations: Array.isArray(body?.recommendations) ? body.recommendations : [],
    timeline: Array.isArray(body?.timeline) ? body.timeline : [],
    completeness: body?.completeness || null,
    syncMetadata: body?.syncMetadata || null,
    provenance: body?.provenance || null,
    sourceMetadata: body?.sourceMetadata || null,
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

export async function getFiteatsyConsultantNutritionIntelligence(clientId) {
  return requestFiteatsyJson(`/v1/consultants/clients/${encodeURIComponent(clientId)}/nutrition-intelligence`);
}

export async function getFiteatsyConsultantLatestDietPlan(clientId) {
  return requestFiteatsyJson(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/latest`);
}

export async function generateFiteatsyConsultantDietPlanDraft(clientId, payload = {}) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/draft`, {
    method: 'POST',
    body: payload,
  });
}

export async function updateFiteatsyConsultantDietPlanDraft(clientId, dietPlanId, payload) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}`, {
    method: 'PATCH',
    body: payload,
  });
}

export async function approveFiteatsyConsultantDietPlan(clientId, dietPlanId) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/approve`, {
    method: 'POST',
  });
}

export async function publishFiteatsyConsultantDietPlan(clientId, dietPlanId) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/publish`, {
    method: 'POST',
  });
}
