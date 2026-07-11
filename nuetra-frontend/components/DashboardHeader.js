// nuetra-frontend/components/DashboardHeader.js
import React, { useMemo, useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import Image from 'next/image';
import {
  Activity,
  ChevronDown,
  Command,
  ExternalLink,
  FileText,
  LifeBuoy,
  Menu,
  Moon,
  Search,
  Settings,
  Shield,
  SlidersHorizontal,
  Sparkles,
  SunMedium,
  User,
  UserCog,
  LogOut,
  PanelTop,
  Plus,
} from 'lucide-react';

import { useAuth } from '../context/AuthContext';
import { getRoleKey } from '../lib/roleRoutes';
import LogoutButton from './LogoutButton';
import NotificationSystem from './NotificationSystem';

const OWNER_DIRECTORY = {
  'lalitppaunikar26@gmail.com': {
    displayName: 'Lalit Paunikar',
    roleLabel: 'Platform Owner',
  },
  'zestivapriyanshi@gmail.com': {
    displayName: 'Priyanshi',
    roleLabel: 'Platform Owner',
  },
};

const ROLE_LABELS = {
  TEAM_MEMBER: 'Member',
  TEAM_LEAD: 'Mentor',
  MEMBER: 'Member',
  CORPORATE_CLIENT: 'Corporate Client',
  CORPORATE_ADMIN: 'Organization Admin',
  HR_ADMIN: 'HR Admin',
  PROVIDER: 'Consultant',
  DIETICIAN: 'Senior Consultant',
  SUPER_ADMIN: 'Platform Owner',
  SUPERUSER: 'Platform Owner',
  ADMIN: 'Admin',
};

export default function DashboardHeader({
  searchPlaceholder = 'Search Employee, Session',
  showNavLinks = true,
  onMenuOpen,
  breadcrumbs = [],
  workspaceLabel = '',
  allowSettingsMenu = true,
  quickActionLabel = 'Quick actions',
}) {
  const router = useRouter();
  const { user, logout } = useAuth();

  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [commandQuery, setCommandQuery] = useState('');
  const [appearanceMode, setAppearanceMode] = useState('light');

  const menuRef = useRef(null);
  const settingsRef = useRef(null);

  const userRoleKey = getRoleKey(user?.role);
  const isPlatformOwner = userRoleKey.includes('super') || userRoleKey === 'platform_owner';

  const identity = useMemo(() => {
    const ownerOverride = user?.email ? OWNER_DIRECTORY[user.email.toLowerCase()] : null;
    const firstName = user?.first_name || user?.firstName;
    const lastName = user?.last_name || user?.lastName;
    const displayName = ownerOverride?.displayName
      || [firstName, lastName].filter(Boolean).join(' ').trim()
      || user?.name
      || user?.email?.split('@')[0]?.replace(/[._-]+/g, ' ')
      || 'User';
    const normalizedRole = (user?.role || '').toUpperCase();
    const roleLabel = ownerOverride?.roleLabel || ROLE_LABELS[normalizedRole] || user?.role || 'Workspace User';
    const initials = displayName
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join('')
      .toUpperCase() || 'U';

    return {
      displayName: displayName
        .split(' ')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' '),
      roleLabel,
      initials,
      email: user?.email || 'workspace@nuetra.in',
    };
  }, [user]);

  const getDashboardUrl = () => {
    if (!user?.role) return '/';
    const roleMap = {
      superuser: '/dashboard/owner',
      super_admin: '/dashboard/owner',
      platform_owner: '/dashboard/owner',
      admin: '/dashboard/admin',
      dietician: '/dashboard/provider',
      provider: '/dashboard/provider',
      corporate_admin: '/dashboard/corporate-admin',
      corporate_client: '/dashboard/corporate-admin',
      team_lead: '/dashboard/team-lead',
      team_member: '/dashboard/team-member',
      member: '/dashboard/team-member',
    };
    const roleKey = getRoleKey(user.role);
    return roleMap[roleKey] || '/';
  };

  const commandActions = useMemo(() => {
    const baseActions = [
      {
        id: 'profile',
        label: 'Open my profile',
        hint: '/profile',
        icon: User,
        run: () => router.push('/profile'),
      },
      {
        id: 'settings',
        label: 'Open workspace settings',
        hint: '/settings',
        icon: Settings,
        run: () => router.push('/settings'),
      },
      {
        id: 'logout',
        label: 'Log out safely',
        hint: 'session',
        icon: LogOut,
        run: () => logout(),
      },
    ];

    if (!isPlatformOwner) return baseActions;

    return [
      {
        id: 'command-center',
        label: 'Go to Command Center',
        hint: '/dashboard/owner',
        icon: Sparkles,
        run: () => router.push('/dashboard/owner'),
      },
      {
        id: 'people-access',
        label: 'Open People & Access',
        hint: '/dashboard/owner/people-access',
        icon: UserCog,
        run: () => router.push('/dashboard/owner/people-access'),
      },
      {
        id: 'organizations',
        label: 'Open Organizations',
        hint: '/dashboard/owner/organizations',
        icon: PanelTop,
        run: () => router.push('/dashboard/owner/organizations'),
      },
      {
        id: 'platform-health',
        label: 'Open Platform Health',
        hint: '/dashboard/owner/platform-health',
        icon: Activity,
        run: () => router.push('/dashboard/owner/platform-health'),
      },
      ...baseActions,
    ];
  }, [isPlatformOwner, logout, router]);

  const filteredCommandActions = useMemo(() => {
    const query = commandQuery.trim().toLowerCase();
    if (!query) return commandActions;
    return commandActions.filter((action) =>
      `${action.label} ${action.hint}`.toLowerCase().includes(query)
    );
  }, [commandActions, commandQuery]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      if (settingsRef.current && !settingsRef.current.contains(event.target)) {
        setShowSettingsMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const handleKeyboardShortcuts = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setShowCommandPalette(true);
      }
      if (event.key === 'Escape') {
        setShowCommandPalette(false);
      }
    };

    window.addEventListener('keydown', handleKeyboardShortcuts);
    return () => window.removeEventListener('keydown', handleKeyboardShortcuts);
  }, []);

  useEffect(() => {
    const storedMode = window.localStorage.getItem('nuetra-dashboard-appearance');
    if (storedMode) {
      setAppearanceMode(storedMode);
    }
  }, []);

  useEffect(() => {
    if (typeof document === 'undefined') return;
    window.localStorage.setItem('nuetra-dashboard-appearance', appearanceMode);
    document.documentElement.dataset.dashboardAppearance = appearanceMode;
  }, [appearanceMode]);

  const toggleAppearanceMode = () => {
    setAppearanceMode((current) => (current === 'light' ? 'focus' : 'light'));
  };

  const launchCommand = (action) => {
    setShowCommandPalette(false);
    setCommandQuery('');
    action.run();
  };

  return (
    <div className="bg-white sticky top-0 z-[100] border-b border-gray-100" role="banner">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-[60px] py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 sm:gap-6 lg:gap-[66px] min-w-0">
            {onMenuOpen && (
              <button
                onClick={onMenuOpen}
                className="lg:hidden w-9 h-9 flex items-center justify-center rounded-lg text-gray-600 hover:bg-gray-100 transition-colors shrink-0"
                aria-label="Open navigation menu"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}

            <Link href={getDashboardUrl()} className="flex items-center shrink-0">
              <Image
                src="/zestiva-logo.png"
                alt="Zestiva Logo"
                width={313}
                height={114}
                className="object-contain w-[120px] sm:w-[150px] lg:w-[170px]"
              />
            </Link>

            {breadcrumbs.length > 0 ? (
              <div className="hidden lg:flex min-w-0 flex-col gap-1">
                <div className="flex items-center gap-2 overflow-hidden text-xs font-semibold text-gray-400">
                  {breadcrumbs.map((crumb, index) => (
                    <React.Fragment key={`${crumb.href || crumb.label}-${index}`}>
                      {index > 0 ? <ChevronDown className="h-3 w-3 -rotate-90 shrink-0" /> : null}
                      {crumb.href ? (
                        <Link href={crumb.href} className="truncate transition-colors hover:text-[#237afc]">
                          {crumb.label}
                        </Link>
                      ) : (
                        <span className="truncate">{crumb.label}</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
                {workspaceLabel ? <p className="truncate text-sm font-semibold text-gray-600">{workspaceLabel}</p> : null}
              </div>
            ) : showNavLinks && (
              <div className="hidden md:flex items-center gap-8">
                <Link
                  href="/request-session"
                  className="text-sm font-semibold text-black hover:text-[#237afc] transition-colors whitespace-nowrap"
                >
                  Request Session
                </Link>
                <div className="h-[10px] w-0 flex items-center justify-center">
                  <div className="w-px h-6 bg-gray-200" />
                </div>
                <Link
                  href="/diet-plan"
                  className="text-sm font-semibold text-black hover:text-[#237afc] transition-colors whitespace-nowrap"
                >
                  Get a personalised diet plan
                </Link>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 sm:gap-4 lg:gap-6 shrink-0">
            <div className="hidden sm:block relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                onFocus={() => setShowCommandPalette(true)}
                className="pl-10 pr-16 py-2 w-[220px] lg:w-[300px] border border-gray-200 rounded-lg text-xs bg-[#f5f6fa] focus:outline-none focus:ring-2 focus:ring-[#237afc] transition-all"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 hidden lg:flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-[10px] font-semibold text-gray-400">
                <Command className="h-3 w-3" />
                <span>K</span>
              </div>
            </div>

            {workspaceLabel ? (
              <button
                type="button"
                className="hidden xl:flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-600"
              >
                <Shield className="h-4 w-4" />
                {workspaceLabel}
              </button>
            ) : null}

            <button
              onClick={() => setShowCommandPalette(true)}
              className="hidden lg:flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-600 hover:border-[#237afc] hover:text-[#237afc] transition-colors"
            >
              <Plus className="h-4 w-4" />
              {quickActionLabel}
            </button>

            <NotificationSystem />

            {allowSettingsMenu ? (
            <div className="relative" ref={settingsRef}>
              <button
                onClick={() => setShowSettingsMenu(!showSettingsMenu)}
                className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-50 rounded-xl transition-colors"
              >
                <Settings className="h-6 w-6" />
              </button>

              {showSettingsMenu && (
                <div className="absolute right-0 mt-3 w-80 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden z-[110]">
                  <div className="px-5 py-4 border-b border-gray-100">
                    <p className="text-sm font-bold text-gray-900">Workspace Settings</p>
                    <p className="text-xs text-gray-500 mt-1">Daily controls for access, workflow, and visibility.</p>
                  </div>
                  <div className="p-3 space-y-2">
                    <button
                      onClick={() => router.push('/settings')}
                      className="flex w-full items-center justify-between rounded-xl px-3 py-3 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <SlidersHorizontal className="h-4 w-4 text-gray-400" />
                        <div>
                          <p className="text-sm font-semibold text-gray-800">Workspace preferences</p>
                          <p className="text-xs text-gray-500">General settings, alerts, and defaults.</p>
                        </div>
                      </div>
                      <ExternalLink className="h-4 w-4 text-gray-300" />
                    </button>

                    <button
                      onClick={toggleAppearanceMode}
                      className="flex w-full items-center justify-between rounded-xl px-3 py-3 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {appearanceMode === 'light' ? (
                          <Moon className="h-4 w-4 text-gray-400" />
                        ) : (
                          <SunMedium className="h-4 w-4 text-gray-400" />
                        )}
                        <div>
                          <p className="text-sm font-semibold text-gray-800">Appearance mode</p>
                          <p className="text-xs text-gray-500">{appearanceMode === 'light' ? 'Switch to focus mode' : 'Return to light mode'}</p>
                        </div>
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400">
                        {appearanceMode}
                      </span>
                    </button>

                    <button
                      onClick={() => setShowCommandPalette(true)}
                      className="flex w-full items-center justify-between rounded-xl px-3 py-3 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <Command className="h-4 w-4 text-gray-400" />
                        <div>
                          <p className="text-sm font-semibold text-gray-800">Command palette</p>
                          <p className="text-xs text-gray-500">Jump between owner tasks with keyboard shortcuts.</p>
                        </div>
                      </div>
                      <span className="rounded-md border border-gray-200 px-2 py-1 text-[10px] font-semibold text-gray-400">⌘K</span>
                    </button>

                    {isPlatformOwner && (
                      <button
                        onClick={() => router.push('/dashboard/owner/platform-health')}
                        className="flex w-full items-center justify-between rounded-xl px-3 py-3 text-left hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <Shield className="h-4 w-4 text-gray-400" />
                          <div>
                            <p className="text-sm font-semibold text-gray-800">Audit and platform health</p>
                            <p className="text-xs text-gray-500">Review system signals and operational risk.</p>
                          </div>
                        </div>
                        <ExternalLink className="h-4 w-4 text-gray-300" />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
            ) : null}

            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 lg:gap-3 p-1 hover:bg-gray-50 rounded-xl transition-all"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-[#237afc] to-[#0ea5e9] rounded-full flex items-center justify-center shadow-sm">
                  <span className="text-white text-sm font-bold">{identity.initials}</span>
                </div>
                <div className="hidden lg:block text-left mr-1">
                  <p className="text-sm font-bold text-gray-800 leading-none mb-1">{identity.displayName}</p>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{identity.roleLabel}</p>
                </div>
                <ChevronDown className="h-4 w-4 text-gray-300" />
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-3 w-64 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden z-[110] transform transition-all animate-scaleIn origin-top-right">
                  <div className="px-6 py-5 bg-gray-50/50 border-b border-gray-100">
                    <p className="font-bold text-gray-900 mb-0.5 truncate">{identity.displayName}</p>
                    <p className="text-xs text-gray-500 truncate mb-3">{identity.email}</p>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-blue-50 text-[#237afc] text-[9px] font-black uppercase tracking-widest rounded-md border border-blue-100">
                        {identity.roleLabel}
                      </span>
                    </div>
                  </div>

                  <div className="py-2">
                    <Link href="/profile" className="flex items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                        <User className="h-4 w-4" />
                      </div>
                      My Profile
                    </Link>

                    <Link href="/settings" className="flex items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                        <Settings className="h-4 w-4" />
                      </div>
                      Workspace Settings
                    </Link>

                    {isPlatformOwner && (
                      <button
                        onClick={() => router.push('/dashboard/owner/people-access')}
                        className="flex w-full items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors"
                      >
                        <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                          <UserCog className="h-4 w-4" />
                        </div>
                        People & Access
                      </button>
                    )}

                    <div className="h-px bg-gray-100 mx-4 my-2" />

                    <Link href="/privacy-policy" className="flex items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                        <Shield className="h-4 w-4" />
                      </div>
                      Privacy Policy
                    </Link>

                    <Link href="/terms-of-service" className="flex items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                        <FileText className="h-4 w-4" />
                      </div>
                      Terms of Service
                    </Link>

                    <a
                      href="mailto:support@nuetra.in"
                      className="flex items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors"
                    >
                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                        <LifeBuoy className="h-4 w-4" />
                      </div>
                      Support
                    </a>
                  </div>

                  <div className="p-4 bg-gray-50 border-t border-gray-100">
                    <LogoutButton className="w-full text-center font-bold justify-center py-2.5 rounded-xl bg-white border border-red-100 shadow-sm" />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showCommandPalette && (
        <div className="fixed inset-0 z-[130] bg-[#0f172a]/35 backdrop-blur-sm px-4 py-12" onClick={() => setShowCommandPalette(false)}>
          <div className="mx-auto w-full max-w-2xl rounded-3xl border border-gray-200 bg-white shadow-2xl" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center gap-3 border-b border-gray-100 px-5 py-4">
              <Command className="h-5 w-5 text-gray-400" />
              <input
                autoFocus
                value={commandQuery}
                onChange={(event) => setCommandQuery(event.target.value)}
                placeholder="Search actions, screens, and workflows..."
                className="w-full bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400"
              />
              <span className="rounded-lg border border-gray-200 px-2 py-1 text-[10px] font-semibold text-gray-400">
                ESC
              </span>
            </div>
            <div className="max-h-[420px] overflow-y-auto p-3">
              {filteredCommandActions.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-gray-200 px-4 py-10 text-center">
                  <p className="text-sm font-semibold text-gray-700">No matching commands</p>
                  <p className="mt-1 text-xs text-gray-500">Try searching for people, organizations, or settings.</p>
                </div>
              ) : (
                filteredCommandActions.map((action) => (
                  <button
                    key={action.id}
                    onClick={() => launchCommand(action)}
                    className="flex w-full items-center justify-between rounded-2xl px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-50 text-gray-500">
                        <action.icon className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{action.label}</p>
                        <p className="text-xs text-gray-500">{action.hint}</p>
                      </div>
                    </div>
                    <ChevronDown className="h-4 w-4 -rotate-90 text-gray-300" />
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
