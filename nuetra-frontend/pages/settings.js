import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../lib/api';
import { getDashboardPathForRole } from '../lib/roleRoutes';
import ProtectedRoute from '../components/ProtectedRoute';
import Link from 'next/link';
import { 
  Settings as SettingsIcon,
  Bell, 
  Mail, 
  Lock, 
  Shield, 
  Moon,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Loader2,
  ArrowLeft,
  User,
  Eye,
  EyeOff
} from 'lucide-react';

function SettingsPage() {
  const router = useRouter();
  const { user: authUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('notifications');
  const [showChangePassword, setShowChangePassword] = useState(false);

  const getDashboardPath = () => {
    if (!authUser) {
      return '/dashboard/team-member'; // Fallback while loading
    }
    return getDashboardPathForRole(authUser.role, '/dashboard/team-member');
  };

  // Settings state
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      sessionReminders: true,
      goalUpdates: true,
      teamInvites: true,
    },
    privacy: {
      profileVisibility: 'team',
      showMetrics: true,
      showActivity: true,
    },
    email: {
      weeklyDigest: true,
      monthlyReport: true,
      marketing: false,
    }
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      // In a real app, fetch from API
      // For now, use defaults
      setLoading(false);
    } catch (err) {
      console.error('Settings fetch error:', err);
      setError('Failed to load settings');
      setLoading(false);
    }
  };

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      // In a real app, save to API
      // For now, just simulate
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccess('Settings saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 12) {
      setError('Password must be at least 12 characters long');
      return;
    }

    setSaving(true);
    try {
      await apiRequest('/auth/change-password', {
        method: 'POST',
        body: {
          current_password: passwordData.currentPassword,
          new_password: passwordData.newPassword,
          confirm_password: passwordData.confirmPassword,
        },
      });

      setSuccess('Password changed successfully!');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      setShowChangePassword(false);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.data?.error || err.message || 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'privacy', label: 'Privacy', icon: Shield },
    { id: 'email', label: 'Email Preferences', icon: Mail },
    { id: 'password', label: 'Change Password', icon: Lock },
  ];

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-[#64ae00]" />
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <Link href={getDashboardPath()} className="inline-flex items-center text-sm text-gray-600 hover:text-[#64ae00] mb-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-600 mt-2">Manage your account settings and preferences</p>
          </div>

          {/* Success/Error Messages */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2"
            >
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </motion.div>
          )}

          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2"
            >
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
              <span className="text-sm text-green-700">{success}</span>
            </motion.div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar Tabs */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <nav className="space-y-2">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => {
                          setActiveTab(tab.id);
                          if (tab.id === 'password') {
                            setShowChangePassword(true);
                          } else {
                            setShowChangePassword(false);
                          }
                        }}
                        className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                          activeTab === tab.id
                            ? 'bg-[#64ae00] text-white'
                            : 'text-gray-700 hover:bg-gray-50 hover:text-[#64ae00]'
                        }`}
                      >
                        <Icon className="h-5 w-5" />
                        <span className="font-medium">{tab.label}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                {/* Notifications Tab */}
                {activeTab === 'notifications' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Notification Preferences</h2>
                    <div className="space-y-6">
                      <div className="flex items-center justify-between py-4 border-b border-gray-200">
                        <div>
                          <h3 className="font-medium text-gray-900">Email Notifications</h3>
                          <p className="text-sm text-gray-600">Receive notifications via email</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.notifications.email}
                            onChange={(e) => handleSettingChange('notifications', 'email', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between py-4 border-b border-gray-200">
                        <div>
                          <h3 className="font-medium text-gray-900">Session Reminders</h3>
                          <p className="text-sm text-gray-600">Get reminded before scheduled sessions</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.notifications.sessionReminders}
                            onChange={(e) => handleSettingChange('notifications', 'sessionReminders', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between py-4 border-b border-gray-200">
                        <div>
                          <h3 className="font-medium text-gray-900">Goal Updates</h3>
                          <p className="text-sm text-gray-600">Notifications when goals are updated</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.notifications.goalUpdates}
                            onChange={(e) => handleSettingChange('notifications', 'goalUpdates', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between py-4">
                        <div>
                          <h3 className="font-medium text-gray-900">Team Invites</h3>
                          <p className="text-sm text-gray-600">Notifications for team invitations</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.notifications.teamInvites}
                            onChange={(e) => handleSettingChange('notifications', 'teamInvites', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Privacy Tab */}
                {activeTab === 'privacy' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Privacy Settings</h2>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Profile Visibility</label>
                        <select
                          value={settings.privacy.profileVisibility}
                          onChange={(e) => handleSettingChange('privacy', 'profileVisibility', e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                        >
                          <option value="public">Public</option>
                          <option value="team">Team Only</option>
                          <option value="private">Private</option>
                        </select>
                      </div>

                      <div className="flex items-center justify-between py-4 border-b border-gray-200">
                        <div>
                          <h3 className="font-medium text-gray-900">Show Metrics</h3>
                          <p className="text-sm text-gray-600">Allow others to see your wellness metrics</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.privacy.showMetrics}
                            onChange={(e) => handleSettingChange('privacy', 'showMetrics', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between py-4">
                        <div>
                          <h3 className="font-medium text-gray-900">Show Activity</h3>
                          <p className="text-sm text-gray-600">Display your activity in team feeds</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.privacy.showActivity}
                            onChange={(e) => handleSettingChange('privacy', 'showActivity', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Email Preferences Tab */}
                {activeTab === 'email' && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Email Preferences</h2>
                    <div className="space-y-6">
                      <div className="flex items-center justify-between py-4 border-b border-gray-200">
                        <div>
                          <h3 className="font-medium text-gray-900">Weekly Digest</h3>
                          <p className="text-sm text-gray-600">Receive a weekly summary of your wellness activities</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.email.weeklyDigest}
                            onChange={(e) => handleSettingChange('email', 'weeklyDigest', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between py-4 border-b border-gray-200">
                        <div>
                          <h3 className="font-medium text-gray-900">Monthly Report</h3>
                          <p className="text-sm text-gray-600">Get monthly wellness reports</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.email.monthlyReport}
                            onChange={(e) => handleSettingChange('email', 'monthlyReport', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between py-4">
                        <div>
                          <h3 className="font-medium text-gray-900">Marketing Emails</h3>
                          <p className="text-sm text-gray-600">Receive updates about new features and wellness tips</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.email.marketing}
                            onChange={(e) => handleSettingChange('email', 'marketing', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#64ae00] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#64ae00]"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Change Password Tab */}
                {(activeTab === 'password' || showChangePassword) && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Change Password</h2>
                    <form onSubmit={handleChangePassword} className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
                        <div className="relative">
                          <input
                            type={showPasswords.current ? 'text' : 'password'}
                            name="currentPassword"
                            value={passwordData.currentPassword}
                            onChange={handlePasswordChange}
                            required
                            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                            placeholder="Enter current password"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPasswords(prev => ({ ...prev, current: !prev.current }))}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                          >
                            {showPasswords.current ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
                        <div className="relative">
                          <input
                            type={showPasswords.new ? 'text' : 'password'}
                            name="newPassword"
                            value={passwordData.newPassword}
                            onChange={handlePasswordChange}
                            required
                            minLength={8}
                            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                            placeholder="Enter new password (min 8 characters)"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPasswords(prev => ({ ...prev, new: !prev.new }))}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                          >
                            {showPasswords.new ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                          </button>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Password must be at least 8 characters long</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
                        <div className="relative">
                          <input
                            type={showPasswords.confirm ? 'text' : 'password'}
                            name="confirmPassword"
                            value={passwordData.confirmPassword}
                            onChange={handlePasswordChange}
                            required
                            minLength={8}
                            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
                            placeholder="Confirm new password"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPasswords(prev => ({ ...prev, confirm: !prev.confirm }))}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                          >
                            {showPasswords.confirm ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                          </button>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4 pt-4">
                        <button
                          type="submit"
                          disabled={saving}
                          className="px-6 py-3 bg-[#64ae00] text-white rounded-lg font-medium hover:bg-[#579700] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                          {saving ? (
                            <>
                              <Loader2 className="h-5 w-5 animate-spin" />
                              <span>Changing Password...</span>
                            </>
                          ) : (
                            <>
                              <Lock className="h-5 w-5" />
                              <span>Change Password</span>
                            </>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setShowChangePassword(false);
                            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
                            setError('');
                          }}
                          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Save Button (for other tabs) */}
                {activeTab !== 'password' && (
                  <div className="mt-8 pt-6 border-t border-gray-200">
                    <button
                      onClick={handleSaveSettings}
                      disabled={saving}
                      className="px-6 py-3 bg-[#64ae00] text-white rounded-lg font-medium hover:bg-[#579700] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                      {saving ? (
                        <>
                          <Loader2 className="h-5 w-5 animate-spin" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <Save className="h-5 w-5" />
                          <span>Save Settings</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

export default SettingsPage;
