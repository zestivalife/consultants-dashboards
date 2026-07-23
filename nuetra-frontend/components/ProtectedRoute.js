// apps/web/frontend/components/ProtectedRoute.js
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { isRoleAllowed } from '../lib/roleRoutes';

export default function ProtectedRoute({ children, allowedRoles = [] }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push('/login');
      } else if (!isRoleAllowed(user.role, allowedRoles)) {
        router.push('/unauthorized');
      }
    }
  }, [user, isLoading, router, allowedRoles]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#64ae00]"></div>
      </div>
    );
  }

  if (
    !user ||
    !isRoleAllowed(user.role, allowedRoles)
  ) {
    return null;
  }

  return children;
}
