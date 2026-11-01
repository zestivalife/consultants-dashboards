import { useAuth } from '../../context/AuthContext';

export default function WorkspaceServiceUnavailable() {
  const { refreshSession, isLoading } = useAuth();
  return <main className="flex min-h-screen items-center justify-center bg-[#f4faff] p-6">
    <section className="max-w-lg rounded-3xl bg-white p-8 text-center shadow-sm">
      <h1 className="text-2xl font-bold text-gray-900">Workspace access is temporarily unavailable</h1>
      <p className="mt-3 text-sm text-gray-600">Your session was not classified as a missing membership. Retry when the membership service is available.</p>
      <button type="button" disabled={isLoading} onClick={() => refreshSession()}
        className="mt-6 rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white disabled:opacity-50">
        {isLoading ? 'Checking…' : 'Retry'}
      </button>
    </section>
  </main>;
}
