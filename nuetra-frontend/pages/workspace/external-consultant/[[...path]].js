import { ExternalConsultantWorkspaceRoute } from '../../../components/external/ExternalConsultantWorkspaceRoute';
import withAuth from '../../../hocs/withAuth';

export default withAuth(ExternalConsultantWorkspaceRoute, { workspaceId: 'external-consultant' });
