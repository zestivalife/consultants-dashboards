import { useCallback, useMemo } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';

import DashboardHeader from '../DashboardHeader';
import { useAuth } from '../../context/AuthContext';
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
import { useOwnerPeopleAccess } from '../../hooks/useOwnerPeopleAccess';
import { getRoleKey } from '../../lib/roleRoutes';

const roleTitles = {
  platform_owner: 'Platform Owner',
  superuser: 'Platform Owner',
  admin: 'Admin',
};

function replaceRouteQuery(router, patch) {
  const nextQuery = { ...router.query, ...patch };
  Object.keys(nextQuery).forEach((key) => {
    if (nextQuery[key] === '' || nextQuery[key] === null || nextQuery[key] === undefined) {
      delete nextQuery[key];
    }
  });
  router.replace({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
}

export default function OwnerConsolePage({ moduleSlug = 'command-center' }) {
  const router = useRouter();
  const { user } = useAuth();
  const route = getOwnerRouteBySlug(moduleSlug);

  const ownerName = useMemo(() => {
    const firstName = user?.first_name || user?.firstName;
    const lastName = user?.last_name || user?.lastName;
    if (firstName || lastName) return [firstName, lastName].filter(Boolean).join(' ');
    if ((user?.email || '').toLowerCase() === 'lalitppaunikar26@gmail.com') return 'Lalit Paunikar';
    if ((user?.email || '').toLowerCase() === 'zestivapriyanshi@gmail.com') return 'Priyanshi';
    return user?.name || 'Platform Owner';
  }, [user]);

  const currentRoleLabel = roleTitles[getRoleKey(user?.role) || 'platform_owner'] || 'Platform Owner';
  const breadcrumbs = useMemo(() => getOwnerBreadcrumbs(route.slug), [route.slug]);
  const permissionRoleId = typeof router.query.role_id === 'string' ? router.query.role_id : '';
  const permissionQuery = typeof router.query.permission_q === 'string' ? router.query.permission_q : '';
  const shouldLoadPeopleAccess = route.moduleKey === 'users' || route.moduleKey === 'roles';

  const peopleAccess = useOwnerPeopleAccess({
    router,
    enabled: shouldLoadPeopleAccess && Boolean(user),
    detailEnabled: route.moduleKey === 'users',
  });

  const handlePermissionRoleChange = useCallback((roleId) => {
    if ((roleId || '') === permissionRoleId) return;
    replaceRouteQuery(router, { role_id: roleId || null });
  }, [permissionRoleId, router]);

  const handlePermissionQueryChange = useCallback((value) => {
    if ((value || '') === permissionQuery) return;
    replaceRouteQuery(router, { permission_q: value || null });
  }, [permissionQuery, router]);

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
            summary={peopleAccess.summary}
            metadata={peopleAccess.metadata}
            people={peopleAccess.users}
            pagination={peopleAccess.pagination}
            selectedUser={peopleAccess.selectedUser}
            loading={peopleAccess.loading}
            detailLoading={peopleAccess.detailLoading}
            error={peopleAccess.error}
            filters={peopleAccess.filters}
            invitations={peopleAccess.invitations}
            invitationPagination={peopleAccess.invitationPagination}
            onSelectUser={peopleAccess.onSelectUser}
            onFilterChange={peopleAccess.onFilterChange}
            onCreateUser={peopleAccess.onCreateUser}
            onUpdateUser={peopleAccess.onUpdateUser}
            onBulkAction={peopleAccess.onBulkAction}
            onAddNote={peopleAccess.onAddNote}
            onAddAttachment={peopleAccess.onAddAttachment}
            onCreateInvitation={peopleAccess.onCreateInvitation}
            onResendInvitation={peopleAccess.onResendInvitation}
            onCancelInvitation={peopleAccess.onCancelInvitation}
            onAssignProducts={peopleAccess.onAssignProducts}
            onAssignPackages={peopleAccess.onAssignPackages}
            onAssignServices={peopleAccess.onAssignServices}
            onRevokeSession={peopleAccess.onRevokeSession}
            onForceLogout={peopleAccess.onForceLogout}
            onExportUsersCsv={peopleAccess.onExportUsersCsv}
            onImportUsers={peopleAccess.onImportUsers}
            onRefresh={peopleAccess.refresh}
          />
        );
      case 'roles':
        return (
          <PermissionMatrixModule
            metadata={peopleAccess.metadata}
            loading={peopleAccess.loading}
            onUpdateRolePermissions={peopleAccess.onUpdateRolePermissions}
            onCreateRole={peopleAccess.onCreateRole}
            onCloneRole={peopleAccess.onCloneRole}
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
    <div className="relative min-h-screen overflow-hidden font-sans">
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
