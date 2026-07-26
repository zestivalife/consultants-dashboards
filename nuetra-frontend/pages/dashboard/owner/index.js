import withAuth from '../../../hocs/withAuth';
import OwnerConsolePage from '../../../components/platform/OwnerConsolePage';
import { OWNER_ACCESS_POLICY } from '../../../lib/roleRoutes';

function OwnerDashboardIndex() {
  return <OwnerConsolePage moduleSlug="command-center" />;
}

export default withAuth(OwnerDashboardIndex, OWNER_ACCESS_POLICY);
