export const OWNER_ROUTE_DEFINITIONS = [
  { slug: 'command-center', moduleKey: 'dashboard', label: 'Command Center', section: 'Owner Console' },
  { slug: 'organizations', moduleKey: 'companies', label: 'Organizations', section: 'Owner Console' },
  { slug: 'people-access', moduleKey: 'users', label: 'People & Access', section: 'Owner Console' },
  { slug: 'permissions', moduleKey: 'roles', label: 'Permissions', section: 'Owner Console' },
  {
    slug: 'master-data',
    moduleKey: 'master-data',
    label: 'Master Data',
    section: 'Platform',
    hidden: process.env.NEXT_PUBLIC_ENABLE_MASTER_DATA !== 'true',
  },
  { slug: 'packages', moduleKey: 'packages', label: 'Package Builder', section: 'Owner Console' },
  { slug: 'services', moduleKey: 'services', label: 'Service Catalog', section: 'Owner Console' },
  { slug: 'practitioners', moduleKey: 'providers', label: 'Practitioners', section: 'Owner Console' },
  { slug: 'mentors', moduleKey: 'mentors', label: 'Mentors', section: 'Owner Console' },
  { slug: 'consultants', moduleKey: 'consultants', label: 'Consultants', section: 'Owner Console' },
  { slug: 'reports', moduleKey: 'reports', label: 'Reports', section: 'Owner Console' },
  { slug: 'audit', moduleKey: 'audit', label: 'Audit Logs', section: 'Owner Console' },
  { slug: 'platform-health', moduleKey: 'system', label: 'Platform Health', section: 'Owner Console' },
  { slug: 'settings', moduleKey: 'settings', label: 'Settings', section: 'Owner Console' },
];

export const OWNER_LEGACY_TAB_TO_ROUTE = {
  dashboard: 'command-center',
  companies: 'organizations',
  users: 'people-access',
  roles: 'permissions',
  master_data: 'master-data',
  packages: 'packages',
  services: 'services',
  providers: 'practitioners',
  mentors: 'mentors',
  consultants: 'consultants',
  reports: 'reports',
  audit: 'audit',
  system: 'platform-health',
  settings: 'settings',
};

export const OWNER_ROUTE_TO_LEGACY_TAB = Object.fromEntries(
  Object.entries(OWNER_LEGACY_TAB_TO_ROUTE).map(([legacyKey, routeKey]) => [routeKey, legacyKey])
);

export function getOwnerRouteBySlug(slug) {
  return OWNER_ROUTE_DEFINITIONS.find((item) => item.slug === slug) || OWNER_ROUTE_DEFINITIONS[0];
}

export function getOwnerRouteByLegacyTab(tab) {
  const slug = OWNER_LEGACY_TAB_TO_ROUTE[tab] || 'command-center';
  return getOwnerRouteBySlug(slug);
}

export function getOwnerConsolePath(slug = 'command-center') {
  return slug === 'command-center' ? '/dashboard/owner' : `/dashboard/owner/${slug}`;
}

export function getOwnerBreadcrumbs(slug = 'command-center') {
  const route = getOwnerRouteBySlug(slug);
  const crumbs = [{ label: route.section, href: '/dashboard/owner' }];
  if (route.slug !== 'command-center') {
    crumbs.push({ label: route.label, href: getOwnerConsolePath(route.slug) });
  }
  return crumbs;
}
