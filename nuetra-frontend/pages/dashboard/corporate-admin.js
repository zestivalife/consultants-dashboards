import { OrganizationWorkspace } from '../../components/platform/PlatformWorkspace';
import withAuth from '../../hocs/withAuth';
import { ORGANIZATION_ACCESS_POLICY } from '../../lib/roleRoutes';

export default withAuth(OrganizationWorkspace, { ...ORGANIZATION_ACCESS_POLICY, workspaceRoles: ['organization_admin', 'corporate_admin', 'corporate_client'] });
