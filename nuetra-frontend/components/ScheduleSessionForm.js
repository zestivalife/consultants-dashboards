import React, { useState, useEffect } from 'react';
import { apiRequest } from '../lib/api';

// ScheduleSessionForm.jsx
// A single-file React + Tailwind form component that uses the app's fetchWithAuth
// logic inline to POST to /corporate-admin/sessions. Drop this file into your
// components folder and import into the modal parent.

// Usage:
// <ScheduleSessionForm onClose={() => setShow(false)} onSaved={() => fetchDashboardStats()} />

export default function ScheduleSessionForm({ onClose = () => { }, onSaved = () => { } }) {

    const [teams, setTeams] = useState([]);
    const [teamsLoading, setTeamsLoading] = useState(true);
    const [teamsError, setTeamsError] = useState(null);


    useEffect(() => {
        let mounted = true;

        async function loadTeams() {
            setTeamsLoading(true);
            setTeamsError(null);

            try {
                const res = await apiRequest('/corporate-admin/teams');
                if (!mounted) return;
                setTeams(Array.isArray(res) ? res : []);
            } catch (err) {
                console.error('Failed to fetch teams', err);
                if (!mounted) return;
                setTeamsError(err?.data?.message || err.message || 'Failed to load teams');
            } finally {
                if (mounted) setTeamsLoading(false);
            }
        }

        loadTeams();
        return () => { mounted = false; };
    }, []);

    const SESSION_TYPES = [
        'MINDFULNESS', 'PHYSICAL_WELLNESS', 'MENTAL_HEALTH', 'NUTRITION', 'STRESS_MANAGEMENT', 'TEAM_BUILDING', 'WORKSHOP', 'ONE_ON_ONE'
    ];

    const [formData, setFormData] = useState({
        title: '',
        description: '',
        type: 'MINDFULNESS',
        mode: 'VIRTUAL',
        scheduledAt: '', // uses datetime-local value
        duration: 60,
        timezone: 'Asia/Kolkata',
        location: '',
        meetingLink: '',
        teamId: '',
        instructorId: '',
        externalInstructor: '',
        maxParticipants: '',
        materials: '' // comma-separated string in UI, convert before send
    });

    const [loading, setLoading] = useState(false);

    function updateField(name, value) {
        setFormData(prev => ({ ...prev, [name]: value }));
    }

    function handleMaterialsChange(e) {
        updateField('materials', e.target.value);
    }

    async function handleSubmit(e) {
        e.preventDefault();
        if (!formData.title || !formData.scheduledAt) {
            return window.alert('Title and scheduled date/time are required');
        }

        setLoading(true);
        try {
            // convert datetime-local ("yyyy-mm-ddThh:mm") into an ISO string
            // assume the user entered local datetime for the chosen timezone. If you
            // want to enforce timezone-aware datetimes, consider a datetime picker
            // that returns an explicit timezone or require ISO input.
            const scheduledAtLocal = formData.scheduledAt;
            // If user typed an ISO already, use it. Otherwise convert from datetime-local
            let scheduledAtISO = scheduledAtLocal;
            if (!scheduledAtLocal.endsWith('Z') && !scheduledAtLocal.includes('+')) {
                // datetime-local doesn't include timezone, treat it as local and convert
                const dt = new Date(scheduledAtLocal);
                scheduledAtISO = dt.toISOString();
            }

            const payload = {
                title: formData.title,
                description: formData.description || null,
                type: formData.type,
                mode: formData.mode,
                scheduledAt: scheduledAtISO,
                duration: parseInt(formData.duration, 10) || 60,
                timezone: formData.timezone || 'Asia/Kolkata',
                location: formData.location || null,
                meetingLink: formData.meetingLink || null,
                teamId: formData.teamId || null,
                instructorId: formData.instructorId || null,
                externalInstructor: formData.externalInstructor || null,
                maxParticipants: formData.maxParticipants ? parseInt(formData.maxParticipants, 10) : null,
                materials: formData.materials ? formData.materials.split(',').map(s => s.trim()).filter(Boolean) : null
            };

            await apiRequest('/corporate-admin/sessions', {
                method: 'POST',
                body: payload
            });

            // success
            window.alert('Session scheduled successfully');
            onSaved();
            onClose();

        } catch (err) {
            console.error('Failed to schedule session', err);
            window.alert(err?.data?.message || err.message || 'Failed to schedule session');
        } finally {
            setLoading(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Session Title *</label>
                <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => updateField('title', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Mindful Monday: Stress Relief"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                    value={formData.description}
                    onChange={(e) => updateField('description', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Describe what participants will learn..."
                />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Session Type *</label>
                    <select
                        value={formData.type}
                        onChange={(e) => updateField('type', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    >
                        {SESSION_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Mode *</label>
                    <select
                        value={formData.mode}
                        onChange={(e) => updateField('mode', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    >
                        <option value="VIRTUAL">Virtual</option>
                        {/* <option value="IN_PERSON">In-Person</option>
            <option value="HYBRID">Hybrid</option> */}
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Scheduled Date & Time *</label>
                    <input
                        type="datetime-local"
                        required
                        value={formData.scheduledAt}
                        onChange={(e) => updateField('scheduledAt', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Duration (minutes) *</label>
                    <input
                        type="number"
                        required
                        value={formData.duration}
                        onChange={(e) => updateField('duration', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        min="5"
                        step="5"
                    />
                </div>
            </div>

            {formData.mode !== 'IN_PERSON' && (
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Meeting Link</label>
                    <input
                        type="url"
                        value={formData.meetingLink}
                        onChange={(e) => updateField('meetingLink', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        placeholder="https://zoom.us/j/..."
                    />
                </div>
            )}

            {formData.mode !== 'VIRTUAL' && (
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                    <input
                        type="text"
                        value={formData.location}
                        onChange={(e) => updateField('location', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        placeholder="Conference Room A, 3rd Floor"
                    />
                </div>
            )}

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Assign to Team (Optional)</label>

                {teamsLoading ? (
                    <div className="text-sm text-gray-500">Loading teams...</div>
                ) : teamsError ? (
                    <div className="text-sm text-red-600">Failed to load teams: {teamsError}</div>
                ) : (
                    <select
                        value={formData.teamId}
                        onChange={(e) => updateField('teamId', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    >
                        <option value="">All Employees</option>
                        {teams.map(t => (
                            // t.id and t.name are returned by your backend route
                            <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                    </select>
                )}
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Instructor</label>
                <input
                    type="text"
                    value={formData.externalInstructor}
                    onChange={(e) => updateField('externalInstructor', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Dr. Sarah Chen"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Participants (Optional)</label>
                <input
                    type="number"
                    value={formData.maxParticipants || ''}
                    onChange={(e) => updateField('maxParticipants', e.target.value ? parseInt(e.target.value, 10) : '')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Unlimited"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Materials (comma-separated URLs)</label>
                <input
                    name="materials"
                    onChange={handleMaterialsChange}
                    value={formData.materials}
                    placeholder="https://..., https://..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
            </div>

            <div className="flex justify-end space-x-3 pt-4 sticky bottom-0 bg-white py-4">
                <button
                    type="button"
                    onClick={onClose}
                    disabled={loading}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:from-green-600 hover:to-blue-600 transition-all"
                >
                    {loading ? 'Scheduling...' : 'Schedule Session'}
                </button>
            </div>
        </form>
    );
}
