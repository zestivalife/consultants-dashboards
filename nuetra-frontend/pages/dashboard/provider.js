import { ExternalConsultantWorkspaceRoute } from '../../components/external/ExternalConsultantWorkspaceRoute';
import withAuth from '../../hocs/withAuth';
import { CONSULTANT_ACCESS_POLICY } from '../../lib/roleRoutes';

export default withAuth(ExternalConsultantWorkspaceRoute, CONSULTANT_ACCESS_POLICY);
