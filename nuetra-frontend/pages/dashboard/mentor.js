import { MentorWorkspace } from '../../components/platform/PlatformWorkspace';
import withAuth from '../../hocs/withAuth';
import { MENTOR_ACCESS_POLICY } from '../../lib/roleRoutes';

export default withAuth(MentorWorkspace, { ...MENTOR_ACCESS_POLICY, workspaceRoles: ['mentor', 'team_lead'] });
