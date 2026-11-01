import LegacyWorkspaceRedirect from '../../components/workspace/LegacyWorkspaceRedirect';
import withAuth from '../../hocs/withAuth';
import { DELIVERY_ACCESS_POLICY } from '../../lib/roleRoutes';

const LegacySeniorConsultant = () => <LegacyWorkspaceRedirect workspaceId="senior-consultant" />;
export default withAuth(LegacySeniorConsultant, { ...DELIVERY_ACCESS_POLICY, workspaceRoles: ['senior_consultant'] });
