import { SeniorConsultantWorkspace } from '../../components/platform/PlatformWorkspace';
import withAuth from '../../hocs/withAuth';
import { DELIVERY_ACCESS_POLICY } from '../../lib/roleRoutes';

export default withAuth(SeniorConsultantWorkspace, { ...DELIVERY_ACCESS_POLICY, workspaceRoles: ['senior_consultant'] });
