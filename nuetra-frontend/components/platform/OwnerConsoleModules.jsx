import { useMemo, useState } from 'react';
import {
  Activity,
  ArrowUpRight,
  BadgeCheck,
  Blocks,
  Bot,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Copy,
  Download,
  Eye,
  FileSpreadsheet,
  Filter,
  FolderKanban,
  GripVertical,
  KeyRound,
  LayoutPanelTop,
  ListFilter,
  Mail,
  MoreHorizontal,
  PencilLine,
  Plus,
  Save,
  Search,
  Settings,
  Shield,
  SlidersHorizontal,
  Sparkles,
  Tag,
  Upload,
  UserCog,
  Users,
  XCircle,
} from 'lucide-react';
import { motion } from 'framer-motion';

function cn(...values) {
  return values.filter(Boolean).join(' ');
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
}

function StatPill({ icon: Icon, label, value, tone = 'from-[#237afc] to-[#58b6ff]' }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-gradient-to-br from-white to-gray-50 p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-gray-400">{label}</p>
          <p className="mt-3 text-3xl font-black tracking-tight text-gray-900">{value}</p>
        </div>
        <div className={cn('rounded-2xl bg-gradient-to-br p-3 text-white shadow-sm', tone)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function ModuleFrame({ badge, title, description, actions, children }) {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-[#f2f2f7] rounded-3xl p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-[11px] font-black uppercase tracking-[0.24em] text-[#237afc]">
              <BadgeCheck className="h-3.5 w-3.5" />
              {badge}
            </div>
            <h2 className="mt-4 text-3xl font-black tracking-tight text-gray-900">{title}</h2>
            <p className="mt-2 max-w-3xl text-sm text-gray-500">{description}</p>
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
        </div>
        <div className="mt-8">{children}</div>
      </div>
    </div>
  );
}

function ActionButton({ icon: Icon, label, tone = 'secondary' }) {
  return (
    <button
      className={cn(
        'inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold transition-colors',
        tone === 'primary'
          ? 'bg-[#237afc] text-white shadow-md hover:bg-[#1a62d6]'
          : 'border border-gray-200 bg-white text-gray-700 hover:border-[#237afc] hover:text-[#237afc]'
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

function ControlBar({
  searchPlaceholder,
  filters = [],
  activeFilter,
  onFilterChange,
  rightControls,
}) {
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-gray-100 bg-gray-50/70 p-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-1 items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3">
        <Search className="h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder={searchPlaceholder}
          className="w-full bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400"
        />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {filters.map((filter) => (
          <button
            key={filter.key}
            onClick={() => onFilterChange?.(filter.key)}
            className={cn(
              'rounded-full px-4 py-2 text-sm font-bold transition-colors',
              activeFilter === filter.key
                ? 'bg-[#237afc] text-white shadow-sm'
                : 'bg-white text-gray-600 border border-gray-200 hover:border-[#237afc] hover:text-[#237afc]'
            )}
          >
            {filter.label}
          </button>
        ))}
        {rightControls}
      </div>
    </div>
  );
}

function Badge({ children, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-gray-100 text-gray-700 border-gray-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    violet: 'bg-violet-50 text-violet-700 border-violet-200',
    red: 'bg-red-50 text-red-700 border-red-200',
  };
  return <span className={cn('rounded-full border px-3 py-1 text-xs font-bold', tones[tone])}>{children}</span>;
}

function Panel({ title, subtitle, action, children }) {
  return (
    <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          {subtitle ? <p className="mt-1 text-sm text-gray-500">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      <div className="mt-5">{children}</div>
    </div>
  );
}

function MiniBarChart({ data, suffix = '', color = 'from-[#237afc] to-[#58b6ff]' }) {
  const max = Math.max(...data.map((item) => item.value), 1);
  return (
    <div className="space-y-3">
      {data.map((item) => (
        <div key={item.label}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700">{item.label}</span>
            <span className="font-bold text-gray-900">
              {item.value}
              {suffix}
            </span>
          </div>
          <div className="h-2 rounded-full bg-gray-100">
            <div
              className={cn('h-2 rounded-full bg-gradient-to-r', color)}
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="rounded-3xl border border-dashed border-gray-200 bg-white px-6 py-16 text-center">
      <Icon className="mx-auto h-10 w-10 text-gray-300" />
      <h4 className="mt-4 text-lg font-bold text-gray-900">{title}</h4>
      <p className="mt-2 text-sm text-gray-500">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function CommandCenterModule({ data }) {
  const activeOrgs = data.organizations.filter((item) => item.status === 'Active').length;
  const livePeople = data.people.filter((item) => item.status === 'Active').length;

  return (
    <ModuleFrame
      badge="Command center"
      title="Enterprise operations at a glance"
      description="Platform-wide visibility across organizations, workforce access, service packaging, delivery quality, and system readiness."
      actions={
        <>
          <ActionButton icon={Download} label="Export board" />
          <ActionButton icon={Sparkles} label="Review critical queue" tone="primary" />
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatPill icon={Building2} label="Active organizations" value={activeOrgs} />
        <StatPill icon={Users} label="Live identities" value={livePeople} tone="from-emerald-500 to-teal-500" />
        <StatPill icon={FolderKanban} label="Published packages" value={data.packages.filter((item) => item.status === 'Published').length} tone="from-violet-500 to-fuchsia-500" />
        <StatPill icon={Activity} label="Audit events today" value={data.auditLogs.length} tone="from-amber-500 to-orange-500" />
      </div>

      <div className="mt-8 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Panel title="Operational queues" subtitle="Prioritized actions for platform owners this week.">
          <div className="space-y-3">
            {[
              ['Meridian HealthOps renewal is blocked by legal review', 'High priority', 'red'],
              ['Aster Pulse engagement fell below renewal threshold', 'Watchlist', 'amber'],
              ['3 pending role approvals need owner sign-off', 'Needs action', 'blue'],
              ['Northstar Labs package rollout scheduled for Friday', 'Upcoming', 'green'],
            ].map(([item, state, tone]) => (
              <div key={item} className="flex items-center justify-between rounded-2xl border border-gray-100 bg-gray-50 px-4 py-4">
                <p className="max-w-xl text-sm font-semibold text-gray-800">{item}</p>
                <Badge tone={tone}>{state}</Badge>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Revenue quality mix" subtitle="Month-to-date enterprise health indicators.">
          <MiniBarChart
            data={[
              { label: 'Revenue', value: 234 },
              { label: 'Recovery quality', value: 81 },
              { label: 'Nutrition activation', value: 79 },
              { label: 'Assessment completion', value: 72 },
            ]}
            color="from-[#111827] to-[#374151]"
          />
        </Panel>
      </div>
    </ModuleFrame>
  );
}

export function OrganizationsModule({ organizations }) {
  const [selectedId, setSelectedId] = useState(organizations[0]?.id || '');
  const [subPage, setSubPage] = useState('list');
  const selected = useMemo(
    () => organizations.find((item) => item.id === selectedId) || organizations[0],
    [organizations, selectedId]
  );

  const subPages = [
    ['list', 'Organization List'],
    ['details', 'Organization Details'],
    ['create', 'Create Organization'],
    ['edit', 'Edit Organization'],
    ['analytics', 'Organization Analytics'],
    ['settings', 'Organization Settings'],
    ['members', 'Members'],
    ['packages', 'Packages'],
    ['practitioners', 'Practitioners'],
    ['mentors', 'Mentors'],
    ['consultants', 'Consultants'],
    ['audit', 'Audit Logs'],
  ];

  return (
    <ModuleFrame
      badge="Organization management"
      title="Organizations, contracts, deployment, and operating controls"
      description="Manage account lifecycle, package assignments, staffing, analytics, and audit visibility across enterprise clients."
      actions={
        <>
          <ActionButton icon={FileSpreadsheet} label="Generate report" />
          <ActionButton icon={Plus} label="Create organization" tone="primary" />
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatPill icon={Building2} label="Organizations" value={organizations.length} />
        <StatPill icon={Users} label="Employees" value={organizations.reduce((sum, item) => sum + item.employees, 0)} tone="from-emerald-500 to-teal-500" />
        <StatPill icon={ClipboardList} label="Assessments" value={organizations.reduce((sum, item) => sum + item.assessments, 0)} tone="from-violet-500 to-fuchsia-500" />
        <StatPill icon={Sparkles} label="Avg recovery" value={`${Math.round(organizations.reduce((sum, item) => sum + item.recoveryRate, 0) / organizations.length)}%`} tone="from-amber-500 to-orange-500" />
        <StatPill icon={Settings} label="At risk / suspended" value={organizations.filter((item) => item.status !== 'Active').length} tone="from-rose-500 to-red-500" />
      </div>

      <div className="mt-8 flex flex-wrap gap-2">
        {subPages.map(([key, label]) => (
          <button
            key={key}
            onClick={() => setSubPage(key)}
            className={cn(
              'rounded-full px-4 py-2 text-sm font-bold transition-colors',
              subPage === key
                ? 'bg-[#237afc] text-white shadow-sm'
                : 'bg-white text-gray-600 border border-gray-200 hover:border-[#237afc] hover:text-[#237afc]'
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-8 grid gap-8 xl:grid-cols-[1.25fr_0.95fr]">
        <div className="space-y-6">
          <ControlBar
            searchPlaceholder="Search organization, GST number, contact, or package..."
            filters={[
              { key: 'all', label: 'All' },
              { key: 'active', label: 'Active' },
              { key: 'risk', label: 'At Risk' },
              { key: 'suspended', label: 'Suspended' },
            ]}
            activeFilter="all"
            rightControls={
              <div className="ml-2 flex items-center gap-2">
                <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
                  <Filter className="h-4 w-4" />
                  Saved Views
                </button>
                <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
                  <Download className="h-4 w-4" />
                  Export
                </button>
              </div>
            }
          />

          {(subPage === 'list' || subPage === 'details') && (
            <Panel title="Organization roster" subtitle="Search, sort, and inspect enterprise accounts.">
              <div className="space-y-3">
                {organizations.map((organization) => (
                  <button
                    key={organization.id}
                    onClick={() => {
                      setSelectedId(organization.id);
                      setSubPage('details');
                    }}
                    className={cn(
                      'flex w-full items-start justify-between rounded-2xl border px-5 py-4 text-left transition',
                      selected?.id === organization.id
                        ? 'border-[#237afc] bg-[#f5f9ff]'
                        : 'border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50'
                    )}
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#237afc] to-[#58b6ff] text-sm font-black text-white">
                        {organization.logo}
                      </div>
                      <div>
                        <p className="text-base font-black text-gray-900">{organization.name}</p>
                        <p className="mt-1 text-sm text-gray-500">
                          {organization.subscription} · {organization.companySize}
                        </p>
                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <Badge tone={organization.status === 'Active' ? 'green' : organization.status === 'At Risk' ? 'amber' : 'red'}>
                            {organization.status}
                          </Badge>
                          <Badge tone="blue">{organization.industry}</Badge>
                          <Badge>{organization.country}</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-gray-900">{organization.primaryContact}</p>
                      <p className="mt-1 text-xs text-gray-500">Renews {organization.renewalDate}</p>
                    </div>
                  </button>
                ))}
              </div>
            </Panel>
          )}

          {subPage === 'create' && (
            <Panel title="Create organization workflow" subtitle="Capture legal, commercial, and delivery setup in one flow.">
              <div className="grid gap-4 md:grid-cols-2">
                {[
                  'Organization Name',
                  'Industry',
                  'Company Size',
                  'GST Number',
                  'Address',
                  'Timezone',
                  'Country',
                  'Primary Contact',
                  'Subscription',
                  'Renewal Date',
                ].map((field) => (
                  <label key={field} className="space-y-2">
                    <span className="text-sm font-bold text-gray-700">{field}</span>
                    <input
                      className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-[#237afc]"
                      placeholder={`Add ${field.toLowerCase()}`}
                    />
                  </label>
                ))}
              </div>
            </Panel>
          )}

          {subPage === 'analytics' && (
            <Panel title="Organization analytics" subtitle="Compare usage, recovery, nutrition adoption, and assessments by account.">
              <MiniBarChart
                data={organizations.map((organization) => ({
                  label: organization.name,
                  value: organization.engagement,
                }))}
                suffix="%"
                color="from-emerald-500 to-teal-500"
              />
            </Panel>
          )}
        </div>

        <div className="space-y-6">
          {selected ? (
            <>
              <Panel
                title={selected.name}
                subtitle="Organization details, health metrics, and quick actions."
                action={<button className="rounded-xl border border-gray-200 p-2 text-gray-500"><MoreHorizontal className="h-4 w-4" /></button>}
              >
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl bg-gray-50 p-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Primary contact</p>
                    <p className="mt-2 text-sm font-bold text-gray-900">{selected.primaryContact}</p>
                    <p className="text-sm text-gray-500">{selected.contactEmail}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 p-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Subscription</p>
                    <p className="mt-2 text-sm font-bold text-gray-900">{selected.subscription}</p>
                    <p className="text-sm text-gray-500">Renews {selected.renewalDate}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 p-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Analytics</p>
                    <p className="mt-2 text-sm font-bold text-gray-900">{selected.recoveryRate}% recovery · {selected.engagement}% engagement</p>
                    <p className="text-sm text-gray-500">{selected.assessments} assessments · {selected.nutritionRate}% nutrition</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 p-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Delivery</p>
                    <p className="mt-2 text-sm font-bold text-gray-900">{selected.practitioners.length} practitioners · {selected.mentors.length} mentors</p>
                    <p className="text-sm text-gray-500">{selected.activePackage}</p>
                  </div>
                </div>
              </Panel>

              <Panel title="Quick actions" subtitle="Owner controls for this account.">
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    ['Suspend', XCircle],
                    ['Assign Package', FolderKanban],
                    ['Assign Practitioner', BriefcaseBusiness],
                    ['Assign Mentor', UserCog],
                    ['Assign Consultant', Users],
                    ['Invite Employees', Mail],
                    ['Generate Report', FileSpreadsheet],
                    ['Open Settings', Settings],
                  ].map(([label, Icon]) => (
                    <button key={label} className="flex items-center justify-between rounded-2xl border border-gray-100 bg-gray-50 px-4 py-4 text-left hover:border-[#237afc] hover:bg-white">
                      <span className="text-sm font-bold text-gray-800">{label}</span>
                      <Icon className="h-4 w-4 text-gray-400" />
                    </button>
                  ))}
                </div>
              </Panel>
            </>
          ) : (
            <EmptyState icon={Building2} title="No organization selected" description="Pick an organization to inspect details and actions." />
          )}
        </div>
      </div>
    </ModuleFrame>
  );
}

export function PeopleAccessModule({ people }) {
  const [selectedId, setSelectedId] = useState(people[0]?.id || '');
  const [profileTab, setProfileTab] = useState('General');
  const selected = useMemo(() => people.find((item) => item.id === selectedId) || people[0], [people, selectedId]);
  const profileTabs = ['General', 'Professional', 'Organizations', 'Permissions', 'Activity Timeline', 'Login Sessions', 'Audit History', 'Assigned Packages', 'Assigned Services', 'Notes'];

  return (
    <ModuleFrame
      badge="People & access"
      title="Identity, authority, sessions, and workforce governance"
      description="Search, filter, bulk-edit, import, export, and govern platform identities across owners, admins, mentors, consultants, practitioners, and employees."
      actions={
        <>
          <ActionButton icon={Upload} label="CSV Import" />
          <ActionButton icon={Download} label="CSV Export" />
          <ActionButton icon={UserCog} label="Bulk Actions" tone="primary" />
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatPill icon={Users} label="People" value={people.length} />
        <StatPill icon={Shield} label="Admins" value={people.filter((item) => ['admin', 'platform_owner', 'organization_admin'].includes(item.role)).length} tone="from-violet-500 to-fuchsia-500" />
        <StatPill icon={UserCog} label="Mentors" value={people.filter((item) => item.role === 'mentor').length} tone="from-amber-500 to-orange-500" />
        <StatPill icon={BriefcaseBusiness} label="Consultants" value={people.filter((item) => ['consultant', 'practitioner'].includes(item.role)).length} tone="from-emerald-500 to-teal-500" />
        <StatPill icon={Mail} label="Suspended" value={people.filter((item) => item.status !== 'Active').length} tone="from-rose-500 to-red-500" />
      </div>

      <div className="mt-8 grid gap-8 xl:grid-cols-[1.2fr_1fr]">
        <div className="space-y-6">
          <ControlBar
            searchPlaceholder="Search people, roles, organizations, sessions, or package assignments..."
            filters={[
              { key: 'all', label: 'All' },
              { key: 'owners', label: 'Platform Owners' },
              { key: 'admins', label: 'Admins' },
              { key: 'mentors', label: 'Mentors' },
              { key: 'employees', label: 'Employees' },
            ]}
            activeFilter="all"
            rightControls={
              <div className="ml-2 flex items-center gap-2">
                <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
                  <ListFilter className="h-4 w-4" />
                  Column visibility
                </button>
                <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
                  <SlidersHorizontal className="h-4 w-4" />
                  Saved views
                </button>
              </div>
            }
          />

          <Panel title="Enterprise roster" subtitle="Bulk-ready people management with status, role, and org visibility.">
            <div className="overflow-hidden rounded-3xl border border-gray-100">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Select', 'Person', 'Role', 'Organizations', 'Assigned packages', 'Status'].map((header) => (
                      <th key={header} className="px-5 py-4 text-left text-xs font-black uppercase tracking-[0.24em] text-gray-400">{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {people.map((person) => (
                    <tr key={person.id} className="hover:bg-gray-50/80">
                      <td className="px-5 py-4">
                        <input type="checkbox" className="h-4 w-4 rounded border-gray-300" />
                      </td>
                      <td className="px-5 py-4">
                        <button onClick={() => setSelectedId(person.id)} className="text-left">
                          <p className="font-bold text-gray-900">{person.name}</p>
                          <p className="text-xs text-gray-500">{person.email}</p>
                        </button>
                      </td>
                      <td className="px-5 py-4"><Badge tone="blue">{person.role.replace(/_/g, ' ')}</Badge></td>
                      <td className="px-5 py-4 text-sm text-gray-500">{person.organizations.join(', ')}</td>
                      <td className="px-5 py-4 text-sm text-gray-500">{person.packages.join(', ')}</td>
                      <td className="px-5 py-4">
                        <Badge tone={person.status === 'Active' ? 'green' : 'red'}>{person.status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {['Bulk role change', 'Bulk suspend', 'Bulk activate', 'Bulk invite', 'Export selected'].map((item) => (
                <button key={item} className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-bold text-gray-600">
                  {item}
                </button>
              ))}
            </div>
          </Panel>
        </div>

        <Panel title={selected?.name || 'User profile'} subtitle="Profile-level governance and authority review.">
          {selected ? (
            <>
              <div className="flex items-center gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#237afc] to-[#53b6ff] text-lg font-black text-white">
                  {selected.name.split(' ').map((part) => part[0]).join('').slice(0, 2)}
                </div>
                <div>
                  <p className="text-lg font-black text-gray-900">{selected.name}</p>
                  <p className="text-sm text-gray-500">{selected.professional}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <Badge tone="blue">{selected.role.replace(/_/g, ' ')}</Badge>
                    <Badge tone={selected.status === 'Active' ? 'green' : 'red'}>{selected.status}</Badge>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex flex-wrap gap-2">
                {profileTabs.map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setProfileTab(tab)}
                    className={cn(
                      'rounded-full px-3 py-2 text-xs font-bold transition-colors',
                      profileTab === tab
                        ? 'bg-[#237afc] text-white'
                        : 'bg-gray-50 text-gray-600 border border-gray-200'
                    )}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="mt-6 rounded-3xl bg-gray-50 p-5">
                {profileTab === 'General' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    <p><span className="font-bold text-gray-900">Email:</span> {selected.email}</p>
                    <p><span className="font-bold text-gray-900">Primary organizations:</span> {selected.organizations.join(', ')}</p>
                    <p><span className="font-bold text-gray-900">Status:</span> {selected.status}</p>
                  </div>
                )}
                {profileTab === 'Professional' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    <p><span className="font-bold text-gray-900">Role focus:</span> {selected.professional}</p>
                    <p><span className="font-bold text-gray-900">Assigned services:</span> {selected.services.join(', ')}</p>
                    <p><span className="font-bold text-gray-900">Packages:</span> {selected.packages.join(', ')}</p>
                  </div>
                )}
                {profileTab === 'Permissions' && (
                  <div className="flex flex-wrap gap-2">
                    {selected.permissions.map((permission) => (
                      <Badge key={permission} tone="violet">{permission}</Badge>
                    ))}
                  </div>
                )}
                {profileTab === 'Login Sessions' && (
                  <div className="space-y-2 text-sm text-gray-600">
                    <p><span className="font-bold text-gray-900">Active sessions:</span> {selected.loginSessions}</p>
                    <p>Last session from Chrome on macOS.</p>
                    <p>Device trust: Enterprise approved.</p>
                  </div>
                )}
                {profileTab === 'Notes' && <p className="text-sm text-gray-600">{selected.notes}</p>}
                {!['General', 'Professional', 'Permissions', 'Login Sessions', 'Notes'].includes(profileTab) && (
                  <p className="text-sm text-gray-600">
                    {profileTab} workflow is prepared for production and can be connected to live APIs without changing the layout.
                  </p>
                )}
              </div>
            </>
          ) : (
            <EmptyState icon={Users} title="No person selected" description="Pick a user to inspect detailed access, activity, and notes." />
          )}
        </Panel>
      </div>
    </ModuleFrame>
  );
}

export function PermissionMatrixModule({ permissionGroups, roles }) {
  const [expanded, setExpanded] = useState(permissionGroups.reduce((acc, group) => ({ ...acc, [group.module]: true }), {}));

  return (
    <ModuleFrame
      badge="Role & permission management"
      title="Permission matrix for platform roles and custom authority sets"
      description="Search permissions, expand modules, duplicate roles, and prepare custom role definitions without leaving the owner workspace."
      actions={
        <>
          <ActionButton icon={Copy} label="Duplicate role" />
          <ActionButton icon={Plus} label="Create custom role" tone="primary" />
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.4fr]">
        <Panel title="Role library" subtitle="Cloneable and governed roles for enterprise operations.">
          <div className="space-y-3">
            {roles.map((role) => (
              <div key={role.id} className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-bold text-gray-900">{role.name}</p>
                    <p className="text-sm text-gray-500">{role.users} assigned users</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {role.cloneable ? <Badge tone="blue">Cloneable</Badge> : <Badge tone="red">Fixed</Badge>}
                    <button className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">Clone</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Permission matrix" subtitle="Module-scoped access controls with search-ready rows.">
          <div className="mb-4 flex flex-wrap gap-2">
            <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
              <Search className="h-4 w-4" />
              Search permissions
            </button>
            <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
              <ChevronDown className="h-4 w-4" />
              Expand / collapse
            </button>
          </div>

          <div className="space-y-4">
            {permissionGroups.map((group) => (
              <div key={group.module} className="overflow-hidden rounded-2xl border border-gray-100">
                <button
                  onClick={() => setExpanded((current) => ({ ...current, [group.module]: !current[group.module] }))}
                  className="flex w-full items-center justify-between bg-gray-50 px-4 py-4 text-left"
                >
                  <div>
                    <p className="font-bold text-gray-900">{group.module}</p>
                    <p className="text-sm text-gray-500">{group.permissions.length} permission points</p>
                  </div>
                  <ChevronDown className={cn('h-4 w-4 text-gray-400 transition-transform', expanded[group.module] ? 'rotate-180' : '')} />
                </button>
                {expanded[group.module] && (
                  <div className="overflow-x-auto bg-white">
                    <table className="w-full text-sm">
                      <thead className="border-y border-gray-100 bg-white">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-black uppercase tracking-[0.24em] text-gray-400">Permission</th>
                          {roles.map((role) => (
                            <th key={role.id} className="px-4 py-3 text-center text-xs font-black uppercase tracking-[0.24em] text-gray-400">
                              {role.name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {group.permissions.map((permission, index) => (
                          <tr key={permission}>
                            <td className="px-4 py-3 font-semibold text-gray-800">{permission}</td>
                            {roles.map((role, roleIndex) => {
                              const checked = role.name === 'Platform Owner' || roleIndex <= Math.min(index % roles.length, roles.length - 1);
                              return (
                                <td key={`${role.id}-${permission}`} className="px-4 py-3 text-center">
                                  <input type="checkbox" checked={checked} readOnly className="h-4 w-4 rounded border-gray-300 text-[#237afc]" />
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </ModuleFrame>
  );
}

export function PackageBuilderModule({ packages }) {
  const [selectedId, setSelectedId] = useState(packages[0]?.id || '');
  const selected = useMemo(() => packages.find((item) => item.id === selectedId) || packages[0], [packages, selectedId]);
  const sectionBlueprint = ['General', 'Pricing', 'Services', 'Resources', 'Assessments', 'Recovery', 'Nutrition', 'Assignments', 'Conditions', 'Analytics'];

  return (
    <ModuleFrame
      badge="Package builder"
      title="Build package workflows for Nuetra, Fiteatsy, corporate, and retail delivery"
      description="Compose sections, services, resources, assignments, and conditions in a drag-and-drop-ready workflow builder."
      actions={
        <>
          <ActionButton icon={Save} label="Save draft" />
          <ActionButton icon={Plus} label="Create package" tone="primary" />
        </>
      }
    >
      <div className="grid gap-8 xl:grid-cols-[0.95fr_1.35fr]">
        <Panel title="Package library" subtitle="Current package states, brands, and pricing.">
          <div className="space-y-3">
            {packages.map((pkg) => (
              <button
                key={pkg.id}
                onClick={() => setSelectedId(pkg.id)}
                className={cn(
                  'w-full rounded-2xl border px-5 py-4 text-left transition',
                  selected?.id === pkg.id
                    ? 'border-[#237afc] bg-[#f5f9ff]'
                    : 'border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50'
                )}
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-black text-gray-900">{pkg.name}</p>
                    <p className="mt-1 text-sm text-gray-500">{pkg.brand} · {pkg.type} · {pkg.price}</p>
                  </div>
                  <Badge tone={pkg.status === 'Published' ? 'green' : 'amber'}>{pkg.status}</Badge>
                </div>
              </button>
            ))}
          </div>
        </Panel>

        <Panel title={selected?.name || 'Package builder'} subtitle="Modular structure for pricing, resources, and delivery conditions.">
          {selected ? (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Price</p>
                  <p className="mt-2 text-base font-bold text-gray-900">{selected.price}</p>
                </div>
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Services</p>
                  <p className="mt-2 text-base font-bold text-gray-900">{selected.services.length} configured</p>
                </div>
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Analytics</p>
                  <p className="mt-2 text-base font-bold text-gray-900">{selected.analytics}</p>
                </div>
              </div>

              <div className="mt-6 rounded-3xl border border-dashed border-gray-200 bg-[#fbfcff] p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-black uppercase tracking-[0.24em] text-gray-400">Builder canvas</p>
                    <h4 className="mt-2 text-lg font-black text-gray-900">Drag-and-drop section stack</h4>
                  </div>
                  <button className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
                    Add section
                  </button>
                </div>
                <div className="mt-5 space-y-3">
                  {sectionBlueprint.map((section) => (
                    <div key={section} className="flex items-center justify-between rounded-2xl border border-gray-100 bg-white px-4 py-4 shadow-sm">
                      <div className="flex items-center gap-3">
                        <GripVertical className="h-4 w-4 text-gray-300" />
                        <div>
                          <p className="font-bold text-gray-900">{section}</p>
                          <p className="text-sm text-gray-500">
                            {section === 'Resources'
                              ? 'Meal plans, exercise plans, PDFs, videos, questionnaires, protocols, AI resources'
                              : section === 'Conditions'
                                ? selected.conditions.join(', ')
                                : section === 'Services'
                                  ? selected.services.join(', ')
                                  : 'Configured workflow block ready for refinement'}
                          </p>
                        </div>
                      </div>
                      <button className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-600">
                        Edit
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <EmptyState icon={FolderKanban} title="No package selected" description="Pick a package to edit pricing, resources, and conditions." />
          )}
        </Panel>
      </div>
    </ModuleFrame>
  );
}

export function ServiceCatalogModule({ services }) {
  const [selectedId, setSelectedId] = useState(services[0]?.id || '');
  const selected = useMemo(() => services.find((item) => item.id === selectedId) || services[0], [services, selectedId]);

  return (
    <ModuleFrame
      badge="Service catalog"
      title="Reusable services for nutrition, consultation, recovery, exercise, AI, and diagnostics"
      description="Create reusable service definitions with pricing, duration, provider type, conditions, and assignment logic."
      actions={
        <>
          <ActionButton icon={Upload} label="Import services" />
          <ActionButton icon={Plus} label="Create service" tone="primary" />
        </>
      }
    >
      <div className="grid gap-8 xl:grid-cols-[1fr_1.2fr]">
        <Panel title="Catalog list" subtitle="Standardized reusable services by category.">
          <div className="space-y-3">
            {services.map((service) => (
              <button
                key={service.id}
                onClick={() => setSelectedId(service.id)}
                className={cn(
                  'w-full rounded-2xl border px-5 py-4 text-left transition',
                  selected?.id === service.id
                    ? 'border-[#237afc] bg-[#f5f9ff]'
                    : 'border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50'
                )}
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-black text-gray-900">{service.name}</p>
                    <p className="mt-1 text-sm text-gray-500">{service.category} · {service.duration} · {service.pricing}</p>
                  </div>
                  <Badge tone={service.visibility === 'Public' ? 'green' : 'amber'}>{service.visibility}</Badge>
                </div>
              </button>
            ))}
          </div>
        </Panel>
        <Panel title={selected?.name || 'Service details'} subtitle="Operational metadata and assignment model.">
          {selected ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Category</p><p className="mt-2 text-sm font-bold text-gray-900">{selected.category}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Provider type</p><p className="mt-2 text-sm font-bold text-gray-900">{selected.providerType}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Conditions</p><p className="mt-2 text-sm font-bold text-gray-900">{selected.conditions.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Resources</p><p className="mt-2 text-sm font-bold text-gray-900">{selected.resources.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4 md:col-span-2"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Assignment</p><p className="mt-2 text-sm font-bold text-gray-900">{selected.assignment}</p></div>
            </div>
          ) : (
            <EmptyState icon={Blocks} title="No service selected" description="Select a service to inspect pricing, resources, and visibility." />
          )}
        </Panel>
      </div>
    </ModuleFrame>
  );
}

export function PractitionersModule({ practitioners }) {
  return (
    <ModuleFrame
      badge="Practitioners"
      title="Professional profiles, qualifications, performance, and revenue"
      description="Manage certificates, schedules, organizations, packages, services, ratings, and commercial performance."
      actions={
        <>
          <ActionButton icon={CalendarDays} label="Open availability" />
          <ActionButton icon={Plus} label="Add practitioner" tone="primary" />
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-2">
        {practitioners.map((practitioner) => (
          <Panel key={practitioner.id} title={practitioner.name} subtitle={practitioner.title}>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Certificates</p><p className="mt-2 text-sm font-bold text-gray-900">{practitioner.certificates.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Qualifications</p><p className="mt-2 text-sm font-bold text-gray-900">{practitioner.qualifications.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Availability</p><p className="mt-2 text-sm font-bold text-gray-900">{practitioner.availability}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Revenue</p><p className="mt-2 text-sm font-bold text-gray-900">{practitioner.revenue}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4 md:col-span-2"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Organizations / packages / services</p><p className="mt-2 text-sm font-bold text-gray-900">{practitioner.organizations.join(', ')} · {practitioner.packages.join(', ')} · {practitioner.services.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4 md:col-span-2"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Performance</p><p className="mt-2 text-sm font-bold text-gray-900">{practitioner.performance} · {practitioner.rating}/5 rating</p></div>
            </div>
          </Panel>
        ))}
      </div>
    </ModuleFrame>
  );
}

export function MentorsModule({ mentors }) {
  return (
    <ModuleFrame
      badge="Mentors"
      title="Mentor programs, availability, package coverage, and delivery performance"
      description="Track mentor-led recovery programs, schedule availability, package alignment, service coverage, and cohort performance."
      actions={
        <>
          <ActionButton icon={Download} label="Export mentor performance" />
          <ActionButton icon={Plus} label="Add mentor" tone="primary" />
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-2">
        {mentors.map((mentor) => (
          <Panel key={mentor.id} title={mentor.name} subtitle={mentor.programs.join(' · ')}>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Availability</p><p className="mt-2 text-sm font-bold text-gray-900">{mentor.availability}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Nutrition plan relationship</p><p className="mt-2 text-sm font-bold text-gray-900">{mentor.nutritionPlans}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4 md:col-span-2"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Organizations / packages / services</p><p className="mt-2 text-sm font-bold text-gray-900">{mentor.organizations.join(', ')} · {mentor.packages.join(', ')} · {mentor.services.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4 md:col-span-2"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Performance</p><p className="mt-2 text-sm font-bold text-gray-900">{mentor.performance}</p></div>
            </div>
          </Panel>
        ))}
      </div>
    </ModuleFrame>
  );
}

export function ReportsModule({ reports }) {
  return (
    <ModuleFrame
      badge="Reports"
      title="Interactive revenue, workforce, recovery, package, and outcome analytics"
      description="Use date filters, exports, saved views, and cross-module charts to understand business and care performance."
      actions={
        <>
          <ActionButton icon={Save} label="Saved reports" />
          <ActionButton icon={Download} label="Export analytics" tone="primary" />
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-3">
        <Panel title="Revenue" subtitle="Monthly revenue trend">
          <MiniBarChart data={reports.revenue} color="from-[#111827] to-[#374151]" />
        </Panel>
        <Panel title="Recovery" subtitle="Organization recovery percentage">
          <MiniBarChart data={reports.recovery} suffix="%" color="from-emerald-500 to-teal-500" />
        </Panel>
        <Panel title="Package mix" subtitle="Revenue split by package family">
          <MiniBarChart data={reports.packageMix} suffix="%" color="from-violet-500 to-fuchsia-500" />
        </Panel>
      </div>
    </ModuleFrame>
  );
}

export function AuditLogsModule({ auditLogs }) {
  return (
    <ModuleFrame
      badge="Audit logs"
      title="Enterprise-grade audit visibility for sensitive platform actions"
      description="Filter by actor, action, target, timestamp, browser, IP, or request ID and export evidence when needed."
      actions={
        <>
          <ActionButton icon={Filter} label="Advanced filters" />
          <ActionButton icon={Download} label="Export logs" tone="primary" />
        </>
      }
    >
      <Panel title="Audit timeline" subtitle="Immutable operational history for sensitive changes.">
        <div className="overflow-hidden rounded-3xl border border-gray-100">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['Actor', 'Action', 'Target', 'Old Value', 'New Value', 'Timestamp', 'IP', 'Browser', 'Request ID'].map((header) => (
                  <th key={header} className="px-4 py-4 text-left text-xs font-black uppercase tracking-[0.24em] text-gray-400">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50/70">
                  <td className="px-4 py-4 font-bold text-gray-900">{log.actor}</td>
                  <td className="px-4 py-4 text-gray-600">{log.action}</td>
                  <td className="px-4 py-4 text-gray-600">{log.target}</td>
                  <td className="px-4 py-4 text-gray-500">{log.oldValue}</td>
                  <td className="px-4 py-4 text-gray-500">{log.newValue}</td>
                  <td className="px-4 py-4 text-gray-500">{log.timestamp}</td>
                  <td className="px-4 py-4 text-gray-500">{log.ip}</td>
                  <td className="px-4 py-4 text-gray-500">{log.browser}</td>
                  <td className="px-4 py-4"><Badge tone="blue">{log.requestId}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </ModuleFrame>
  );
}

export function SettingsModule({ settings }) {
  return (
    <ModuleFrame
      badge="Settings"
      title="Workspace, branding, auth, feature flags, email, API keys, and master data"
      description="Operational settings for platform identity, security, communication, and environment-level control."
      actions={
        <>
          <ActionButton icon={Eye} label="Preview workspace" />
          <ActionButton icon={Settings} label="Open settings" tone="primary" />
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-2">
        {settings.map((item) => (
          <Panel key={item.id} title={item.title} subtitle={item.group}>
            <p className="text-sm text-gray-500">{item.description}</p>
            <div className="mt-4 flex items-center justify-between">
              <Badge tone={item.status === 'Configured' || item.status === 'Active' ? 'green' : item.status === 'Sensitive' ? 'violet' : 'amber'}>
                {item.status}
              </Badge>
              <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
                Configure
                <ArrowUpRight className="h-4 w-4" />
              </button>
            </div>
          </Panel>
        ))}
      </div>
    </ModuleFrame>
  );
}

export function PlatformHealthModule() {
  return (
    <ModuleFrame
      badge="Platform health"
      title="Operational status, infrastructure confidence, and system readiness"
      description="Track gateway health, auth readiness, data freshness, notification integrity, and issue recovery posture."
      actions={
        <>
          <ActionButton icon={Activity} label="Open health report" />
          <ActionButton icon={Bot} label="Run incident review" tone="primary" />
        </>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-4">
        {[
          ['Gateway', 'Healthy', 'green'],
          ['Authentication', 'Healthy', 'green'],
          ['Email delivery', 'Needs review', 'amber'],
          ['Diagnostics sync', 'Healthy', 'green'],
        ].map(([label, value, tone]) => (
          <Panel key={label} title={label}>
            <Badge tone={tone}>{value}</Badge>
            <p className="mt-3 text-sm text-gray-500">Last checked within the past 5 minutes.</p>
          </Panel>
        ))}
      </div>
    </ModuleFrame>
  );
}
