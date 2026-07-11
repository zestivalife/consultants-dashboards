import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function DashboardSettingsRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/settings');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f4faff] text-sm font-semibold text-gray-500">
      Opening workspace settings...
    </div>
  );
}
