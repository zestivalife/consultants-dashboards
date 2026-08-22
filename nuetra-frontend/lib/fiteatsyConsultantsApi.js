import { getToken, refreshAccessToken } from './api';

const DEFAULT_FITEATSY_API_URL = 'https://fiteatsy-mobile-production.up.railway.app';

function isLocalhostRuntime() {
  return typeof window !== 'undefined' && window.location.hostname === 'localhost';
}

export function getFiteatsyApiBaseUrl() {
  if (isLocalhostRuntime()) {
    const configured = process.env.NEXT_PUBLIC_FITEATSY_API_URL || DEFAULT_FITEATSY_API_URL;
    return configured.replace(/\/+$/, '');
  }

  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/fiteatsy`;
  }

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

export async function searchFiteatsyAssignmentClients(query = '', offset = 0) {
  const body = await requestFiteatsyJson(`/v1/professional-assignments/clients/search?q=${encodeURIComponent(query)}&limit=25&offset=${offset}`);
  return Array.isArray(body?.clients) ? body.clients : [];
}

export async function listFiteatsyClientAllocationPool({ query = '', assignment = 'all', offset = 0 } = {}) {
  const body = await requestFiteatsyJson(`/v1/professional-assignments/clients/pool?q=${encodeURIComponent(query)}&assignment=${encodeURIComponent(assignment)}&limit=50&offset=${offset}`);
  return Array.isArray(body?.clients) ? body.clients : [];
}

export async function listFiteatsyAssignmentProfessionals(type) {
  const suffix = type ? `?type=${encodeURIComponent(type)}` : '';
  const body = await requestFiteatsyJson(`/v1/professional-assignments/professionals${suffix}`);
  return Array.isArray(body?.professionals) ? body.professionals : [];
}

export async function listFiteatsyProfessionalAssignments() {
  const body = await requestFiteatsyJson('/v1/professional-assignments');
  return Array.isArray(body?.assignments) ? body.assignments : [];
}

export async function createFiteatsyProfessionalAssignment(payload) {
  return requestFiteatsy('/v1/professional-assignments', { method: 'POST', body: payload });
}

export async function revokeFiteatsyProfessionalAssignment(assignmentId, reason) {
  return requestFiteatsy(`/v1/professional-assignments/${encodeURIComponent(assignmentId)}`, { method: 'DELETE', body: { reason } });
}

export async function getFiteatsyConsultantClientProfile(clientId) {
  const encodedClientId = encodeURIComponent(clientId);
  const [body, nutritionBody] = await Promise.all([
    requestFiteatsyJson(`/v1/consultants/clients/${encodedClientId}/workspace`),
    requestFiteatsyJson(`/v1/consultants/clients/${encodedClientId}/nutrition-intelligence`),
  ]);

  return {
    contract: body?.contract || null,
    access: body?.access || null,
    client: body?.client || null,
    profile: body?.profile || null,
    onboarding: body?.onboarding || null,
    healthProfile: body?.healthProfile || null,
    bodyMetrics: body?.bodyMetrics || null,
    nutritionProtocol: body?.nutritionProtocol || null,
    nutritionSnapshot: body?.nutritionSnapshot || null,
    nutritionIntelligence: nutritionBody?.intelligence || body?.nutritionIntelligence || null,
    nutritionMonitoring: nutritionBody?.nutritionMonitoring || null,
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

export async function generateFiteatsyConsultantOptionalGuidance(clientId, dietPlanId) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/optional-guidance/generate`, {
    method: 'POST',
  });
}

export async function searchFiteatsyConsultantOptionalGuidance(clientId, dietPlanId, { query = '', category, context = '' }) {
  const params = new URLSearchParams({ category, ...(query ? { query } : {}), ...(context ? { context } : {}) });
  return requestFiteatsyJson(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/optional-guidance/candidates?${params}`);
}

export async function approveFiteatsyConsultantDietPlan(clientId, dietPlanId) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/approve`, {
    method: 'POST',
  });
}

export async function submitFiteatsyConsultantDietPlanForReview(clientId, dietPlanId) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/submit-review`, {
    method: 'POST',
  });
}

export async function requestFiteatsyConsultantDietPlanChanges(clientId, dietPlanId, comment) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/request-changes`, {
    method: 'POST',
    body: { comment },
  });
}

export async function listFiteatsyDietPlanReviews() {
  const body = await requestFiteatsyJson('/v1/consultants/diet-plan-reviews');
  return Array.isArray(body?.reviews) ? body.reviews : [];
}

export async function publishFiteatsyConsultantDietPlan(clientId, dietPlanId, approvedVersionId) {
  return requestFiteatsy(`/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/publish`, {
    method: 'POST',
    body: { approvedVersionId },
  });
}

export async function downloadFiteatsyConsultantDietPlan(clientId, dietPlanId) {
  const token = getToken();
  const url = `${getFiteatsyApiBaseUrl()}/v1/consultants/clients/${encodeURIComponent(clientId)}/diet-plans/${encodeURIComponent(dietPlanId)}/download`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    const body = await readJsonResponse(response);
    const error = new Error(body?.message || body?.error || `Fiteatsy request failed (${response.status})`);
    error.status = response.status;
    error.data = body;
    throw error;
  }

  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
  return {
    blob,
    filename: match?.[1] || 'fiteatsy-diet-plan.docx',
  };
}
