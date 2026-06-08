import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Users, FileText, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { apiRequest } from '../lib/api';

const SESSION_TYPES = [
  { value: 'VIRTUAL', label: 'Virtual' },
  { value: 'WORKSHOP', label: 'Workshop' }
];

export default function RequestSessionForm({ onClose = () => {}, onSaved = () => {} }) {
  const [teams, setTeams] = useState([]);
  const [teamsLoading, setTeamsLoading] = useState(true);
  const [teamsError, setTeamsError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'VIRTUAL',
    scheduledAt: '', // datetime-local value
    duration: 60,
    timezone: 'Asia/Kolkata',
    teamId: '', // Empty means all employees
    targetAudience: 'ALL_EMPLOYEES',
    requestNotes: ''
  });

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setTeamsLoading(true);
    setTeamsError(null);
    try {
      const res = await apiRequest('/corporate-admin/teams');
      setTeams(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error('Failed to fetch teams', err);
      setTeamsError(err?.data?.message || err.message || 'Failed to load teams');
    } finally {
      setTeamsLoading(false);
    }
  };

  const updateField = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleAudienceChange = (value) => {
    if (value === 'ALL_EMPLOYEES') {
      setFormData(prev => ({ 
        ...prev, 
        targetAudience: 'ALL_EMPLOYEES', 
        teamId: '' 
      }));
    } else {
      setFormData(prev => ({ 
        ...prev, 
        targetAudience: 'SPECIFIC_TEAM', 
        teamId: value 
      }));
    }
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.scheduledAt) {
      setError('Title and scheduled date/time are required');
      return;
    }

    // Validate date is in the future (date-only comparison)
    const today = new Date().toISOString().slice(0, 10);
    if (formData.scheduledAt < today) {
      setError('Session must be scheduled for a future date');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Convert datetime-local to ISO string
      const scheduledAtISO = new Date(formData.scheduledAt).toISOString();

      const payload = {
        title: formData.title,
        description: formData.description || null,
        type: formData.type,
        mode: 'VIRTUAL', // Default for requests
        scheduledAt: scheduledAtISO,
        duration: parseInt(formData.duration, 10) || 60,
        timezone: formData.timezone || 'Asia/Kolkata',
        teamId: formData.teamId || null,
        targetAudience: formData.targetAudience,
        requestNotes: formData.requestNotes || null
      };

      await apiRequest('/corporate-admin/sessions', {
        method: 'POST',
        body: payload
      });

      setSuccess('Session request submitted successfully! Our team will review and schedule it soon.');
      
      // Wait a bit to show the success message
      setTimeout(() => {
        onSaved();
        onClose();
      }, 2000);

    } catch (err) {
      console.error('Failed to submit session request', err);
      setError(err?.data?.message || err.message || 'Failed to submit session request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Success/Error Messages */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start space-x-2">
          <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
          <span className="text-sm text-green-700">{success}</span>
        </div>
      )}

      {/* Info Banner */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> You're requesting a wellness session. Our team will review your request and schedule the session with all necessary details including instructor, meeting link, and materials.
        </p>
      </div>

      {/* Session Title */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Session Title *
        </label>
        <input
          type="text"
          required
          value={formData.title}
          onChange={(e) => updateField('title', e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all"
          placeholder="e.g., Monthly Mindfulness Session"
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => updateField('description', e.target.value)}
          rows={3}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all"
          placeholder="Describe the session objectives and what you'd like employees to learn..."
        />
      </div>

      {/* Session Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Session Type *
        </label>
        <select
          value={formData.type}
          onChange={(e) => updateField('type', e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all"
        >
          {SESSION_TYPES.map((type) => (
            <option key={type.value} value={type.value}>{type.label}</option>
          ))}
        </select>
      </div>

      {/* Preferred Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Calendar className="inline h-4 w-4 mr-1" />
          Preferred Date *
        </label>
        <input
          type="date"
          required
          value={formData.scheduledAt}
          onChange={(e) => updateField('scheduledAt', e.target.value)}
          min={new Date().toISOString().slice(0, 10)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all"
        />
      </div>

      {/* Duration */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Clock className="inline h-4 w-4 mr-1" />
          Duration *
        </label>
        <select
          value={formData.duration}
          onChange={(e) => updateField('duration', e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all"
        >
          <option value={30}>30 mins</option>
          <option value={45}>45 mins</option>
          <option value={60}>60 mins</option>
        </select>
      </div>

      {/* Audience Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Users className="inline h-4 w-4 mr-1" />
          Target Audience *
        </label>

        {teamsLoading ? (
          <div className="flex items-center space-x-2 text-gray-500 p-4 border border-gray-200 rounded-lg">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Loading teams...</span>
          </div>
        ) : teamsError ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">Failed to load teams: {teamsError}</p>
          </div>
        ) : (
          <select
            value={formData.teamId || 'ALL_EMPLOYEES'}
            onChange={(e) => handleAudienceChange(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all"
          >
            <option value="ALL_EMPLOYEES">All Teams</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>{team.name}</option>
            ))}
          </select>
        )}
      </div>

      {/* Additional Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <FileText className="inline h-4 w-4 mr-1" />
          Additional Notes (Optional)
        </label>
        <textarea
          value={formData.requestNotes}
          onChange={(e) => updateField('requestNotes', e.target.value)}
          rows={3}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all"
          placeholder="Any special requirements, preferred instructors, or additional information..."
        />
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-gradient-to-r from-[#64ae00] to-[#4a8200] text-white rounded-lg hover:from-[#579700] hover:to-[#3d6d00] transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Submitting Request...</span>
            </>
          ) : (
            <>
              <CheckCircle className="h-5 w-5" />
              <span>Request Session</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}

