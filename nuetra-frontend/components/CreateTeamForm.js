import { useState, useEffect } from "react";
import { apiRequest } from "../lib/api";

// CreateTeamForm.jsx
// - Now supports loading team leads dynamically from the API filtered by companyId.
// - Props:
//    onClose: fn
//    onSubmit: async fn(payload)
//    leads: optional fallback array of leads
//    companyId: optional company id used to fetch users belonging to the company
//    fetcher: optional function (url, opts) => Promise that returns json (useful to inject your project's fetchWithAuth)

export default function CreateTeamForm({ onClose, onSubmit, leads = [], companyId, fetcher }) {
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        leadId: "",
        settings: {
            allowSelfJoin: false,
            maxMembers: null,
            notificationPreferences: {
                sessionReminders: true,
                goalUpdates: true,
            },
        },
    });

    const [loading, setLoading] = useState(false);
    const [leadOptions, setLeadOptions] = useState(leads);
    const [leadsLoading, setLeadsLoading] = useState(false);
    const [leadsError, setLeadsError] = useState(null);

    useEffect(() => {
        let mounted = true;
        const controller = new AbortController();

        async function loadLeads() {
            setLeadsLoading(true);
            setLeadsError(null);

            try {
                const getJson = fetcher || apiRequest;

                const url = `/corporate-admin/employees`;
                const data = await getJson(url, { method: 'GET', signal: controller.signal });

                if (!mounted) return;

                let employees = Array.isArray(data) ? data : (data && Array.isArray(data.users) ? data.users : []);
                
                const leads = employees
                    .filter(emp => emp.role && emp.role.toLowerCase().includes('lead'))
                    .map(emp => ({
                        id: emp.id,
                        name: `${emp.firstName || ''} ${emp.lastName || ''}`.trim() || emp.email,
                        meta: emp.email
                    }));

                setLeadOptions(leads);

            } catch (err) {
                if (err.name === 'AbortError' || err.cause?.name === 'AbortError') return;
                console.error('Failed to load leads', err);
                setLeadsError(err.message || 'Unknown error');
                setLeadOptions([]);
            } finally {
                if (mounted) setLeadsLoading(false);
            }
        }

        loadLeads();

        return () => {
            mounted = false;
            controller.abort();
        };
    }, [companyId, fetcher]); // Removed 'leads' from dependencies
    
    
    
    function handleChange(e) {
        const { name, value, type, checked } = e.target;

        if (name === "name" || name === "description" || name === "leadId") {
            setFormData((prev) => ({ ...prev, [name]: value }));
            return;
        }

        if (name === "allowSelfJoin") {
            setFormData((prev) => ({
                ...prev,
                settings: { ...prev.settings, allowSelfJoin: checked },
            }));
            return;
        }

        if (name === "maxMembers") {
            const parsed = value === "" ? null : parseInt(value, 10);
            setFormData((prev) => ({
                ...prev,
                settings: { ...prev.settings, maxMembers: Number.isNaN(parsed) ? null : parsed },
            }));
            return;
        }

        if (name === "sessionReminders" || name === "goalUpdates") {
            const boolVal = type === "checkbox" ? checked : value;
            setFormData((prev) => ({
                ...prev,
                settings: {
                    ...prev.settings,
                    notificationPreferences: {
                        ...prev.settings.notificationPreferences,
                        [name]: !!boolVal,
                    },
                },
            }));
            return;
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (!formData.name || !formData.name.trim()) {
            window.alert("Team name is required");
            return;
        }

        setLoading(true);
        try {
            const payload = {
                name: formData.name.trim(),
                description: formData.description?.trim() || undefined,
                leadId: formData.leadId || undefined,
                settings: {
                    allowSelfJoin: !!formData.settings.allowSelfJoin,
                    maxMembers: formData.settings.maxMembers === null ? null : Number(formData.settings.maxMembers),
                    notificationPreferences: {
                        sessionReminders: !!formData.settings.notificationPreferences.sessionReminders,
                        goalUpdates: !!formData.settings.notificationPreferences.goalUpdates,
                    },
                },
            };

            await onSubmit(payload);
        } catch (err) {
            console.error(err);
            window.alert(err?.data?.message || err?.message || "Failed to create team");
        } finally {
            setLoading(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Team Name *</label>
                <input
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Engineering Team"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Describe the team's purpose and goals"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Team Lead (Optional)</label>
                <select
                    name="leadId"
                    value={formData.leadId}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                    <option value="">Select a team lead</option>
                    {leadsLoading ? (
                        <option value="" disabled>Loading team leads...</option>
                    ) : leadOptions && leadOptions.length > 0 ? (
                        leadOptions.map((l) => (
                            <option key={l.id} value={l.id}>
                                {l.name} {l.meta ? `- ${l.meta}` : ""}
                            </option>
                        ))
                    ) : (
                        <option value="" disabled>No team leads found</option>
                    )}
                </select>
                {leadsError && <p className="text-xs text-red-600 mt-1">Failed to load team leads: {String(leadsError.message)}</p>}
            </div>

            <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">Team Settings</label>

                <div className="flex items-center">
                    <input
                        name="allowSelfJoin"
                        type="checkbox"
                        checked={formData.settings.allowSelfJoin}
                        onChange={handleChange}
                        className="w-4 h-4 text-green-600 rounded focus:ring-green-500"
                    />
                    <label className="ml-2 text-sm text-gray-700">Allow employees to self-join this team</label>
                </div>

                <div>
                    <label className="block text-sm text-gray-700 mb-2">Maximum Members (Optional)</label>
                    <input
                        name="maxMembers"
                        type="number"
                        value={formData.settings.maxMembers ?? ""}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        placeholder="Unlimited"
                        min={1}
                    />
                </div>

                <div className="pt-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Notification Preferences</label>

                    <div className="flex items-center">
                        <input
                            name="sessionReminders"
                            type="checkbox"
                            checked={formData.settings.notificationPreferences.sessionReminders}
                            onChange={handleChange}
                            className="w-4 h-4 rounded"
                        />
                        <label className="ml-2 text-sm text-gray-700">Session reminders</label>
                    </div>

                    <div className="flex items-center mt-2">
                        <input
                            name="goalUpdates"
                            type="checkbox"
                            checked={formData.settings.notificationPreferences.goalUpdates}
                            onChange={handleChange}
                            className="w-4 h-4 rounded"
                        />
                        <label className="ml-2 text-sm text-gray-700">Goal updates</label>
                    </div>
                </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
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
                    {loading ? "Creating..." : "Create Team"}
                </button>
            </div>
        </form>
    );
}
