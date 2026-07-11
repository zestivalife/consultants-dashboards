import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  Activity,
  Blocks,
  BriefcaseBusiness,
  Building2,
  ClipboardList,
  FolderKanban,
  LayoutPanelTop,
  Settings,
  Shield,
  Sparkles,
  Stethoscope,
  Users,
} from 'lucide-react';

import { OWNER_ROUTE_DEFINITIONS, getOwnerConsolePath } from '../../lib/ownerConsoleRoutes';

function cn(...values) {
  return values.filter(Boolean).join(' ');
}

const OWNER_NAV_ICONS = {
  'command-center': Sparkles,
  organizations: Building2,
  'people-access': Users,
  permissions: Shield,
  packages: FolderKanban,
  services: Blocks,
  practitioners: Stethoscope,
  mentors: BriefcaseBusiness,
  consultants: BriefcaseBusiness,
  reports: LayoutPanelTop,
  audit: ClipboardList,
  'platform-health': Activity,
  settings: Settings,
};

export default function OwnerConsoleLayout({ activeSlug, children }) {
  const router = useRouter();

  return (
    <div className="relative z-10 mx-auto flex max-w-[1600px] gap-6 px-4 pb-20 pt-6 sm:px-6 lg:px-8">
      <aside className="sticky top-24 hidden h-[calc(100vh-7rem)] w-[280px] shrink-0 overflow-y-auto rounded-[32px] border border-white/70 bg-white/85 p-5 shadow-sm backdrop-blur lg:block">
        <div className="border-b border-gray-100 pb-4">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-gray-400">Platform Owner</p>
          <h2 className="mt-2 text-xl font-black tracking-tight text-gray-900">Enterprise Console</h2>
          <p className="mt-2 text-sm text-gray-500">
            Route-backed navigation for platform operations, workforce governance, and system oversight.
          </p>
        </div>

        <nav className="mt-5 space-y-1" aria-label="Platform owner navigation">
          {OWNER_ROUTE_DEFINITIONS.map((item) => {
            const Icon = OWNER_NAV_ICONS[item.slug] || Sparkles;
            const isActive = item.slug === activeSlug || (item.slug === 'command-center' && !activeSlug);
            return (
              <Link
                key={item.slug}
                href={getOwnerConsolePath(item.slug)}
                className={cn(
                  'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-bold transition-all',
                  isActive
                    ? 'bg-[#237afc] text-white shadow-[0_10px_28px_rgba(35,122,252,0.25)]'
                    : 'text-gray-600 hover:bg-[#f5f9ff] hover:text-[#237afc]'
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-6 rounded-3xl border border-gray-100 bg-gray-50 p-4">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-gray-400">Navigation state</p>
          <p className="mt-2 text-sm font-semibold text-gray-800">URL-backed modules</p>
          <p className="mt-1 text-sm text-gray-500">
            Refresh, bookmarks, and browser history now follow the active module route instead of local tab state.
          </p>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <div className="mb-4 overflow-x-auto rounded-3xl border border-white/70 bg-white/80 p-2 shadow-sm backdrop-blur lg:hidden">
          <div className="flex min-w-max items-center gap-2">
            {OWNER_ROUTE_DEFINITIONS.map((item) => {
              const isActive = item.slug === activeSlug || (item.slug === 'command-center' && !activeSlug);
              return (
                <button
                  key={item.slug}
                  type="button"
                  onClick={() => router.push(getOwnerConsolePath(item.slug))}
                  className={cn(
                    'rounded-full px-3 py-2 text-xs font-bold whitespace-nowrap transition-all',
                    isActive
                      ? 'bg-[#237afc] text-white shadow-sm'
                      : 'border border-gray-200 bg-white text-gray-600'
                  )}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>

        {children}
      </main>
    </div>
  );
}
