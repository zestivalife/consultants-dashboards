/**
 * Centralized API client for the Nuetra microservices backend.
 *
 * All requests go through the API Gateway at NEXT_PUBLIC_API_URL.
 * The gateway validates JWTs and routes to individual services.
 *
 * Standard backend response shape:
 *   { success: bool, data: T | null, message: string, error: string | null, request_id: string }
 */

export function getApiBaseUrl() {
  let baseUrl = process.env.NEXT_PUBLIC_API_URL;

  // Use runtime override if accessed from localhost
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    baseUrl = 'http://localhost:8000';
  }

  // Fallbacks if not set
  if (!baseUrl) {
    if (process.env.NODE_ENV === 'production') {
      baseUrl = 'https://api.nuetra.in';
    } else {
      baseUrl = 'http://localhost:8000';
    }
  }

  // Gateway typically expects /api/v1 routes
  baseUrl = baseUrl.replace(/\/$/, '');
  if (!baseUrl.endsWith('/api/v1')) {
    baseUrl += '/api/v1';
  }

  return baseUrl;
}

const API_BASE = getApiBaseUrl();
// ── token helpers ──────────────────────────────────────────────────

export function getToken() {
  if (typeof window === 'undefined') return null;
  return (
    localStorage.getItem('access_token') ||
    sessionStorage.getItem('access_token') ||
    null
  );
}

export function setToken(token, remember = true) {
  if (typeof window === 'undefined') return;
  if (remember) {
    localStorage.setItem('access_token', token);
    sessionStorage.removeItem('access_token');
  } else {
    sessionStorage.setItem('access_token', token);
    localStorage.removeItem('access_token');
  }
}

export function getRefreshToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token') || null;
}

export function setRefreshToken(token) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('refresh_token', token);
}

export function clearTokens() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  sessionStorage.removeItem('access_token');
}

// ── core request function ──────────────────────────────────────────

/**
 * Make an authenticated request to the API gateway.
 *
 * @param {string} path   - path relative to API_BASE, e.g. "/auth/login"
 * @param {object} opts   - fetch options (method, body, headers, etc.)
 * @returns {object}      - the unwrapped `data` field from the standard response
 * @throws {Error}        - with `.status`, `.data`, `.message` on failure
 */
export async function apiRequest(path, opts = {}) {
  const url = `${API_BASE}${path.startsWith('/') ? path : '/' + path}`;

  const token = getToken();
  const headers = {
    ...(opts.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(opts.headers || {}),
  };

  const finalBody = opts.body instanceof FormData
    ? opts.body
    : opts.body
      ? typeof opts.body === 'string'
        ? opts.body
        : JSON.stringify(opts.body)
      : undefined;

  console.log(`[API REQUEST] ${opts.method || 'GET'} ${url}`, { headers, body: opts.body });

  let res;
  try {
    res = await fetch(url, {
      ...opts,
      headers,
      body: finalBody,
    });
  } catch (networkErr) {
    // Re-throw AbortErrors unchanged so callers using AbortController can detect them.
    if (networkErr.name === 'AbortError') throw networkErr;
    console.error(`[API NETWORK ERROR] ${opts.method || 'GET'} ${url}`, networkErr);
    const err = new Error('Network error: please check if the server is running.');
    err.status = 0;
    err.cause = networkErr;
    throw err;
  }

  const text = await res.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }

  if (!res.ok) {
    console.error(`[API ERROR] ${res.status} ${opts.method || 'GET'} ${url}`, json || text);
    if (res.status === 401 && typeof window !== 'undefined') {
      clearTokens();
    }

    const err = new Error(
      json?.message || json?.error || `Request failed (${res.status})`
    );
    err.status = res.status;
    err.data = json;
    throw err;
  }

  console.log(`[API RESPONSE] ${res.status} ${opts.method || 'GET'} ${url}`, json);

  // Backend wraps everything in { success, data, message, error, request_id }.
  // Return the inner `data` so callers don't need to unwrap every time.
  if (json && typeof json === 'object' && 'success' in json) {
    return json.data;
  }
  return json;
}

// ── Auth endpoints ─────────────────────────────────────────────────

export const authAPI = {
  register({ email, password, companyName, location, employees, industry, role }) {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: { email, password, companyName, location, employees, industry, role },
    });
  },

  verifyOtp(email, otp) {
    return apiRequest('/auth/verify-otp', {
      method: 'POST',
      body: { email, otp },
    });
  },

  login(email, password) {
    return apiRequest('/auth/login', {
      method: 'POST',
      body: { email, password },
    });
  },

  refresh(refreshToken) {
    return apiRequest('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    });
  },

  logout(refreshToken) {
    return apiRequest('/auth/logout', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    });
  },

  me() {
    return apiRequest('/auth/me');
  },

  roles() {
    return apiRequest('/auth/roles');
  },
};

// ── Profile endpoints ──────────────────────────────────────────────

export const profileAPI = {
  create(data) {
    return apiRequest('/profile', { method: 'POST', body: data });
  },

  me() {
    return apiRequest('/profile/me');
  },

  update(data) {
    return apiRequest('/profile/me', { method: 'PUT', body: data });
  },

  onboardingStatus() {
    return apiRequest('/profile/onboarding-status');
  },

  submitOnboarding(data) {
    return apiRequest('/profile', { method: 'POST', body: data });
  },

  uploadReport(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiRequest('/profile/upload-report', {
      method: 'POST',
      body: formData,
    });
  },
};

// ── Assessment endpoints ───────────────────────────────────────────

export const assessmentAPI = {
  submitBrainState(responses) {
    return apiRequest('/assessments/brain-state', {
      method: 'POST',
      body: { answers: responses },
    });
  },

  submitFocusMode(responses) {
    return apiRequest('/assessments/focus-mode', {
      method: 'POST',
      body: { answers: responses },
    });
  },

  submitPSS10(responses) {
    return apiRequest('/assessments/pss10', {
      method: 'POST',
      body: { answers: responses },
    });
  },

  submitPhysicalEase(responses) {
    return apiRequest('/assessments/physical-ease', {
      method: 'POST',
      body: { answers: responses },
    });
  },

  history() {
    return apiRequest('/assessments/history');
  },
};

// ── Scoring endpoints ──────────────────────────────────────────────

export const scoringAPI = {
  compute(force = false) {
    const qs = force ? '?force=true' : '';
    return apiRequest(`/scoring/compute${qs}`, { method: 'POST' });
  },

  me() {
    return apiRequest('/scoring/me');
  },

  timeline(limit = 30) {
    return apiRequest(`/scoring/timeline?limit=${limit}`);
  },
};

// ── Nutrition endpoints ────────────────────────────────────────────

export const nutritionAPI = {
  createDietPlan(data) {
    return apiRequest('/nutrition/diet-plan', { method: 'POST', body: data });
  },

  templates() {
    return apiRequest('/nutrition/templates');
  },

  assign(userId, dietPlanId) {
    return apiRequest('/nutrition/assign', {
      method: 'POST',
      body: { user_id: userId, diet_plan_id: dietPlanId },
    });
  },

  myPlan() {
    return apiRequest('/nutrition/my-plan');
  },

  uploadReport(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiRequest('/nutrition/upload-report', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Upload health report files with optional diet plan ID association
   * @param {File[]} files - Array of File objects
   * @param {string} dietPlanId - Optional diet plan ID to associate files
   * @returns {Promise} Response with uploaded file info
   */
  uploadFiles(files) {
    const formData = new FormData();
    if (!files || files.length === 0) {
      throw new Error('At least one file must be provided');
    }
    
    files.forEach((file) => {
      if (!(file instanceof File)) {
        throw new Error('Invalid file object provided');
      }
      formData.append('file', file);
    });
    
    return apiRequest('/nutrition/upload-report', {
      method: 'POST',
      body: formData,
    });
  },
};

// ── Notification endpoints ─────────────────────────────────────────

export const notificationAPI = {
  list(status = null, limit = 50) {
    const qs = status ? `?status=${status}&limit=${limit}` : `?limit=${limit}`;
    return apiRequest(`/notifications${qs}`);
  },

  markRead(id) {
    return apiRequest(`/notifications/${id}/read`, { method: 'PUT' });
  },

  markAllRead() {
    return apiRequest('/notifications/mark-all-read', { method: 'PUT' });
  },

  delete(id) {
    return apiRequest(`/notifications/${id}`, { method: 'DELETE' });
  },
};

// ── Team Lead endpoints ────────────────────────────────────────────

export const teamLeadAPI = {
  dashboard() {
    return apiRequest('/team-lead/dashboard');
  },

  team() {
    return apiRequest('/team-lead/team');
  },

  members() {
    return apiRequest('/team-lead/team/members');
  },

  upcomingSessions() {
    return apiRequest('/team-lead/sessions/upcoming');
  },
};

// ── Team Member endpoints ──────────────────────────────────────────

export const teamMemberAPI = {
  profile() {
    return apiRequest('/team-member/profile');
  },

  stats() {
    return apiRequest('/team-member/dashboard/stats');
  },

  myTeam() {
    return apiRequest('/team-member/me/team');
  },

  joinTeam(teamCode) {
    return apiRequest('/team-member/teams/join', { method: 'POST', body: { teamCode } });
  },

  logMetric(data) {
    return apiRequest('/team-member/metrics', { method: 'POST', body: data });
  },

  metrics(limit = 10) {
    return apiRequest(`/team-member/metrics?limit=${limit}`);
  },

  notifications(status = 'UNREAD', limit = 5) {
    return apiRequest(`/team-member/notifications?status=${status}&limit=${limit}`);
  },

  getSessions() {
    return apiRequest('/team-member/sessions');
  },

  requestSession(data) {
    return apiRequest('/team-member/sessions', { method: 'POST', body: data });
  },

  logToolUsage(data) {
    return apiRequest('/team-member/tools/log', { method: 'POST', body: data });
  },

  getToolStats() {
    return apiRequest('/team-member/tools/stats');
  },

  getToolRecommendations() {
    return apiRequest('/team-member/tools/recommendations');
  },
};

export default {
  auth: authAPI,
  profile: profileAPI,
  assessment: assessmentAPI,
  scoring: scoringAPI,
  nutrition: nutritionAPI,
  notification: notificationAPI,
  teamLead: teamLeadAPI,
  teamMember: teamMemberAPI,
  request: apiRequest,
};
