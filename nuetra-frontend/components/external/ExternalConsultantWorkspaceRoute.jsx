import { useTenant } from '../../context/TenantContext';
import { resolveConsultantWorkspace } from '../../lib/tenantContext.mjs';
import { ConsultantWorkspace } from '../platform/PlatformWorkspace';
import { ExternalSaaSWorkspace } from './ExternalSaaSWorkspace';

export function ExternalConsultantWorkspaceRoute() {
  const tenant = useTenant();
  const workspace = resolveConsultantWorkspace(tenant);

  if (workspace === 'EXTERNAL') return <ExternalSaaSWorkspace />;
  if (workspace === 'IN_HOUSE') return <ConsultantWorkspace />;
  if (workspace === 'LOADING') {
    return <main className="min-h-screen bg-[#f6f7f8] px-6 py-16 text-center text-sm text-slate-600">Resolving workspace access…</main>;
  }

  return <main className="min-h-screen bg-[#f6f7f8] px-6 py-16"><div role="alert" className="mx-auto max-w-xl rounded-2xl border border-red-200 bg-white p-6 text-center"><h1 className="text-xl font-semibold text-slate-950">Workspace access unavailable</h1><p className="mt-2 text-sm leading-6 text-slate-600">An active tenant membership could not be resolved. Sign out and contact your administrator if this continues.</p></div></main>;
}
