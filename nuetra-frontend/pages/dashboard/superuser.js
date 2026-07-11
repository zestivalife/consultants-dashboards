import { useEffect } from 'react';
import { useRouter } from 'next/router';

import withAuth from '../../hocs/withAuth';
import { getOwnerConsolePath, getOwnerRouteByLegacyTab } from '../../lib/ownerConsoleRoutes';

function SuperuserLegacyRoute() {
  const router = useRouter();

  useEffect(() => {
    if (!router.isReady) return;
    const legacyTab = typeof router.query.tab === 'string' ? router.query.tab : 'dashboard';
    const route = getOwnerRouteByLegacyTab(legacyTab);
    const nextQuery = { ...router.query };
    delete nextQuery.tab;
    router.replace(
      {
        pathname: getOwnerConsolePath(route.slug),
        query: nextQuery,
      },
      undefined,
      { shallow: true }
    );
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f4faff] text-gray-700">
      <div className="rounded-[28px] border border-white/70 bg-white/90 px-8 py-6 text-center shadow-sm backdrop-blur">
        <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-[#237afc] border-t-transparent" />
        <p className="mt-4 text-sm font-semibold">Routing to the Platform Owner console...</p>
      </div>
    </div>
  );
}

export default withAuth(SuperuserLegacyRoute, ['superuser', 'super_admin', 'platform_owner']);
