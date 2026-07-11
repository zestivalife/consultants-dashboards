import withAuth from '../../../hocs/withAuth';
import OwnerConsolePage from '../../../components/platform/OwnerConsolePage';

function OwnerDashboardIndex() {
  return <OwnerConsolePage moduleSlug="command-center" />;
}

export default withAuth(OwnerDashboardIndex, ['superuser', 'super_admin', 'platform_owner']);
