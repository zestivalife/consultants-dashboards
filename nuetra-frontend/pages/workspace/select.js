import { useRouter } from 'next/router';
import withAuth from '../../hocs/withAuth';
import { CANONICAL_WORKSPACE_PATHS, getWorkspaceAuthorities } from '../../lib/roleRoutes';
import { useAuth } from '../../context/AuthContext';

function WorkspaceSelector() {
  const router = useRouter();
  const { user } = useAuth();
  const authorities = getWorkspaceAuthorities(user) || [];
  return (
    <main className="min-h-screen bg-[#f4faff] px-6 py-16">
      <section className="mx-auto max-w-3xl rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900">Choose a workspace</h1>
        <p className="mt-2 text-sm text-gray-600">Select one of your backend-authorised roles and organisations.</p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {authorities.map((authority) => (
            <button key={`${authority.workspaceId}:${authority.tenantId || 'platform'}`} type="button"
              className="rounded-2xl border border-gray-200 p-5 text-left hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={() => router.push({ pathname: authority.landingPage || CANONICAL_WORKSPACE_PATHS[authority.workspaceId], query: authority.tenantId ? { tenant: authority.tenantId } : {} })}>
              <span className="block font-semibold text-gray-900">{authority.workspaceId.split('-').map((part) => part[0].toUpperCase() + part.slice(1)).join(' ')}</span>
              <span className="mt-1 block text-sm text-gray-600">{authority.tenantName || 'Zestiva platform'}</span>
              <span className="mt-2 block text-xs uppercase tracking-wide text-gray-500">{authority.role}</span>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}

export default withAuth(WorkspaceSelector);
