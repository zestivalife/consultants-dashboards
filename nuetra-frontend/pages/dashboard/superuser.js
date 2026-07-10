import { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Building2, Shield, Sparkles, Users } from 'lucide-react';
import { useRouter } from 'next/router';

import DashboardHeader from '../../components/DashboardHeader';
import { TopNavTabs } from '../../components/dashboard';
import withAuth from '../../hocs/withAuth';
import { useAuth } from '../../context/AuthContext';
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

function SuperuserDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');

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
          <TopNavTabs activeTab={activeTab} onTabChange={handleTabChange} tabs={platformOwnerModuleTabs} className="mb-0" />
        </div>

        <div className="space-y-6">
          <OwnerSummaryBar ownerName={ownerName} />

          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28 }}>
            {activeTab === 'dashboard' && <CommandCenterModule data={platformOwnerConsoleData} />}
            {activeTab === 'companies' && <OrganizationsModule organizations={platformOwnerConsoleData.organizations} />}
            {activeTab === 'users' && <PeopleAccessModule people={platformOwnerConsoleData.people} />}
            {activeTab === 'roles' && (
              <PermissionMatrixModule
                permissionGroups={platformOwnerConsoleData.permissionGroups}
                roles={platformOwnerConsoleData.roles}
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

export default withAuth(SuperuserDashboard, ['superuser', 'super_admin']);
