import LegacyWorkspaceRedirect from '../../components/workspace/LegacyWorkspaceRedirect';
import withAuth from '../../hocs/withAuth';
import { DELIVERY_ACCESS_POLICY } from '../../lib/roleRoutes';

const LegacyConsultant = () => <LegacyWorkspaceRedirect workspaceId="external-consultant" />;
export default withAuth(LegacyConsultant, { ...DELIVERY_ACCESS_POLICY, workspaceRoles: ['consultant', 'provider', 'dietician', 'dietitian', 'practitioner'] });
