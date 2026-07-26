import withAuth from '../../../hocs/withAuth';
import OwnerConsolePage from '../../../components/platform/OwnerConsolePage';
import { getOwnerRouteBySlug } from '../../../lib/ownerConsoleRoutes';
import { OWNER_ACCESS_POLICY } from '../../../lib/roleRoutes';

function OwnerDashboardModule({ moduleSlug }) {
  return <OwnerConsolePage moduleSlug={moduleSlug} />;
}

export async function getServerSideProps(context) {
  const moduleSlug = Array.isArray(context.params?.module)
    ? context.params.module[0]
    : context.params?.module || 'command-center';
  const route = getOwnerRouteBySlug(moduleSlug);

  return {
    props: {
      moduleSlug: route.slug,
    },
  };
}

export default withAuth(OwnerDashboardModule, OWNER_ACCESS_POLICY);
