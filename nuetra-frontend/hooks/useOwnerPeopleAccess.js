import { useCallback, useEffect, useMemo, useState } from 'react';

import { ownerPeopleAccessAPI } from '../lib/api';

const DEFAULT_FILTERS = {
  search: '',
  role: '',
  organization_id: '',
  department_id: '',
  product_id: '',
  status: '',
  verification: '',
  page: 1,
  page_size: 20,
  sort_by: 'created_at',
  sort_order: 'desc',
  archived: false,
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
      organization_id: typeof query.organization_id === 'string' ? query.organization_id : '',
      department_id: typeof query.department_id === 'string' ? query.department_id : '',
      product_id: typeof query.product_id === 'string' ? query.product_id : '',
      status: typeof query.status === 'string' ? query.status : '',
      verification: typeof query.verification === 'string' ? query.verification : '',
      page: parsePositiveInt(query.page, 1),
      page_size: parsePositiveInt(query.page_size, 20),
      sort_by: typeof query.sort_by === 'string' ? query.sort_by : 'created_at',
      sort_order: query.sort_order === 'asc' ? 'asc' : 'desc',
      archived: query.archived === 'true',
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

function queryValue(value) {
  return Array.isArray(value) ? value[0] : value;
}

export function useOwnerPeopleAccess({ router, enabled, detailEnabled }) {
  const [summary, setSummary] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [users, setUsers] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  const peopleRouteStateKey = useMemo(() => JSON.stringify({
    search: queryValue(router.query.search) || '',
    role: queryValue(router.query.role) || '',
    organization_id: queryValue(router.query.organization_id) || '',
    department_id: queryValue(router.query.department_id) || '',
    product_id: queryValue(router.query.product_id) || '',
    status: queryValue(router.query.status) || '',
    verification: queryValue(router.query.verification) || '',
    page: queryValue(router.query.page) || '',
    page_size: queryValue(router.query.page_size) || '',
    sort_by: queryValue(router.query.sort_by) || '',
    sort_order: queryValue(router.query.sort_order) || '',
    archived: queryValue(router.query.archived) || '',
    user: queryValue(router.query.user) || '',
  }), [
    router.query.archived,
    router.query.department_id,
    router.query.organization_id,
    router.query.page,
    router.query.page_size,
    router.query.product_id,
    router.query.role,
    router.query.search,
    router.query.sort_by,
    router.query.sort_order,
    router.query.status,
    router.query.user,
    router.query.verification,
  ]);
  const peopleRouteState = useMemo(() => parsePeopleRouteState(JSON.parse(peopleRouteStateKey)), [peopleRouteStateKey]);

  const replaceCurrentQuery = useCallback((patch) => {
    const nextQuery = compactQuery(router.query, patch);
    router.replace({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
  }, [router]);

  const loadSummary = useCallback(async () => {
    const nextSummary = await ownerPeopleAccessAPI.summary();
    setSummary(nextSummary);
    return nextSummary;
  }, []);

  const loadMetadata = useCallback(async () => {
    const nextMetadata = await ownerPeopleAccessAPI.metadata();
    setMetadata(nextMetadata);
    return nextMetadata;
  }, []);

  const loadUsers = useCallback(async (nextFilters) => {
    setFilters(nextFilters);
    const response = await ownerPeopleAccessAPI.listUsers(nextFilters);
    setUsers(response?.items || []);
    setPagination(response?.pagination || null);
    setSelectedUserId((currentSelectedUserId) => {
      if (!currentSelectedUserId && response?.items?.length) {
        return response.items[0].id;
      }
      if (currentSelectedUserId && !response?.items?.some((item) => item.id === currentSelectedUserId)) {
        return response?.items?.[0]?.id || null;
      }
      return currentSelectedUserId;
    });
    return response;
  }, []);

  const loadSelectedUser = useCallback(async (userId) => {
    if (!userId) {
      setSelectedUser(null);
      return null;
    }
    setDetailLoading(true);
    try {
      const detail = await ownerPeopleAccessAPI.getUser(userId);
      setSelectedUser(detail);
      return detail;
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const refresh = useCallback(async (nextFilters = peopleRouteState.filters) => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        loadSummary(),
        loadMetadata(),
        loadUsers(nextFilters),
      ]);
    } catch (nextError) {
      setError(nextError?.message || 'Unable to load People & Access.');
    } finally {
      setLoading(false);
    }
  }, [loadMetadata, loadSummary, loadUsers, peopleRouteState.filters]);

  useEffect(() => {
    if (!router.isReady || !enabled) return;
    refresh(peopleRouteState.filters).catch(() => null);
  }, [enabled, peopleRouteState.filters, refresh, router.isReady]);

  useEffect(() => {
    if (!router.isReady || !enabled) return;
    if (!peopleRouteState.selectedUserId) return;
    setSelectedUserId(peopleRouteState.selectedUserId);
  }, [enabled, peopleRouteState.selectedUserId, router.isReady]);

  useEffect(() => {
    if (!enabled || !detailEnabled || !selectedUserId) return;
    loadSelectedUser(selectedUserId).catch((nextError) => {
      setError(nextError?.message || 'Unable to load user detail.');
    });
  }, [detailEnabled, enabled, loadSelectedUser, selectedUserId]);

  const onFilterChange = useCallback((patch) => {
    replaceCurrentQuery({
      search: patch.search !== undefined ? patch.search : peopleRouteState.filters.search,
      role: patch.role !== undefined ? patch.role : peopleRouteState.filters.role,
      organization_id: patch.organization_id !== undefined ? patch.organization_id : peopleRouteState.filters.organization_id,
      department_id: patch.department_id !== undefined ? patch.department_id : peopleRouteState.filters.department_id,
      product_id: patch.product_id !== undefined ? patch.product_id : peopleRouteState.filters.product_id,
      status: patch.status !== undefined ? patch.status : peopleRouteState.filters.status,
      verification: patch.verification !== undefined ? patch.verification : peopleRouteState.filters.verification,
      page: patch.page !== undefined ? patch.page : peopleRouteState.filters.page,
      page_size: patch.page_size !== undefined ? patch.page_size : peopleRouteState.filters.page_size,
      sort_by: patch.sort_by !== undefined ? patch.sort_by : peopleRouteState.filters.sort_by,
      sort_order: patch.sort_order !== undefined ? patch.sort_order : peopleRouteState.filters.sort_order,
      archived: patch.archived !== undefined ? patch.archived : peopleRouteState.filters.archived,
    });
  }, [peopleRouteState.filters, replaceCurrentQuery]);

  const onSelectUser = useCallback((userId) => {
    if (selectedUserId === userId) return;
    setSelectedUserId(userId);
    replaceCurrentQuery({ user: userId });
  }, [replaceCurrentQuery, selectedUserId]);

  const onCreateUser = useCallback(async (payload) => {
    const created = await ownerPeopleAccessAPI.createUser(payload);
    await refresh();
    if (created?.id) {
      onSelectUser(created.id);
      await loadSelectedUser(created.id);
    }
    return created;
  }, [loadSelectedUser, onSelectUser, refresh]);

  const onUpdateUser = useCallback(async (userId, payload) => {
    const updated = await ownerPeopleAccessAPI.updateUser(userId, payload);
    await refresh();
    if (updated?.id) {
      onSelectUser(updated.id);
      await loadSelectedUser(updated.id);
    }
    return updated;
  }, [loadSelectedUser, onSelectUser, refresh]);

  const onArchiveUser = useCallback(async (userId, reason) => {
    const updated = await ownerPeopleAccessAPI.archiveUser(userId, { reason });
    await refresh();
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return updated;
  }, [loadSelectedUser, refresh, selectedUserId]);

  const onRestoreUser = useCallback(async (userId) => {
    const updated = await ownerPeopleAccessAPI.restoreUser(userId);
    await refresh();
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return updated;
  }, [loadSelectedUser, refresh, selectedUserId]);

  const onBulkAction = useCallback(async (payload) => {
    const result = await ownerPeopleAccessAPI.bulkAction(payload);
    await refresh();
    if (selectedUserId) {
      await loadSelectedUser(selectedUserId);
    }
    return result;
  }, [loadSelectedUser, refresh, selectedUserId]);

  const onAddNote = useCallback(async (userId, body) => {
    const notes = await ownerPeopleAccessAPI.addNote(userId, body);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return notes;
  }, [loadSelectedUser, selectedUserId]);

  const onAddAttachment = useCallback(async (userId, payload) => {
    const attachments = await ownerPeopleAccessAPI.addAttachment(userId, payload);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return attachments;
  }, [loadSelectedUser, selectedUserId]);

  const onAssignProducts = useCallback(async (userId, assignments) => {
    const result = await ownerPeopleAccessAPI.assignProducts(userId, assignments);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    await refresh();
    return result;
  }, [loadSelectedUser, refresh, selectedUserId]);

  const onAssignPackages = useCallback(async (userId, assignments) => {
    const result = await ownerPeopleAccessAPI.assignPackages(userId, assignments);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    await refresh();
    return result;
  }, [loadSelectedUser, refresh, selectedUserId]);

  const onAssignServices = useCallback(async (userId, assignments) => {
    const result = await ownerPeopleAccessAPI.assignServices(userId, assignments);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    await refresh();
    return result;
  }, [loadSelectedUser, refresh, selectedUserId]);

  const onRevokeSession = useCallback(async (userId, sessionId) => {
    const result = await ownerPeopleAccessAPI.revokeSession(userId, sessionId);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return result;
  }, [loadSelectedUser, selectedUserId]);

  const onForceLogout = useCallback(async (userId) => {
    const result = await ownerPeopleAccessAPI.forceLogout(userId);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    return result;
  }, [loadSelectedUser, selectedUserId]);

  const onResetUserPassword = useCallback(async (userId) => {
    const result = await ownerPeopleAccessAPI.resetUserPassword(userId);
    if (selectedUserId === userId) {
      await loadSelectedUser(userId);
    }
    await refresh();
    return result;
  }, [loadSelectedUser, refresh, selectedUserId]);

  const onExportUsersCsv = useCallback(async () => ownerPeopleAccessAPI.exportUsersCsv(), []);

  const onImportUsers = useCallback(async (rows) => {
    const result = await ownerPeopleAccessAPI.importUsers(rows);
    await refresh();
    return result;
  }, [refresh]);

  const onUpdateRolePermissions = useCallback(async (roleId, permissionKeys) => {
    const result = await ownerPeopleAccessAPI.updateRolePermissions(roleId, permissionKeys);
    await refresh();
    return result;
  }, [refresh]);

  const onCreateRole = useCallback(async (payload) => {
    const result = await ownerPeopleAccessAPI.createRole(payload);
    await refresh();
    return result;
  }, [refresh]);

  const onCloneRole = useCallback(async (roleId, payload) => {
    const result = await ownerPeopleAccessAPI.cloneRole(roleId, payload);
    await refresh();
    return result;
  }, [refresh]);

  return {
    summary,
    metadata,
    users,
    pagination,
    filters,
    selectedUser,
    selectedUserId,
    loading,
    detailLoading,
    error,
    routeState: peopleRouteState,
    refresh,
    onFilterChange,
    onSelectUser,
    onCreateUser,
    onUpdateUser,
    onArchiveUser,
    onRestoreUser,
    onBulkAction,
    onAddNote,
    onAddAttachment,
    onAssignProducts,
    onAssignPackages,
    onAssignServices,
    onRevokeSession,
    onForceLogout,
    onResetUserPassword,
    onExportUsersCsv,
    onImportUsers,
    onUpdateRolePermissions,
    onCreateRole,
    onCloneRole,
  };
}
