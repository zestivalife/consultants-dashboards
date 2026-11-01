import { useAuth } from '../../context/AuthContext';

export default function WorkspaceAccessDenied() {
  const { logout } = useAuth();
  return <main className="flex min-h-screen items-center justify-center bg-[#f4faff] p-6">
    <section className="max-w-lg rounded-3xl bg-white p-8 text-center shadow-sm">
      <h1 className="text-2xl font-bold text-gray-900">No active workspace membership</h1>
      <p className="mt-3 text-sm text-gray-600">Your account is authenticated, but it has no active role and tenant membership. Contact your administrator.</p>
      <button type="button" onClick={logout} className="mt-6 rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white">Sign out</button>
    </section>
  </main>;
}
