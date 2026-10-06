import { ConsultantWorkspace } from '../../components/platform/PlatformWorkspace';
import { ExternalConsultantWorkspace } from '../../components/external/ExternalConsultantWorkspace';
import { useTenant } from '../../context/TenantContext';
import withAuth from '../../hocs/withAuth';
import { DELIVERY_ACCESS_POLICY } from '../../lib/roleRoutes';

function ConsultantDashboard(){
  const {tenantType}=useTenant();
  return tenantType&&tenantType!=='ZESTIVA_INTERNAL'?<ExternalConsultantWorkspace/>:<ConsultantWorkspace/>;
}

export default withAuth(ConsultantDashboard, { ...DELIVERY_ACCESS_POLICY, workspaceRoles: ['consultant', 'provider', 'dietician', 'dietitian', 'practitioner'] });
