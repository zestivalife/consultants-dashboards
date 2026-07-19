import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowUpRight,
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
  Mail,
  MoreHorizontal,
  PencilLine,
  Plus,
  Save,
  Search,
  Settings,
  Shield,
  Sparkles,
  Tag,
  Upload,
  UserCog,
  Users,
  XCircle,
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  ActionButton,
  Badge,
  cn,
  ControlBar,
  EmptyState,
  Field,
  FormSection,
  formatCurrency,
  MiniBarChart,
  ModuleFrame,
  Panel,
  ReviewCard,
  StatPill,
  WorkflowCard,
  WorkflowModal,
} from './OwnerConsolePrimitives';
import {
  buildUserProvisioningWorkflowSteps,
  getUserProvisioningWorkflowState,
} from '../../lib/workflows/userProvisioningWorkflow';

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
                    ['Add Employees', Mail],
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

export function PeopleAccessModule({
  summary,
  metadata,
  people = [],
  pagination,
  selectedUser,
  loading = false,
  detailLoading = false,
  error = null,
  filters,
  onSelectUser,
  onFilterChange,
  onCreateUser,
  onUpdateUser,
  onBulkAction,
  onAddNote,
  onAddAttachment,
  onAssignProducts,
  onAssignPackages,
  onAssignServices,
  onRevokeSession,
  onForceLogout,
  onResetUserPassword,
  onExportUsersCsv,
  onImportUsers,
  onRefresh,
}) {
  const [selectedIds, setSelectedIds] = useState([]);
  const [profileTab, setProfileTab] = useState('General');
  const [searchDraft, setSearchDraft] = useState(filters?.search || '');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showProvisioningModal, setShowProvisioningModal] = useState(false);
  const [provisioningStep, setProvisioningStep] = useState(0);
  const [latestProvisioning, setLatestProvisioning] = useState(null);
  const [latestTemporaryCredentials, setLatestTemporaryCredentials] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [isProfileDrawerOpen, setIsProfileDrawerOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [noteDraft, setNoteDraft] = useState('');
  const [attachmentDraft, setAttachmentDraft] = useState({
    file_name: '',
    file_url: '',
    content_type: '',
    attachment_type: 'document',
    note: '',
  });
  const [provisioningDraft, setProvisioningDraft] = useState({
    first_name: '',
    last_name: '',
    email: '',
    mobile_number: '',
    country_code: '+91',
    role: 'consultant',
    platform_key: '',
    product_id: '',
    product_ids: [],
    organization_id: '',
    department_id: '',
  });
  const [csvDraft, setCsvDraft] = useState('');
  const [roleBulkDraft, setRoleBulkDraft] = useState('consultant');
  const [form, setForm] = useState({
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: 'consultant',
    organization_id: '',
    department_id: '',
    employee_id: '',
    package_name: '',
    assigned_practitioner_id: '',
    assigned_mentor_id: '',
    assigned_consultant_id: '',
    primary_product_id: '',
    product_ids: [],
    package_ids: [],
    service_ids: [],
    status: 'ACTIVE',
    permissions: [],
    tags: [],
    note: '',
  });
  const profileTabs = ['General', 'Professional', 'Organizations', 'Permissions', 'Product Access', 'Status History', 'Login Sessions', 'Audit History', 'Assigned Packages', 'Assigned Services', 'Attachments', 'Notes'];
  const roleOptions = metadata?.roles || [];
  const permissionOptions = metadata?.permissions || [];
  const organizationOptions = metadata?.organizations || [];
  const departmentOptions = metadata?.departments || [];
  const productOptions = metadata?.products || [];
  const packageOptions = metadata?.packages || [];
  const serviceOptions = metadata?.services || [];
  const practitioners = metadata?.practitioners || [];
  const mentors = metadata?.mentors || [];
  const consultants = metadata?.consultants || [];
  const provisioningRoles = useMemo(() => {
    const allowed = new Set(['practitioner', 'mentor', 'consultant', 'corporate_admin']);
    const fromMetadata = roleOptions
      .map((role) => ({
        id: role.id,
        value: role.name.toLowerCase().replace(/ /g, '_'),
        label: role.name.replace(/_/g, ' '),
      }))
      .filter((role) => allowed.has(role.value));
    if (fromMetadata.length) return fromMetadata;
    return [
      { id: 'practitioner', value: 'practitioner', label: 'Practitioner' },
      { id: 'mentor', value: 'mentor', label: 'Mentor' },
      { id: 'consultant', value: 'consultant', label: 'Consultant' },
      { id: 'corporate_admin', value: 'corporate_admin', label: 'Corporate admin' },
    ];
  }, [roleOptions]);
  const provisioningWorkspaces = useMemo(
    () => departmentOptions.filter((department) => !provisioningDraft.organization_id || department.organization_id === provisioningDraft.organization_id),
    [departmentOptions, provisioningDraft.organization_id]
  );
  const provisioningPlatformOptions = useMemo(() => {
    const platformDefinitions = [
      {
        key: 'nuetra',
        name: 'Nuetra',
        description: 'Organization and workspace-scoped user creation path',
      },
      {
        key: 'fiteatsy',
        name: 'Fiteatsy',
        description: 'Product-scoped user creation path',
      },
    ];

    return platformDefinitions.map((platform) => {
      const product = productOptions.find((item) => {
        const searchable = `${item.key || ''} ${item.name || ''}`.toLowerCase();
        return searchable.includes(platform.key);
      });
      return {
        ...platform,
        product,
        product_id: product?.id || '',
      };
    });
  }, [productOptions]);
  const selectedProvisioningProductIdSet = useMemo(() => new Set(provisioningDraft.product_ids || []), [provisioningDraft.product_ids]);
  const selectedProvisioningPrimaryProduct = useMemo(() => {
    const primaryId = provisioningDraft.product_id || provisioningDraft.product_ids?.[0] || '';
    const product = productOptions.find((item) => item.id === primaryId);
    if (product) return product;
    const selectedPlatform = provisioningPlatformOptions.find((platform) => platform.key === provisioningDraft.platform_key);
    return selectedPlatform
      ? {
          id: selectedPlatform.product_id || selectedPlatform.key,
          key: selectedPlatform.key,
          name: selectedPlatform.name,
          status: selectedPlatform.product?.status || 'metadata_unavailable',
        }
      : null;
  }, [provisioningDraft.platform_key, provisioningDraft.product_id, provisioningDraft.product_ids, provisioningPlatformOptions, productOptions]);
  const provisioningSteps = useMemo(
    () => buildUserProvisioningWorkflowSteps({
      selectedProduct: selectedProvisioningPrimaryProduct,
      selectedPlatformKey: provisioningDraft.platform_key,
    }),
    [provisioningDraft.platform_key, selectedProvisioningPrimaryProduct]
  );
  const userProvisioningWorkflow = useMemo(
    () => getUserProvisioningWorkflowState({
      steps: provisioningSteps,
      activeStep: provisioningStep,
      selectedProduct: selectedProvisioningPrimaryProduct,
      selectedPlatformKey: provisioningDraft.platform_key,
    }),
    [provisioningDraft.platform_key, provisioningStep, provisioningSteps, selectedProvisioningPrimaryProduct]
  );
  const {
    productMode: provisioningProductMode,
    stepId: provisioningStepId,
    createStepIndex: provisioningCreateStepIndex,
    lastStepIndex: provisioningLastStepIndex,
    roleStepIndex: provisioningRoleStepIndex,
    contactStepIndex: provisioningContactStepIndex,
    platformStepIndex: provisioningProductStepIndex,
    organizationStepIndex: provisioningOrganizationStepIndex,
    workspaceStepIndex: provisioningWorkspaceStepIndex,
    scopeStepIndex: provisioningScopeStepIndex,
    requiresOrganization: provisioningRequiresOrganization,
    requiresWorkspace: provisioningRequiresWorkspace,
  } = userProvisioningWorkflow;
  const isFiteatsyProvisioning = provisioningProductMode === 'fiteatsy';
  const humanizeLabel = (value = '') =>
    value
      .toString()
      .replace(/_/g, ' ')
      .toLowerCase()
      .replace(/^./, (match) => match.toUpperCase());
  const safeSelectedUser = useMemo(() => {
    if (!selectedUser) return null;
    const displayName =
      selectedUser.name ||
      [selectedUser.first_name, selectedUser.last_name].filter(Boolean).join(' ').trim() ||
      selectedUser.email ||
      'User profile';

    return {
      ...selectedUser,
      name: displayName,
      email: selectedUser.email || 'No email added',
      role: selectedUser.role || 'member',
      status: selectedUser.status || 'UNKNOWN',
      verification: selectedUser.verification || 'Pending verification',
      memberships: Array.isArray(selectedUser.memberships) ? selectedUser.memberships : [],
      permissions: Array.isArray(selectedUser.permissions) ? selectedUser.permissions : [],
      product_access: Array.isArray(selectedUser.product_access) ? selectedUser.product_access : [],
      package_assignments: Array.isArray(selectedUser.package_assignments) ? selectedUser.package_assignments : [],
      service_assignments: Array.isArray(selectedUser.service_assignments) ? selectedUser.service_assignments : [],
      sessions: Array.isArray(selectedUser.sessions) ? selectedUser.sessions : [],
      notes: Array.isArray(selectedUser.notes) ? selectedUser.notes : [],
      attachments: Array.isArray(selectedUser.attachments) ? selectedUser.attachments : [],
      status_history: Array.isArray(selectedUser.status_history) ? selectedUser.status_history : [],
      audit_events: Array.isArray(selectedUser.audit_events) ? selectedUser.audit_events : [],
    };
  }, [selectedUser]);

  useEffect(() => {
    setSearchDraft(filters?.search || '');
  }, [filters?.search]);

  useEffect(() => {
    setProvisioningStep((current) => Math.min(current, Math.max(0, provisioningSteps.length - 1)));
  }, [provisioningSteps.length]);

  useEffect(() => {
    if (!safeSelectedUser) return;
    setForm((current) => ({
      ...current,
      email: safeSelectedUser.email || '',
      first_name: safeSelectedUser.first_name || '',
      last_name: safeSelectedUser.last_name || '',
      phone: safeSelectedUser.phone || '',
      role: (safeSelectedUser.role || 'consultant').toLowerCase(),
      organization_id: safeSelectedUser.memberships?.[0]?.organization_id || '',
      department_id: safeSelectedUser.memberships?.[0]?.department_id || '',
      employee_id: safeSelectedUser.memberships?.[0]?.employee_id || '',
      package_name: safeSelectedUser.memberships?.[0]?.package || '',
      assigned_practitioner_id: safeSelectedUser.memberships?.[0]?.practitioner_id || '',
      assigned_mentor_id: safeSelectedUser.memberships?.[0]?.mentor_id || '',
      assigned_consultant_id: safeSelectedUser.memberships?.[0]?.consultant_id || '',
      primary_product_id: safeSelectedUser.memberships?.[0]?.primary_product_id || safeSelectedUser.product_access.find((item) => item.is_primary)?.product_id || '',
      product_ids: safeSelectedUser.product_access.map((item) => item.product_id),
      package_ids: safeSelectedUser.package_assignments.map((item) => item.package_id),
      service_ids: safeSelectedUser.service_assignments.map((item) => item.service_id),
      status: safeSelectedUser.status || 'ACTIVE',
      permissions: safeSelectedUser.permissions || [],
      tags: safeSelectedUser.memberships?.[0]?.tags || [],
      note: '',
    }));
  }, [safeSelectedUser]);

  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const selectedProductIdSet = useMemo(() => new Set(form.product_ids || []), [form.product_ids]);
  const selectedPackageIdSet = useMemo(() => new Set(form.package_ids || []), [form.package_ids]);
  const selectedServiceIdSet = useMemo(() => new Set(form.service_ids || []), [form.service_ids]);
  const summaryMetric = (label) => summary?.metrics?.find((item) => item.label === label)?.value ?? 0;
  const adminsCount = useMemo(
    () => people.filter((item) => ['platform_owner', 'superuser', 'organization_admin', 'corporate_admin', 'support_admin'].includes(item.role)).length,
    [people]
  );
  const mentorCount = useMemo(() => people.filter((item) => item.role === 'mentor').length, [people]);
  const consultantCount = useMemo(() => people.filter((item) => ['consultant', 'senior_consultant', 'practitioner'].includes(item.role)).length, [people]);
  const suspendedCount = useMemo(() => people.filter((item) => item.status !== 'ACTIVE').length, [people]);
  const activeFilterProduct = filters?.product_id || '';
  const activeFilterStatus = filters?.status || '';
  const activeFilterVerification = filters?.verification || '';
  const activeRoleChip =
    filters?.role === 'platform_owner'
      ? 'owners'
      : filters?.role === 'mentor'
        ? 'mentors'
        : filters?.role === 'employee'
          ? 'employees'
          : filters?.role
            ? 'admins'
            : 'all';

  const updateForm = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const requireAction = (handler, label) => {
    if (typeof handler !== 'function') {
      setActionError(`${label} is not available. Refresh the page or contact support if this continues.`);
      return null;
    }
    setActionError(null);
    return handler;
  };
  const runAction = async (label, handler, ...args) => {
    const action = requireAction(handler, label);
    if (!action) return null;
    try {
      return await action(...args);
    } catch (nextError) {
      setActionError(nextError?.message || `${label} failed. Please try again.`);
      return null;
    }
  };
  const applyFilters = (patch) => {
    const action = requireAction(onFilterChange, 'Filtering people');
    if (!action) return;
    action(patch);
  };
  const toggleListValue = (key, value) => {
    setForm((current) => {
      const values = current[key] || [];
      return {
        ...current,
        [key]: values.includes(value) ? values.filter((item) => item !== value) : [...values, value],
      };
    });
  };
  const toggleProvisioningProduct = (productId) => {
    const product = productOptions.find((item) => item.id === productId);
    const nextPlatformKey = /fiteatsy/i.test(`${product?.key || ''} ${product?.name || ''}`) ? 'fiteatsy' : provisioningDraft.platform_key || 'nuetra';
    setProvisioningDraft((current) => {
      const values = current.product_ids || [];
      const nextValues = values.includes(productId)
        ? values.filter((item) => item !== productId)
        : [...values, productId];
      return {
        ...current,
        platform_key: nextPlatformKey,
        product_ids: nextValues,
        product_id: nextValues[0] || '',
      };
    });
  };
  const selectProvisioningPlatform = (platformKey) => {
    const platform = provisioningPlatformOptions.find((item) => item.key === platformKey);
    const productId = platform?.product_id || '';
    const isFiteatsyProduct = platformKey === 'fiteatsy';
    setProvisioningDraft((current) => ({
      ...current,
      platform_key: platformKey,
      product_id: productId,
      product_ids: productId ? [productId] : [],
      organization_id: isFiteatsyProduct ? '' : current.organization_id,
      department_id: isFiteatsyProduct ? '' : current.department_id,
    }));
  };
  const resetProvisioningDraft = (role = 'consultant') => {
    setProvisioningDraft({
      first_name: '',
      last_name: '',
      email: '',
      mobile_number: '',
      country_code: '+91',
      role,
      platform_key: '',
      product_id: '',
      product_ids: [],
      organization_id: '',
      department_id: '',
    });
    setProvisioningStep(0);
    setLatestProvisioning(null);
    setLatestTemporaryCredentials(null);
  };
  const openProvisioningWizard = (role = 'consultant') => {
    resetProvisioningDraft(role);
    setShowProvisioningModal(true);
  };
  const copyTemporaryCredential = async (value, label) => {
    if (!value) {
      setActionError(`${label} is not available.`);
      return;
    }
    if (typeof navigator === 'undefined' || !navigator.clipboard) {
      setActionError('Clipboard access is unavailable. Select and copy the value manually.');
      return;
    }
    await navigator.clipboard.writeText(value);
    setActionError(`${label} copied.`);
  };
  const togglePermission = (permissionKey) => {
    setForm((current) => ({
      ...current,
      permissions: current.permissions.includes(permissionKey)
        ? current.permissions.filter((item) => item !== permissionKey)
        : [...current.permissions, permissionKey],
    }));
  };

  const toggleSelected = (userId) => {
    setSelectedIds((current) =>
      current.includes(userId) ? current.filter((item) => item !== userId) : [...current, userId]
    );
  };

  const openUserDrawer = (userId) => {
    const action = requireAction(onSelectUser, 'Opening user profile');
    if (!action) return;
    action(userId);
    setIsProfileDrawerOpen(true);
  };

  const submitCreateUser = async () => {
    if (!form.email.trim()) {
      setActionError('Create user requires a work email.');
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await runAction('Create user', onCreateUser, {
        ...form,
        organization_id: form.organization_id || null,
        department_id: form.department_id || null,
        assigned_practitioner_id: form.assigned_practitioner_id || null,
        assigned_mentor_id: form.assigned_mentor_id || null,
        assigned_consultant_id: form.assigned_consultant_id || null,
        primary_product_id: form.primary_product_id || null,
        product_ids: form.product_ids,
        package_ids: form.package_ids,
        service_ids: form.service_ids,
        tags: form.tags.filter(Boolean),
      });
      if (result === null) return;
      if (result?.temporary_credentials) {
        setLatestTemporaryCredentials(result.temporary_credentials);
      }
      setShowCreateForm(false);
      setSelectedIds([]);
      setForm({
        email: '',
        first_name: '',
        last_name: '',
        phone: '',
        role: 'consultant',
        organization_id: '',
        department_id: '',
        employee_id: '',
        package_name: '',
        assigned_practitioner_id: '',
        assigned_mentor_id: '',
        assigned_consultant_id: '',
        primary_product_id: '',
        product_ids: [],
        package_ids: [],
        service_ids: [],
        status: 'ACTIVE',
        permissions: [],
        tags: [],
        note: '',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitUpdateUser = async () => {
    if (!selectedUser?.id) return;
    setIsSubmitting(true);
    try {
      await runAction('Update user', onUpdateUser, selectedUser.id, {
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone,
        role: form.role,
        organization_id: form.organization_id || null,
        department_id: form.department_id || null,
        employee_id: form.employee_id || null,
        package_name: form.package_name || null,
        assigned_practitioner_id: form.assigned_practitioner_id || null,
        assigned_mentor_id: form.assigned_mentor_id || null,
        assigned_consultant_id: form.assigned_consultant_id || null,
        primary_product_id: form.primary_product_id || null,
        product_ids: form.product_ids,
        package_ids: form.package_ids,
        service_ids: form.service_ids,
        status: form.status,
        permissions: form.permissions,
        tags: form.tags.filter(Boolean),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const applyBulkAction = async (action, extra = {}) => {
    const targetIds = extra.user_ids?.length ? extra.user_ids : selectedIds;
    if (!targetIds.length) {
      setActionError('Select at least one user before running a bulk action.');
      return;
    }
    setIsSubmitting(true);
    try {
      await runAction('Bulk user action', onBulkAction, { action, user_ids: targetIds, ...extra });
      setSelectedIds([]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitNote = async () => {
    if (!selectedUser?.id || !noteDraft.trim()) {
      setActionError('Select a user and enter a note before saving.');
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await runAction('Add user note', onAddNote, selectedUser.id, noteDraft.trim());
      if (result === null) return;
      setNoteDraft('');
      setProfileTab('Notes');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitAttachment = async () => {
    if (!selectedUser?.id || !attachmentDraft.file_name.trim() || !attachmentDraft.file_url.trim()) {
      setActionError('Attachment requires a selected user, file name, and file URL.');
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await runAction('Add attachment', onAddAttachment, selectedUser.id, {
        ...attachmentDraft,
        content_type: attachmentDraft.content_type || null,
        note: attachmentDraft.note || null,
      });
      if (result === null) return;
      setAttachmentDraft({
        file_name: '',
        file_url: '',
        content_type: '',
        attachment_type: 'document',
        note: '',
      });
      setProfileTab('Attachments');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetSelectedUserPassword = async () => {
    if (!selectedUser?.id) return;
    setIsSubmitting(true);
    try {
      const result = await runAction('Reset password', onResetUserPassword, selectedUser.id);
      if (result === null) return;
      setLatestTemporaryCredentials({
        username: result.username,
        temporary_password: result.temporary_password,
        must_change_password: result.must_change_password,
        message: result.message,
      });
      setActionError('Temporary password generated. Copy it before closing the credential panel.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitProvisioning = async () => {
    if (!provisioningDraft.role) {
      setActionError('Select a role before creating the user.');
      setProvisioningStep(provisioningRoleStepIndex);
      return;
    }
    if (!provisioningDraft.first_name.trim() || !provisioningDraft.last_name.trim() || !provisioningDraft.email.trim()) {
      setActionError('First name, last name, and email are required.');
      setProvisioningStep(provisioningContactStepIndex);
      return;
    }
    if (!provisioningDraft.product_id) {
      setActionError('Select Nuetra or Fiteatsy before creating the user.');
      setProvisioningStep(provisioningProductStepIndex);
      return;
    }
    if (!provisioningDraft.product_ids.length) {
      setActionError('Select at least one product before creating the user.');
      setProvisioningStep(provisioningScopeStepIndex);
      return;
    }
    if (provisioningRequiresOrganization && !provisioningDraft.organization_id) {
      setActionError('Select an organization before creating the user.');
      setProvisioningStep(provisioningOrganizationStepIndex);
      return;
    }
    if (provisioningRequiresWorkspace && provisioningWorkspaces.length && !provisioningDraft.department_id) {
      setActionError('Select a workspace before creating the user.');
      setProvisioningStep(provisioningWorkspaceStepIndex);
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await runAction('Create user', onCreateUser, {
        first_name: provisioningDraft.first_name.trim(),
        last_name: provisioningDraft.last_name.trim(),
        email: provisioningDraft.email.trim(),
        phone: [provisioningDraft.country_code.trim(), provisioningDraft.mobile_number.trim()].filter(Boolean).join(' ') || null,
        role: provisioningDraft.role,
        primary_product_id: provisioningDraft.product_id || provisioningDraft.product_ids[0] || null,
        product_ids: provisioningDraft.product_ids,
        organization_id: provisioningDraft.organization_id || null,
        department_id: provisioningWorkspaces.length ? provisioningDraft.department_id || null : null,
        status: 'ACTIVE',
      });
      if (result === null) return;
      setLatestProvisioning(result);
      setLatestTemporaryCredentials(result?.temporary_credentials || null);
      setProvisioningStep(provisioningCreateStepIndex >= 0 ? provisioningCreateStepIndex : provisioningLastStepIndex);
    } finally {
      setIsSubmitting(false);
    }
  };

  const syncProductAssignments = async () => {
    if (!selectedUser?.id) {
      setActionError('Select a user before syncing assignments.');
      return;
    }
    setIsSubmitting(true);
    try {
      const productResult = await runAction(
        'Assign products',
        onAssignProducts,
        selectedUser.id,
        form.product_ids.map((productId) => ({
          product_id: productId,
          organization_id: form.organization_id || null,
          role_id: null,
          status: 'ACTIVE',
          is_primary: productId === form.primary_product_id,
          permissions: [],
        }))
      );
      if (productResult === null) return;
      const packageResult = await runAction(
        'Assign packages',
        onAssignPackages,
        selectedUser.id,
        form.package_ids.map((packageId) => ({
          package_id: packageId,
          organization_id: form.organization_id || null,
          status: 'ACTIVE',
        }))
      );
      if (packageResult === null) return;
      await runAction(
        'Assign services',
        onAssignServices,
        selectedUser.id,
        form.service_ids.map((serviceId) => ({
          service_id: serviceId,
          organization_id: form.organization_id || null,
          status: 'ACTIVE',
        }))
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCsvExport = async () => {
    const csv = await runAction('Export users CSV', onExportUsersCsv);
    if (!csv || typeof window === 'undefined') return;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'people-access-export.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCsvImport = async () => {
    const lines = csvDraft
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    if (lines.length <= 1) {
      setActionError('CSV import requires a header row and at least one data row.');
      return;
    }
    const [headerLine, ...dataLines] = lines;
    const headers = headerLine.split(',').map((item) => item.trim());
    const rows = dataLines.map((line) => {
      const cells = line.split(',').map((item) => item.trim());
      return headers.reduce((acc, header, index) => ({ ...acc, [header]: cells[index] || '' }), {});
    });
    setIsSubmitting(true);
    try {
      const result = await runAction('Import users CSV', onImportUsers, rows);
      if (result === null) return;
      setCsvDraft('');
      setShowImportModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ModuleFrame
      badge="People & access"
      title="Identity, authority, sessions, and workforce governance"
      description="Search, filter, bulk-edit, import, export, and govern platform identities across owners, admins, mentors, consultants, practitioners, and employees."
      actions={
        <>
          <ActionButton icon={Upload} label="CSV import" onClick={() => setShowImportModal(true)} />
          <ActionButton icon={Download} label="CSV export" onClick={handleCsvExport} />
          <ActionButton icon={UserCog} label="Refresh" onClick={() => runAction('Refresh People & Access', onRefresh)} />
          <ActionButton icon={Plus} label="Add practitioner" onClick={() => openProvisioningWizard('practitioner')} />
          <ActionButton icon={Plus} label="Add mentor" onClick={() => openProvisioningWizard('mentor')} />
          <ActionButton icon={Plus} label="Add consultant" onClick={() => openProvisioningWizard('consultant')} />
          <ActionButton icon={Plus} label="Add corporate admin" tone="primary" onClick={() => openProvisioningWizard('corporate_admin')} />
        </>
      }
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {[
          { label: 'People', value: summaryMetric('People') || people.length, icon: Users, tone: 'from-[#237afc] to-[#58b6ff]', patch: { role: '', status: '', page: 1 } },
          { label: 'Admins', value: adminsCount, icon: Shield, tone: 'from-violet-500 to-fuchsia-500', patch: { role: 'organization_admin', page: 1 } },
          { label: 'Mentors', value: mentorCount, icon: UserCog, tone: 'from-amber-500 to-orange-500', patch: { role: 'mentor', page: 1 } },
          { label: 'Consultants', value: consultantCount, icon: BriefcaseBusiness, tone: 'from-emerald-500 to-teal-500', patch: { role: 'consultant', page: 1 } },
          { label: 'Suspended', value: suspendedCount, icon: Mail, tone: 'from-rose-500 to-red-500', patch: { status: 'SUSPENDED', page: 1 } },
        ].map((metric) => (
          <button
            key={metric.label}
            type="button"
            onClick={() => applyFilters(metric.patch)}
            className="text-left transition-transform hover:-translate-y-0.5"
          >
            <StatPill icon={metric.icon} label={metric.label} value={metric.value} tone={metric.tone} />
          </button>
        ))}
      </div>

      {error ? (
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
          {error}
        </div>
      ) : null}
      {actionError ? (
        <div className="fixed right-6 top-6 z-50 max-w-md rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800 shadow-2xl">
          {actionError}
        </div>
      ) : null}

      <div className="mt-8 space-y-6">
          <ControlBar
            searchPlaceholder="Search people, roles, organizations, sessions, or package assignments..."
            searchValue={searchDraft}
            onSearchChange={setSearchDraft}
            onSearchKeyDown={(event) => {
              if (event.key === 'Enter') applyFilters({ search: searchDraft, page: 1 });
            }}
            filters={[
              { key: 'all', label: 'All' },
              { key: 'owners', label: 'Platform Owners' },
              { key: 'admins', label: 'Admins' },
              { key: 'mentors', label: 'Mentors' },
              { key: 'employees', label: 'Employees' },
            ]}
            activeFilter={activeRoleChip}
            onFilterChange={(key) => {
              if (key === 'all') return applyFilters({ role: '', page: 1 });
              if (key === 'owners') return applyFilters({ role: 'platform_owner', page: 1 });
              if (key === 'mentors') return applyFilters({ role: 'mentor', page: 1 });
              if (key === 'employees') return applyFilters({ role: 'employee', page: 1 });
              return applyFilters({ role: 'organization_admin', page: 1 });
            }}
            rightControls={
              <div className="ml-2 flex items-center gap-2">
                <select
                  value={activeFilterProduct}
                  onChange={(event) => applyFilters({ product_id: event.target.value, page: 1 })}
                  className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600 outline-none"
                >
                  <option value="">All products</option>
                  {productOptions.map((product) => (
                    <option key={product.id} value={product.id}>{product.name}</option>
                  ))}
                </select>
                <select
                  value={activeFilterStatus}
                  onChange={(event) => applyFilters({ status: event.target.value, page: 1 })}
                  className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600 outline-none"
                >
                  <option value="">All statuses</option>
                  <option value="ACTIVE">Active</option>
                  <option value="ACTIVE">Active</option>
                  <option value="PENDING_VERIFICATION">Pending verification</option>
                  <option value="INACTIVE">Inactive</option>
                  <option value="LOCKED">Locked</option>
                  <option value="SUSPENDED">Suspended</option>
                </select>
                <select
                  value={activeFilterVerification}
                  onChange={(event) => applyFilters({ verification: event.target.value, page: 1 })}
                  className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600 outline-none"
                >
                  <option value="">All verification</option>
                  <option value="verified">Verified</option>
                  <option value="pending">Pending</option>
                </select>
                <button
                  onClick={() => setShowAdvancedFilters(true)}
                  className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600"
                >
                  <Filter className="h-4 w-4" />
                  Advanced
                </button>
                <button
                  onClick={() => applyFilters({ search: searchDraft, page: 1 })}
                  className="inline-flex items-center gap-2 rounded-xl border border-[#237afc] bg-[#f5f9ff] px-3 py-2 text-sm font-bold text-[#237afc]"
                >
                  <Search className="h-4 w-4" />
                  Apply search
                </button>
              </div>
            }
          />

          <Panel title="Enterprise roster" subtitle="Bulk-ready people management with status, role, and org visibility.">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-gray-50 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="blue">{selectedIds.length} selected</Badge>
                <button onClick={() => applyBulkAction('activate')} className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">Activate</button>
                <button onClick={() => applyBulkAction('suspend')} className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">Suspend</button>
                <button onClick={() => applyBulkAction('deactivate')} className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">Deactivate</button>
                <select
                  value={roleBulkDraft}
                  onChange={(event) => setRoleBulkDraft(event.target.value)}
                  className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600 outline-none"
                >
                  <option value="consultant">consultant</option>
                  <option value="mentor">mentor</option>
                  <option value="practitioner">practitioner</option>
                  <option value="organization_admin">organization admin</option>
                </select>
                <button onClick={() => applyBulkAction('assign_role', { role: roleBulkDraft })} className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">Assign role</button>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button onClick={() => setShowProvisioningModal(true)} className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">Create user</button>
                <button onClick={() => setShowImportModal(true)} className="rounded-full border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">Import CSV</button>
              </div>
            </div>
            <div className="overflow-hidden rounded-3xl border border-gray-100">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Select', 'Person', 'Role', 'Products', 'Organizations', 'Assigned packages', 'Verification', 'Status'].map((header) => (
                      <th key={header} className="px-4 py-3 text-left text-[11px] font-black uppercase tracking-[0.18em] text-gray-400">{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {people.map((person) => (
                    <tr key={person.id} className="cursor-pointer hover:bg-gray-50/80" onClick={() => openUserDrawer(person.id)}>
                      <td className="px-4 py-3" onClick={(event) => event.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedIdSet.has(person.id)}
                          onChange={() => toggleSelected(person.id)}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={() => openUserDrawer(person.id)} className="text-left">
                          <p className="font-semibold text-gray-900">{person.name}</p>
                          <p className="text-xs text-gray-500">{person.email}</p>
                        </button>
                      </td>
                      <td className="px-4 py-3"><Badge tone="blue">{person.role.replace(/_/g, ' ')}</Badge></td>
                      <td className="px-4 py-3 text-sm text-gray-500">{person.products?.length ? person.products.join(', ') : 'No products'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{person.organization || 'Unassigned'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{person.package || 'No package'}</td>
                      <td className="px-4 py-3">
                        <Badge tone={person.verification === 'Verified' ? 'green' : 'amber'}>{person.verification}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={person.status === 'ACTIVE' ? 'green' : 'red'}>{person.status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {pagination ? (
              <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                <p>
                  Page {pagination.page} of {pagination.total_pages} · {pagination.total} total identities
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => applyFilters({ page: Math.max(1, pagination.page - 1) })}
                    disabled={pagination.page <= 1}
                    className="rounded-full border border-gray-200 bg-white px-4 py-2 font-bold text-gray-600 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => applyFilters({ page: Math.min(pagination.total_pages, pagination.page + 1) })}
                    disabled={pagination.page >= pagination.total_pages}
                    className="rounded-full border border-gray-200 bg-white px-4 py-2 font-bold text-gray-600 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            ) : null}
          </Panel>

      </div>

      {showCreateForm ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/40 p-6">
          <div className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-[28px] bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-[#237afc]">Create identity</p>
                <h3 className="mt-2 text-2xl font-black text-gray-900">Add a mentor, consultant, admin, or employee</h3>
                <p className="mt-2 text-sm text-gray-500">Keep creation in a focused workflow instead of pinning a long form to the workspace.</p>
              </div>
              <button onClick={() => setShowCreateForm(false)} className="rounded-2xl border border-gray-200 px-3 py-2 text-sm font-bold text-gray-500">
                Close
              </button>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <input value={form.email} onChange={(event) => updateForm('email', event.target.value)} placeholder="Work email" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
              <input value={form.phone} onChange={(event) => updateForm('phone', event.target.value)} placeholder="Phone number" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
              <input value={form.first_name} onChange={(event) => updateForm('first_name', event.target.value)} placeholder="First name" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
              <input value={form.last_name} onChange={(event) => updateForm('last_name', event.target.value)} placeholder="Last name" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
              <select value={form.role} onChange={(event) => updateForm('role', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                {roleOptions.map((role) => (
                  <option key={role.id} value={role.name.toLowerCase().replace(/ /g, '_')}>{role.name}</option>
                ))}
              </select>
              <select value={form.status} onChange={(event) => updateForm('status', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                {['ACTIVE', 'PENDING_VERIFICATION', 'ACTIVE', 'INACTIVE', 'LOCKED', 'SUSPENDED'].map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
              <select value={form.organization_id} onChange={(event) => updateForm('organization_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">Select organization</option>
                {organizationOptions.map((organization) => (
                  <option key={organization.id} value={organization.id}>{organization.name}</option>
                ))}
              </select>
              <select value={form.department_id} onChange={(event) => updateForm('department_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">Select department</option>
                {departmentOptions
                  .filter((department) => !form.organization_id || department.organization_id === form.organization_id)
                  .map((department) => (
                    <option key={department.id} value={department.id}>{department.name}</option>
                  ))}
              </select>
              <input value={form.employee_id} onChange={(event) => updateForm('employee_id', event.target.value)} placeholder="Employee ID" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
              <input value={form.package_name} onChange={(event) => updateForm('package_name', event.target.value)} placeholder="Assigned package" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
              <select value={form.primary_product_id} onChange={(event) => updateForm('primary_product_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">Primary product</option>
                {productOptions.map((product) => (
                  <option key={product.id} value={product.id}>{product.name}</option>
                ))}
              </select>
              <select value={form.assigned_practitioner_id} onChange={(event) => updateForm('assigned_practitioner_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">Assigned practitioner</option>
                {practitioners.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}
              </select>
              <select value={form.assigned_mentor_id} onChange={(event) => updateForm('assigned_mentor_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">Assigned mentor</option>
                {mentors.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}
              </select>
              <select value={form.assigned_consultant_id} onChange={(event) => updateForm('assigned_consultant_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none md:col-span-2">
                <option value="">Assigned consultant</option>
                {consultants.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}
              </select>
              <div className="rounded-2xl border border-gray-200 px-4 py-3 md:col-span-2">
                <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Products</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {productOptions.map((product) => (
                    <button
                      key={product.id}
                      type="button"
                      onClick={() => toggleListValue('product_ids', product.id)}
                      className={cn(
                        'rounded-full border px-3 py-2 text-xs font-bold',
                        selectedProductIdSet.has(product.id) ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]' : 'border-gray-200 bg-white text-gray-600'
                      )}
                    >
                      {product.name}
                    </button>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-gray-200 px-4 py-3 md:col-span-2">
                <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Package assignments</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {packageOptions.map((pkg) => (
                    <button
                      key={pkg.id}
                      type="button"
                      onClick={() => toggleListValue('package_ids', pkg.id)}
                      className={cn(
                        'rounded-full border px-3 py-2 text-xs font-bold',
                        selectedPackageIdSet.has(pkg.id) ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]' : 'border-gray-200 bg-white text-gray-600'
                      )}
                    >
                      {pkg.name}
                    </button>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-gray-200 px-4 py-3 md:col-span-2">
                <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Service assignments</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {serviceOptions.map((service) => (
                    <button
                      key={service.id}
                      type="button"
                      onClick={() => toggleListValue('service_ids', service.id)}
                      className={cn(
                        'rounded-full border px-3 py-2 text-xs font-bold',
                        selectedServiceIdSet.has(service.id) ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]' : 'border-gray-200 bg-white text-gray-600'
                      )}
                    >
                      {service.name}
                    </button>
                  ))}
                </div>
              </div>
              <textarea value={form.note} onChange={(event) => updateForm('note', event.target.value)} placeholder="Operator note" className="min-h-[110px] rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none md:col-span-2" />
            </div>
            <div className="mt-6">
              <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Authorities</p>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {permissionOptions.map((permission) => (
                  <label key={permission.id} className="flex items-start gap-3 rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3 text-sm">
                    <input
                      type="checkbox"
                      checked={form.permissions.includes(permission.key)}
                      onChange={() => togglePermission(permission.key)}
                      className="mt-1 h-4 w-4 rounded border-gray-300"
                    />
                    <span>
                      <span className="block font-bold text-gray-900">{permission.label}</span>
                      <span className="block text-xs text-gray-500">{permission.key}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="mt-6 flex gap-3">
              <ActionButton icon={Plus} label="Create user" tone="primary" onClick={submitCreateUser} disabled={isSubmitting} />
              <ActionButton icon={XCircle} label="Cancel" onClick={() => setShowCreateForm(false)} />
            </div>
          </div>
        </div>
      ) : null}

      {showProvisioningModal ? (
        <WorkflowModal
          eyebrow="User credential workflow"
          title="Create a practitioner, mentor, consultant, or corporate admin"
          description="Create the user account immediately, then copy the one-time temporary password for manual secure sharing."
          steps={provisioningSteps}
          activeStep={provisioningStep}
          onStepChange={(index) => !latestProvisioning && setProvisioningStep(index)}
          onClose={() => setShowProvisioningModal(false)}
          footer={
            <div className="flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setProvisioningStep((current) => Math.max(0, current - 1))}
                disabled={provisioningStep === 0 || Boolean(latestProvisioning)}
                className="z-btn z-btn-secondary"
              >
                Back
              </button>
              <div className="flex flex-wrap gap-3">
                <button type="button" className="z-btn z-btn-secondary" onClick={() => setShowProvisioningModal(false)}>
                  Cancel
                </button>
                {!latestProvisioning && provisioningStep < provisioningLastStepIndex ? (
                  <button
                    type="button"
                    className="z-btn z-btn-primary"
                    onClick={() => setProvisioningStep((current) => Math.min(provisioningLastStepIndex, current + 1))}
                  >
                    Next
                  </button>
                ) : null}
                {!latestProvisioning && provisioningCreateStepIndex >= 0 && provisioningStep === provisioningCreateStepIndex ? (
                  <ActionButton icon={KeyRound} label="Create user" tone="primary" onClick={submitProvisioning} disabled={isSubmitting} />
                ) : null}
              </div>
            </div>
          }
        >
          {provisioningStepId === 'role' ? (
            <WorkflowCard
              title="Select role"
              description="Choose the operational role. The user remains part of the same platform identity workflow."
            >
              <div className="grid gap-3 md:grid-cols-2">
                {provisioningRoles.map((role) => (
                  <button
                    key={role.value}
                    type="button"
                    onClick={() => setProvisioningDraft((current) => ({ ...current, role: role.value }))}
                    className={cn(
                      'rounded-2xl border px-4 py-4 text-left transition',
                      provisioningDraft.role === role.value ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc] shadow-sm' : 'border-gray-100 bg-white text-gray-700'
                    )}
                  >
                    <span className="block z-h4">{humanizeLabel(role.label)}</span>
                    <span className="mt-1 block z-subtitle text-gray-500">Permission-scoped account creation</span>
                  </button>
                ))}
              </div>
            </WorkflowCard>
          ) : null}

          {provisioningStepId === 'contact' ? (
            <WorkflowCard
              title="Enter contact information"
              description="These details are stored on the user profile and carried into onboarding."
            >
              <FormSection title="User details" description="Use the person’s legal or work profile details for onboarding continuity.">
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="First name">
                    <input
                      value={provisioningDraft.first_name}
                      onChange={(event) => setProvisioningDraft((current) => ({ ...current, first_name: event.target.value }))}
                      placeholder="Enter first name"
                      className="z-input"
                    />
                  </Field>
                  <Field label="Last name">
                    <input
                      value={provisioningDraft.last_name}
                      onChange={(event) => setProvisioningDraft((current) => ({ ...current, last_name: event.target.value }))}
                      placeholder="Enter last name"
                      className="z-input"
                    />
                  </Field>
                  <Field label="Email">
                    <input
                      value={provisioningDraft.email}
                      onChange={(event) => setProvisioningDraft((current) => ({ ...current, email: event.target.value }))}
                      placeholder="name@company.com"
                      className="z-input"
                      type="email"
                    />
                  </Field>
                  <div className="grid grid-cols-[112px_1fr] gap-3">
                    <Field label="Country code">
                      <input
                        value={provisioningDraft.country_code}
                        onChange={(event) => setProvisioningDraft((current) => ({ ...current, country_code: event.target.value }))}
                        placeholder="+91"
                        className="z-input"
                      />
                    </Field>
                    <Field label="Mobile number">
                      <input
                        value={provisioningDraft.mobile_number}
                        onChange={(event) => setProvisioningDraft((current) => ({ ...current, mobile_number: event.target.value }))}
                        placeholder="Enter mobile number"
                        className="z-input"
                      />
                    </Field>
                  </div>
                </div>
              </FormSection>
            </WorkflowCard>
          ) : null}

          {provisioningStepId === 'platform' ? (
            <WorkflowCard
              title="Select platform"
              description="Choose the primary product first. The next steps adapt automatically for Nuetra or Fiteatsy."
            >
              <div className="grid gap-3 md:grid-cols-2">
                {provisioningPlatformOptions.map((platform) => (
                  <button
                    key={platform.key}
                    type="button"
                    onClick={() => selectProvisioningPlatform(platform.key)}
                    className={cn(
                      'rounded-2xl border px-4 py-4 text-left transition',
                      provisioningDraft.platform_key === platform.key ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc] shadow-sm' : 'border-gray-100 bg-white text-gray-700'
                    )}
                  >
                    <span className="block z-h4">{platform.name}</span>
                    <span className="mt-1 block z-subtitle text-gray-500">{platform.description}</span>
                    {!platform.product_id ? (
                      <span className="mt-3 block rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-700">
                        Product metadata unavailable
                      </span>
                    ) : null}
                  </button>
                ))}
              </div>
            </WorkflowCard>
          ) : null}

          {provisioningStepId === 'organization' ? (
            <WorkflowCard title="Select organization" description="Choose the Nuetra organization this user will belong to.">
              <div className="grid gap-3 md:grid-cols-2">
                {organizationOptions.map((organization) => (
                  <button
                    key={organization.id}
                    type="button"
                    onClick={() => setProvisioningDraft((current) => ({ ...current, organization_id: organization.id, department_id: '' }))}
                    className={cn(
                      'rounded-2xl border px-4 py-4 text-left transition',
                      provisioningDraft.organization_id === organization.id ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc] shadow-sm' : 'border-gray-100 bg-white text-gray-700'
                    )}
                  >
                    <span className="block z-h4">{organization.name}</span>
                    <span className="mt-1 block z-subtitle text-gray-500">{organization.status || 'Organization'} workspace</span>
                  </button>
                ))}
                {!organizationOptions.length ? (
                  <div className="rounded-2xl border border-amber-100 bg-amber-50 px-4 py-4 text-left">
                    <span className="block z-h4 text-amber-800">No organizations available</span>
                    <span className="mt-1 block z-subtitle text-amber-700">Organization metadata could not be loaded for this Nuetra user.</span>
                  </div>
                ) : null}
              </div>
            </WorkflowCard>
          ) : null}

          {provisioningStepId === 'workspace' ? (
            <WorkflowCard title="Select workspace" description="Choose the department or workspace where this user will start.">
              <div className="grid gap-3 md:grid-cols-2">
                {provisioningWorkspaces.map((department) => (
                  <button
                    key={department.id}
                    type="button"
                    onClick={() => setProvisioningDraft((current) => ({ ...current, department_id: department.id }))}
                    className={cn(
                      'rounded-2xl border px-4 py-4 text-left transition',
                      provisioningDraft.department_id === department.id ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc] shadow-sm' : 'border-gray-100 bg-white text-gray-700'
                    )}
                  >
                    <span className="block z-h4">{department.name}</span>
                    <span className="mt-1 block z-subtitle text-gray-500">Workspace assignment</span>
                  </button>
                ))}
                {!provisioningWorkspaces.length ? (
                  <div className="rounded-2xl border border-[#237afc] bg-[#f5f9ff] px-4 py-4 text-left text-[#237afc] shadow-sm">
                    <span className="block z-h4">{departmentOptions.length ? 'Organization default workspace' : 'No workspaces available'}</span>
                    <span className="mt-1 block z-subtitle text-gray-500">
                      {departmentOptions.length
                        ? 'No departments are configured for this organization, so this user will start at the organization workspace.'
                        : 'Workspace metadata could not be loaded for this Nuetra user.'}
                    </span>
                  </div>
                ) : null}
              </div>
            </WorkflowCard>
          ) : null}

          {provisioningStepId === 'products' || provisioningStepId === 'scope' ? (
            <WorkflowCard
              title="Select products"
              description={isFiteatsyProvisioning ? 'Confirm the Fiteatsy product scope for this user.' : 'Configure products, packages, services, and permission context for this Nuetra user.'}
            >
              <div className="space-y-5">
                <div>
                  <p className="z-label text-gray-500">Products</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {productOptions.map((product) => (
                      <button
                        key={product.id}
                        type="button"
                        onClick={() => toggleProvisioningProduct(product.id)}
                        className={cn(
                          'rounded-full border px-4 py-3 z-btn',
                          selectedProvisioningProductIdSet.has(product.id) ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]' : 'border-gray-200 bg-white text-gray-600'
                        )}
                      >
                        {product.name}
                      </button>
                    ))}
                    {!productOptions.length ? (
                      <div className="rounded-2xl border border-amber-100 bg-amber-50 px-4 py-4 text-left">
                        <span className="block z-h4 text-amber-800">Unable to load products</span>
                        <span className="mt-1 block z-subtitle text-amber-700">The workflow remains available, but product metadata is unavailable right now.</span>
                      </div>
                    ) : null}
                  </div>
                </div>

                {!isFiteatsyProvisioning ? (
                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="rounded-2xl border border-gray-100/80 bg-gray-50/80 p-4">
                      <p className="z-label text-gray-500">Available packages</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {packageOptions.length ? packageOptions.slice(0, 8).map((pkg) => (
                          <span key={pkg.id} className="rounded-full border border-gray-200 bg-white px-3 py-2 z-subtitle text-gray-600">{pkg.name}</span>
                        )) : <span className="z-subtitle text-gray-500">No packages configured yet.</span>}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-gray-100/80 bg-gray-50/80 p-4">
                      <p className="z-label text-gray-500">Available services</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {serviceOptions.length ? serviceOptions.slice(0, 8).map((service) => (
                          <span key={service.id} className="rounded-full border border-gray-200 bg-white px-3 py-2 z-subtitle text-gray-600">{service.name}</span>
                        )) : <span className="z-subtitle text-gray-500">No services configured yet.</span>}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-gray-100/80 bg-gray-50/80 p-4 lg:col-span-2">
                      <p className="z-label text-gray-500">Available permissions</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {permissionOptions.length ? permissionOptions.slice(0, 10).map((permission) => (
                          <span key={permission.key || permission.id} className="rounded-full border border-gray-200 bg-white px-3 py-2 z-subtitle text-gray-600">
                            {permission.label || permission.key}
                          </span>
                        )) : <span className="z-subtitle text-gray-500">No permissions configured yet.</span>}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </WorkflowCard>
          ) : null}

          {provisioningStepId === 'review' ? (
            <WorkflowCard title="Review user" description="Confirm the account details before creating temporary credentials.">
              <div className="grid gap-3 md:grid-cols-2">
                {[
                  ['Role', humanizeLabel(provisioningDraft.role)],
                  ['User', `${provisioningDraft.first_name} ${provisioningDraft.last_name}`.trim() || 'Not added'],
                  ['Email', provisioningDraft.email || 'Not added'],
                  ['Mobile', `${provisioningDraft.country_code || ''} ${provisioningDraft.mobile_number || ''}`.trim() || 'Not added'],
                  ['Platform', selectedProvisioningPrimaryProduct?.name || 'Not selected'],
                  ['Products', productOptions.length ? productOptions.filter((item) => provisioningDraft.product_ids.includes(item.id)).map((item) => item.name).join(', ') || 'Not selected' : 'Unable to load products'],
                  ['Organization', isFiteatsyProvisioning ? 'Not required for Fiteatsy' : organizationOptions.find((item) => item.id === provisioningDraft.organization_id)?.name || 'Not selected'],
                  ['Workspace', isFiteatsyProvisioning ? 'Product workspace' : provisioningWorkspaces.find((item) => item.id === provisioningDraft.department_id)?.name || 'Organization default workspace'],
                ].map(([label, value]) => <ReviewCard key={label} label={label} value={value} />)}
              </div>
            </WorkflowCard>
          ) : null}

          {provisioningStepId === 'create' ? (
            latestProvisioning ? (
              <WorkflowCard title="User created" description="Copy these credentials now. The temporary password will not be shown again after you close this workflow.">
                <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="mt-1 h-6 w-6 text-emerald-500" />
                    <div>
                      <p className="z-h4 text-gray-900">Temporary credentials are ready</p>
                      <p className="mt-2 z-body text-gray-700">
                        Share them through your approved secure channel. The user must change this password before entering the workspace.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="mt-5 grid gap-3 md:grid-cols-2">
                  <div className="rounded-2xl border border-gray-100 bg-white p-4">
                    <p className="z-label text-gray-500">Username</p>
                    <p className="mt-2 break-all z-table-content font-semibold text-gray-900">
                      {latestTemporaryCredentials?.username || latestProvisioning.email || 'Not available'}
                    </p>
                    <ActionButton
                      icon={Copy}
                      label="Copy username"
                      onClick={() => copyTemporaryCredential(latestTemporaryCredentials?.username || latestProvisioning.email, 'Username')}
                    />
                  </div>
                  <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
                    <p className="z-label text-amber-700">Temporary password</p>
                    <p className="mt-2 break-all font-mono text-lg font-black text-gray-900">
                      {latestTemporaryCredentials?.temporary_password || 'Not returned'}
                    </p>
                    <ActionButton
                      icon={Copy}
                      label="Copy temporary password"
                      tone="primary"
                      onClick={() => copyTemporaryCredential(latestTemporaryCredentials?.temporary_password, 'Temporary password')}
                      disabled={!latestTemporaryCredentials?.temporary_password}
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => resetProvisioningDraft(provisioningDraft.role)}
                  className="mt-5 z-btn z-btn-secondary"
                >
                  Create another user
                </button>
              </WorkflowCard>
            ) : (
              <WorkflowCard title="Create user" description="This persists the user, creates audit events, and generates a one-time temporary password without requiring email delivery.">
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-2xl bg-gray-50 p-4">
                    <p className="z-label text-gray-500">User</p>
                    <p className="mt-1 z-table-content font-semibold text-gray-900">{provisioningDraft.email || 'Not added'}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 p-4">
                    <p className="z-label text-gray-500">Role</p>
                    <p className="mt-1 z-table-content font-semibold text-gray-900">{humanizeLabel(provisioningDraft.role)}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 p-4">
                    <p className="z-label text-gray-500">Product</p>
                    <p className="mt-1 z-table-content font-semibold text-gray-900">{selectedProvisioningPrimaryProduct?.name || 'Not selected'}</p>
                    {!provisioningDraft.product_id ? (
                      <p className="mt-2 text-xs font-semibold text-amber-700">Unable to load product metadata for submission.</p>
                    ) : null}
                  </div>
                </div>
                <div className="mt-5 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-800">
                  The temporary password is returned once. Copy it from the success screen before closing this workflow.
                </div>
              </WorkflowCard>
            )
          ) : null}
        </WorkflowModal>
      ) : null}

      {showImportModal ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/40 p-6">
          <div className="w-full max-w-3xl rounded-[28px] bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-[#237afc]">CSV import</p>
                <h3 className="mt-2 text-2xl font-black text-gray-900">Paste or stage a roster import</h3>
                <p className="mt-2 text-sm text-gray-500">Expected headers: email, first_name, last_name, role, organization_id, department_id, employee_id, primary_product_id, status.</p>
              </div>
              <button onClick={() => setShowImportModal(false)} className="rounded-2xl border border-gray-200 px-3 py-2 text-sm font-bold text-gray-500">Close</button>
            </div>
            <textarea
              value={csvDraft}
              onChange={(event) => setCsvDraft(event.target.value)}
              placeholder="email,first_name,last_name,role,organization_id,department_id,employee_id,primary_product_id,status"
              className="mt-6 min-h-[220px] w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none"
            />
            <div className="mt-6 flex gap-3">
              <ActionButton icon={Upload} label="Run import" tone="primary" onClick={handleCsvImport} disabled={isSubmitting || !csvDraft.trim()} />
              <ActionButton icon={Download} label="Export current roster" onClick={handleCsvExport} />
            </div>
          </div>
        </div>
      ) : null}

      {latestTemporaryCredentials && !showProvisioningModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-6">
          <div className="w-full max-w-2xl rounded-[28px] bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-[#237afc]">One-time credentials</p>
                <h3 className="mt-2 text-2xl font-black text-gray-900">Temporary password generated</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Copy this password now. It is never stored in plaintext and will not be shown again after this panel closes.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setLatestTemporaryCredentials(null)}
                className="rounded-2xl border border-gray-200 px-3 py-2 text-sm font-bold text-gray-500"
              >
                Close
              </button>
            </div>
            <div className="mt-6 grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
                <p className="z-label text-gray-500">Username</p>
                <p className="mt-2 break-all z-table-content font-semibold text-gray-900">{latestTemporaryCredentials.username}</p>
                <ActionButton icon={Copy} label="Copy username" onClick={() => copyTemporaryCredential(latestTemporaryCredentials.username, 'Username')} />
              </div>
              <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
                <p className="z-label text-amber-700">Temporary password</p>
                <p className="mt-2 break-all font-mono text-lg font-black text-gray-900">{latestTemporaryCredentials.temporary_password}</p>
                <ActionButton
                  icon={Copy}
                  label="Copy temporary password"
                  tone="primary"
                  onClick={() => copyTemporaryCredential(latestTemporaryCredentials.temporary_password, 'Temporary password')}
                  disabled={!latestTemporaryCredentials.temporary_password}
                />
              </div>
            </div>
            <div className="mt-5 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm font-semibold text-amber-800">
              The user must sign in with this temporary password and complete mandatory password change before reaching the workspace.
            </div>
          </div>
        </div>
      ) : null}

      {showAdvancedFilters ? (
        <div className="fixed inset-0 z-40 bg-slate-950/25">
          <div className="absolute right-0 top-0 h-full w-full max-w-md overflow-y-auto border-l border-gray-200 bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-[#237afc]">Advanced filters</p>
                <h3 className="mt-2 text-2xl font-black text-gray-900">Refine the roster</h3>
              </div>
              <button onClick={() => setShowAdvancedFilters(false)} className="rounded-2xl border border-gray-200 px-3 py-2 text-sm font-bold text-gray-500">Close</button>
            </div>
            <div className="mt-6 space-y-4">
              <select value={filters?.role || ''} onChange={(event) => applyFilters({ role: event.target.value, page: 1 })} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">All roles</option>
                {roleOptions.map((role) => (
                  <option key={role.id} value={role.name.toLowerCase().replace(/ /g, '_')}>{role.name}</option>
                ))}
              </select>
              <select value={activeFilterProduct} onChange={(event) => applyFilters({ product_id: event.target.value, page: 1 })} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">All products</option>
                {productOptions.map((product) => (
                  <option key={product.id} value={product.id}>{product.name}</option>
                ))}
              </select>
              <select value={activeFilterStatus} onChange={(event) => applyFilters({ status: event.target.value, page: 1 })} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">All statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="ACTIVE">Active</option>
                <option value="PENDING_VERIFICATION">Pending verification</option>
                <option value="INACTIVE">Inactive</option>
                <option value="LOCKED">Locked</option>
                <option value="SUSPENDED">Suspended</option>
              </select>
              <select value={activeFilterVerification} onChange={(event) => applyFilters({ verification: event.target.value, page: 1 })} className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                <option value="">All verification</option>
                <option value="verified">Verified</option>
                <option value="pending">Pending</option>
              </select>
            </div>
            <div className="mt-6 flex gap-3">
              <ActionButton icon={Filter} label="Apply filters" tone="primary" onClick={() => setShowAdvancedFilters(false)} />
              <ActionButton icon={XCircle} label="Reset" onClick={() => applyFilters({ role: '', product_id: '', status: '', verification: '', search: '', page: 1 })} />
            </div>
          </div>
        </div>
      ) : null}

      {isProfileDrawerOpen ? (
        <div className="fixed inset-0 z-40 bg-slate-950/25">
          <div className="absolute right-0 top-0 h-full w-full max-w-[760px] overflow-y-auto border-l border-gray-200 bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-[#237afc]">User 360 profile</p>
                <h3 className="mt-2 text-2xl font-black text-gray-900">{safeSelectedUser?.name || 'User profile'}</h3>
                <p className="mt-2 text-sm text-gray-500">Profile-level governance, assignments, sessions, notes, attachments, and audit review.</p>
              </div>
              <button onClick={() => setIsProfileDrawerOpen(false)} className="rounded-2xl border border-gray-200 px-3 py-2 text-sm font-bold text-gray-500">Close</button>
            </div>
            {detailLoading ? (
              <div className="mt-6 rounded-3xl bg-gray-50 px-6 py-16 text-center text-sm font-semibold text-gray-500">
                Loading user detail...
              </div>
            ) : safeSelectedUser ? (
              <>
                <div className="mt-6 flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#237afc] to-[#53b6ff] text-lg font-black text-white">
                    {safeSelectedUser.name.split(' ').map((part) => part[0]).join('').slice(0, 2)}
                  </div>
                  <div>
                    <p className="text-lg font-black text-gray-900">{safeSelectedUser.name}</p>
                    <p className="text-sm text-gray-500">{safeSelectedUser.professional_title || 'Assigned user profile'}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <Badge tone="blue">{safeSelectedUser.role.replace(/_/g, ' ')}</Badge>
                      <Badge tone={safeSelectedUser.status === 'ACTIVE' ? 'green' : 'red'}>{safeSelectedUser.status}</Badge>
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
                          : 'border border-gray-200 bg-gray-50 text-gray-600'
                      )}
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                <div className="mt-6 grid gap-3 md:grid-cols-4">
                  <div className="rounded-2xl bg-gray-50 px-4 py-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Active devices</p>
                    <p className="mt-2 text-2xl font-black text-gray-900">{safeSelectedUser.sessions.filter((session) => session.status === 'ACTIVE').length}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 px-4 py-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Products</p>
                    <p className="mt-2 text-2xl font-black text-gray-900">{safeSelectedUser.product_access.length}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 px-4 py-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Notes</p>
                    <p className="mt-2 text-2xl font-black text-gray-900">{safeSelectedUser.notes.length}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 px-4 py-4">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Attachments</p>
                    <p className="mt-2 text-2xl font-black text-gray-900">{safeSelectedUser.attachments.length}</p>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-2">
                <input value={form.first_name} onChange={(event) => updateForm('first_name', event.target.value)} placeholder="First name" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
                <input value={form.last_name} onChange={(event) => updateForm('last_name', event.target.value)} placeholder="Last name" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
                <input value={form.phone} onChange={(event) => updateForm('phone', event.target.value)} placeholder="Phone number" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
                <select value={form.role} onChange={(event) => updateForm('role', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                  {roleOptions.map((role) => (
                    <option key={role.id} value={role.name.toLowerCase().replace(/ /g, '_')}>{role.name}</option>
                  ))}
                </select>
                <select value={form.status} onChange={(event) => updateForm('status', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                  {['ACTIVE', 'INACTIVE', 'LOCKED', 'SUSPENDED', 'DELETED'].map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
                <select value={form.organization_id} onChange={(event) => updateForm('organization_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                  <option value="">Select organization</option>
                  {organizationOptions.map((organization) => (
                    <option key={organization.id} value={organization.id}>{organization.name}</option>
                  ))}
                </select>
                <select value={form.department_id} onChange={(event) => updateForm('department_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                  <option value="">Select department</option>
                  {departmentOptions
                    .filter((department) => !form.organization_id || department.organization_id === form.organization_id)
                    .map((department) => (
                      <option key={department.id} value={department.id}>{department.name}</option>
                    ))}
                </select>
                <select value={form.primary_product_id} onChange={(event) => updateForm('primary_product_id', event.target.value)} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                  <option value="">Primary product</option>
                  {productOptions.map((product) => (
                    <option key={product.id} value={product.id}>{product.name}</option>
                  ))}
                </select>
                <input value={form.package_name} onChange={(event) => updateForm('package_name', event.target.value)} placeholder="Assigned package" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
              </div>

                <div className="mt-4 flex flex-wrap gap-3">
                  <ActionButton icon={Save} label="Save profile changes" tone="primary" onClick={submitUpdateUser} disabled={isSubmitting} />
                  <ActionButton icon={CheckCircle2} label="Activate" onClick={() => applyBulkAction('activate', { user_ids: [safeSelectedUser.id] })} />
                  <ActionButton icon={XCircle} label="Suspend" onClick={() => applyBulkAction('suspend', { user_ids: [safeSelectedUser.id] })} />
                  <ActionButton icon={KeyRound} label="Reset password" onClick={resetSelectedUserPassword} disabled={isSubmitting} />
                  <ActionButton icon={KeyRound} label="Force logout" onClick={() => runAction('Force logout', onForceLogout, safeSelectedUser.id)} />
                  <ActionButton icon={Save} label="Sync assignments" onClick={syncProductAssignments} disabled={isSubmitting} />
                </div>

                <div className="mt-6 rounded-3xl bg-gray-50 p-5">
                {profileTab === 'General' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    <p><span className="font-bold text-gray-900">Email:</span> {safeSelectedUser.email}</p>
                    <p><span className="font-bold text-gray-900">Phone:</span> {safeSelectedUser.phone || 'Not added'}</p>
                    <p><span className="font-bold text-gray-900">Created:</span> {safeSelectedUser.created_at ? new Date(safeSelectedUser.created_at).toLocaleString() : 'Not recorded'}</p>
                    <p><span className="font-bold text-gray-900">Status:</span> {safeSelectedUser.status}</p>
                  </div>
                )}
                {profileTab === 'Professional' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    <p><span className="font-bold text-gray-900">Role focus:</span> {safeSelectedUser.professional_title || safeSelectedUser.role}</p>
                    <p><span className="font-bold text-gray-900">Verification:</span> {safeSelectedUser.verification}</p>
                    <p><span className="font-bold text-gray-900">Primary role:</span> {safeSelectedUser.role.replace(/_/g, ' ')}</p>
                  </div>
                )}
                {profileTab === 'Organizations' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    {safeSelectedUser.memberships.length ? safeSelectedUser.memberships.map((membership) => (
                      <div key={membership.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                        <p className="font-bold text-gray-900">{membership.organization}</p>
                        <p className="mt-1 text-xs text-gray-500">{membership.department || 'No department'} · {membership.primary_product || 'No primary product'} · {membership.package || 'No package'} · {membership.status}</p>
                        <p className="mt-1 text-xs text-gray-500">Practitioner: {membership.practitioner || '—'} · Mentor: {membership.mentor || '—'} · Consultant: {membership.consultant || '—'}</p>
                      </div>
                    )) : <p>No organization memberships yet.</p>}
                  </div>
                )}
                {profileTab === 'Permissions' && (
                  <div className="flex flex-wrap gap-2">
                    {safeSelectedUser.permissions.map((permission) => (
                      <Badge key={permission} tone="violet">{permission}</Badge>
                    ))}
                  </div>
                )}
                {profileTab === 'Product Access' && (
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-gray-200 bg-white px-4 py-4">
                      <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Product scope</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {productOptions.map((product) => (
                          <button
                            key={product.id}
                            type="button"
                            onClick={() => toggleListValue('product_ids', product.id)}
                            className={cn(
                              'rounded-full border px-3 py-2 text-xs font-bold',
                              selectedProductIdSet.has(product.id) ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]' : 'border-gray-200 bg-white text-gray-600'
                            )}
                          >
                            {product.name}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-3 text-sm text-gray-600">
                      {safeSelectedUser.product_access.length ? safeSelectedUser.product_access.map((access) => (
                        <div key={access.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <p className="font-bold text-gray-900">{access.product}</p>
                            <div className="flex items-center gap-2">
                              {access.is_primary ? <Badge tone="blue">Primary</Badge> : null}
                              <Badge tone={access.status === 'ACTIVE' ? 'green' : 'red'}>{access.status}</Badge>
                            </div>
                          </div>
                          <p className="mt-1 text-xs text-gray-500">{access.organization || 'Global scope'} · {access.role || 'No scoped role'}</p>
                        </div>
                      )) : <p>No product access assigned yet.</p>}
                    </div>
                  </div>
                )}
                {profileTab === 'Status History' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    {safeSelectedUser.status_history.length ? safeSelectedUser.status_history.map((history) => (
                      <div key={history.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                        <p className="font-bold text-gray-900">{history.new_status}</p>
                        <p className="text-xs text-gray-500">{history.previous_status || 'No previous status'} → {history.new_status}</p>
                        <p className="mt-1 text-xs text-gray-500">{history.reason || 'Status change recorded'} · {history.changed_by} · {new Date(history.created_at).toLocaleString()}</p>
                      </div>
                    )) : <p>No activity recorded yet.</p>}
                  </div>
                )}
                {profileTab === 'Login Sessions' && (
                  <div className="space-y-2 text-sm text-gray-600">
                    {safeSelectedUser.sessions.length ? safeSelectedUser.sessions.map((session) => (
                      <div key={session.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="font-bold text-gray-900">{session.device_label || session.browser || 'Unknown browser'} · {session.platform || 'Unknown platform'}</p>
                            <p className="text-xs text-gray-500">{session.ip_address || 'Unknown IP'} · {session.status} · last seen {new Date(session.last_seen_at).toLocaleString()}</p>
                          </div>
                          <button onClick={() => runAction('Revoke session', onRevokeSession, safeSelectedUser.id, session.id)} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">
                            Revoke
                          </button>
                        </div>
                      </div>
                    )) : <p>No login sessions recorded yet.</p>}
                  </div>
                )}
                {profileTab === 'Audit History' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    {safeSelectedUser.audit_events.length ? safeSelectedUser.audit_events.map((event) => (
                      <div key={event.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                        <p className="font-bold text-gray-900">{event.action}</p>
                        <p className="text-xs text-gray-500">{event.actor} · {event.entity_type} · {event.product || 'No product'} · {new Date(event.created_at).toLocaleString()}</p>
                        <p className="mt-1 text-xs text-gray-400">{event.request_id || 'No request id'}</p>
                      </div>
                    )) : <p>No audit history available yet.</p>}
                  </div>
                )}
                {profileTab === 'Assigned Packages' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    <div className="rounded-2xl border border-gray-200 bg-white px-4 py-4">
                      <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Package scope</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {packageOptions.map((pkg) => (
                          <button
                            key={pkg.id}
                            type="button"
                            onClick={() => toggleListValue('package_ids', pkg.id)}
                            className={cn(
                              'rounded-full border px-3 py-2 text-xs font-bold',
                              selectedPackageIdSet.has(pkg.id) ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]' : 'border-gray-200 bg-white text-gray-600'
                            )}
                          >
                            {pkg.name}
                          </button>
                        ))}
                      </div>
                    </div>
                    {safeSelectedUser.package_assignments.length ? safeSelectedUser.package_assignments.map((assignment) => (
                      <div key={assignment.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                        <p className="font-bold text-gray-900">{assignment.package}</p>
                        <p className="text-xs text-gray-500">{assignment.product} · {assignment.organization || 'Global scope'} · {assignment.status}</p>
                      </div>
                    )) : <p>No package assignments yet.</p>}
                  </div>
                )}
                {profileTab === 'Assigned Services' && (
                  <div className="space-y-3 text-sm text-gray-600">
                    <div className="rounded-2xl border border-gray-200 bg-white px-4 py-4">
                      <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Service scope</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {serviceOptions.map((service) => (
                          <button
                            key={service.id}
                            type="button"
                            onClick={() => toggleListValue('service_ids', service.id)}
                            className={cn(
                              'rounded-full border px-3 py-2 text-xs font-bold',
                              selectedServiceIdSet.has(service.id) ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]' : 'border-gray-200 bg-white text-gray-600'
                            )}
                          >
                            {service.name}
                          </button>
                        ))}
                      </div>
                    </div>
                    {safeSelectedUser.service_assignments.length ? safeSelectedUser.service_assignments.map((assignment) => (
                      <div key={assignment.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                        <p className="font-bold text-gray-900">{assignment.service}</p>
                        <p className="text-xs text-gray-500">{assignment.product} · {assignment.organization || 'Global scope'} · {assignment.status}</p>
                      </div>
                    )) : <p>No service assignments yet.</p>}
                  </div>
                )}
                {profileTab === 'Attachments' && (
                  <div className="space-y-4">
                    <div className="space-y-3 text-sm text-gray-600">
                      {safeSelectedUser.attachments.length ? safeSelectedUser.attachments.map((attachment) => (
                        <div key={attachment.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <div>
                              <p className="font-semibold text-gray-900">{attachment.file_name}</p>
                              <p className="mt-1 text-xs text-gray-500">{attachment.attachment_type || 'attachment'} · {attachment.content_type || 'unknown type'}</p>
                            </div>
                            <a href={attachment.file_url} target="_blank" rel="noreferrer" className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">
                              Open
                            </a>
                          </div>
                          {attachment.note ? <p className="mt-2 text-sm text-gray-600">{attachment.note}</p> : null}
                        </div>
                      )) : <p>No attachments uploaded yet.</p>}
                    </div>
                    <div className="grid gap-3 md:grid-cols-2">
                      <input value={attachmentDraft.file_name} onChange={(event) => setAttachmentDraft((current) => ({ ...current, file_name: event.target.value }))} placeholder="File name" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
                      <input value={attachmentDraft.file_url} onChange={(event) => setAttachmentDraft((current) => ({ ...current, file_url: event.target.value }))} placeholder="File URL" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
                      <input value={attachmentDraft.content_type} onChange={(event) => setAttachmentDraft((current) => ({ ...current, content_type: event.target.value }))} placeholder="Content type" className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
                      <select value={attachmentDraft.attachment_type} onChange={(event) => setAttachmentDraft((current) => ({ ...current, attachment_type: event.target.value }))} className="rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none">
                        <option value="document">Document</option>
                        <option value="certificate">Certificate</option>
                        <option value="agreement">Agreement</option>
                        <option value="proof">Proof</option>
                      </select>
                      <textarea value={attachmentDraft.note} onChange={(event) => setAttachmentDraft((current) => ({ ...current, note: event.target.value }))} placeholder="Attachment note" className="min-h-[90px] rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none md:col-span-2" />
                    </div>
                    <ActionButton icon={Plus} label="Save attachment" tone="primary" onClick={submitAttachment} disabled={isSubmitting || !attachmentDraft.file_name.trim() || !attachmentDraft.file_url.trim()} />
                  </div>
                )}
                {profileTab === 'Notes' && (
                  <div className="space-y-4">
                    <div className="space-y-3 text-sm text-gray-600">
                      {safeSelectedUser.notes.length ? safeSelectedUser.notes.map((note) => (
                        <div key={note.id} className="rounded-2xl border border-gray-100 bg-white px-4 py-3">
                          <p className="font-semibold text-gray-900">{note.author}</p>
                          <p className="mt-1 text-sm text-gray-600">{note.body}</p>
                          <p className="mt-2 text-xs text-gray-500">{new Date(note.created_at).toLocaleString()}</p>
                        </div>
                      )) : <p>No operator notes yet.</p>}
                    </div>
                    <textarea value={noteDraft} onChange={(event) => setNoteDraft(event.target.value)} placeholder="Add an internal note for this user..." className="min-h-[110px] w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
                    <ActionButton icon={Plus} label="Save note" tone="primary" onClick={submitNote} disabled={isSubmitting || !noteDraft.trim()} />
                  </div>
                )}
                {!['General', 'Professional', 'Permissions', 'Product Access', 'Status History', 'Login Sessions', 'Audit History', 'Assigned Packages', 'Assigned Services', 'Attachments', 'Notes', 'Organizations'].includes(profileTab) && (
                  null
                )}
                </div>
              </>
            ) : (
              <EmptyState icon={Users} title="No person selected" description="Pick a user to inspect detailed access, activity, and notes." />
            )}
          </div>
        </div>
      ) : null}
    </ModuleFrame>
  );
}

export function PermissionMatrixModule({
  metadata,
  loading = false,
  onUpdateRolePermissions,
  onCreateRole,
  onCloneRole,
  selectedRoleId: controlledSelectedRoleId,
  onSelectedRoleChange,
  searchQuery,
  onSearchQueryChange,
}) {
  const [query, setQuery] = useState(searchQuery || '');
  const [selectedRoleId, setSelectedRoleId] = useState(controlledSelectedRoleId || '');
  const [draftPermissions, setDraftPermissions] = useState({});
  const [roleDraft, setRoleDraft] = useState({ name: '', description: '' });
  const [cloneDraft, setCloneDraft] = useState({ name: '', description: '' });
  const [isSaving, setIsSaving] = useState(false);
  const [matrixError, setMatrixError] = useState(null);
  const roleRows = metadata?.roles || [];
  const permissionGroups = useMemo(() => {
    const grouped = new Map();
    (metadata?.permissions || []).forEach((permission) => {
      const group = grouped.get(permission.module) || [];
      if (!query || permission.key.toLowerCase().includes(query.toLowerCase()) || permission.label.toLowerCase().includes(query.toLowerCase())) {
        group.push(permission);
      }
      grouped.set(permission.module, group);
    });
    return Array.from(grouped.entries())
      .map(([module, permissions]) => ({ module, permissions }))
      .filter((group) => group.permissions.length > 0);
  }, [metadata?.permissions, query]);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    setQuery(searchQuery || '');
  }, [searchQuery]);

  useEffect(() => {
    if (controlledSelectedRoleId !== undefined) {
      setSelectedRoleId(controlledSelectedRoleId || '');
    }
  }, [controlledSelectedRoleId]);

  useEffect(() => {
    setExpanded(permissionGroups.reduce((acc, group) => ({ ...acc, [group.module]: true }), {}));
  }, [metadata?.permissions]);

  const allExpanded = permissionGroups.length > 0 && permissionGroups.every((group) => expanded[group.module]);

  useEffect(() => {
    if (!roleRows.length) return;
    const nextRoleId = selectedRoleId || roleRows[0].id;
    const selectedRole = roleRows.find((role) => role.id === nextRoleId) || roleRows[0];
    setSelectedRoleId(selectedRole.id);
    onSelectedRoleChange?.(selectedRole.id);
    setDraftPermissions((current) => ({
      ...current,
      [selectedRole.id]: current[selectedRole.id] || [...(selectedRole.permissions || [])],
    }));
  }, [onSelectedRoleChange, roleRows, selectedRoleId]);

  const selectedRole = roleRows.find((role) => role.id === selectedRoleId) || roleRows[0];
  const selectedRolePermissions = draftPermissions[selectedRole?.id] || selectedRole?.permissions || [];
  const runMatrixAction = async (label, handler, ...args) => {
    if (typeof handler !== 'function') {
      setMatrixError(`${label} is not available. Refresh the page or contact support if this continues.`);
      return null;
    }
    setMatrixError(null);
    try {
      return await handler(...args);
    } catch (nextError) {
      setMatrixError(nextError?.message || `${label} failed. Please try again.`);
      return null;
    }
  };
  const toggleDraftPermission = (permissionKey) => {
    if (!selectedRole) return;
    setDraftPermissions((current) => {
      const existing = current[selectedRole.id] || selectedRole.permissions || [];
      const nextPermissions = existing.includes(permissionKey)
        ? existing.filter((item) => item !== permissionKey)
        : [...existing, permissionKey];
      return { ...current, [selectedRole.id]: nextPermissions };
    });
  };

  const savePermissions = async () => {
    if (!selectedRole) return;
    setIsSaving(true);
    try {
      await runMatrixAction('Save permission matrix', onUpdateRolePermissions, selectedRole.id, selectedRolePermissions);
    } finally {
      setIsSaving(false);
    }
  };

  const createRole = async () => {
    if (!roleDraft.name.trim()) {
      setMatrixError('Create custom role requires a role name.');
      return;
    }
    setIsSaving(true);
    try {
      const result = await runMatrixAction('Create custom role', onCreateRole, {
        name: roleDraft.name.trim(),
        description: roleDraft.description.trim() || null,
        permission_keys: selectedRolePermissions,
      });
      if (result === null) return;
      setRoleDraft({ name: '', description: '' });
    } finally {
      setIsSaving(false);
    }
  };

  const cloneRole = async (roleId) => {
    if (!cloneDraft.name.trim()) {
      setMatrixError('Enter a clone role name before cloning a role.');
      return;
    }
    setIsSaving(true);
    try {
      const result = await runMatrixAction('Clone role', onCloneRole, roleId, {
        name: cloneDraft.name.trim(),
        description: cloneDraft.description.trim() || null,
      });
      if (result === null) return;
      setCloneDraft({ name: '', description: '' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ModuleFrame
      badge="Role & permission management"
      title="Permission matrix for platform roles and custom authority sets"
      description="Search permissions, expand modules, duplicate roles, and prepare custom role definitions without leaving the owner workspace."
      actions={
        <>
          <ActionButton icon={Save} label="Save matrix" onClick={savePermissions} disabled={isSaving || !selectedRole} />
          <ActionButton icon={Plus} label="Create custom role" tone="primary" onClick={createRole} disabled={isSaving || !roleDraft.name.trim()} />
        </>
      }
    >
      {matrixError ? (
        <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">
          {matrixError}
        </div>
      ) : null}
      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.4fr]">
        <Panel title="Role library" subtitle="Cloneable and governed roles for enterprise operations.">
          <div className="space-y-3">
            {roleRows.map((role) => (
              <div key={role.id} className={cn('rounded-2xl border px-4 py-4', selectedRoleId === role.id ? 'border-[#237afc] bg-[#f5f9ff]' : 'border-gray-100 bg-gray-50')}>
                <div className="flex items-center justify-between gap-4">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedRoleId(role.id);
                      onSelectedRoleChange?.(role.id);
                    }}
                    className="text-left"
                  >
                    <p className="font-bold text-gray-900">{role.name}</p>
                    <p className="text-sm text-gray-500">{role.users} assigned users</p>
                  </button>
                  <div className="flex items-center gap-2">
                    {role.cloneable ? <Badge tone="blue">Cloneable</Badge> : <Badge tone="red">Fixed</Badge>}
                    {role.cloneable ? (
                      <button onClick={() => cloneRole(role.id)} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-600">
                        Clone
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-5 space-y-3 rounded-2xl border border-gray-100 bg-white p-4">
            <p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Create / clone role</p>
            <input value={roleDraft.name} onChange={(event) => setRoleDraft((current) => ({ ...current, name: event.target.value }))} placeholder="New role name" className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
            <textarea value={roleDraft.description} onChange={(event) => setRoleDraft((current) => ({ ...current, description: event.target.value }))} placeholder="Role description" className="min-h-[90px] w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
            <input value={cloneDraft.name} onChange={(event) => setCloneDraft((current) => ({ ...current, name: event.target.value }))} placeholder="Clone selected role as..." className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
            <textarea value={cloneDraft.description} onChange={(event) => setCloneDraft((current) => ({ ...current, description: event.target.value }))} placeholder="Clone description" className="min-h-[90px] w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm outline-none" />
          </div>
        </Panel>

        <Panel title="Permission matrix" subtitle="Module-scoped access controls with search-ready rows.">
          <div className="mb-4 flex flex-wrap gap-2">
            <button className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600">
              <Search className="h-4 w-4" />
                <input
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    onSearchQueryChange?.(event.target.value);
                  }}
                  placeholder="Search permissions"
                  className="bg-transparent outline-none"
                />
            </button>
            <button
              onClick={() => {
                const nextState = !allExpanded;
                setExpanded(permissionGroups.reduce((acc, group) => ({ ...acc, [group.module]: nextState }), {}));
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold text-gray-600"
            >
              <ChevronDown className="h-4 w-4" />
              {allExpanded ? 'Collapse all' : 'Expand all'}
            </button>
          </div>

          {loading ? (
            <div className="rounded-3xl bg-gray-50 px-6 py-16 text-center text-sm font-semibold text-gray-500">
              Loading permission matrix...
            </div>
          ) : (
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
                          {roleRows.map((role) => (
                            <th key={role.id} className="px-4 py-3 text-center text-xs font-black uppercase tracking-[0.24em] text-gray-400">
                              {role.name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {group.permissions.map((permission, index) => (
                          <tr key={permission.id}>
                            <td className="px-4 py-3 font-semibold text-gray-800">
                              <p>{permission.label}</p>
                              <p className="text-xs text-gray-400">{permission.key}</p>
                            </td>
                            {roleRows.map((role) => {
                              const checked = (role.permissions || []).includes(permission.key);
                              return (
                            <td key={`${role.id}-${permission.id}`} className="px-4 py-3 text-center">
                                  <input
                                    type="checkbox"
                                    checked={role.id === selectedRole?.id ? selectedRolePermissions.includes(permission.key) : checked}
                                    readOnly={role.id !== selectedRole?.id}
                                    onChange={role.id === selectedRole?.id ? () => toggleDraftPermission(permission.key) : undefined}
                                    className="h-4 w-4 rounded border-gray-300 text-[#237afc]"
                                  />
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
          )}
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

export function ConsultantsModule({ consultants }) {
  return (
    <ModuleFrame
      badge="Consultants"
      title="Consulting coverage, approvals, package ownership, and performance"
      description="Review consultant specialization, assigned organizations, package accountability, service scope, quality performance, and commercial contribution."
      actions={
        <>
          <ActionButton icon={CalendarDays} label="Open consultant calendar" />
          <ActionButton icon={Plus} label="Add consultant" tone="primary" />
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-2">
        {consultants.map((consultant) => (
          <Panel key={consultant.id} title={consultant.name} subtitle={consultant.title}>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Certificates</p><p className="mt-2 text-sm font-bold text-gray-900">{consultant.certificates.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Qualifications</p><p className="mt-2 text-sm font-bold text-gray-900">{consultant.qualifications.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Availability</p><p className="mt-2 text-sm font-bold text-gray-900">{consultant.availability}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Revenue</p><p className="mt-2 text-sm font-bold text-gray-900">{consultant.revenue}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4 md:col-span-2"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Organizations / packages / services</p><p className="mt-2 text-sm font-bold text-gray-900">{consultant.organizations.join(', ')} · {consultant.packages.join(', ')} · {consultant.services.join(', ')}</p></div>
              <div className="rounded-2xl bg-gray-50 p-4 md:col-span-2"><p className="text-xs font-black uppercase tracking-[0.24em] text-gray-400">Performance</p><p className="mt-2 text-sm font-bold text-gray-900">{consultant.performance} · {consultant.rating}/5 rating</p></div>
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
