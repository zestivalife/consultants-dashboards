import { ConsultantWorkspace } from '../../components/platform/PlatformWorkspace';
import withAuth from '../../hocs/withAuth';
import { CONSULTANT_ACCESS_POLICY } from '../../lib/roleRoutes';

export default withAuth(ConsultantWorkspace, CONSULTANT_ACCESS_POLICY);
