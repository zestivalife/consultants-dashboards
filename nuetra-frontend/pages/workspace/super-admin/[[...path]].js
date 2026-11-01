import { useRouter } from 'next/router';
import OwnerConsolePage from '../../../components/platform/OwnerConsolePage';
import withAuth from '../../../hocs/withAuth';

function SuperAdminWorkspace() {
  const router = useRouter();
  const path = Array.isArray(router.query.path) ? router.query.path : [];
  return <OwnerConsolePage moduleSlug={path[0] || 'command-center'} />;
}

export default withAuth(SuperAdminWorkspace, { workspaceId: 'super-admin' });
