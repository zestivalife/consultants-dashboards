/**
 * Domain-specific API modules built on top of the centralized client.
 *
 * These re-export the modules from lib/api.js and add any
 * component-specific wrappers needed by legacy components.
 */
import {
  apiRequest,
  authAPI,
  profileAPI,
  assessmentAPI,
  scoringAPI,
  nutritionAPI,
} from '../lib/api';

// Re-export domain APIs for components that import from utils/api
export {
  authAPI,
  profileAPI,
  assessmentAPI,
  scoringAPI,
  nutritionAPI,
};

// Legacy `apiCall` wrapper — components that call apiCall('/some/path', opts)
// will be routed through the centralized client.
export async function apiCall(path, options = {}) {
  return apiRequest(path, options);
}

// Diet Plan API (mapped to nutrition-service)
export const dietPlanAPI = {
  async getDietPlans() {
    return nutritionAPI.templates();
  },
  async getDietPlan(id) {
    return apiRequest(`/nutrition/templates/${id}`);
  },
  async createDietPlan(data) {
    return nutritionAPI.createDietPlan(data);
  },
  /**
   * Upload health report files
   * @param {string} dietPlanId - Diet plan ID (for reference, not sent to API)
   * @param {File[]} files - Array of File objects to upload
   * @returns {Promise} Response with uploaded file metadata
   */
  async uploadFiles(dietPlanId, files) {
    try {
      // Validate files before upload
      if (!files || !Array.isArray(files) || files.length === 0) {
        throw new Error('No files provided for upload');
      }

      // Use the updated nutritionAPI uploadFiles method
      const response = await nutritionAPI.uploadFiles(files);
      
      // Store the dietPlanId reference for the flow (not sent to backend)
      return {
        ...response,
        dietPlanId: dietPlanId,
        files: response.files || [{ id: response.id, file_url: response.file_url }]
      };
    } catch (error) {
      console.error('File upload error:', error);
      throw error;
    }
  },
  async submitPSS10(dietPlanId, responses) {
    return assessmentAPI.submitPSS10(responses);
  },
  async getPSS10(dietPlanId) {
    return assessmentAPI.history();
  },
};

// Appointment API (consultation-service — not yet implemented)
export const appointmentAPI = {
  async getAppointments() {
    return apiRequest('/consultations/appointments');
  },
  async createAppointment(data) {
    return apiRequest('/consultations/appointments', { method: 'POST', body: data });
  },
  async getAppointment(id) {
    return apiRequest(`/consultations/appointments/${id}`);
  },
  async cancelAppointment(id) {
    return apiRequest(`/consultations/appointments/${id}`, { method: 'DELETE' });
  },
  /**
   * Get available slots for consultation booking
   * @param {string} providerId - Provider/dietician ID
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise} Array of available time slots
   */
  async getAvailableSlots(providerId, date) {
    try {
      return await apiRequest(`/consultations/providers/${providerId}/available-slots?date=${date}`);
    } catch (err) {
      // If endpoint doesn't exist, return empty array (caller will generate defaults)
      if (err.status === 404) {
        return [];
      }
      throw err;
    }
  },
};

// Corporate Session API (analytics-service — not yet implemented)
export const corporateSessionAPI = {
  async getSessions() {
    return apiRequest('/analytics/sessions');
  },
  async createSession(data) {
    return apiRequest('/analytics/sessions', { method: 'POST', body: data });
  },
};
export { corporateSessionAPI as corporateAPI };

// Team API (not yet implemented)
export const teamAPI = {
  async getTeams() {
    return apiRequest('/admin/teams');
  },
  async getTeamMembers(teamId) {
    return apiRequest(`/admin/teams/${teamId}/members`);
  },
};

export default {
  dietPlan: dietPlanAPI,
  appointment: appointmentAPI,
  corporateSession: corporateSessionAPI,
  auth: authAPI,
  profile: profileAPI,
  assessment: assessmentAPI,
  scoring: scoringAPI,
  nutrition: nutritionAPI,
  team: teamAPI,
  call: apiCall,
};
