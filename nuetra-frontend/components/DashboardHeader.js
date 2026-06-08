// nuetra-frontend/components/DashboardHeader.js
import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import LogoutButton from './LogoutButton';
import Image from 'next/image';
import {
  Search,
  Bell,
  User,
  Settings,
  FileText,
  Shield,
  ChevronDown,
  MoreVertical
} from 'lucide-react';

export default function DashboardHeader({ 
  searchPlaceholder = "Search Employee, Session",
  notificationCount = 0,
  showNavLinks = true 
}) {
  const router = useRouter();
  const { user } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const menuRef = useRef(null);
  const notificationRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getUserInitials = () => {
    if (user?.firstName && user?.lastName) {
      return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
    }
    if (user?.email) {
      return user.email[0].toUpperCase();
    }
    return 'U';
  };

  const getUserName = () => {
    if (user?.firstName && user?.lastName) {
      return `${user.firstName} ${user.lastName}`;
    }
    // Return name if available, otherwise just email
    return user?.name || user?.email || 'User';
  };

  const getUserRole = () => {
    if (user?.role) {
      const normalizedRole = user.role.toUpperCase();
      const roleMap = {
        'TEAM_MEMBER': 'Member',
        'TEAM_LEAD': 'Team Lead',
        'MEMBER': 'Member',
        'CORPORATE_CLIENT': 'Corporate Client',
        'CORPORATE_ADMIN': 'Corporate Admin',
        'HR_ADMIN': 'HR Admin',
        'PROVIDER': 'Provider',
        'SUPER_ADMIN': 'Admin'
      };
      return roleMap[normalizedRole] || user.role;
    }
    return 'Member';
  };

  return (
    <div className="bg-white sticky top-0 z-[100] border-b border-gray-100">
      <div className="max-w-[1440px] mx-auto px-8 lg:px-[60px] py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-[66px]">
            {/* Logo */}
            <Link href="/" className="flex items-center shrink-0">
              <Image
                src="/nuetra-logo-new.svg"
                alt="Nuetra Logo"
                width={150}
                height={30}
                className="object-contain"
              />
            </Link>

            {/* Center Navigation Links */}
            {showNavLinks && (
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

          {/* Right Side */}
          <div className="flex items-center gap-6">
            {/* Search */}
            <div className="hidden sm:block relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                className="pl-10 pr-4 py-2 w-[220px] lg:w-[261px] border border-gray-200 rounded-lg text-xs bg-[#f5f6fa] focus:outline-none focus:ring-2 focus:ring-[#237afc] transition-all"
              />
            </div>

            {/* Notifications */}
            <div className="relative" ref={notificationRef}>
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-1.5 text-gray-500 hover:text-gray-900 transition-colors"
              >
                <Bell className="h-6 w-6" />
                {notificationCount > 0 && (
                  <span className="absolute top-0 right-0 w-4 h-4 bg-[#ff3b30] rounded-full border-2 border-white flex items-center justify-center">
                    <span className="text-white text-[9px] font-bold">{notificationCount}</span>
                  </span>
                )}
              </button>
            </div>

            {/* User Menu */}
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 lg:gap-3 p-1 hover:bg-gray-50 rounded-xl transition-all"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-[#237afc] to-[#0ea5e9] rounded-full flex items-center justify-center shadow-sm">
                  <span className="text-white text-sm font-bold">{getUserInitials()}</span>
                </div>
                <div className="hidden lg:block text-left mr-1">
                  <p className="text-sm font-bold text-gray-800 leading-none mb-1">{getUserName()}</p>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{getUserRole()}</p>
                </div>
                <MoreVertical className="h-4 w-4 text-gray-300" />
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-3 w-64 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden z-[110] transform transition-all animate-scaleIn origin-top-right">
                  {/* Menu Header */}
                  <div className="px-6 py-5 bg-gray-50/50 border-b border-gray-100">
                    <p className="font-bold text-gray-900 mb-0.5 truncate">{getUserName()}</p>
                    <p className="text-xs text-gray-500 truncate mb-3">{user?.email}</p>
                    <div className="flex items-center gap-2">
                       <span className="px-2 py-0.5 bg-blue-50 text-[#237afc] text-[9px] font-black uppercase tracking-widest rounded-md border border-blue-100">
                        {getUserRole()}
                      </span>
                    </div>
                  </div>
                  
                  {/* Menu Actions */}
                  <div className="py-2">
                    <Link href="/profile" className="flex items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400 group-hover:bg-white">
                        <User className="h-4 w-4" />
                      </div>
                      My Profile
                    </Link>
                    
                    <Link href="/settings" className="flex items-center gap-3 px-6 py-3 text-sm font-semibold text-gray-600 hover:bg-blue-50 hover:text-[#237afc] transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                        <Settings className="h-4 w-4" />
                      </div>
                      Settings
                    </Link>
                    
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
                  </div>
                  
                  {/* Logout Section */}
                  <div className="p-4 bg-gray-50 border-t border-gray-100">
                    <LogoutButton className="w-full text-center font-bold justify-center py-2.5 rounded-xl bg-white border border-red-100 shadow-sm" />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
