import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import { getDashboardPathForRole } from '../../lib/roleRoutes';

export default function DashboardRouter() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!user) {
      router.replace('/login');
      return;
    }
    router.replace(getDashboardPathForRole(user.role));
  }, [isLoading, router, user]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0d0f12] text-white">
      <div className="rounded-[28px] border border-white/8 bg-[#111318] px-8 py-6 text-center shadow-[0_20px_60px_rgba(0,0,0,0.28)]">
        <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-[#4285F4] border-t-transparent" />
        <p className="mt-4 text-sm text-[#BDC1C6]">Routing to your operations workspace...</p>
      </div>
    </div>
  );
}
