import { ExternalConsultantWorkspaceRoute } from '../../components/external/ExternalConsultantWorkspaceRoute';
import withAuth from '../../hocs/withAuth';
import { DELIVERY_ACCESS_POLICY } from '../../lib/roleRoutes';

export default withAuth(ExternalConsultantWorkspaceRoute, { ...DELIVERY_ACCESS_POLICY, workspaceRoles: ['consultant', 'provider', 'dietician', 'dietitian', 'practitioner'] });
