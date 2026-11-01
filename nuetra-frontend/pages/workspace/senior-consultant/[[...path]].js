import { SeniorConsultantWorkspace } from '../../../components/platform/PlatformWorkspace';
import withAuth from '../../../hocs/withAuth';

export default withAuth(SeniorConsultantWorkspace, { workspaceId: 'senior-consultant' });
