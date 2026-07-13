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

  // In deployed browser sessions, use the app's own proxy route so the browser
  // never depends on cross-origin CORS headers from the backend gateway.
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    baseUrl = `${window.location.origin}/api/gateway`;
  }

  // Fallbacks if not set
  if (!baseUrl) {
    if (process.env.NODE_ENV === 'production') {
      baseUrl = '/api/gateway';
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
const DEBUG_API = process.env.NEXT_PUBLIC_DEBUG_API === 'true';
// ── token helpers ──────────────────────────────────────────────────
let refreshPromise = null;

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
  return (
    localStorage.getItem('refresh_token') ||
    sessionStorage.getItem('refresh_token') ||
    null
  );
}

export function setRefreshToken(token, remember = true) {
  if (typeof window === 'undefined') return;
  if (remember) {
    localStorage.setItem('refresh_token', token);
    sessionStorage.removeItem('refresh_token');
  } else {
    sessionStorage.setItem('refresh_token', token);
    localStorage.removeItem('refresh_token');
  }
}

export function isRememberedAuthSession() {
  if (typeof window === 'undefined') return true;
  return Boolean(
    localStorage.getItem('access_token') ||
    localStorage.getItem('refresh_token')
  );
}

export function clearTokens() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
}

function redactHeaders(headers) {
  if (!headers?.Authorization) return headers;
  return { ...headers, Authorization: 'Bearer [redacted]' };
}

function requestWithXhr(url, options = {}) {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || typeof XMLHttpRequest === 'undefined') {
      reject(new Error('XMLHttpRequest is not available.'));
      return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open(options.method || 'GET', url, true);

    Object.entries(options.headers || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        xhr.setRequestHeader(key, value);
      }
    });

    xhr.onload = () => {
      resolve({
        ok: xhr.status >= 200 && xhr.status < 300,
        status: xhr.status,
        text: async () => xhr.responseText || '',
      });
    };
    xhr.onerror = () => reject(new Error('Network error: XMLHttpRequest failed.'));
    xhr.ontimeout = () => reject(new Error('Network error: XMLHttpRequest timed out.'));
    xhr.send(options.body);
  });
}

async function refreshAccessToken() {
  if (typeof window === 'undefined') return null;

  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  if (!refreshPromise) {
    const remember = isRememberedAuthSession();
    refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (res) => {
        const text = await res.text();
        let json = null;
        try {
          json = text ? JSON.parse(text) : null;
        } catch {
          json = null;
        }

        if (!res.ok) {
          const err = new Error(json?.message || json?.error || 'Session refresh failed.');
          err.status = res.status;
          err.data = json;
          throw err;
        }

        const tokens = json?.data || json;
        if (!tokens?.access_token || !tokens?.refresh_token) {
          throw new Error('Session refresh response is incomplete.');
        }

        setToken(tokens.access_token, remember);
        setRefreshToken(tokens.refresh_token, remember);
        return tokens.access_token;
      })
      .catch((err) => {
        clearTokens();
        throw err;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
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
  const { skipAuthRefresh = false, responseType = 'json', ...fetchOptions } = opts;
  const url = `${API_BASE}${path.startsWith('/') ? path : '/' + path}`;
  const shouldSkipAuthRefresh = skipAuthRefresh || path.startsWith('/auth/refresh') || path.startsWith('/auth/login');

  const token = getToken();
  const headers = {
    ...(fetchOptions.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(fetchOptions.headers || {}),
  };

  const finalBody = fetchOptions.body instanceof FormData
    ? fetchOptions.body
    : fetchOptions.body
      ? typeof fetchOptions.body === 'string'
        ? fetchOptions.body
        : JSON.stringify(fetchOptions.body)
      : undefined;

  if (DEBUG_API) {
    console.log(`[API REQUEST] ${fetchOptions.method || 'GET'} ${url}`, {
      headers: redactHeaders(headers),
      body: fetchOptions.body,
    });
  }

  let res;
  try {
    res = await fetch(url, {
      ...fetchOptions,
      headers,
      body: finalBody,
    });
  } catch (networkErr) {
    // Re-throw AbortErrors unchanged so callers using AbortController can detect them.
    if (networkErr.name === 'AbortError') throw networkErr;
    try {
      res = await requestWithXhr(url, {
        method: fetchOptions.method || 'GET',
        headers,
        body: finalBody,
      });
    } catch (xhrErr) {
      console.error(`[API NETWORK ERROR] ${fetchOptions.method || 'GET'} ${url}`, networkErr, xhrErr);
      const err = new Error('Network error: please check if the server is running.');
      err.status = 0;
      err.cause = networkErr;
      throw err;
    }
  }

  let text = await res.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }

  if (!res.ok) {
    if (res.status === 401 && !shouldSkipAuthRefresh && typeof window !== 'undefined') {
      try {
        const nextAccessToken = await refreshAccessToken();
        if (nextAccessToken) {
          const retryHeaders = {
            ...headers,
            Authorization: `Bearer ${nextAccessToken}`,
          };
          const retryResponse = await fetch(url, {
            ...fetchOptions,
            headers: retryHeaders,
            body: finalBody,
          });
          const retryText = await retryResponse.text();
          let retryJson = null;
          try {
            retryJson = retryText ? JSON.parse(retryText) : null;
          } catch {
            retryJson = null;
          }

          if (retryResponse.ok) {
            if (responseType === 'text') return retryText;
            if (retryJson && typeof retryJson === 'object' && 'success' in retryJson) {
              return retryJson.data;
            }
            return retryJson;
          }

          res = retryResponse;
          json = retryJson;
          text = retryText;
        }
      } catch {
        clearTokens();
      }
    }

    console.error(`[API ERROR] ${res.status} ${fetchOptions.method || 'GET'} ${url}`, json || text);
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

  if (DEBUG_API) {
    console.log(`[API RESPONSE] ${res.status} ${fetchOptions.method || 'GET'} ${url}`, json);
  }

  if (responseType === 'text') return text;

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
      skipAuthRefresh: true,
    });
  },

  logout(refreshToken) {
    return apiRequest('/auth/logout', {
      method: 'POST',
      body: { refresh_token: refreshToken },
      skipAuthRefresh: true,
    });
  },

  forgotPassword(email) {
    return apiRequest('/auth/forgot-password', {
      method: 'POST',
      body: { email },
    });
  },

  me() {
    return apiRequest('/auth/me');
  },

  roles() {
    return apiRequest('/auth/roles');
  },
};

export const ownerPeopleAccessAPI = {
  summary() {
    return apiRequest('/owner/people-access/summary');
  },

  metadata() {
    return apiRequest('/owner/people-access/metadata');
  },

  listUsers(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return;
      searchParams.set(key, String(value));
    });
    const suffix = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest(`/owner/people-access/users${suffix}`);
  },

  getUser(userId) {
    return apiRequest(`/owner/people-access/users/${userId}`);
  },

  createUser(payload) {
    return apiRequest('/owner/people-access/users', {
      method: 'POST',
      body: payload,
    });
  },

  updateUser(userId, payload) {
    return apiRequest(`/owner/people-access/users/${userId}`, {
      method: 'PATCH',
      body: payload,
    });
  },

  addNote(userId, body) {
    return apiRequest(`/owner/people-access/users/${userId}/notes`, {
      method: 'POST',
      body: { body },
    });
  },

  addAttachment(userId, payload) {
    return apiRequest(`/owner/people-access/users/${userId}/attachments`, {
      method: 'POST',
      body: payload,
    });
  },

  bulkAction(payload) {
    return apiRequest('/owner/people-access/users/bulk-actions', {
      method: 'POST',
      body: payload,
    });
  },

  listInvitations(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return;
      searchParams.set(key, String(value));
    });
    const suffix = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiRequest(`/owner/people-access/invitations${suffix}`);
  },

  createInvitation(payload) {
    return apiRequest('/owner/people-access/invitations', {
      method: 'POST',
      body: payload,
    });
  },

  resendInvitation(invitationId) {
    return apiRequest(`/owner/people-access/invitations/${invitationId}/resend`, {
      method: 'POST',
    });
  },

  cancelInvitation(invitationId) {
    return apiRequest(`/owner/people-access/invitations/${invitationId}/cancel`, {
      method: 'POST',
    });
  },

  updateRolePermissions(roleId, permissionKeys) {
    return apiRequest(`/owner/people-access/roles/${roleId}/permissions`, {
      method: 'PATCH',
      body: { permission_keys: permissionKeys },
    });
  },

  createRole(payload) {
    return apiRequest('/owner/people-access/roles', {
      method: 'POST',
      body: payload,
    });
  },

  cloneRole(roleId, payload) {
    return apiRequest(`/owner/people-access/roles/${roleId}/clone`, {
      method: 'POST',
      body: payload,
    });
  },

  assignProducts(userId, assignments) {
    return apiRequest(`/owner/people-access/users/${userId}/products`, {
      method: 'PUT',
      body: assignments,
    });
  },

  assignPackages(userId, assignments) {
    return apiRequest(`/owner/people-access/users/${userId}/packages`, {
      method: 'PUT',
      body: assignments,
    });
  },

  assignServices(userId, assignments) {
    return apiRequest(`/owner/people-access/users/${userId}/services`, {
      method: 'PUT',
      body: assignments,
    });
  },

  revokeSession(userId, sessionId) {
    return apiRequest(`/owner/people-access/users/${userId}/sessions/${sessionId}/revoke`, {
      method: 'POST',
    });
  },

  forceLogout(userId) {
    return apiRequest(`/owner/people-access/users/${userId}/force-logout`, {
      method: 'POST',
    });
  },

  async exportUsersCsv() {
    return apiRequest('/owner/people-access/exports/users', {
      responseType: 'text',
    });
  },

  importUsers(rows) {
    return apiRequest('/owner/people-access/users/import', {
      method: 'POST',
      body: { rows },
    });
  },

  createOrganization(payload) {
    return apiRequest('/owner/people-access/organizations', {
      method: 'POST',
      body: payload,
    });
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

export const corporateAPI = {
  authorityOptions() {
    return apiRequest('/corporate-admin/authority-options');
  },

  people() {
    return apiRequest('/corporate-admin/people');
  },

  createPerson(data) {
    return apiRequest('/corporate-admin/people', {
      method: 'POST',
      body: data,
    });
  },

  updatePersonAuthorities(userId, authorities) {
    return apiRequest(`/corporate-admin/people/${userId}/authorities`, {
      method: 'PATCH',
      body: { authorities },
    });
  },

  consultants() {
    return apiRequest('/corporate-admin/consultants');
  },

  createConsultant(data) {
    return apiRequest('/corporate-admin/consultants', {
      method: 'POST',
      body: data,
    });
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
  corporate: corporateAPI,
  request: apiRequest,
};
