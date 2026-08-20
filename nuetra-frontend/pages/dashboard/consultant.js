import { ConsultantWorkspace } from '../../components/platform/PlatformWorkspace';
import withAuth from '../../hocs/withAuth';
import { DELIVERY_ACCESS_POLICY } from '../../lib/roleRoutes';

export default withAuth(ConsultantWorkspace, { ...DELIVERY_ACCESS_POLICY, workspaceRoles: ['consultant', 'provider', 'dietician', 'dietitian', 'practitioner'] });
