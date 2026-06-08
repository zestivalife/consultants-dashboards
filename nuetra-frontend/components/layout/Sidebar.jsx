import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import {
  LayoutDashboard, Users, Calendar, Activity, Settings,
  ChevronLeft, ChevronRight, Bell, Search, LogOut,
  User, Building2, Shield, Target, Apple, Heart, Menu
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

/**
 * Modern Sidebar Navigation Component
 * Inspired by modern dashboard designs with collapsible functionality
 */
const Sidebar = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const router = useRouter();
  const { user, logout } = useAuth();

  // Role-based navigation items
  const getNavigationItems = () => {
    const baseItems = [
      { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard', roles: ['ALL'] },
      { icon: Activity, label: 'Wellness', href: '/wellness', roles: ['TEAM_MEMBER', 'TEAM_LEAD'] },
      { icon: Calendar, label: 'Sessions', href: '/sessions', roles: ['ALL'] },
      { icon: Apple, label: 'Diet Plans', href: '/diet-plans', roles: ['TEAM_MEMBER', 'DIETICIAN'] },
    ];

    const roleSpecific = {
      CORPORATE_ADMIN: [
        { icon: Users, label: 'Employees', href: '/employees' },
        { icon: Building2, label: 'Teams', href: '/teams' },
        { icon: Target, label: 'Goals', href: '/goals' },
      ],
      TEAM_LEAD: [
        { icon: Users, label: 'My Team', href: '/my-team' },
        { icon: Target, label: 'Team Goals', href: '/team-goals' },
      ],
      ADMIN: [
        { icon: Building2, label: 'Companies', href: '/companies' },
        { icon: Users, label: 'Users', href: '/users' },
        { icon: Shield, label: 'Access Control', href: '/access' },
      ],
      SUPERUSER: [
        { icon: Shield, label: 'System', href: '/system' },
        { icon: Activity, label: 'Analytics', href: '/analytics' },
        { icon: Settings, label: 'Platform Settings', href: '/platform-settings' },
      ],
      DIETICIAN: [
        { icon: Users, label: 'Clients', href: '/clients' },
        { icon: Apple, label: 'Diet Plans', href: '/diet-plans' },
        { icon: Calendar, label: 'Appointments', href: '/appointments' },
      ],
    };

    const userRole = user?.role;
    const roleItems = roleSpecific[userRole] || [];
    
    return [...baseItems, ...roleItems].filter(item => 
      !item.roles || item.roles.includes('ALL') || item.roles.includes(userRole)
    );
  };

  const navigationItems = getNavigationItems();

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="flex h-screen bg-[#f8fafc]"> {/* Very light gray background for whole app */}
      {/* Sidebar - Clean Minimal Design */}
      <aside className="w-64 bg-white flex flex-col shadow-sm relative z-50 border-r border-gray-100">
        {/* Logo Section */}
        <div className="h-20 flex items-center px-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#64ae00] rounded-lg flex items-center justify-center">
              <Heart className="w-5 h-5 text-white fill-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Nuetra</h1>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 overflow-y-auto">
          <div className="space-y-1">
            {navigationItems.map((item, index) => {
              const isActive = router.pathname === item.href || 
                             router.pathname.startsWith(item.href + '/');
              const Icon = item.icon;

              return (
                <Link
                  key={index}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                    isActive
                      ? 'bg-[#64ae00] text-white font-medium'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-[#64ae00]'
                  }`}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className="text-sm">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Bottom Section */}
        <div className="p-4 space-y-2">
          <Link href="/settings" className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-[#64ae00] transition-all">
            <Settings className="w-5 h-5" />
            <span className="text-sm">Settings</span>
          </Link>
          
          {/* User Profile */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-[#64ae00] to-[#7dc41f] rounded-full flex items-center justify-center text-white font-semibold text-sm">
                {user?.firstName?.[0]}{user?.lastName?.[0]}
              </div>
              <div className="flex-1 text-left overflow-hidden">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {user?.firstName} {user?.lastName}
                </p>
                <p className="text-xs text-gray-500 truncate">{user?.role}</p>
              </div>
            </button>
            
            {/* User Menu Dropdown */}
            {showUserMenu && (
              <div className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-red-50 transition-colors text-red-600"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="text-sm">Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <header className="bg-white/70 backdrop-blur-md h-20 px-8 flex items-center justify-between sticky top-0 z-40">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-sm text-gray-500">Welcome back, {user?.firstName} 👋</h2>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-gray-600 hover:text-[#64ae00] transition-colors shadow-sm">
              <Bell className="w-5 h-5" />
            </button>
            <div className="w-10 h-10 bg-gradient-to-br from-[#64ae00] to-[#7dc41f] rounded-full flex items-center justify-center text-white font-semibold text-sm shadow-md">
              {user?.firstName?.[0]}{user?.lastName?.[0]}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Sidebar;

