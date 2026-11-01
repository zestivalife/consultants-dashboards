import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { CANONICAL_WORKSPACE_PATHS } from '../../lib/roleRoutes';

export default function LegacyWorkspaceRedirect({ workspaceId }) {
  const router = useRouter();
  useEffect(() => {
    if (!router.isReady) return;
    router.replace({ pathname: CANONICAL_WORKSPACE_PATHS[workspaceId], query: router.query });
  }, [router, workspaceId]);
  return <div className="flex min-h-screen items-center justify-center">Redirecting to your workspace…</div>;
}
