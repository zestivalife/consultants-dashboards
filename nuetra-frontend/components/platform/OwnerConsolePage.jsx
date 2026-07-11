import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';

import DashboardHeader from '../DashboardHeader';
import { useAuth } from '../../context/AuthContext';
import { ownerPeopleAccessAPI } from '../../lib/api';
import {
  AuditLogsModule,
  CommandCenterModule,
  ConsultantsModule,
  MentorsModule,
  OrganizationsModule,
  PackageBuilderModule,
  PeopleAccessModule,
  PermissionMatrixModule,
  PlatformHealthModule,
  PractitionersModule,
  ReportsModule,
  ServiceCatalogModule,
  SettingsModule,
} from './OwnerConsoleModules';
import OwnerConsoleLayout from './OwnerConsoleLayout';
import { platformOwnerConsoleData } from '../../data/platformOwnerConsoleData';
import { getOwnerBreadcrumbs, getOwnerRouteBySlug } from '../../lib/ownerConsoleRoutes';

const roleTitles = {
  platform_owner: 'Platform Owner',
  superuser: 'Platform Owner',
  admin: 'Admin',
};

function parsePositiveInt(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function parsePeopleRouteState(query) {
  return {
    filters: {
      search: typeof query.search === 'string' ? query.search : '',
      role: typeof query.role === 'string' ? query.role : '',
      product_id: typeof query.product_id === 'string' ? query.product_id : '',
      status: typeof query.status === 'string' ? query.status : '',
      verification: typeof query.verification === 'string' ? query.verification : '',
      page: parsePositiveInt(query.page, 1),
      page_size: parsePositiveInt(query.page_size, 20),
      sort_by: typeof query.sort_by === 'string' ? query.sort_by : 'created_at',
      sort_order: query.sort_order === 'asc' ? 'asc' : 'desc',
    },
    selectedUserId: typeof query.user === 'string' ? query.user : null,
  };
}

function compactQuery(currentQuery, patch) {
  const nextQuery = { ...currentQuery, ...patch };
  Object.keys(nextQuery).forEach((key) => {
    const value = nextQuery[key];
    if (
      value === '' ||
      value === null ||
      value === undefined ||
      value === false ||
      (Array.isArray(value) && value.length === 0)
    ) {
      delete nextQuery[key];
    }
  });
  return nextQuery;
}

export default function OwnerConsolePage({ moduleSlug = 'command-center' }) {
  const router = useRouter();
  const { user } = useAuth();
  const route = getOwnerRouteBySlug(moduleSlug);
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

  const currentRoleLabel = roleTitles[(user?.role || 'platform_owner').toLowerCase()] || 'Platform Owner';
  const breadcrumbs = useMemo(() => getOwnerBreadcrumbs(route.slug), [route.slug]);
  const peopleRouteState = useMemo(() => parsePeopleRouteState(router.query), [router.query]);
  const permissionRoleId = typeof router.query.role_id === 'string' ? router.query.role_id : '';
  const permissionQuery = typeof router.query.permission_q === 'string' ? router.query.permission_q : '';
  const shouldLoadPeopleAccess = route.moduleKey === 'users' || route.moduleKey === 'roles';

  const replaceCurrentQuery = useCallback((patch) => {
    const nextQuery = compactQuery(router.query, patch);
    router.replace({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
  }, [router]);

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

  const loadPeopleAccessUsers = useCallback(async (nextFilters) => {
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
  }, [selectedUserId]);

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

  const refreshPeopleAccess = useCallback(async (nextFilters = peopleRouteState.filters) => {
    setPeopleAccessLoading(true);
    setPeopleAccessError(null);
    try {
      await Promise.all([
        loadPeopleAccessSummary(),
        loadPeopleAccessMetadata(),
        loadPeopleAccessUsers(nextFilters),
        loadInvitations(),
      ]);
    } catch (error) {
      setPeopleAccessError(error?.message || 'Unable to load People & Access.');
    } finally {
      setPeopleAccessLoading(false);
    }
  }, [loadInvitations, loadPeopleAccessMetadata, loadPeopleAccessSummary, loadPeopleAccessUsers, peopleRouteState.filters]);

  useEffect(() => {
    if (!router.isReady || !user || !shouldLoadPeopleAccess) return;
    setSelectedUserId(peopleRouteState.selectedUserId);
    refreshPeopleAccess(peopleRouteState.filters).catch(() => null);
  }, [peopleRouteState.filters, peopleRouteState.selectedUserId, refreshPeopleAccess, router.isReady, shouldLoadPeopleAccess, user]);

  useEffect(() => {
    if (!shouldLoadPeopleAccess || route.moduleKey !== 'users' || !selectedUserId) return;
    loadSelectedUser(selectedUserId).catch((error) => {
      setPeopleAccessError(error?.message || 'Unable to load user detail.');
    });
  }, [loadSelectedUser, route.moduleKey, selectedUserId, shouldLoadPeopleAccess]);

  const handlePeopleFilterChange = useCallback((patch) => {
    replaceCurrentQuery({
      search: patch.search !== undefined ? patch.search : peopleRouteState.filters.search,
      role: patch.role !== undefined ? patch.role : peopleRouteState.filters.role,
      product_id: patch.product_id !== undefined ? patch.product_id : peopleRouteState.filters.product_id,
      status: patch.status !== undefined ? patch.status : peopleRouteState.filters.status,
      verification: patch.verification !== undefined ? patch.verification : peopleRouteState.filters.verification,
      page: patch.page !== undefined ? patch.page : peopleRouteState.filters.page,
      page_size: patch.page_size !== undefined ? patch.page_size : peopleRouteState.filters.page_size,
      sort_by: patch.sort_by !== undefined ? patch.sort_by : peopleRouteState.filters.sort_by,
      sort_order: patch.sort_order !== undefined ? patch.sort_order : peopleRouteState.filters.sort_order,
    });
  }, [peopleRouteState.filters, replaceCurrentQuery]);

  const handleSelectUser = useCallback((userId) => {
    if (selectedUserId === userId) return;
    setSelectedUserId(userId);
    replaceCurrentQuery({ user: userId });
  }, [replaceCurrentQuery, selectedUserId]);

  const handleCreateUser = useCallback(async (payload) => {
    const created = await ownerPeopleAccessAPI.createUser(payload);
    await refreshPeopleAccess();
    if (created?.id) {
      handleSelectUser(created.id);
      await loadSelectedUser(created.id);
    }
    return created;
  }, [handleSelectUser, loadSelectedUser, refreshPeopleAccess]);

  const handleUpdateUser = useCallback(async (userId, payload) => {
    const updated = await ownerPeopleAccessAPI.updateUser(userId, payload);
    await refreshPeopleAccess();
    if (updated?.id) {
      handleSelectUser(updated.id);
      await loadSelectedUser(updated.id);
    }
    return updated;
  }, [handleSelectUser, loadSelectedUser, refreshPeopleAccess]);

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

  const handlePermissionRoleChange = useCallback((roleId) => {
    if ((roleId || '') === permissionRoleId) return;
    replaceCurrentQuery({ role_id: roleId || null });
  }, [permissionRoleId, replaceCurrentQuery]);

  const handlePermissionQueryChange = useCallback((value) => {
    if ((value || '') === permissionQuery) return;
    replaceCurrentQuery({ permission_q: value || null });
  }, [permissionQuery, replaceCurrentQuery]);

  const consultants = useMemo(
    () => platformOwnerConsoleData.practitioners.filter((person) => /consultant/i.test(person.title)),
    []
  );

  const renderModule = () => {
    switch (route.moduleKey) {
      case 'dashboard':
        return <CommandCenterModule data={platformOwnerConsoleData} />;
      case 'companies':
        return <OrganizationsModule organizations={platformOwnerConsoleData.organizations} />;
      case 'users':
        return (
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
            onSelectUser={handleSelectUser}
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
        );
      case 'roles':
        return (
          <PermissionMatrixModule
            metadata={peopleAccessMetadata}
            loading={peopleAccessLoading}
            onUpdateRolePermissions={handleUpdateRolePermissions}
            onCreateRole={handleCreateRole}
            onCloneRole={handleCloneRole}
            selectedRoleId={permissionRoleId}
            onSelectedRoleChange={handlePermissionRoleChange}
            searchQuery={permissionQuery}
            onSearchQueryChange={handlePermissionQueryChange}
          />
        );
      case 'packages':
        return <PackageBuilderModule packages={platformOwnerConsoleData.packages} />;
      case 'services':
        return <ServiceCatalogModule services={platformOwnerConsoleData.services} />;
      case 'providers':
        return <PractitionersModule practitioners={platformOwnerConsoleData.practitioners} />;
      case 'consultants':
        return <ConsultantsModule consultants={consultants} />;
      case 'mentors':
        return <MentorsModule mentors={platformOwnerConsoleData.mentors} />;
      case 'reports':
        return <ReportsModule reports={platformOwnerConsoleData.reports} />;
      case 'audit':
        return <AuditLogsModule auditLogs={platformOwnerConsoleData.auditLogs} />;
      case 'system':
        return <PlatformHealthModule />;
      case 'settings':
        return <SettingsModule settings={platformOwnerConsoleData.settings} />;
      default:
        return <CommandCenterModule data={platformOwnerConsoleData} />;
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden font-sans">
      <div className="absolute inset-0 bg-[#f4faff]">
        <div className="absolute -left-[420px] -top-[420px] h-[980px] w-[980px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255, 208, 208, 0.82) 0%, rgba(255, 220, 220, 0.36) 44%, transparent 72%)', filter: 'blur(88px)' }} />
        <div className="absolute -right-[90px] top-[60px] h-[820px] w-[820px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255, 225, 208, 0.72) 0%, rgba(255, 236, 220, 0.28) 50%, transparent 74%)', filter: 'blur(74px)' }} />
        <div className="absolute bottom-[-260px] right-[-320px] h-[900px] w-[900px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(214, 235, 255, 0.84) 0%, rgba(225, 242, 255, 0.28) 46%, transparent 72%)', filter: 'blur(92px)' }} />
      </div>

      <div className="relative z-[100]">
        <DashboardHeader
          searchPlaceholder="Search organizations, users, packages, services, reports, or audits..."
          showNavLinks={false}
          allowSettingsMenu={false}
          breadcrumbs={breadcrumbs}
          workspaceLabel={`${ownerName} · ${currentRoleLabel}`}
          quickActionLabel="Quick create"
        />
      </div>

      <OwnerConsoleLayout activeSlug={route.slug}>
        <motion.div
          key={route.slug}
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.22 }}
        >
          {renderModule()}
        </motion.div>
      </OwnerConsoleLayout>
    </div>
  );
}
