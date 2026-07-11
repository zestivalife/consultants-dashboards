/**
 * withAuth — Higher-Order Component for role-based access control.
 *
 * Usage:
 *   export default withAuth(MyPage, ['corporate_client', 'corporate_admin']);
 *   export default withAuth(MyPage); // any authenticated user
 */
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { getRoleKey } from '../lib/roleRoutes';

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-[#f4faff] flex flex-col items-center justify-center gap-4">
      <div className="w-12 h-12 rounded-full border-4 border-[#237afc] border-t-transparent animate-spin" />
      <p className="text-gray-500 text-sm">Checking access…</p>
    </div>
  );
}

function RedirectScreen({ message = 'Redirecting…' }) {
  return (
    <div className="min-h-screen bg-[#f4faff] flex flex-col items-center justify-center gap-4">
      <div className="w-12 h-12 rounded-full border-4 border-[#237afc] border-t-transparent animate-spin" />
      <p className="text-gray-500 text-sm">{message}</p>
    </div>
  );
}

function UnauthorizedScreen({ role }) {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-[#f4faff] flex flex-col items-center justify-center gap-4 p-8">
      <div className="bg-white rounded-2xl p-8 shadow-lg max-w-md w-full text-center border border-red-100">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-red-500 text-2xl">🚫</span>
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">Access Denied</h1>
        <p className="text-gray-500 text-sm mb-6">
          Your role <strong>{role}</strong> does not have permission to view this page.
        </p>
        <button
          onClick={() => router.replace('/dashboard')}
          className="w-full bg-[#237afc] hover:bg-[#1a5fc7] text-white font-semibold py-3 rounded-xl transition-colors"
        >
          Go to My Dashboard
        </button>
      </div>
    </div>
  );
}

export default function withAuth(WrappedComponent, allowedRoles = []) {
  function AuthGuard(props) {
    const router = useRouter();
    const { user, isLoading } = useAuth();

    useEffect(() => {
      if (!isLoading && !user) {
        router.replace('/login');
      }
    }, [user, isLoading, router]);

    if (isLoading) return <LoadingScreen />;
    if (!user) return <RedirectScreen message="Redirecting to login…" />;

    const role = getRoleKey(user.role);
    const allowed =
      allowedRoles.length === 0 ||
      allowedRoles.map((r) => r.toLowerCase()).includes(role);

    if (!allowed) return <UnauthorizedScreen role={user.role} />;

    return <WrappedComponent {...props} />;
  }

  AuthGuard.displayName = `withAuth(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;
  return AuthGuard;
}
