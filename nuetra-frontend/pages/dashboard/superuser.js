import { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Building2, Shield, Sparkles, Users } from 'lucide-react';
import { useRouter } from 'next/router';

import DashboardHeader from '../../components/DashboardHeader';
import withAuth from '../../hocs/withAuth';
import { useAuth } from '../../context/AuthContext';
import { ownerPeopleAccessAPI } from '../../lib/api';
import {
  CommandCenterModule,
  OrganizationsModule,
  PeopleAccessModule,
  PermissionMatrixModule,
  PackageBuilderModule,
  ServiceCatalogModule,
  PractitionersModule,
  MentorsModule,
  ReportsModule,
  AuditLogsModule,
  SettingsModule,
  PlatformHealthModule,
} from '../../components/platform/OwnerConsoleModules';
import { platformOwnerConsoleData, platformOwnerModuleTabs } from '../../data/platformOwnerConsoleData';

const roleTitles = {
  platform_owner: 'Platform Owner',
  superuser: 'Platform Owner',
  admin: 'Admin',
};

const cn = (...values) => values.filter(Boolean).join(' ');

const ownerNavigationGroups = [
  {
    key: 'operations',
    label: 'Operations',
    description: 'Platform command, organizations, and daily execution.',
    tabs: ['dashboard', 'companies'],
  },
  {
    key: 'people',
    label: 'People & Access',
    description: 'Identity, authority, sessions, and governance.',
    tabs: ['users', 'roles'],
  },
  {
    key: 'catalog',
    label: 'Catalog',
    description: 'Packages and reusable service definitions.',
    tabs: ['packages', 'services'],
  },
  {
    key: 'delivery',
    label: 'Care Team',
    description: 'Practitioners, mentors, and operating capacity.',
    tabs: ['providers', 'mentors'],
  },
  {
    key: 'insights',
    label: 'Insights',
    description: 'Performance reporting and audit visibility.',
    tabs: ['reports', 'audit'],
  },
  {
    key: 'workspace',
    label: 'Workspace',
    description: 'Platform health, settings, and admin controls.',
    tabs: ['system', 'settings'],
  },
];

function OwnerSummaryBar({ ownerName }) {
  const organizations = platformOwnerConsoleData.organizations;
  const people = platformOwnerConsoleData.people;

  return (
    <div className="bg-white border border-[#f2f2f7] rounded-3xl p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-[11px] font-black uppercase tracking-[0.24em] text-[#237afc]">
            <Shield className="h-3.5 w-3.5" />
            Platform owner workspace
          </div>
          <h1 className="mt-4 text-3xl font-black tracking-tight text-gray-900">
            Enterprise operations console for {ownerName}
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-gray-500">
            Manage organizations, people, authorities, packages, services, mentors, practitioners, reports, and settings from one workspace.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            {
              icon: Building2,
              label: 'Organizations',
              value: organizations.length,
              tone: 'from-[#237afc] to-[#58b6ff]',
            },
            {
              icon: Users,
              label: 'People',
              value: people.length,
              tone: 'from-emerald-500 to-teal-500',
            },
            {
              icon: Sparkles,
              label: 'Packages',
              value: platformOwnerConsoleData.packages.length,
              tone: 'from-violet-500 to-fuchsia-500',
            },
            {
              icon: Shield,
              label: 'Roles',
              value: platformOwnerConsoleData.roles.length,
              tone: 'from-amber-500 to-orange-500',
            },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl border border-gray-100 bg-gradient-to-br from-white to-gray-50 p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.24em] text-gray-400">{item.label}</p>
                  <p className="mt-3 text-2xl font-black tracking-tight text-gray-900">{item.value}</p>
                </div>
                <div className={`rounded-2xl bg-gradient-to-br ${item.tone} p-3 text-white shadow-sm`}>
                  <item.icon className="h-4 w-4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function OwnerConsoleNav({ activeTab, onTabChange }) {
  const activeGroup =
    ownerNavigationGroups.find((group) => group.tabs.includes(activeTab)) || ownerNavigationGroups[0];

  const secondaryTabs = activeGroup.tabs
    .map((key) => platformOwnerModuleTabs.find((tab) => tab.key === key))
    .filter(Boolean);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        {ownerNavigationGroups.map((group) => {
          const isActive = group.key === activeGroup.key;
          return (
            <button
              key={group.key}
              type="button"
              onClick={() => onTabChange(group.tabs[0])}
              className={cn(
                'rounded-2xl border px-4 py-3 text-left transition-all',
                isActive
                  ? 'border-[#237afc] bg-[#f5f9ff] shadow-sm'
                  : 'border-gray-200 bg-white hover:border-[#237afc]/40 hover:bg-[#fbfdff]'
              )}
            >
              <p className={cn('text-sm font-black', isActive ? 'text-[#237afc]' : 'text-gray-900')}>{group.label}</p>
              <p className="mt-1 text-xs text-gray-500">{group.description}</p>
            </button>
          );
        })}
      </div>

      <div className="rounded-3xl border border-gray-100 bg-white/90 p-3 shadow-sm">
        <div className="flex flex-wrap gap-2">
          {secondaryTabs.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => onTabChange(tab.key)}
                className={cn(
                  'rounded-full px-4 py-2 text-sm font-bold transition-all',
                  isActive
                    ? 'bg-[#237afc] text-white shadow-sm'
                    : 'border border-gray-200 bg-white text-gray-600 hover:border-[#237afc] hover:text-[#237afc]'
                )}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SuperuserDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [peopleAccessSummary, setPeopleAccessSummary] = useState(null);
  const [peopleAccessMetadata, setPeopleAccessMetadata] = useState(null);
  const [peopleAccessUsers, setPeopleAccessUsers] = useState([]);
  const [peopleAccessPagination, setPeopleAccessPagination] = useState(null);
  const [peopleAccessInvitations, setPeopleAccessInvitations] = useState([]);
  const [peopleAccessInvitationPagination, setPeopleAccessInvitationPagination] = useState(null);
  const [peopleAccessFilters, setPeopleAccessFilters] = useState({
    search: '',
    role: '',
    product_id: '',
    status: '',
    verification: '',
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
  });
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [peopleAccessLoading, setPeopleAccessLoading] = useState(false);
  const [peopleDetailLoading, setPeopleDetailLoading] = useState(false);
  const [peopleAccessError, setPeopleAccessError] = useState(null);

  const ownerName = useMemo(() => {
    const firstName = user?.first_name || user?.firstName;
    const lastName = user?.last_name || user?.lastName;
    if (firstName || lastName) return [firstName, lastName].filter(Boolean).join(' ');
    if ((user?.email || '').toLowerCase() === 'lalitppaunikar26@gmail.com') return 'Lalit Paunikar';
    if ((user?.email || '').toLowerCase() === 'zestivapriyanshi@gmail.com') return 'Priyanshi';
    return user?.name || 'Platform Owner';
  }, [user]);

  useEffect(() => {
    if (!router.isReady) return;
    const tabFromQuery = typeof router.query.tab === 'string' ? router.query.tab : 'dashboard';
    if (platformOwnerModuleTabs.some((tab) => tab.key === tabFromQuery) && tabFromQuery !== activeTab) {
      setActiveTab(tabFromQuery);
    }
  }, [activeTab, router.isReady, router.query.tab]);

  const handleTabChange = useCallback((nextTab) => {
    setActiveTab(nextTab);
    const nextQuery = nextTab === 'dashboard' ? {} : { tab: nextTab };
    router.replace({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
  }, [router]);

  const currentRoleLabel = roleTitles[(user?.role || 'platform_owner').toLowerCase()] || 'Platform Owner';

  const loadPeopleAccessSummary = useCallback(async () => {
    const summary = await ownerPeopleAccessAPI.summary();
    setPeopleAccessSummary(summary);
    return summary;
  }, []);

  const loadPeopleAccessMetadata = useCallback(async () => {
    const metadata = await ownerPeopleAccessAPI.metadata();
    setPeopleAccessMetadata(metadata);
    return metadata;
  }, []);

  const loadPeopleAccessUsers = useCallback(async (overrides = {}) => {
    const nextFilters = { ...peopleAccessFilters, ...overrides };
    setPeopleAccessFilters(nextFilters);
    const response = await ownerPeopleAccessAPI.listUsers(nextFilters);
    setPeopleAccessUsers(response?.items || []);
    setPeopleAccessPagination(response?.pagination || null);
    if (!selectedUserId && response?.items?.length) {
      setSelectedUserId(response.items[0].id);
    } else if (selectedUserId && !response?.items?.some((item) => item.id === selectedUserId)) {
      setSelectedUserId(response?.items?.[0]?.id || null);
    }
    return response;
  }, [peopleAccessFilters, selectedUserId]);

  const loadSelectedUser = useCallback(async (userId) => {
    if (!userId) {
      setSelectedUser(null);
      return null;
    }
    setPeopleDetailLoading(true);
    try {
      const detail = await ownerPeopleAccessAPI.getUser(userId);
      setSelectedUser(detail);
      return detail;
    } finally {
      setPeopleDetailLoading(false);
    }
  }, []);

  const loadInvitations = useCallback(async (params = {}) => {
    const response = await ownerPeopleAccessAPI.listInvitations(params);
    setPeopleAccessInvitations(response?.items || []);
    setPeopleAccessInvitationPagination(response?.pagination || null);
    return response;
  }, []);

  const refreshPeopleAccess = useCallback(async (userOverrides = {}) => {
    setPeopleAccessLoading(true);
    setPeopleAccessError(null);
    try {
      await Promise.all([
        loadPeopleAccessSummary(),
        loadPeopleAccessMetadata(),
        loadPeopleAccessUsers(userOverrides),
        loadInvitations(),
      ]);
    } catch (error) {
      setPeopleAccessError(error?.message || 'Unable to load People & Access.');
    } finally {
      setPeopleAccessLoading(false);
    }
  }, [loadInvitations, loadPeopleAccessMetadata, loadPeopleAccessSummary, loadPeopleAccessUsers]);

  useEffect(() => {
    if (!user) return;
    refreshPeopleAccess().catch(() => null);
  }, [refreshPeopleAccess, user]);

  useEffect(() => {
    if (!selectedUserId) return;
    loadSelectedUser(selectedUserId).catch((error) => {
      setPeopleAccessError(error?.message || 'Unable to load user detail.');
    });
  }, [loadSelectedUser, selectedUserId]);

  const handlePeopleFilterChange = useCallback((patch) => {
    refreshPeopleAccess({ ...patch, page: patch.page || 1 }).catch((error) => {
      setPeopleAccessError(error?.message || 'Unable to update People & Access filters.');
    });
  }, [refreshPeopleAccess]);

  const handleCreateUser = useCallback(async (payload) => {
    const created = await ownerPeopleAccessAPI.createUser(payload);
    await refreshPeopleAccess();
    if (created?.id) {
      setSelectedUserId(created.id);
      await loadSelectedUser(created.id);
    }
    return created;
  }, [loadSelectedUser, refreshPeopleAccess]);

  const handleUpdateUser = useCallback(async (userId, payload) => {
    const updated = await ownerPeopleAccessAPI.updateUser(userId, payload);
    await refreshPeopleAccess();
    if (updated?.id) {
      setSelectedUserId(updated.id);
      await loadSelectedUser(updated.id);
    }
    return updated;
  }, [loadSelectedUser, refreshPeopleAccess]);

  const handleBulkAction = useCallback(async (payload) => {
    const result = await ownerPeopleAccessAPI.bulkAction(payload);
    await refreshPeopleAccess();
    if (selectedUserId) {
      await loadSelectedUser(selectedUserId);
    }
    return result;
  }, [loadSelectedUser, refreshPeopleAccess, selectedUserId]);

  const handleAddNote = useCallback(async (userId, body) => {
    const notes = await ownerPeopleAccessAPI.addNote(userId, body);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return notes;
  }, [loadSelectedUser, selectedUserId]);

  const handleAddAttachment = useCallback(async (userId, payload) => {
    const attachments = await ownerPeopleAccessAPI.addAttachment(userId, payload);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return attachments;
  }, [loadSelectedUser, selectedUserId]);

  const handleCreateInvitation = useCallback(async (payload) => {
    const invitation = await ownerPeopleAccessAPI.createInvitation(payload);
    await loadInvitations();
    return invitation;
  }, [loadInvitations]);

  const handleResendInvitation = useCallback(async (invitationId) => {
    const invitation = await ownerPeopleAccessAPI.resendInvitation(invitationId);
    await loadInvitations();
    return invitation;
  }, [loadInvitations]);

  const handleCancelInvitation = useCallback(async (invitationId) => {
    const invitation = await ownerPeopleAccessAPI.cancelInvitation(invitationId);
    await loadInvitations();
    return invitation;
  }, [loadInvitations]);

  const handleAssignProducts = useCallback(async (userId, assignments) => {
    const result = await ownerPeopleAccessAPI.assignProducts(userId, assignments);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    await refreshPeopleAccess();
    return result;
  }, [loadSelectedUser, refreshPeopleAccess, selectedUserId]);

  const handleAssignPackages = useCallback(async (userId, assignments) => {
    const result = await ownerPeopleAccessAPI.assignPackages(userId, assignments);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    await refreshPeopleAccess();
    return result;
  }, [loadSelectedUser, refreshPeopleAccess, selectedUserId]);

  const handleAssignServices = useCallback(async (userId, assignments) => {
    const result = await ownerPeopleAccessAPI.assignServices(userId, assignments);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    await refreshPeopleAccess();
    return result;
  }, [loadSelectedUser, refreshPeopleAccess, selectedUserId]);

  const handleRevokeSession = useCallback(async (userId, sessionId) => {
    const result = await ownerPeopleAccessAPI.revokeSession(userId, sessionId);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return result;
  }, [loadSelectedUser, selectedUserId]);

  const handleForceLogout = useCallback(async (userId) => {
    const result = await ownerPeopleAccessAPI.forceLogout(userId);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return result;
  }, [loadSelectedUser, selectedUserId]);

  const handleExportUsersCsv = useCallback(async () => ownerPeopleAccessAPI.exportUsersCsv(), []);

  const handleImportUsers = useCallback(async (rows) => {
    const result = await ownerPeopleAccessAPI.importUsers(rows);
    await refreshPeopleAccess();
    return result;
  }, [refreshPeopleAccess]);

  const handleUpdateRolePermissions = useCallback(async (roleId, permissionKeys) => {
    const result = await ownerPeopleAccessAPI.updateRolePermissions(roleId, permissionKeys);
    await refreshPeopleAccess();
    return result;
  }, [refreshPeopleAccess]);

  const handleCreateRole = useCallback(async (payload) => {
    const result = await ownerPeopleAccessAPI.createRole(payload);
    await refreshPeopleAccess();
    return result;
  }, [refreshPeopleAccess]);

  const handleCloneRole = useCallback(async (roleId, payload) => {
    const result = await ownerPeopleAccessAPI.cloneRole(roleId, payload);
    await refreshPeopleAccess();
    return result;
  }, [refreshPeopleAccess]);

  return (
    <div className="min-h-screen relative overflow-hidden font-sans">
      <div className="absolute inset-0 bg-[#f4faff]">
        <div className="absolute -left-[420px] -top-[420px] h-[980px] w-[980px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255, 208, 208, 0.82) 0%, rgba(255, 220, 220, 0.36) 44%, transparent 72%)', filter: 'blur(88px)' }} />
        <div className="absolute -right-[90px] top-[60px] h-[820px] w-[820px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255, 225, 208, 0.72) 0%, rgba(255, 236, 220, 0.28) 50%, transparent 74%)', filter: 'blur(74px)' }} />
        <div className="absolute bottom-[-260px] right-[-320px] h-[900px] w-[900px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(214, 235, 255, 0.84) 0%, rgba(225, 242, 255, 0.28) 46%, transparent 72%)', filter: 'blur(92px)' }} />
      </div>

      <div className="relative z-[100]">
        <DashboardHeader searchPlaceholder="Search organizations, users, packages, reports, audits..." />
      </div>

      <div className="relative z-10 mx-auto max-w-[1600px] px-4 pb-20 pt-6 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-col gap-4 rounded-3xl border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-gray-400">
                Nuetra + Fiteatsy · {currentRoleLabel}
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Existing routing preserved. Module UX extended for enterprise management workflows.
              </p>
            </div>
          </div>
          <OwnerConsoleNav activeTab={activeTab} onTabChange={handleTabChange} />
        </div>

        <div className="space-y-6">
          <OwnerSummaryBar ownerName={ownerName} />

          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28 }}>
            {activeTab === 'dashboard' && <CommandCenterModule data={platformOwnerConsoleData} />}
            {activeTab === 'companies' && <OrganizationsModule organizations={platformOwnerConsoleData.organizations} />}
            {activeTab === 'users' && (
              <PeopleAccessModule
                summary={peopleAccessSummary}
                metadata={peopleAccessMetadata}
                people={peopleAccessUsers}
                pagination={peopleAccessPagination}
                selectedUser={selectedUser}
                loading={peopleAccessLoading}
                detailLoading={peopleDetailLoading}
                error={peopleAccessError}
                filters={peopleAccessFilters}
                invitations={peopleAccessInvitations}
                invitationPagination={peopleAccessInvitationPagination}
                onSelectUser={setSelectedUserId}
                onFilterChange={handlePeopleFilterChange}
                onCreateUser={handleCreateUser}
                onUpdateUser={handleUpdateUser}
                onBulkAction={handleBulkAction}
                onAddNote={handleAddNote}
                onAddAttachment={handleAddAttachment}
                onCreateInvitation={handleCreateInvitation}
                onResendInvitation={handleResendInvitation}
                onCancelInvitation={handleCancelInvitation}
                onAssignProducts={handleAssignProducts}
                onAssignPackages={handleAssignPackages}
                onAssignServices={handleAssignServices}
                onRevokeSession={handleRevokeSession}
                onForceLogout={handleForceLogout}
                onExportUsersCsv={handleExportUsersCsv}
                onImportUsers={handleImportUsers}
                onRefresh={refreshPeopleAccess}
              />
            )}
            {activeTab === 'roles' && (
              <PermissionMatrixModule
                metadata={peopleAccessMetadata}
                loading={peopleAccessLoading}
                onUpdateRolePermissions={handleUpdateRolePermissions}
                onCreateRole={handleCreateRole}
                onCloneRole={handleCloneRole}
                onRefresh={refreshPeopleAccess}
              />
            )}
            {activeTab === 'packages' && <PackageBuilderModule packages={platformOwnerConsoleData.packages} />}
            {activeTab === 'services' && <ServiceCatalogModule services={platformOwnerConsoleData.services} />}
            {activeTab === 'providers' && <PractitionersModule practitioners={platformOwnerConsoleData.practitioners} />}
            {activeTab === 'mentors' && <MentorsModule mentors={platformOwnerConsoleData.mentors} />}
            {activeTab === 'reports' && <ReportsModule reports={platformOwnerConsoleData.reports} />}
            {activeTab === 'audit' && <AuditLogsModule auditLogs={platformOwnerConsoleData.auditLogs} />}
            {activeTab === 'system' && <PlatformHealthModule />}
            {activeTab === 'settings' && <SettingsModule settings={platformOwnerConsoleData.settings} />}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default withAuth(SuperuserDashboard, ['superuser', 'super_admin', 'platform_owner']);
