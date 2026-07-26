// apps/web/frontend/components/ProtectedRoute.js
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { getAccountActionRoute, isAccessAllowed } from '../lib/roleRoutes';

export default function ProtectedRoute({ children, allowedRoles = [], accessPolicy = null }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const policy = accessPolicy || allowedRoles;

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push('/login');
      } else {
        const requiredAccountRoute = getAccountActionRoute(user);
        if (requiredAccountRoute && router.pathname.startsWith('/dashboard')) {
          router.push(requiredAccountRoute);
        } else if (!isAccessAllowed(user, policy)) {
          router.push('/unauthorized');
        }
      }
    }
  }, [user, isLoading, router, policy]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#64ae00]"></div>
      </div>
    );
  }

  if (
    !user ||
    (getAccountActionRoute(user) && router.pathname.startsWith('/dashboard')) ||
    !isAccessAllowed(user, policy)
  ) {
    return null;
  }

  return children;
}
