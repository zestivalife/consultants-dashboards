import { useEffect } from 'react';
import { useRouter } from 'next/router';
import withAuth from '../../hocs/withAuth';
import { MEMBER_ACCESS_POLICY } from '../../lib/roleRoutes';

function TeamMemberWorkspaceEntry() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/profile');
  }, [router]);

  return (
    <div className="min-h-screen bg-[#f4faff] flex flex-col items-center justify-center gap-4">
      <div className="w-12 h-12 rounded-full border-4 border-[#237afc] border-t-transparent animate-spin" />
      <p className="text-gray-500 text-sm">Opening your personal workspace…</p>
    </div>
  );
}

export default withAuth(TeamMemberWorkspaceEntry, MEMBER_ACCESS_POLICY);
