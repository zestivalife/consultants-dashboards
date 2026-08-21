import { useCallback, useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Activity,
  Bell,
  Bot,
  CalendarDays,
  ClipboardCheck,
  ChevronRight,
  Clock3,
  Command,
  Dumbbell,
  FileBarChart2,
  Filter,
  Flame,
  HeartPulse,
  LayoutGrid,
  ListChecks,
  Mail,
  MessageSquare,
  Phone,
  Ruler,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Scale,
  TrendingUp,
  Users,
  Wallet,
  X,
} from 'lucide-react';
import withAuth from '../../hocs/withAuth';
import { useAuth } from '../../context/AuthContext';
import { buildInitialPlatformState, getRoleDisplayName } from '../../data/mockPlatformData';
import {
  acknowledgeFiteatsyConsultantMedicationException,
  approveFiteatsyConsultantDietPlan,
  generateFiteatsyConsultantDietPlanDraft,
  listFiteatsyDietPlanReviews,
  getFiteatsyConsultantClientMedications,
  getFiteatsyConsultantClientProfile,
  getFiteatsyConsultantClientStressSummary,
  getFiteatsyConsultantLatestDietPlan,
  getFiteatsyConsultantNutritionIntelligence,
  listFiteatsyConsultantClients,
  listFiteatsyClientAllocationPool,
  listFiteatsyConsultantMedicationExceptions,
  searchFiteatsyAssignmentClients,
  listFiteatsyAssignmentProfessionals,
  listFiteatsyProfessionalAssignments,
  createFiteatsyProfessionalAssignment,
  revokeFiteatsyProfessionalAssignment,
  publishFiteatsyConsultantDietPlan,
  requestFiteatsyConsultantDietPlanChanges,
  submitFiteatsyConsultantDietPlanForReview,
  updateFiteatsyConsultantDietPlanDraft,
} from '../../lib/fiteatsyConsultantsApi';
import { corporateAPI } from '../../lib/api';
import { ADMIN_ACCESS_POLICY, DELIVERY_ACCESS_POLICY, MENTOR_ACCESS_POLICY, ORGANIZATION_ACCESS_POLICY } from '../../lib/roleRoutes';

const roleKinds = {
  consultant: 'consultant',
  provider: 'consultant',
  dietician: 'consultant',
  team_member: 'consultant',
  member: 'consultant',
  senior_consultant: 'consultant',
  admin: 'admin',
  superuser: 'admin',
  platform_owner: 'admin',
  care_operations: 'admin',
  mentor: 'mentor',
  team_lead: 'mentor',
  organization_admin: 'admin',
  corporate_admin: 'admin',
  corporate_client: 'admin',
};

const consultantNav = [
  { id: 'command-center', label: 'Command Center', icon: LayoutGrid },
  { id: 'clients', label: 'Clients', icon: Users },
  { id: 'consultations', label: 'Consultations', icon: CalendarDays },
  { id: 'operations', label: 'Tasks & Timeline', icon: ListChecks },
  { id: 'progress', label: 'Goals & Progress', icon: TrendingUp },
  { id: 'practice', label: 'Reports & Profile', icon: ShieldCheck },
];

const seniorConsultantNav = [
  ...consultantNav,
  { id: 'diet-plan-reviews', label: 'Diet Plan Reviews', icon: ClipboardCheck },
];

const mentorNav = [
  { id: 'command-center', label: 'Command Center', icon: LayoutGrid },
  { id: 'clients', label: 'Clients', icon: Users },
  { id: 'communication', label: 'Communication', icon: MessageSquare },
  { id: 'organizations', label: 'Organizations', icon: FileBarChart2 },
];

const adminNav = [
  { id: 'command-center', label: 'Command Center', icon: LayoutGrid },
  { id: 'clients', label: 'Clients', icon: Users },
  { id: 'assignments', label: 'Client Assignments', icon: Users },
  { id: 'intelligence', label: 'Intelligence', icon: TrendingUp },
  { id: 'organizations', label: 'Organizations', icon: FileBarChart2 },
  { id: 'people', label: 'People', icon: ListChecks },
];

const timeframeOptions = ['Day', 'Week', 'Month', 'Quarter', 'Custom Range'];
const intelligenceRangeOptions = [
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
  { id: 'quarter', label: 'Quarter' },
  { id: 'year', label: 'Yearly' },
  { id: 'custom', label: 'Custom' },
];
const clientWorkspaceTabs = ['Overview', 'Biomarkers', 'Behaviors', 'Diet Plan', 'Reports', 'Notes', 'Chat', 'Timeline'];
const superAdminRoles = new Set(['superuser', 'platform_owner']);
const assignmentManagerRoles = new Set(['admin', 'super_admin', 'platform_owner', 'care_operations']);
const managedRoleOptions = [
  { value: 'mentor', label: 'Mentor', audience: 'mentor' },
  { value: 'consultant', label: 'Consultant', audience: 'consultant' },
  { value: 'provider', label: 'Provider', audience: 'consultant' },
  { value: 'dietician', label: 'Dietician', audience: 'consultant' },
  { value: 'senior_consultant', label: 'Senior Consultant', audience: 'consultant' },
  { value: 'admin', label: 'Admin', audience: 'admin' },
  { value: 'organization_admin', label: 'Organization Admin', audience: 'admin' },
  { value: 'corporate_admin', label: 'Corporate Admin', audience: 'admin' },
];
const defaultAuthorityOptions = [
  { id: 'client_read', label: 'Client Directory', description: 'View assigned client records and progress.', audience: 'all' },
  { id: 'plan_review', label: 'Plan Review', description: 'Review and approve nutrition or recovery plans.', audience: 'consultant' },
  { id: 'report_interpretation', label: 'Report Interpretation', description: 'Interpret uploaded blood reports and biomarker summaries.', audience: 'consultant' },
  { id: 'mentor_queue', label: 'Mentor Queue', description: 'Access mentor escalations, support notes, and supervision views.', audience: 'mentor' },
  { id: 'team_supervision', label: 'Team Supervision', description: 'Oversee consultants, mentor follow-through, and review pipeline health.', audience: 'mentor' },
  { id: 'user_management', label: 'User Management', description: 'Create and manage practitioners and admins.', audience: 'admin' },
  { id: 'analytics_read', label: 'Analytics Access', description: 'View intelligence, revenue, and quality dashboards.', audience: 'admin' },
  { id: 'authority_management', label: 'Authority Management', description: 'Grant or revoke authorities for practitioner accounts.', audience: 'admin' },
];

const fadeThrough = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: 'easeOut' } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.16, ease: 'easeInOut' } },
};

const hoverLift = { whileHover: { y: -1.5 }, whileTap: { scale: 0.995 } };

const regionalMealLibrary = {
  Maharashtrian: ['Poha + sprouts + curd', 'Thalipeeth + dahi', 'Bhakri + pithla', 'Dal khichdi', 'Koshimbir + chaas'],
  Gujarati: ['Thepla + dahi', 'Roti sabzi', 'Khichdi kadhi', 'Handvo', 'Roasted chana + chaas'],
  'South Indian': ['Idli + sambar', 'Vegetable upma', 'Pesarattu', 'Curd rice', 'Lemon rice + sundal'],
  Punjabi: ['Paneer bhurji + phulka', 'Dal + roti', 'Chole + salad', 'Besan chilla', 'Jeera rice + rajma'],
  Bengali: ['Chire doi', 'Rice + fish curry', 'Moong dal + bhaja', 'Vegetable stew', 'Fruit + makhana'],
};

const noteTypeOptions = [
  'Clinical Observation',
  'Behavioral Pattern',
  'Escalation',
  'Adherence Concern',
  'Intervention Outcome',
  'Follow-Up Reminder',
  'Mentor Review',
  'Risk Annotation',
];

const noteSeverityOptions = ['critical', 'high', 'medium', 'stable'];
const aiDraftProgressStages = [
  { progress: 12, label: 'Reading biomarkers and recent reports' },
  { progress: 28, label: 'Interpreting adherence and meal timing patterns' },
  { progress: 47, label: 'Matching condition-aware recovery protocols' },
  { progress: 63, label: 'Applying intervention memory from similar profiles' },
  { progress: 79, label: 'Building modular meal and routine blocks' },
  { progress: 92, label: 'Running consultant safety and confidence checks' },
  { progress: 100, label: 'Finalizing diet plan for review' },
];

const mentorByOrganization = {
  'Zenith Forge': 'Maya Iyer',
  'Northstar Labs': 'Maya Iyer',
  'Aster Pulse': 'Maya Iyer',
};

const consultantNutritionRoles = new Set(['consultant', 'senior_consultant']);
const consultantWorkspaceStoragePrefix = 'nuetra:consultant-workspace:';
const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function createDefaultConsultantWorkspaceState() {
  return {
    appointments: [],
    tasks: [],
    followUps: [],
    consultationNotes: {},
    activityLog: [],
    profile: {
      specialisation: '',
      consultationStyle: '',
      responseWindow: '',
      consultationCadence: '',
    },
    availability: {
      workingDays: [],
      startTime: '',
      endTime: '',
      breakBufferMinutes: '',
      teleconsultEnabled: true,
    },
  };
}

function readConsultantWorkspaceState(storageKey) {
  if (typeof window === 'undefined' || !storageKey) return createDefaultConsultantWorkspaceState();

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return createDefaultConsultantWorkspaceState();
    const parsed = JSON.parse(raw);
    return {
      ...createDefaultConsultantWorkspaceState(),
      ...parsed,
      appointments: Array.isArray(parsed?.appointments) ? parsed.appointments : [],
      tasks: Array.isArray(parsed?.tasks) ? parsed.tasks : [],
      followUps: Array.isArray(parsed?.followUps) ? parsed.followUps : [],
      activityLog: Array.isArray(parsed?.activityLog) ? parsed.activityLog : [],
      consultationNotes: parsed?.consultationNotes && typeof parsed.consultationNotes === 'object' ? parsed.consultationNotes : {},
      profile: {
        ...createDefaultConsultantWorkspaceState().profile,
        ...(parsed?.profile || {}),
      },
      availability: {
        ...createDefaultConsultantWorkspaceState().availability,
        ...(parsed?.availability || {}),
      },
    };
  } catch (error) {
    console.warn('Unable to read consultant workspace state', error);
    return createDefaultConsultantWorkspaceState();
  }
}

function createWorkspaceId(prefix) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function appendConsultantWorkspaceActivity(state, activity) {
  return {
    ...state,
    activityLog: [
      {
        id: activity.id || createWorkspaceId('activity'),
        createdAt: activity.createdAt || new Date().toISOString(),
        ...activity,
      },
      ...(state.activityLog || []),
    ].slice(0, 60),
  };
}

function getDaysSince(dateValue) {
  if (!dateValue) return null;
  const value = new Date(dateValue);
  if (Number.isNaN(value.getTime())) return null;
  return Math.floor((Date.now() - value.getTime()) / (1000 * 60 * 60 * 24));
}

function getTodayDateKey() {
  return new Date().toISOString().slice(0, 10);
}

function formatTimeLabel(value) {
  if (!value) return 'Not scheduled';
  const [hours, minutes] = String(value).split(':');
  if (hours == null || minutes == null) return value;
  const numericHour = Number(hours);
  if (Number.isNaN(numericHour)) return value;
  const period = numericHour >= 12 ? 'PM' : 'AM';
  const displayHour = numericHour % 12 || 12;
  return `${displayHour}:${minutes} ${period}`;
}

function buildConsultantAttentionItem(client) {
  const reasons = [];
  if (!client.profileCompleted) reasons.push('Onboarding needs completion');
  if ((client.reportsCount || 0) > 0) reasons.push('Reports available for consultant review');
  if (client.biomarkerStatus && String(client.biomarkerStatus).toLowerCase() !== 'normal') reasons.push(`Biomarker status: ${client.biomarkerStatus}`);
  if ((getDaysSince(client.lastHealthUpdate || client.lastActiveAt || client.registeredAt) || 0) > 10) reasons.push('Recent health activity is cooling');

  return {
    clientId: client.id,
    name: client.name,
    title: reasons[0] || 'Routine profile review',
    reason: reasons[1] || client.trendSummary?.title || 'Open the client workspace to continue care planning.',
    tone: !client.profileCompleted ? 'medium' : reasons.length > 1 ? 'high' : 'stable',
    lastTouch: client.lastActivity,
    goal: client.goal || 'Not assigned',
  };
}

function getRoleKind(role) {
  return roleKinds[role] || 'consultant';
}

function formatStatusLabel(value = '') {
  return value.replace(/_/g, ' ');
}

function getAuthorityAudience(role) {
  const option = managedRoleOptions.find((item) => item.value === String(role).toLowerCase());
  return option?.audience || 'consultant';
}

function groupManagedPeople(people) {
  return {
    mentors: people.filter((item) => ['mentor', 'team_lead'].includes(item.role)),
    consultants: people.filter((item) => ['consultant', 'provider', 'dietician', 'senior_consultant'].includes(item.role)),
    admins: people.filter((item) => ['admin', 'organization_admin', 'corporate_admin', 'superuser'].includes(item.role)),
  };
}

function toneForStatus(status) {
  const tones = {
    critical: 'bg-[var(--fluent-color-status-danger-background)] text-[var(--fluent-color-status-danger-foreground)]',
    declining: 'bg-[var(--fluent-color-status-danger-background)] text-[var(--fluent-color-status-danger-foreground)]',
    high: 'bg-[var(--fluent-color-status-warning-background)] text-[var(--fluent-color-status-warning-foreground)]',
    medium: 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)]',
    stable: 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-2)]',
    improving: 'bg-[var(--fluent-color-status-success-background)] text-[var(--fluent-color-status-success-foreground)]',
    pending: 'bg-[rgba(99,124,239,0.18)] text-[#3658d4]',
    approved: 'bg-[var(--fluent-color-status-success-background)] text-[var(--fluent-color-status-success-foreground)]',
    published: 'bg-[var(--fluent-color-status-success-background)] text-[var(--fluent-color-status-success-foreground)]',
    overdue: 'bg-[var(--fluent-color-status-danger-background)] text-[var(--fluent-color-status-danger-foreground)]',
    consultant_modified: 'bg-[rgba(99,124,239,0.18)] text-[#3658d4]',
    consultant_review: 'bg-[rgba(99,124,239,0.18)] text-[#3658d4]',
    senior_review: 'bg-[var(--fluent-color-status-warning-background)] text-[var(--fluent-color-status-warning-foreground)]',
    revision_requested: 'bg-[var(--fluent-color-status-danger-background)] text-[var(--fluent-color-status-danger-foreground)]',
    followup_pending: 'bg-[var(--fluent-color-status-warning-background)] text-[var(--fluent-color-status-warning-foreground)]',
    insights_generated: 'bg-[var(--fluent-color-status-success-background)] text-[var(--fluent-color-status-success-foreground)]',
    biomarkers_detected: 'bg-[var(--fluent-color-status-warning-background)] text-[var(--fluent-color-status-warning-foreground)]',
    processing: 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)]',
    complete: 'bg-[var(--fluent-color-status-success-background)] text-[var(--fluent-color-status-success-foreground)]',
  };
  return tones[status] || 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-3)]';
}

function getRiskLevel(employee) {
  if (employee.burnoutRisk === 'critical' || employee.readiness < 52) return 'critical';
  if (employee.burnoutRisk === 'high' || employee.stress > 72 || employee.biomarkers.some((item) => item.status === 'critical')) return 'high';
  if (employee.sleepQuality < 60 || employee.hydration < 55) return 'medium';
  return 'stable';
}

function getAdherenceScore(employee) {
  const values = employee.interventions.map((item) => item.adherence);
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

function getLatestActivity(employee) {
  return employee.reports?.[0]?.uploadedAt || employee.notes?.[0]?.time || 'Recently';
}

function getPlanStatus(plan) {
  return plan?.state || 'draft_generated';
}

function getConfidence(employee) {
  const dataPoints = employee.reports.length * 14 + employee.interventions.length * 8;
  return Math.min(92, 68 + Math.round(dataPoints / 8));
}

function getConditionFocus(employee) {
  const joined = employee.conditions.join(' ').toLowerCase();
  if (joined.includes('prediabetes') || employee.biomarkers.some((item) => item.name === 'HbA1c' && item.status !== 'stable')) {
    return {
      condition: 'Diabetes risk',
      drivers: ['inconsistent dinner timing', 'movement adherence softened', 'stress variability elevated'],
      action: 'Shift carb density earlier, add post-meal walk intervention, and tighten sleep consistency.',
    };
  }
  if (joined.includes('thyroid')) {
    return {
      condition: 'Thyroid support',
      drivers: ['fatigue persistence', 'recovery lag', 'meal timing inconsistency'],
      action: 'Stabilize morning protein, protect lunch timing, and reduce long fasting gaps.',
    };
  }
  if (employee.burnoutRisk === 'critical' || employee.burnoutRisk === 'high') {
    return {
      condition: 'Burnout recovery',
      drivers: ['sleep debt', 'stress volatility', 'routine adherence breakdown'],
      action: 'Reduce decision load, intensify mentor cadence, and anchor evening shutdown rituals.',
    };
  }
  return {
    condition: 'General recovery',
    drivers: ['hydration inconsistency', 'travel disruption', 'variable routine quality'],
    action: 'Keep interventions practical and bias toward consistency over intensity.',
  };
}

function buildTrendSummary(employee) {
  const condition = getConditionFocus(employee);
  const hbA1c = employee.biomarkers.find((item) => item.name === 'HbA1c');
  if (hbA1c && hbA1c.values.length > 1) {
    const delta = (hbA1c.values[hbA1c.values.length - 1] - hbA1c.values[hbA1c.values.length - 2]).toFixed(1);
    return {
      title: `${hbA1c.name} ${Number(delta) >= 0 ? 'worsening' : 'improving'} ${delta.startsWith('-') ? delta : `+${delta}`}`,
      explanation: `Likely drivers: ${condition.drivers.join(', ')}.`,
      action: condition.action,
    };
  }
  return {
    title: `${condition.condition} requires review`,
    explanation: `Likely drivers: ${condition.drivers.join(', ')}.`,
    action: condition.action,
  };
}

function getRecoveryMomentum(employee) {
  if (employee.recovery >= 72 && employee.adherenceScore >= 74) return { label: 'Accelerating', direction: 'up', status: 'improving' };
  if (employee.recovery >= 64) return { label: 'Improving', direction: 'up-right', status: 'improving' };
  if (employee.recovery >= 56) return { label: 'Stable', direction: 'right', status: 'stable' };
  if (employee.recovery >= 48) return { label: 'Plateauing', direction: 'down-right', status: 'medium' };
  return { label: 'Declining', direction: 'down', status: 'declining' };
}

function getBehavioralCorrelation(employee) {
  if (employee.sleepQuality < 60 && employee.stress > 70) {
    return 'Sleep down -> Stress up -> Glucose volatility risk up';
  }
  if (employee.hydration < 55) {
    return 'Hydration down -> Recovery down';
  }
  return 'Movement consistency up -> Energy and recovery improving';
}

function buildClientRecords(state) {
  const plansByEmployee = Object.fromEntries(state.plans.map((plan) => [plan.employeeId, plan]));
  return state.employees.map((employee) => ({
    ...employee,
    mentorName: mentorByOrganization[employee.organization] || 'Maya Iyer',
    riskLevel: getRiskLevel(employee),
    adherenceScore: getAdherenceScore(employee),
    lastActivity: getLatestActivity(employee),
    planStatus: getPlanStatus(plansByEmployee[employee.id]),
    confidence: getConfidence(employee),
    conditionFocus: getConditionFocus(employee),
    trendSummary: buildTrendSummary(employee),
    recoveryMomentum: getRecoveryMomentum({
      ...employee,
      adherenceScore: getAdherenceScore(employee),
    }),
    behavioralCorrelation: getBehavioralCorrelation(employee),
    brandContext: employee.brand === 'Fiteatsy' ? 'Hormonal recovery' : 'Corporate wellness',
    packageLabel: employee.packageName || (employee.brand === 'Nuetra' ? 'Annual Corporate Program' : 'Recovery Program'),
  }));
}

function formatDateLabel(value) {
  if (!value) return 'Not available';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Not available';
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function buildFiteatsyClientRecords(apiClients) {
  return apiClients.map((client) => ({
    id: client.clientId,
    clientId: client.clientId,
    name: client.name,
    brand: 'Fiteatsy',
    email: client.email,
    mobile: client.mobile,
    mobileNumberMasked: client.mobileNumberMasked,
    assignmentStatus: client.assignmentStatus || null,
    consultantName: client.consultantName || null,
    subscriptionStatus: client.subscriptionStatus || 'none',
    status: client.status,
    accountStatus: client.accountStatus,
    packageName: 'Not assigned',
    packageLabel: 'Not assigned',
    organization: 'Fiteatsy',
    recoveryStage: client.profileCompleted ? 'Onboarding completed' : 'Registration completed',
    profileCompleted: client.profileCompleted,
    age: client.age,
    gender: client.gender,
    height: client.height,
    weight: client.weight,
    goal: client.goal,
    activityLevel: client.activityLevel,
    dietPreference: client.dietPreference,
    reportsCount: client.reportsCount ?? 0,
    lastHealthUpdate: client.lastHealthUpdate,
    biomarkerStatus: client.biomarkerStatus,
    registeredAt: client.registeredAt,
    lastActivity: formatDateLabel(client.lastHealthUpdate || client.lastActiveAt || client.registeredAt),
    lastActiveAt: client.lastActiveAt,
    riskLevel: 'stable',
    adherenceScore: null,
    mentorName: 'Not assigned',
    planStatus: client.profileCompleted ? 'complete' : 'pending',
    confidence: null,
    conditions: client.medicalConditions || [],
    biomarkers: [],
    reports: [],
    interventions: [],
    notes: [],
    goals: client.goal ? [client.goal] : [],
    region: 'Not available',
    dietaryStyle: client.dietPreference || 'Not available',
    recovery: 0,
    sleepQuality: 0,
    hydration: 0,
    stress: 0,
    burnoutRisk: 'stable',
    trendSummary: {
      title: client.goal
        ? `${client.goal} • ${client.reportsCount ?? 0} ${client.reportsCount === 1 ? 'report' : 'reports'}`
        : client.profileCompleted
          ? 'Profile completed • live registration'
          : 'Registration completed • onboarding pending',
      explanation: 'Only real registration and onboarding data are shown here until deeper clinical intelligence is synchronized.',
      action: 'No action assigned',
    },
    conditionFocus: {
      condition: 'Client profile foundation',
      drivers: [],
      action: 'No action assigned',
    },
    recoveryMomentum: {
      label: 'Not available',
      direction: 'right',
      status: 'stable',
    },
    behavioralCorrelation: 'Not available until health data synchronization is enabled.',
    brandContext: 'Fiteatsy client profile',
  }));
}

function getFiteatsyClientsErrorMessage(error) {
  if (!error) return null;
  if (error.status === 401) return 'Session expired';
  if (error.status === 403) return 'Consultant access required';
  return error.message || 'Unable to load Fiteatsy clients.';
}

function buildEmptyPlatformState() {
  return {
    employees: [],
    plans: [],
    sessions: [],
    tasks: [],
    communicationThreads: [],
    recoveryAlerts: [],
    reportPipeline: [],
    finance: {
      billing: [],
      revenue: [],
    },
    quality: [],
    organizationOverview: [],
    notifications: [],
    knowledgeBase: [],
  };
}

function buildNutritionProfileSnapshot(employee) {
  const bodyComposition = [
    ['Current weight', `${58 + (employee.id.length % 8)} kg`],
    ['Goal weight', `${55 + (employee.id.length % 6)} kg`],
    ['Waist', `${78 + (employee.id.length % 9)} cm`],
    ['BMI', `${(21.5 + (employee.id.length % 4) * 0.7).toFixed(1)}`],
  ];

  const lifestyle = [
    ['Occupation', employee.role],
    ['Activity level', employee.recovery >= 58 ? 'Moderate' : 'Low to moderate'],
    ['Work rhythm', employee.workSchedule],
    ['Travel frequency', employee.brand === 'Fiteatsy' ? 'Occasional' : 'Work-led'],
  ];

  const mealBehaviour = [
    ['Wake time', '6:30 AM'],
    ['Breakfast', '8:00 AM'],
    ['Dinner', '8:15 PM'],
    ['Water goal', `${Math.max(2, Math.round(employee.hydration / 30))} L`],
  ];

  const missing = [
    employee.brand === 'Fiteatsy' ? 'Goal weight confirmation' : null,
    employee.hydration < 55 ? 'Water intake pattern' : null,
    employee.biomarkers.some((item) => item.status !== 'stable') ? 'Latest blood report review' : null,
    employee.sleepQuality < 58 ? 'Sleep timing consistency' : null,
    employee.symptomProfile?.[0] ? null : 'Food preferences',
  ].filter(Boolean);

  const completionPercent = Math.max(58, 92 - missing.length * 8);
  const readinessPercent = Math.max(52, completionPercent - (missing.includes('Latest blood report review') ? 12 : 4));

  const timeline = [
    { id: `${employee.id}-nt-1`, time: '20 Jun', title: `Goal weight updated (${58 + (employee.id.length % 8)} -> ${55 + (employee.id.length % 6)} kg)` },
    { id: `${employee.id}-nt-2`, time: '18 Jun', title: `Activity level refined to ${employee.recovery >= 58 ? 'Moderate' : 'Low to moderate'}` },
    { id: `${employee.id}-nt-3`, time: '15 Jun', title: `New ${employee.reports[0]?.lab || 'lab'} report uploaded and OCR completed` },
    { id: `${employee.id}-nt-4`, time: '12 Jun', title: `Food profile updated for ${employee.dietaryStyle} and ${employee.region} meals` },
  ];

  return {
    completionPercent,
    readinessPercent,
    aiReady: readinessPercent >= 75,
    missing,
    bodyComposition,
    lifestyle,
    mealBehaviour,
    latestReport: employee.reports[0],
    timeline,
  };
}

function getRegionalMeals(employee) {
  return regionalMealLibrary[employee.region] || ['Balanced regional meal', 'Protein-forward snack', 'Simple recovery dinner'];
}

function buildDietSheetRows(employee, plan) {
  const meals = getRegionalMeals(employee);
  const biomarkerLink = employee.biomarkers.find((item) => item.status === 'declining' || item.status === 'critical')?.name || employee.biomarkers[0]?.name || 'Readiness';
  const supplements = employee.conditions.some((item) => item.toLowerCase().includes('vitamin d')) ? 'Vitamin D3' : employee.conditions.some((item) => item.toLowerCase().includes('thyroid')) ? 'Selenium support' : 'Electrolyte support';

  return [
    {
      id: `${employee.id}-meal-1`,
      time: '07:30',
      mealType: 'Breakfast',
      foodItem: meals[0],
      quantity: '1 serving',
      calories: 320,
      protein: 18,
      carbs: 42,
      fat: 9,
      fiber: 7,
      glycemicLoad: 12,
      hydration: '350 mL water',
      supplements,
      notes: 'Anchor the day early to reduce later drift.',
      alternatives: meals[1],
      adherenceDifficulty: 'Low',
      linkedBiomarker: biomarkerLink,
      behavioralGoal: 'Protect breakfast timing',
    },
    {
      id: `${employee.id}-meal-2`,
      time: '11:00',
      mealType: 'Mid-morning',
      foodItem: employee.dietaryStyle === 'Jain' ? 'Roasted chana + chaas' : 'Fruit + curd',
      quantity: '1 bowl',
      calories: 180,
      protein: 9,
      carbs: 22,
      fat: 5,
      fiber: 4,
      glycemicLoad: 8,
      hydration: '300 mL infused water',
      supplements: 'None',
      notes: 'Prevents long fasting gaps during work blocks.',
      alternatives: 'Makhana + buttermilk',
      adherenceDifficulty: 'Low',
      linkedBiomarker: biomarkerLink,
      behavioralGoal: 'Avoid skipped meals',
    },
    {
      id: `${employee.id}-meal-3`,
      time: '13:30',
      mealType: 'Lunch',
      foodItem: meals[2],
      quantity: '1 plate',
      calories: 460,
      protein: 24,
      carbs: 54,
      fat: 14,
      fiber: 8,
      glycemicLoad: 16,
      hydration: '250 mL chaas',
      supplements: 'None',
      notes: 'Keep lunch culturally familiar for adherence.',
      alternatives: meals[3],
      adherenceDifficulty: 'Medium',
      linkedBiomarker: biomarkerLink,
      behavioralGoal: 'Support mid-day energy stability',
    },
    {
      id: `${employee.id}-meal-4`,
      time: '17:00',
      mealType: 'Snack',
      foodItem: employee.dietaryStyle === 'vegetarian' ? 'Sprouts chaat' : 'Egg + fruit',
      quantity: '1 portion',
      calories: 190,
      protein: 12,
      carbs: 18,
      fat: 6,
      fiber: 5,
      glycemicLoad: 7,
      hydration: '300 mL water',
      supplements: 'None',
      notes: 'Reduces evening rebound hunger and late dinner load.',
      alternatives: meals[4],
      adherenceDifficulty: 'Medium',
      linkedBiomarker: biomarkerLink,
      behavioralGoal: 'Reduce evening cravings',
    },
    {
      id: `${employee.id}-meal-5`,
      time: '19:45',
      mealType: 'Dinner',
      foodItem: meals[3] || meals[2],
      quantity: '1 light plate',
      calories: 390,
      protein: 22,
      carbs: 36,
      fat: 12,
      fiber: 7,
      glycemicLoad: 11,
      hydration: '250 mL water',
      supplements: 'Magnesium support',
      notes: plan?.state === 'consultant_modified' ? 'Dinner carbohydrate density reduced after recent biomarker drift.' : 'Keep dinner lighter to protect recovery and sleep.',
      alternatives: meals[0],
      adherenceDifficulty: 'High',
      linkedBiomarker: biomarkerLink,
      behavioralGoal: 'Earlier lighter dinner',
    },
  ];
}

function buildInternalNotes(employee) {
  return employee.notes.map((note, index) => ({
    id: `${employee.id}-internal-${index}`,
    type: note.type || (index === 0 ? 'Clinical Observation' : index === 1 ? 'Behavioral Pattern' : 'Risk Annotation'),
    severity: note.severity || (employee.riskLevel === 'critical' ? 'critical' : employee.riskLevel === 'high' ? 'high' : 'medium'),
    tags: note.tags || [employee.region, employee.dietaryStyle, employee.conditionFocus?.condition || employee.conditions[0]],
    linkedBiomarker: note.linkedBiomarker || employee.biomarkers.find((item) => item.status !== 'stable')?.name || employee.biomarkers[0]?.name,
    linkedIntervention: note.linkedIntervention || employee.interventions[0]?.name || 'Routine support',
    linkedReport: note.linkedReport || employee.reports[0]?.name || 'Latest report',
    reminder: note.reminder || 'Review in next consultant check-in',
    pinned: index === 0,
    ...note,
  }));
}

function buildSharedClientNotes(employee) {
  return [
    {
      id: `${employee.id}-shared-1`,
      type: 'Daily Reflection',
      time: 'Today, 08:10',
      author: employee.name,
      text: employee.stress > 70 ? 'Sleep felt broken and cravings were stronger after late work.' : 'Energy felt steadier when lunch timing was on time.',
    },
    {
      id: `${employee.id}-shared-2`,
      type: employee.hydration < 55 ? 'Recovery Update' : 'Meal Feedback',
      time: 'Yesterday, 20:20',
      author: employee.name,
      text: employee.hydration < 55 ? 'Hydration dropped during travel and I felt more fatigued by evening.' : 'Regional meals felt easier to follow than the older plan format.',
    },
  ];
}

function buildChatMessages(employee, plan) {
  return [
    {
      id: `${employee.id}-chat-1`,
      sender: 'Nuetra AI',
      role: 'ai',
      type: 'Adherence Alert',
      time: 'Today, 07:45',
      text: employee.trendSummary.title,
      links: [employee.biomarkers[0]?.name, employee.interventions[0]?.name, 'Meal compliance'],
    },
    {
      id: `${employee.id}-chat-2`,
      sender: 'Dr. Aditi Kulkarni',
      role: 'consultant',
      type: 'Plan Clarification',
      time: 'Today, 09:05',
      text: `We are simplifying ${employee.region} meal options and protecting dinner timing before the next review.`,
      links: ['Dinner timing', plan?.state || 'draft_generated'],
    },
    {
      id: `${employee.id}-chat-3`,
      sender: employee.name,
      role: 'client',
      type: 'Check-In',
      time: 'Today, 12:15',
      text: employee.stress > 70 ? 'Late work made dinner slip again. I can manage easier snack prep this week.' : 'The current meal flow is manageable. Need more travel-friendly alternatives.',
      links: ['Meal timing', employee.goals[0]],
    },
  ];
}

function buildTimelineEvents(employee, plan) {
  const biomarkerEvent = employee.biomarkers
    .filter((item) => item.status !== 'stable')
    .slice(0, 2)
    .map((item, index) => ({
      id: `${employee.id}-timeline-bio-${index}`,
      kind: 'Biomarker movement',
      time: index === 0 ? 'Today, 07:40' : 'Yesterday, 16:10',
      title: `${item.name} ${item.status === 'improving' ? 'improved' : 'shifted into attention'}`,
      detail: `Current ${item.current} vs previous ${item.previous}.`,
      status: item.status,
    }));

  const reportEvents = employee.reports.map((report, index) => ({
    id: `${employee.id}-timeline-report-${index}`,
    kind: 'Report',
    time: report.uploadedAt,
    title: report.name,
    detail: `${report.ocrState} • confidence ${report.extractionConfidence}%`,
    status: report.ocrState === 'complete' ? 'improving' : 'medium',
  }));

  const noteEvents = employee.notes.slice(0, 2).map((note, index) => ({
    id: `${employee.id}-timeline-note-${index}`,
    kind: 'Internal note',
    time: note.time,
    title: `${note.author} added note`,
    detail: note.text,
    status: 'pending',
  }));

  const planEvents = (plan?.versions || []).slice(0, 2).map((version, index) => ({
    id: `${employee.id}-timeline-plan-${index}`,
    kind: 'Diet plan',
    time: version.time,
    title: version.label,
    detail: version.note,
    status: 'medium',
  }));

  return [...biomarkerEvent, ...reportEvents, ...noteEvents, ...planEvents];
}

function buildDietProtocolModules(employee, plan) {
  const meals = getRegionalMeals(employee);
  const coreBiomarker = employee.biomarkers.find((item) => item.status !== 'stable')?.name || employee.biomarkers[0]?.name;
  const isFiteatsy = employee.brand === 'Fiteatsy';

  return [
    {
      id: 'hydration-plan',
      title: 'Hydration Plan',
      summary: employee.hydration < 55 ? 'Hydration adherence is a friction point.' : 'Hydration is stable but can be optimized.',
      rationale: `Linked to ${coreBiomarker} movement and recovery stability.`,
      options: [
        { name: 'Morning hydration anchor', calories: 0, protein: 0, fiber: 0, glycemicLoad: 0, prepTime: '1 min', alternatives: 'Electrolyte water', biomarkerLinkage: coreBiomarker },
        { name: 'Commute hydration reminder', calories: 0, protein: 0, fiber: 0, glycemicLoad: 0, prepTime: '1 min', alternatives: 'Chaas on office days', biomarkerLinkage: 'Recovery' },
      ],
    },
    {
      id: 'breakfast',
      title: 'Breakfast',
      summary: isFiteatsy ? 'Earlier protein-forward breakfast to stabilize cravings and hormonal rhythm.' : 'Earlier protein-forward breakfast to reduce later drift.',
      rationale: `Added because ${summaryReason(employee)}.`,
      options: [
        { name: meals[0], calories: 320, protein: 18, fiber: 7, glycemicLoad: 12, prepTime: '15 min', alternatives: meals[1], biomarkerLinkage: coreBiomarker },
        { name: employee.dietaryStyle === 'vegetarian' ? 'Besan chilla + curd' : 'Egg bhurji + phulka', calories: 340, protein: 22, fiber: 5, glycemicLoad: 10, prepTime: '12 min', alternatives: 'Moong chilla', biomarkerLinkage: 'Readiness' },
      ],
    },
    {
      id: 'lunch',
      title: 'Lunch',
      summary: 'Culturally familiar midday structure for better adherence.',
      rationale: 'Lunch remains familiar because adherence improves when food identity is preserved.',
      options: [
        { name: meals[2], calories: 460, protein: 24, fiber: 8, glycemicLoad: 16, prepTime: '20 min', alternatives: meals[3], biomarkerLinkage: coreBiomarker },
      ],
    },
    {
      id: 'evening-snacks',
      title: 'Evening Snacks',
      summary: 'Designed to reduce rebound hunger and late dinner overload.',
      rationale: 'Snack compliance helps protect dinner timing and stress-driven eating.',
      options: [
        { name: employee.dietaryStyle === 'Jain' ? 'Roasted chana + chaas' : 'Sprouts chaat', calories: 180, protein: 11, fiber: 5, glycemicLoad: 7, prepTime: '5 min', alternatives: 'Makhana + buttermilk', biomarkerLinkage: 'Stress' },
      ],
    },
    {
      id: 'dinner',
      title: 'Dinner',
      summary: 'Lighter dinner to improve glucose and recovery stability.',
      rationale: 'Dinner carbohydrate density was reduced due to longitudinal biomarker drift.',
      options: [
        { name: meals[3] || meals[2], calories: 390, protein: 22, fiber: 7, glycemicLoad: 11, prepTime: '18 min', alternatives: meals[4] || meals[0], biomarkerLinkage: coreBiomarker },
      ],
    },
    {
      id: 'supplements',
      title: 'Supplements',
      summary: 'Protocol support for deficiencies and recovery windows.',
      rationale: 'Supplement cadence is linked to current deficiency and adherence reliability.',
      options: [
        { name: employee.conditions.some((item) => item.toLowerCase().includes('vitamin d')) ? 'Vitamin D3 + K2' : 'Magnesium glycinate', calories: 0, protein: 0, fiber: 0, glycemicLoad: 0, prepTime: '1 min', alternatives: 'Weekly supervision pack', biomarkerLinkage: coreBiomarker },
      ],
    },
    {
      id: 'behavioral-goals',
      title: 'Behavioral Goals',
      summary: 'Low-friction behavior anchors to support adherence.',
      rationale: 'Behavioral goals reduce decision fatigue and keep interventions human-readable.',
      options: [
        { name: 'Dinner before 8 PM', calories: 0, protein: 0, fiber: 0, glycemicLoad: 0, prepTime: 'Daily anchor', alternatives: 'Post-meal walk if dinner runs late', biomarkerLinkage: coreBiomarker },
        { name: 'Hydration checkpoint by noon', calories: 0, protein: 0, fiber: 0, glycemicLoad: 0, prepTime: 'Daily anchor', alternatives: 'Mentor reminder flow', biomarkerLinkage: 'Recovery' },
      ],
    },
    ...(isFiteatsy
      ? [
          {
            id: 'daily-seed-cycling',
            title: 'Daily Seed Cycling',
            summary: 'Seed rotation supports cycle awareness and lower hormonal friction.',
            rationale: 'Used when PCOS, cravings, and inflammatory symptoms need a low-complexity daily anchor.',
            options: [
              { name: 'Flax + pumpkin rotation', calories: 90, protein: 4, fiber: 4, glycemicLoad: 1, prepTime: '2 min', alternatives: 'Sesame + sunflower blend', biomarkerLinkage: 'Cycle stability' },
            ],
          },
          {
            id: 'herbal-tea-routine',
            title: 'Herbal Tea Routine',
            summary: 'Evening routine designed to reduce cravings and calm sympathetic load.',
            rationale: 'Supports stress, digestion, and bedtime transition during hormonal recovery.',
            options: [
              { name: 'Spearmint or fennel tea', calories: 0, protein: 0, fiber: 0, glycemicLoad: 0, prepTime: '5 min', alternatives: 'Cinnamon-cumin infusion', biomarkerLinkage: 'Stress' },
            ],
          },
          {
            id: 'night-hormone-routine',
            title: 'Night Hormone Routine',
            summary: 'Low-friction sleep and recovery routine to protect hormonal stabilization.',
            rationale: 'Sleep consistency is a core lever for cycle regulation and craving control.',
            options: [
              { name: 'Digital sunset + magnesium support', calories: 0, protein: 0, fiber: 0, glycemicLoad: 0, prepTime: '20 min routine', alternatives: 'Breathwork + warm shower reset', biomarkerLinkage: 'Sleep quality' },
            ],
          },
        ]
      : []),
  ];
}

function summaryReason(employee) {
  if (employee.biomarkers.some((item) => item.name === 'HbA1c' && item.status !== 'stable')) return 'worsening glucose stability required earlier protein and lower evening load';
  if (employee.burnoutRisk === 'critical' || employee.burnoutRisk === 'high') return 'recovery instability required simpler morning anchors and less late-night decision load';
  return 'adherence works better when meals remain familiar, simple, and schedule-friendly';
}

function getBiomarkerDomain(name = '') {
  const normalized = name.toLowerCase();
  if (['vitamin d', 'crp'].some((item) => normalized.includes(item))) return 'Inflammation';
  if (['hba1c', 'cholesterol'].some((item) => normalized.includes(item))) return 'Metabolic';
  if (['tsh', 'thyroid'].some((item) => normalized.includes(item))) return 'Thyroid';
  if (['cortisol', 'stress'].some((item) => normalized.includes(item))) return 'Recovery';
  if (['amh', 'fsh', 'lh', 'estrogen', 'progesterone'].some((item) => normalized.includes(item))) return 'Cycle/Reproductive';
  return 'Hormonal';
}

function Surface({ children, className = '', animated = false }) {
  const classes = `rounded-[var(--fluent-radius-card)] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)] ${className}`;

  if (animated) {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.24, ease: 'easeOut' }}
        className={classes}
      >
        {children}
      </motion.div>
    );
  }

  return <div className={classes}>{children}</div>;
}

function StatusChip({ status, children }) {
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize ${toneForStatus(status)}`}>{children}</span>;
}

function LoadingSkeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-[14px] bg-[var(--fluent-color-neutral-background-3)] ${className}`} />;
}

function formatDisplayValue(value, fallback = 'Not available') {
  if (value == null || value === '') return fallback;
  if (Array.isArray(value)) return value.length ? value.join(', ') : fallback;
  return String(value);
}

function medicationStatusTone(status) {
  const normalized = String(status || '').toUpperCase();
  const tones = {
    TAKEN: 'bg-[var(--fluent-color-status-success-background)] text-[var(--fluent-color-status-success-foreground)]',
    DUE: 'bg-[var(--fluent-color-status-warning-background)] text-[var(--fluent-color-status-warning-foreground)]',
    UPCOMING: 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-2)]',
    SNOOZED: 'bg-[rgba(99,124,239,0.18)] text-[#637CEF]',
    SKIPPED: 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-2)]',
    MISSED: 'bg-[var(--fluent-color-status-danger-background)] text-[var(--fluent-color-status-danger-foreground)]',
  };
  return tones[normalized] || tones.UPCOMING;
}

function formatMedicationStatus(status) {
  if (!status) return 'Upcoming';
  return String(status).toLowerCase().replace(/^\w/, (letter) => letter.toUpperCase());
}

function formatMedicationAdherencePercent(summary) {
  if (!summary || !summary.scheduled) return 'Not enough data';
  return summary.adherencePercent == null ? 'Not enough data' : `${summary.adherencePercent}%`;
}

function formatMedicationAdherence(summary) {
  if (!summary || !summary.scheduled) return 'Not enough data';
  return `${summary.taken || 0} / ${summary.scheduled} taken`;
}

function formatNextMedicationDose(nextDose) {
  if (!nextDose) return 'No upcoming dose';
  return `${nextDose.medicationName || 'Medication'}${nextDose.dosage ? ` ${nextDose.dosage}` : ''} · ${nextDose.scheduledTime || 'Time pending'}`;
}

function formatMedicationDateTime(value) {
  if (!value) return 'Not available';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Not available';
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatMedicationFrequency(frequency) {
  if (!frequency || typeof frequency !== 'object') return 'Not available';
  if (frequency.type === 'daily') return 'Daily';
  if (frequency.type === 'selected_days') return `Selected days${Array.isArray(frequency.daysOfWeek) && frequency.daysOfWeek.length ? ` · ${frequency.daysOfWeek.join(', ')}` : ''}`;
  if (frequency.type === 'interval_hours') return `Every ${frequency.intervalHours || 'configured'} hours`;
  if (frequency.type === 'as_needed') return 'As needed';
  return String(frequency.type || 'Not available').replace(/_/g, ' ');
}

function formatMedicationDuration(duration) {
  if (!duration || typeof duration !== 'object') return 'Not available';
  const start = duration.startDateISO ? formatDateLabel(duration.startDateISO) : 'Start pending';
  const end = duration.endDateISO ? formatDateLabel(duration.endDateISO) : 'Ongoing';
  return `${start} - ${end}`;
}

function formatMetricNumber(value, suffix = '') {
  if (value == null || Number.isNaN(Number(value))) return 'Not available';
  return `${value}${suffix}`;
}

function formatMetricCardValue(metric, fallback) {
  if (!metric || metric.status !== 'AVAILABLE') return fallback;
  return `${metric.value}${metric.unit ? ` ${metric.unit}` : ''}`;
}

function getHealthMetricStatusLabel(metric, fallback) {
  if (!metric) return fallback;
  if (metric.status === 'AVAILABLE') return metric.category || 'Available';
  return metric.reason || fallback;
}

function getProfileErrorMessage(error) {
  if (!error) return null;
  if (error.status === 401) return 'Session expired';
  if (error.status === 403) return 'Consultant access required';
  if (error.status === 404) return 'Client profile not found';
  return error.message || 'Unable to load client profile.';
}

function getNutritionWorkflowErrorMessage(error, fallback) {
  if (!error) return fallback;
  if (error.status === 401) return 'Session expired. Sign in again to continue the nutrition workflow.';
  if (error.status === 403) return 'Your account does not have permission for this nutrition action.';
  if (error.status === 404) return 'This nutrition record is no longer available.';
  if (String(error.message || '').toLowerCase() === 'failed to fetch') {
    return 'We could not reach the Fiteatsy backend. Check the production API connection and try again.';
  }
  return error.message || fallback;
}

function biomarkerTone(status) {
  const normalized = String(status || '').toUpperCase();
  if (['LOW', 'HIGH', 'CRITICAL'].includes(normalized)) return 'critical';
  return 'stable';
}

function wellnessTone(score) {
  if (score == null) return 'stable';
  if (score >= 75) return 'improving';
  if (score >= 55) return 'medium';
  return 'critical';
}

function formatScoreValue(score) {
  if (score == null || Number.isNaN(Number(score))) return 'Not available';
  return `${Math.round(Number(score))}`;
}

function formatLifecycleLabel(value) {
  if (!value) return 'Not started';
  return String(value).replace(/_/g, ' ');
}

async function fetchRealClientWorkspace(clientId) {
  return getFiteatsyConsultantClientProfile(clientId);
}

const mealPlanSectionEntries = [
  ['earlyMorning', 'Early Morning'],
  ['breakfast', 'Breakfast'],
  ['midMorningSnack', 'Mid Morning Snack'],
  ['lunch', 'Lunch'],
  ['eveningSnack', 'Evening Snack'],
  ['dinner', 'Dinner'],
  ['bedtimeNutrition', 'Bedtime Nourishment'],
];

function lifecycleTone(status) {
  if (status === 'published' || status === 'approved') return 'improving';
  if (status === 'submitted_for_review') return 'medium';
  if (status === 'changes_requested') return 'high';
  if (status === 'draft') return 'pending';
  return 'stable';
}

function workflowLabelFromLifecycle(status) {
  if (!status) return 'Not started';
  const labels = {
    draft: 'Draft',
    submitted_for_review: 'Awaiting Senior Consultant Review',
    changes_requested: 'Changes Requested',
    approved: 'Approved',
    published: 'Published',
    archived: 'Archived',
  };
  return labels[status] || formatLifecycleLabel(status);
}

function getWellnessAvailabilityCopy(key) {
  const copy = {
    activePerformance: {
      label: 'Awaiting movement sync',
      detail: 'Connect wearables or recent activity logs to unlock readiness and movement performance signals.',
    },
    energyBalance: {
      label: 'Awaiting sleep and energy signals',
      detail: 'Sleep rhythm, fatigue, and check-in history are needed before energy balance can be explained clearly.',
    },
    bodySupport: {
      label: 'Profile and markers required',
      detail: 'Body support strengthens once profile inputs and validated biomarker context are available together.',
    },
    nourishment: {
      label: 'Meal quality not mapped yet',
      detail: 'Nutrition logs, hydration rhythm, and plan adherence will unlock nourishment intelligence.',
    },
    recovery: {
      label: 'Recovery baseline in progress',
      detail: 'Recovery habits need a few days of profile, behavior, or wearable evidence before this score becomes reliable.',
    },
    physicalWellnessIndex: {
      label: 'Body resilience baseline pending',
      detail: 'Physical wellness becomes available after enough profile depth and supporting health signals are collected.',
    },
    stressResilience: {
      label: 'Stress assessment needed',
      detail: 'Stress Test inputs, routine quality, and recovery context are required before stress resilience can be scored.',
    },
  };
  return copy[key] || {
    label: 'Awaiting data',
    detail: 'This signal will appear when enough synced health context is available.',
  };
}

function deriveClientHealthStatus({ nutritionIntelligence, syncMetadata, wearableSummary, biomarkers }) {
  if (nutritionIntelligence?.riskLevel === 'high') {
    return {
      label: 'Needs clinical attention',
      tone: 'critical',
      detail: 'Nutrition intelligence detected higher-risk nutrition or biomarker signals.',
    };
  }
  if (biomarkers.some((item) => ['HIGH', 'LOW', 'CRITICAL'].includes(String(item.status || '').toUpperCase()))) {
    return {
      label: 'Review biomarkers',
      tone: 'medium',
      detail: 'Validated markers need consultant interpretation before finalizing the plan.',
    };
  }
  if (wearableSummary?.connected === false || !syncMetadata?.lastSyncedAt) {
    return {
      label: 'Building baseline',
      tone: 'pending',
      detail: 'Profile and manual data are active while connected health signals are still limited.',
    };
  }
  return {
    label: 'Ready for action',
    tone: 'improving',
    detail: 'Profile, targets, and health signals are available for guided next steps.',
  };
}

function buildDietPlanPayload(plan, version) {
  if (!plan || !version) return null;
  return {
    plan,
    version,
    templateVersion: plan.templateVersion,
    currentLifecycle: version.lifecycleStatus,
    currentVersionNumber: version.versionNumber,
    sourceSnapshot: version.sourceSnapshot,
    contentSummary: version.contentSummary,
    content: version.content,
  };
}

function trendLabel(trend) {
  if (!trend) return 'No trend';
  if (trend === 'UP') return 'Trending up';
  if (trend === 'DOWN') return 'Trending down';
  return 'Stable trend';
}

function HealthMetricCard({ icon: Icon, title, value, detail }) {
  return (
    <Surface className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-2.5 text-[var(--fluent-color-brand-foreground-link)]">
            <Icon size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{title}</p>
            <p className="mt-2 text-[24px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">{value}</p>
          </div>
        </div>
      </div>
      <p className="mt-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{detail}</p>
    </Surface>
  );
}

function WellnessIntelligenceCard({ item }) {
  const emptyState = item.value == null;
  const fallback = getWellnessAvailabilityCopy(item.key);

  return (
    <div className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{item.title}</p>
          <p className="mt-2 text-[30px] font-semibold tracking-[-0.03em] text-[var(--fluent-color-neutral-foreground-1)]">
            {emptyState ? fallback.label : formatScoreValue(item.value)}
          </p>
        </div>
        <StatusChip status={emptyState ? 'pending' : wellnessTone(item.value)}>
          {emptyState ? 'Awaiting sync' : 'Live'}
        </StatusChip>
      </div>
      <p className="mt-3 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
        {emptyState ? fallback.detail : item.detail}
      </p>
    </div>
  );
}

function OverviewStat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-3 rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3">
      <div className="mt-0.5 rounded-[12px] bg-[var(--fluent-color-neutral-background-1)] p-2 text-[var(--fluent-color-brand-foreground-link)] shadow-[0_1px_4px_rgba(15,23,42,0.08)]">
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{label}</p>
        <p className="mt-1 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)] break-words">{value}</p>
      </div>
    </div>
  );
}

function DetailField({ label, value }) {
  return (
    <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3">
      <p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{label}</p>
      <p className="mt-1 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{value}</p>
    </div>
  );
}

function RealClientProfileDrawer({
  isOpen,
  onClose,
  summaryClient,
  profile,
  loading,
  error,
  onProfileRefresh,
  onCreateMedicationFollowUp,
  onCreateFollowUp,
  canManageNutrition = false,
  canReviewDietPlans = false,
  canPublishDietPlans = false,
}) {
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState('Overview');
  const [dietPlanState, setDietPlanState] = useState(() => profile?.dietPlan || null);
  const [dietPlanContentDraft, setDietPlanContentDraft] = useState(() => profile?.dietPlan?.content || null);
  const [nutritionIntelligenceState, setNutritionIntelligenceState] = useState(() => profile?.nutritionIntelligence || null);
  const [medicationState, setMedicationState] = useState(() => profile?.medicationMonitoring || null);
  const [stressState, setStressState] = useState(() => profile?.stressAssessment || null);
  const [medicationLoading, setMedicationLoading] = useState(false);
  const [medicationError, setMedicationError] = useState(null);
  const [selectedMedicationId, setSelectedMedicationId] = useState(null);
  const [nutritionActionLoading, setNutritionActionLoading] = useState(false);
  const [nutritionActionError, setNutritionActionError] = useState(null);
  const [nutritionActionSuccess, setNutritionActionSuccess] = useState(null);
  const message = getProfileErrorMessage(error);
  const client = profile?.client;
  const onboarding = profile?.onboarding;
  const healthProfile = profile?.healthProfile;
  const metrics = profile?.healthMetrics;
  const bodyMetrics = profile?.bodyMetrics;
  const nutritionProtocol = profile?.nutritionProtocol;
  const nutritionIntelligence = profile?.nutritionIntelligence;
  const nutritionSnapshot = profile?.nutritionSnapshot;
  const syncMetadata = profile?.syncMetadata;
  const wearableSummary = profile?.wearableSummary;
  const planWorkflow = profile?.planWorkflow;
  const backendRecommendations = profile?.recommendations || [];
  const biomarkers = profile?.biomarkers || [];
  const reports = profile?.reports || [];
  const timeline = profile?.timeline || [];
  const workspaceTabs = ['Overview', 'Health Profile', 'Lifestyle', 'Reports', 'Biomarkers', 'Medication', 'Stress', ...(canManageNutrition ? ['Nutrition Plan'] : []), 'Activity', 'Timeline'];
  const groupedWorkspaceTabs = [
    { key: 'Overview', label: 'Overview' },
    { key: 'Health Profile', label: 'Health Intelligence' },
    { key: 'Medication', label: 'Medication' },
    { key: 'Stress', label: 'Stress / Assessments' },
    ...(canManageNutrition ? [{ key: 'Nutrition Plan', label: 'Nutrition' }] : []),
    { key: 'Reports', label: 'Reports' },
    { key: 'Activity', label: 'Activity' },
    { key: 'Timeline', label: 'Timeline' },
  ];
  const goalLabel = onboarding?.goal || summaryClient?.program || 'Not assigned';
  const profileStrength = syncMetadata?.completenessScore ?? healthProfile?.completionPercent ?? healthProfile?.profileCompleteness ?? summaryClient?.profileCompletedPercent;
  const lastSynced = syncMetadata?.lastSyncedAt || healthProfile?.updatedAtISO || healthProfile?.lastHealthUpdate || client?.lastActiveAt || summaryClient?.lastActivityAt;
  const bodyComposition = {
    waistCm: onboarding?.bodyComposition?.waistCm ?? healthProfile?.waistCm ?? null,
    hipCm: onboarding?.bodyComposition?.hipCm ?? healthProfile?.hipCm ?? null,
    neckCm: onboarding?.bodyComposition?.neckCm ?? healthProfile?.neckCm ?? null,
    goalWeightKg: onboarding?.bodyComposition?.goalWeightKg ?? healthProfile?.goalWeightKg ?? null,
  };
  const sleepQuality = onboarding?.lifestyle?.sleepQuality ?? healthProfile?.sleepQualityLabel ?? null;
  const stressLevel = onboarding?.lifestyle?.stressLevel ?? healthProfile?.stressLevelLabel ?? null;
  const healthStatus = deriveClientHealthStatus({
    nutritionIntelligence,
    syncMetadata,
    wearableSummary,
    biomarkers,
  });
  const riskFlags = [
    biomarkers.some((item) => String(item.name || '').toLowerCase().includes('b12') && ['LOW', 'CRITICAL'].includes(String(item.status || '').toUpperCase())) ? 'Low B12' : null,
    ['Poor', 'Average', 'Fair', 'Worst'].includes(String(sleepQuality || '')) ? 'Sleep quality needs attention' : null,
    ['High', 'Very High', '4', '5'].includes(String(stressLevel || '')) ? 'High stress load' : null,
    wearableSummary?.connected === false ? 'Wearable not connected' : null,
  ].filter(Boolean);
  const recommendedActions = backendRecommendations.length
    ? backendRecommendations.map((item) => item.action || item.title).filter(Boolean)
    : [
        nutritionProtocol?.macroTargets?.proteinGrams != null ? 'Review protein target with the client' : null,
        sleepQuality ? 'Improve sleep routine before advancing intensity' : null,
        biomarkers.length ? 'Review latest validated report markers' : null,
      ].filter(Boolean);
  const metricCards = [
    {
      key: 'bmi',
      icon: Scale,
      title: 'BMI',
      value: formatMetricCardValue(metrics?.bmi, 'Not available'),
      detail: getHealthMetricStatusLabel(metrics?.bmi, 'Height and weight required'),
    },
    {
      key: 'bmr',
      icon: Flame,
      title: 'BMR',
      value: formatMetricCardValue(metrics?.bmr, 'Not available'),
      detail: getHealthMetricStatusLabel(metrics?.bmr, 'Age, sex, height, and weight required'),
    },
    {
      key: 'tdee',
      icon: Activity,
      title: 'TDEE',
      value: formatMetricCardValue(metrics?.tdee, 'Not available'),
      detail: getHealthMetricStatusLabel(metrics?.tdee, 'Activity level required'),
    },
    {
      key: 'targetHeartRate',
      icon: HeartPulse,
      title: 'Target Heart Rate',
      value:
        metrics?.targetHeartRate?.status === 'AVAILABLE'
          ? metrics.targetHeartRate.category || formatMetricCardValue(metrics.targetHeartRate, 'Not available')
          : 'Not available',
      detail: metrics?.targetHeartRate?.status === 'AVAILABLE' ? 'Recommended working range' : getHealthMetricStatusLabel(metrics?.targetHeartRate, 'Age required'),
    },
    {
      key: 'bodyFat',
      icon: Ruler,
      title: 'Body Fat',
      value: formatMetricCardValue(metrics?.bodyFat, 'Measurements required'),
      detail: metrics?.bodyFat?.status === 'AVAILABLE' ? 'Estimated body fat percentage' : 'Measurements required',
    },
    {
      key: 'oneRepMax',
      icon: Dumbbell,
      title: 'One Rep Max',
      value: formatMetricCardValue(metrics?.oneRepMax, 'Workout data required'),
      detail: metrics?.oneRepMax?.status === 'AVAILABLE' ? 'Estimated strength ceiling' : 'Workout data required',
    },
  ];
  const snapshotCards = [
    { icon: Scale, title: 'BMI', value: bodyMetrics?.bmi != null ? `${bodyMetrics.bmi}` : formatMetricCardValue(metrics?.bmi, 'Complete profile'), detail: 'Body status' },
    { icon: ListChecks, title: 'Goal', value: formatDisplayValue(goalLabel), detail: 'Current programme focus' },
    { icon: Flame, title: 'Calories', value: nutritionProtocol?.calorieTarget != null ? `${nutritionProtocol.calorieTarget} kcal` : formatMetricCardValue(metrics?.tdee, 'Needs profile'), detail: 'Daily target' },
    { icon: Dumbbell, title: 'Protein', value: nutritionProtocol?.macroTargets?.proteinGrams != null ? `${nutritionProtocol.macroTargets.proteinGrams}g` : 'Needs profile', detail: 'Daily target' },
    { icon: Activity, title: 'Hydration', value: nutritionProtocol?.hydrationTargetLiters != null ? `${nutritionProtocol.hydrationTargetLiters}L` : 'Needs profile', detail: 'Daily target' },
  ];
  const wellnessScoreCards = [
    { key: 'activePerformance', title: 'Active Performance', value: nutritionIntelligence?.wellnessScores?.activePerformance ?? profile?.recoveryMetrics?.activityScore?.scoreValue ?? null, detail: 'Movement and daily performance readiness' },
    { key: 'energyBalance', title: 'Energy Balance', value: nutritionIntelligence?.wellnessScores?.energyBalance ?? profile?.recoveryMetrics?.sleepScore?.scoreValue ?? null, detail: 'Sleep and energy regulation quality' },
    { key: 'bodySupport', title: 'Body Support', value: nutritionIntelligence?.wellnessScores?.bodySupport ?? profile?.recoveryMetrics?.bodySupportScore?.scoreValue ?? null, detail: 'Clinical support from profile and markers' },
    { key: 'nourishment', title: 'Nourishment', value: nutritionIntelligence?.wellnessScores?.nourishment ?? profile?.recoveryMetrics?.nourishmentScore?.scoreValue ?? null, detail: 'Food quality, hydration, and meal rhythm' },
    { key: 'recovery', title: 'Recovery', value: nutritionIntelligence?.wellnessScores?.recovery ?? profile?.recoveryMetrics?.recoveryScore?.scoreValue ?? null, detail: 'Recovery habits and restoration capacity' },
    { key: 'physicalWellnessIndex', title: 'Physical Wellness Index', value: nutritionIntelligence?.wellnessScores?.physicalWellnessIndex ?? profile?.recoveryMetrics?.physicalWellnessIndex?.scoreValue ?? null, detail: 'Overall backend-computed body resilience' },
    { key: 'stressResilience', title: 'Stress Resilience', value: nutritionIntelligence?.wellnessScores?.stressResilience ?? profile?.recoveryMetrics?.calmScore?.scoreValue ?? null, detail: 'Stress handling from Stress Test and recovery context' },
  ];
  const medicationMonitoring = medicationState || profile?.medicationMonitoring || null;
  const stressAssessment = stressState || profile?.stressAssessment || null;
  const medicationSummary = medicationMonitoring?.summary || null;
  const activeMedications = Array.isArray(medicationMonitoring?.activeMedications) ? medicationMonitoring.activeMedications : [];
  const todaysMedicationDoses = Array.isArray(medicationMonitoring?.todaysDoses) ? medicationMonitoring.todaysDoses : [];
  const medicationHistory = Array.isArray(medicationMonitoring?.history) ? medicationMonitoring.history : [];
  const selectedMedication = activeMedications.find((item) => item.id === selectedMedicationId) || activeMedications[0] || null;

  useEffect(() => {
    setDietPlanState(profile?.dietPlan || null);
    setDietPlanContentDraft(profile?.dietPlan?.content || null);
    setNutritionIntelligenceState(profile?.nutritionIntelligence || null);
    setMedicationState(profile?.medicationMonitoring || null);
    setStressState(profile?.stressAssessment || null);
    setSelectedMedicationId(null);
    setMedicationError(null);
    setNutritionActionError(null);
    setNutritionActionSuccess(null);
  }, [profile?.dietPlan, profile?.nutritionIntelligence, profile?.medicationMonitoring, profile?.client?.id]);

  useEffect(() => {
    if (!isOpen || !summaryClient?.id || profile?.stressAssessment) return;
    void getFiteatsyConsultantClientStressSummary(summaryClient.id)
      .then((payload) => setStressState(payload?.assessment || null))
      .catch(() => setStressState(null));
  }, [isOpen, profile?.stressAssessment, summaryClient?.id]);

  useEffect(() => {
    if (isOpen) setActiveWorkspaceTab('Overview');
  }, [isOpen, summaryClient?.id]);

  useEffect(() => {
    if (!workspaceTabs.includes(activeWorkspaceTab)) {
      setActiveWorkspaceTab('Overview');
    }
  }, [activeWorkspaceTab, workspaceTabs]);

  const refreshWorkspace = useCallback(async () => {
    if (typeof onProfileRefresh !== 'function' || !summaryClient?.id) return null;
    const refreshed = await onProfileRefresh(summaryClient.id);
    return refreshed;
  }, [onProfileRefresh, summaryClient?.id]);

  const refreshMedications = useCallback(async () => {
    if (!summaryClient?.id) return null;
    setMedicationLoading(true);
    setMedicationError(null);
    try {
      const payload = await getFiteatsyConsultantClientMedications(summaryClient.id);
      const monitoring = payload?.medicationMonitoring || null;
      setMedicationState(monitoring);
      setSelectedMedicationId((current) => current || monitoring?.activeMedications?.[0]?.id || null);
      return monitoring;
    } catch (fetchError) {
      setMedicationError(fetchError);
      return null;
    } finally {
      setMedicationLoading(false);
    }
  }, [summaryClient?.id]);

  const syncNutritionSurfaces = useCallback(async () => {
    if (!summaryClient?.id) return;
    try {
      const [latestPlan, latestIntelligence] = await Promise.all([
        getFiteatsyConsultantLatestDietPlan(summaryClient.id).catch((error) => {
          if (error?.status === 404) return null;
          throw error;
        }),
        getFiteatsyConsultantNutritionIntelligence(summaryClient.id).catch((error) => {
          if (error?.status === 404) return null;
          throw error;
        }),
      ]);

      if (latestPlan?.plan && latestPlan?.version) {
        const nextDietPlan = buildDietPlanPayload(latestPlan.plan, latestPlan.version);
        setDietPlanState(nextDietPlan);
        setDietPlanContentDraft(nextDietPlan?.content || null);
      } else if (!profile?.dietPlan) {
        setDietPlanState(null);
        setDietPlanContentDraft(null);
      }

      if (latestIntelligence?.intelligence) {
        setNutritionIntelligenceState(latestIntelligence.intelligence);
      } else if (!profile?.nutritionIntelligence) {
        setNutritionIntelligenceState(null);
      }
    } catch (error) {
      setNutritionActionError(
        getNutritionWorkflowErrorMessage(error, 'Unable to load nutrition intelligence.')
      );
    }
  }, [profile?.dietPlan, profile?.nutritionIntelligence, summaryClient?.id]);

  useEffect(() => {
    if (!isOpen || !summaryClient?.id) return;
    void syncNutritionSurfaces();
  }, [isOpen, summaryClient?.id, syncNutritionSurfaces]);

  useEffect(() => {
    if (!isOpen || !summaryClient?.id) return;
    void refreshMedications();
  }, [isOpen, summaryClient?.id, refreshMedications]);

  const handleGenerateDietPlan = useCallback(async () => {
    if (!summaryClient?.id || nutritionActionLoading) return;
    setNutritionActionLoading(true);
    setNutritionActionError(null);
    setNutritionActionSuccess(null);
    try {
      const response = await generateFiteatsyConsultantDietPlanDraft(summaryClient.id, {});
      const nextDietPlan = buildDietPlanPayload(response?.plan, response?.version);
      setDietPlanState(nextDietPlan);
      setDietPlanContentDraft(nextDietPlan?.content || null);
      if (response?.intelligence) {
        setNutritionIntelligenceState(response.intelligence);
      }
      await refreshWorkspace();
      setActiveWorkspaceTab('Nutrition Plan');
      setNutritionActionSuccess('Diet chart draft generated from the live Fiteatsy intelligence contract.');
    } catch (actionError) {
      setNutritionActionError(getNutritionWorkflowErrorMessage(actionError, 'Unable to generate a diet chart draft right now.'));
    } finally {
      setNutritionActionLoading(false);
    }
  }, [nutritionActionLoading, refreshWorkspace, summaryClient?.id]);

  const handleDietFieldChange = useCallback((path, value) => {
    setDietPlanContentDraft((current) => {
      if (!current) return current;
      const next = structuredClone(current);
      let cursor = next;
      for (let index = 0; index < path.length - 1; index += 1) {
        cursor = cursor[path[index]];
      }
      cursor[path[path.length - 1]] = value;
      return next;
    });
  }, []);

  const handleSaveDraft = useCallback(async () => {
    if (!summaryClient?.id || !dietPlanState?.plan?.id || !dietPlanContentDraft || nutritionActionLoading) return;
    setNutritionActionLoading(true);
    setNutritionActionError(null);
    setNutritionActionSuccess(null);
    try {
      const response = await updateFiteatsyConsultantDietPlanDraft(summaryClient.id, dietPlanState.plan.id, {
        content: dietPlanContentDraft,
        reviewNotes: 'Consultant reviewed and updated diet chart.',
      });
      const nextDietPlan = buildDietPlanPayload(response?.plan, response?.version);
      setDietPlanState(nextDietPlan);
      setDietPlanContentDraft(nextDietPlan?.content || dietPlanContentDraft);
      await refreshWorkspace();
      setNutritionActionSuccess('Diet chart draft saved. Submit it when it is ready for review.');
    } catch (actionError) {
      setNutritionActionError(getNutritionWorkflowErrorMessage(actionError, 'Unable to save the diet chart changes right now.'));
    } finally {
      setNutritionActionLoading(false);
    }
  }, [dietPlanContentDraft, dietPlanState?.plan?.id, nutritionActionLoading, refreshWorkspace, summaryClient?.id]);

  const handleSubmitForReview = useCallback(async () => {
    if (!summaryClient?.id || !dietPlanState?.plan?.id || nutritionActionLoading) return;
    setNutritionActionLoading(true);
    setNutritionActionError(null);
    setNutritionActionSuccess(null);
    try {
      const response = await submitFiteatsyConsultantDietPlanForReview(summaryClient.id, dietPlanState.plan.id);
      const nextDietPlan = buildDietPlanPayload(response?.plan, response?.version);
      setDietPlanState(nextDietPlan);
      setDietPlanContentDraft(nextDietPlan?.content || dietPlanContentDraft);
      await refreshWorkspace();
      setNutritionActionSuccess('Diet chart submitted for Senior Consultant review.');
    } catch (actionError) {
      setNutritionActionError(getNutritionWorkflowErrorMessage(actionError, 'Unable to submit this diet chart for review.'));
    } finally {
      setNutritionActionLoading(false);
    }
  }, [dietPlanContentDraft, dietPlanState?.plan?.id, nutritionActionLoading, refreshWorkspace, summaryClient?.id]);

  const handleApprovePlan = useCallback(async () => {
    if (!summaryClient?.id || !dietPlanState?.plan?.id || nutritionActionLoading) return;
    setNutritionActionLoading(true);
    setNutritionActionError(null);
    setNutritionActionSuccess(null);
    try {
      const response = await approveFiteatsyConsultantDietPlan(summaryClient.id, dietPlanState.plan.id);
      const nextDietPlan = buildDietPlanPayload(response?.plan, response?.version);
      setDietPlanState(nextDietPlan);
      setDietPlanContentDraft(nextDietPlan?.content || dietPlanContentDraft);
      await refreshWorkspace();
      setNutritionActionSuccess('Diet chart approved. It is ready for publish when you are satisfied.');
    } catch (actionError) {
      setNutritionActionError(getNutritionWorkflowErrorMessage(actionError, 'Unable to approve this diet chart.'));
    } finally {
      setNutritionActionLoading(false);
    }
  }, [dietPlanContentDraft, dietPlanState?.plan?.id, nutritionActionLoading, refreshWorkspace, summaryClient?.id]);

  const handlePublishPlan = useCallback(async () => {
    if (
      !summaryClient?.id ||
      !dietPlanState?.plan?.id ||
      !dietPlanState?.version?.id ||
      dietPlanState.currentLifecycle !== 'approved' ||
      nutritionActionLoading
    ) return;
    const versionLabel = `Version ${dietPlanState.currentVersionNumber}`;
    const clientName = summaryClient.name || profile?.client?.name || 'this client';
    const confirmed = window.confirm(
      `Publish diet plan to client?\n\nThe approved ${versionLabel} will become ${clientName}'s active nutrition plan in Fiteatsy.`,
    );
    if (!confirmed) return;
    setNutritionActionLoading(true);
    setNutritionActionError(null);
    setNutritionActionSuccess(null);
    try {
      const response = await publishFiteatsyConsultantDietPlan(
        summaryClient.id,
        dietPlanState.plan.id,
        dietPlanState.version.id,
      );
      const nextDietPlan = buildDietPlanPayload(response?.plan, response?.version);
      setDietPlanState(nextDietPlan);
      setDietPlanContentDraft(nextDietPlan?.content || dietPlanContentDraft);
      await refreshWorkspace();
      setNutritionActionSuccess('Diet chart published. The client mobile app can now consume the published plan only.');
    } catch (actionError) {
      setNutritionActionError(getNutritionWorkflowErrorMessage(actionError, 'Unable to publish this diet chart.'));
    } finally {
      setNutritionActionLoading(false);
    }
  }, [dietPlanContentDraft, dietPlanState, nutritionActionLoading, profile?.client?.name, refreshWorkspace, summaryClient]);

  const renderOverview = () => (
    <div className="space-y-4">
      <Surface className="p-5" animated>
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-[620px]">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Health Snapshot</p>
            <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
              A consultant-ready view of today&apos;s measurable health state, backend nutrition targets, and the clearest next action.
            </p>
          </div>
          <div className="min-w-[220px] rounded-[20px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Client health status</p>
                <p className="mt-2 text-base font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{healthStatus.label}</p>
              </div>
              <StatusChip status={healthStatus.tone}>{healthStatus.tone === 'pending' ? 'Baseline' : 'Live'}</StatusChip>
            </div>
            <p className="mt-3 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">{healthStatus.detail}</p>
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {snapshotCards.map((metric) => (
            <HealthMetricCard key={metric.title} icon={metric.icon} title={metric.title} value={metric.value} detail={metric.detail} />
          ))}
        </div>
      </Surface>
      <Surface className="p-5" animated>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Medication</p>
            <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
              Read-only adherence snapshot from the client&apos;s medication tracker.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveWorkspaceTab('Medication')}
              className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-neutral-foreground-1)]"
            >
              View medication
            </button>
            {typeof onCreateMedicationFollowUp === 'function' ? (
              <button
                onClick={() => onCreateMedicationFollowUp(summaryClient?.id, 'Review medication adherence')}
                className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-neutral-foreground-1)]"
              >
                Create follow-up
              </button>
            ) : null}
          </div>
        </div>
        {medicationLoading && !medicationMonitoring ? (
          <div className="mt-4 grid gap-3 md:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => <LoadingSkeleton key={index} className="h-20 w-full" />)}
          </div>
        ) : medicationError ? (
          <div className="mt-4 rounded-[16px] bg-[var(--fluent-color-status-danger-background)] px-4 py-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
            Unable to load medication monitoring. {medicationError?.status === 403 ? 'This client is not assigned for medication access.' : medicationError?.message || ''}
          </div>
        ) : medicationSummary ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <DetailField label="Active medications" value={`${medicationSummary.activeMedicationCount || 0}`} />
            <DetailField label="Today" value={formatMedicationAdherence(medicationSummary.today, 'takenCount')} />
            <DetailField label="7-day adherence" value={formatMedicationAdherencePercent(medicationSummary.sevenDay)} />
            <DetailField label="Missed" value={`${medicationSummary.sevenDay?.missed || medicationSummary.today?.missed || 0}`} />
            <DetailField label="Next dose" value={formatNextMedicationDose(medicationSummary.nextDose)} />
          </div>
        ) : (
          <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
            No medication data synced for this client yet.
          </div>
        )}
      </Surface>
      <div className="grid gap-4 lg:grid-cols-2">
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Risk Flags</p>
          <div className="mt-4 space-y-2">
            {riskFlags.length ? riskFlags.map((flag) => (
              <div key={flag} className="rounded-[16px] bg-[var(--fluent-color-status-warning-background)] px-4 py-3 text-sm font-medium text-[var(--fluent-color-status-warning-foreground)]">
                {flag}
              </div>
            )) : (
              <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No active risk flags from synced data yet.
              </div>
            )}
          </div>
        </Surface>
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Recommended Actions</p>
          <div className="mt-4 space-y-2">
            {recommendedActions.length ? recommendedActions.map((action, index) => (
              <div key={action} className="flex gap-3 rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)]">
                <span className="font-semibold text-[var(--fluent-color-brand-foreground-link)]">{index + 1}.</span>
                <span>{action}</span>
              </div>
            )) : (
              <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No action assigned. Profile and report data will unlock consultant recommendations.
              </div>
            )}
          </div>
        </Surface>
      </div>
      <Surface className="p-5" animated>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Wellness Intelligence</p>
            <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              Backend-owned scores based on profile, reports, biomarkers, wearables, and stress assessment.
            </p>
          </div>
          <div className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">
            Source: {formatDisplayValue(syncMetadata?.dataSource, 'Fiteatsy intelligence')}
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {wellnessScoreCards.map((item) => (
            <WellnessIntelligenceCard key={item.key} item={item} />
          ))}
        </div>
      </Surface>
      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Nutrition Intelligence</p>
          {nutritionIntelligenceState ? (
            <div className="mt-4 space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <StatusChip status={nutritionIntelligenceState.riskLevel === 'high' ? 'critical' : nutritionIntelligenceState.riskLevel === 'needs_attention' ? 'medium' : 'improving'}>
                  {nutritionIntelligenceState.riskLevel.replace(/_/g, ' ')}
                </StatusChip>
                {(nutritionIntelligenceState.nutritionFocus || []).slice(0, 4).map((item) => (
                  <span key={item} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{item}</span>
                ))}
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {(nutritionIntelligenceState.observations || []).slice(0, 4).map((item) => (
                  <div key={item.title} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                    <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
                    <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Sources: {item.sources.join(', ')}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              Nutrition intelligence is not available yet for this client.
            </div>
          )}
        </Surface>
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Biomarker Snapshot</p>
          <div className="mt-4 space-y-3">
            {nutritionIntelligenceState?.biomarkerSnapshot?.length ? nutritionIntelligenceState.biomarkerSnapshot.slice(0, 5).map((item) => (
              <div key={`${item.name}-${item.testDate}`} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{`${item.value} ${item.unit}`.trim()} • {formatDisplayValue(item.referenceRange)}</p>
                  </div>
                  <StatusChip status={biomarkerTone(item.status)}>{item.status}</StatusChip>
                </div>
              </div>
            )) : (
              <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No biomarker snapshot is available yet.
              </div>
            )}
          </div>
        </Surface>
      </div>
    </div>
  );

  const renderHealthProfile = () => (
    <div className="space-y-4">
      <Surface className="p-5" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Personal Information</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <DetailField label="Age" value={formatDisplayValue(client?.age)} />
          <DetailField label="Gender" value={formatDisplayValue(client?.gender)} />
          <DetailField label="Height" value={onboarding?.height != null ? `${onboarding.height} cm` : 'Complete profile to calculate'} />
          <DetailField label="Weight" value={onboarding?.weight != null ? `${onboarding.weight} kg` : 'Complete profile to calculate'} />
        </div>
      </Surface>
      <Surface className="p-5" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Body Composition</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <DetailField label="BMI" value={bodyMetrics?.bmi != null ? `${bodyMetrics.bmi}` : 'Complete profile to calculate'} />
          <DetailField label="Body Fat" value={bodyMetrics?.bodyFat != null ? `${bodyMetrics.bodyFat}%` : formatMetricCardValue(metrics?.bodyFat, 'Measurements required')} />
          <DetailField label="Waist" value={bodyComposition.waistCm != null ? `${bodyComposition.waistCm} cm` : 'Not available'} />
          <DetailField label="Hip" value={bodyComposition.hipCm != null ? `${bodyComposition.hipCm} cm` : 'Not available'} />
          <DetailField label="Neck" value={bodyComposition.neckCm != null ? `${bodyComposition.neckCm} cm` : 'Not available'} />
          <DetailField label="Goal weight" value={bodyComposition.goalWeightKg != null ? `${bodyComposition.goalWeightKg} kg` : 'Not available'} />
        </div>
      </Surface>
      <Surface className="p-5" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Medical History</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <DetailField label="Diabetes" value={formatDisplayValue(onboarding?.healthHistory?.diabetes)} />
          <DetailField label="Thyroid" value={formatDisplayValue(onboarding?.healthHistory?.thyroid)} />
          <DetailField label="PCOS" value={formatDisplayValue(onboarding?.healthHistory?.pcos)} />
          <DetailField label="Cholesterol" value={formatDisplayValue(onboarding?.healthHistory?.cholesterol)} />
          <DetailField label="Heart conditions" value={formatDisplayValue(onboarding?.healthHistory?.heartConditions)} />
          <DetailField label="Medical conditions" value={formatDisplayValue(onboarding?.medicalConditions)} />
        </div>
      </Surface>
    </div>
  );

  const renderLifestyle = () => (
    <Surface className="p-5" animated>
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Lifestyle</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <DetailField label="Sleep" value={onboarding?.lifestyle?.sleepHours != null ? `${onboarding.lifestyle.sleepHours} hrs` : 'Complete profile to calculate'} />
        <DetailField label="Sleep quality" value={formatDisplayValue(sleepQuality)} />
        <DetailField label="Stress" value={formatDisplayValue(stressLevel)} />
        <DetailField label="Activity" value={formatDisplayValue(onboarding?.activityLevel)} />
        <DetailField label="Food preference" value={formatDisplayValue(onboarding?.dietPreference)} />
        <DetailField label="Preferred cuisines" value={formatDisplayValue(onboarding?.nutrition?.preferredCuisines)} />
        <DetailField label="Allergies" value={formatDisplayValue(onboarding?.nutrition?.foodAllergies)} />
        <DetailField label="Dislikes" value={formatDisplayValue(onboarding?.nutrition?.foodDislikes)} />
      </div>
    </Surface>
  );

  const renderReports = () => (
    <Surface className="p-5" animated>
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Reports Timeline</p>
      <div className="mt-4 space-y-3">
        {reports.length ? reports.map((report) => (
          <div key={report.id || report.reportId} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{formatDateLabel(report.reportDate || report.createdAt || report.uploadedAt)}</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{report.title || report.originalFilename || 'Blood Report Uploaded'}</p>
              </div>
              <StatusChip status={String(report.processingStatus || report.status || '').toUpperCase() === 'PUBLISHED' ? 'stable' : 'medium'}>{report.processingStatus || report.status || 'Uploaded'}</StatusChip>
            </div>
            <p className="mt-3 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
              AI Extracted: {biomarkers.slice(0, 5).map((item) => item.name).join(', ') || 'No validated biomarkers yet'}
            </p>
          </div>
        )) : (
          <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
            Client has not uploaded any health reports yet.
          </div>
        )}
      </div>
    </Surface>
  );

  const renderBiomarkers = () => (
    <Surface className="p-5" animated>
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Validated Biomarkers</p>
      {biomarkers.length ? (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {biomarkers.map((biomarker) => (
            <div key={biomarker.biomarkerId} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{biomarker.name}</p>
                  <p className="mt-2 text-[24px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">
                    {`${biomarker.value} ${biomarker.unit}`.trim()}
                  </p>
                </div>
                <StatusChip status={biomarkerTone(biomarker.status)}>{biomarker.status}</StatusChip>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <DetailField label="Reference" value={formatDisplayValue(biomarker.referenceRange)} />
                <DetailField label="Trend" value={trendLabel(biomarker.trend)} />
                <DetailField label="Previous value" value={biomarker.previousValue != null ? `${biomarker.previousValue} ${biomarker.unit}`.trim() : 'Not available'} />
                <DetailField label="Test date" value={formatDateLabel(biomarker.testDate)} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
          No validated biomarkers available yet.
        </div>
      )}
    </Surface>
  );

  const renderNutrition = () => (
    !canManageNutrition ? (
      <Surface className="p-5" animated>
        <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
          Nutrition workflow is restricted to consultant-authorized roles.
        </div>
      </Surface>
    ) : (
    <div className="space-y-4">
      <Surface className="p-5" animated>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Prepare Personalised Diet Chart</p>
            <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
              Build the diet plan from live Fiteatsy health profile, validated biomarkers, wellness intelligence, and nutrition targets. No frontend calculations are used.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleGenerateDietPlan}
              disabled={nutritionActionLoading}
              className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {nutritionActionLoading && !dietPlanState ? 'Preparing...' : 'Prepare Diet Chart'}
            </button>
            {dietPlanState?.plan?.id ? (
              <>
                <button
                  onClick={handleSaveDraft}
                  disabled={nutritionActionLoading || !dietPlanContentDraft}
                  className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-neutral-foreground-1)] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Save Draft
                </button>
                {!canReviewDietPlans ? (
                  <button
                    onClick={handleSubmitForReview}
                    disabled={nutritionActionLoading || !['draft', 'changes_requested'].includes(dietPlanState.currentLifecycle)}
                    className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Submit for Review
                  </button>
                ) : (
                  <button
                    onClick={handleApprovePlan}
                    disabled={nutritionActionLoading || dietPlanState.currentLifecycle !== 'submitted_for_review'}
                    className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-neutral-foreground-1)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Approve
                  </button>
                )}
                {canPublishDietPlans && dietPlanState.currentLifecycle === 'approved' ? (
                  <button
                    onClick={handlePublishPlan}
                    disabled={nutritionActionLoading}
                    className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {dietPlanState.plan.latestPublishedVersionId ? 'Publish Update' : 'Publish to Client'}
                  </button>
                ) : canPublishDietPlans && dietPlanState.currentLifecycle === 'published' ? (
                  <button
                    disabled
                    className="cursor-not-allowed rounded-full bg-[var(--fluent-color-status-success-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-status-success-foreground)]"
                  >
                    Published
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </div>
        {nutritionActionError ? (
          <div className="mt-4 rounded-[16px] bg-[var(--fluent-color-status-danger-background)] px-4 py-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
            <p className="font-semibold">Unable to load nutrition intelligence.</p>
            <p className="mt-1">{nutritionActionError}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                onClick={() => void syncNutritionSurfaces()}
                className="rounded-full border border-[var(--fluent-color-status-danger-foreground)] px-3 py-1.5 text-xs font-semibold"
              >
                Retry
              </button>
              <button
                className="rounded-full border border-transparent bg-[rgba(255,255,255,0.2)] px-3 py-1.5 text-xs font-semibold"
              >
                Contact support
              </button>
            </div>
          </div>
        ) : null}
        {nutritionActionSuccess ? (
          <div className="mt-4 rounded-[16px] bg-[var(--fluent-color-status-success-background)] px-4 py-3 text-sm text-[var(--fluent-color-status-success-foreground)]">
            {nutritionActionSuccess}
          </div>
        ) : null}
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <DetailField label="Current goal" value={formatDisplayValue(goalLabel)} />
          <DetailField label="Calories" value={nutritionProtocol?.calorieTarget != null ? `${nutritionProtocol.calorieTarget} kcal` : 'No target calculated'} />
          <DetailField label="Protein" value={nutritionProtocol?.macroTargets?.proteinGrams != null ? `${nutritionProtocol.macroTargets.proteinGrams}g` : 'No target calculated'} />
          <DetailField label="Hydration" value={nutritionProtocol?.hydrationTargetLiters != null ? `${nutritionProtocol.hydrationTargetLiters}L` : 'No target calculated'} />
        </div>
      </Surface>

      <div className="grid gap-4 xl:grid-cols-[0.96fr_1.04fr]">
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Generation Inputs</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <DetailField label="Age" value={formatDisplayValue(nutritionIntelligenceState?.clientSummary?.age)} />
            <DetailField label="Gender" value={formatDisplayValue(nutritionIntelligenceState?.clientSummary?.gender)} />
            <DetailField label="Weight" value={nutritionIntelligenceState?.clientSummary?.weightKg != null ? `${nutritionIntelligenceState.clientSummary.weightKg} kg` : 'Not available'} />
            <DetailField label="BMI" value={nutritionIntelligenceState?.clientSummary?.bmi != null ? `${nutritionIntelligenceState.clientSummary.bmi}` : 'Not available'} />
            <DetailField label="Stress" value={formatDisplayValue(nutritionIntelligenceState?.clientSummary?.stressBand)} />
            <DetailField label="Water intake" value={nutritionIntelligenceState?.clientSummary?.waterIntakeLiters != null ? `${nutritionIntelligenceState.clientSummary.waterIntakeLiters} L` : 'Not available'} />
            <DetailField label="Activity level" value={formatDisplayValue(nutritionIntelligenceState?.clientSummary?.activityLevel)} />
            <DetailField label="Diet preference" value={formatDisplayValue(nutritionIntelligenceState?.generationInputs?.dietPreference)} />
          </div>
          <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4">
            <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Lifestyle Summary</p>
            <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
              {nutritionIntelligenceState?.generationInputs?.lifestyleSummary || 'Lifestyle summary is not available yet.'}
            </p>
          </div>
        </Surface>

        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Consultant Guidance</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Health Observations</p>
              <div className="mt-3 space-y-2">
                {(nutritionIntelligenceState?.observations || []).slice(0, 4).map((item) => (
                  <div key={item.title} className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
                  </div>
                ))}
                {!nutritionIntelligenceState?.observations?.length ? (
                  <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                    No observations generated yet.
                  </div>
                ) : null}
              </div>
            </div>
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Consultant Actions</p>
              <div className="mt-3 space-y-2">
                {(nutritionIntelligenceState?.consultantActions || []).slice(0, 5).map((item, index) => (
                  <div key={`${item}-${index}`} className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                    {item}
                  </div>
                ))}
                {!nutritionIntelligenceState?.consultantActions?.length ? (
                  <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                    No consultant actions available yet.
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </Surface>
      </div>

      {dietPlanState?.content && dietPlanContentDraft ? (
        <div className="space-y-4">
          <Surface className="p-5" animated>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Diet Plan Lifecycle</p>
                <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                  Version {dietPlanState.currentVersionNumber} • Template {dietPlanState.templateVersion}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusChip status={lifecycleTone(dietPlanState.currentLifecycle)}>{workflowLabelFromLifecycle(dietPlanState.currentLifecycle)}</StatusChip>
                <span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">
                  Workflow: {formatDisplayValue(planWorkflow?.stageLabel)}
                </span>
              </div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <DetailField label="Prepared by" value={formatDisplayValue(dietPlanContentDraft.nutritionSnapshot?.preparedBy)} />
              <DetailField label="Programme" value={formatDisplayValue(dietPlanContentDraft.nutritionSnapshot?.programmeName)} />
              <DetailField label="Calories" value={dietPlanContentDraft.dailyTargets?.calories != null ? `${dietPlanContentDraft.dailyTargets.calories} kcal` : 'Not available'} />
              <DetailField label="Hydration" value={dietPlanContentDraft.dailyTargets?.hydration != null ? `${dietPlanContentDraft.dailyTargets.hydration} L` : 'Not available'} />
            </div>
          </Surface>

          <Surface className="p-5" animated>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Meal Plan Editor</p>
            <div className="mt-4 space-y-4">
              {mealPlanSectionEntries.map(([key, label]) => {
                const section = dietPlanContentDraft.mealPlan?.[key];
                return (
                  <div key={key} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
                    <div className="grid gap-3 lg:grid-cols-[0.78fr_1.22fr]">
                      <div className="space-y-3">
                        <DetailField label={`${label} window`} value={section?.window || 'Not set'} />
                        <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-1)] px-4 py-3">
                          <p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Focus</p>
                          <textarea
                            value={section?.focus || ''}
                            onChange={(event) => handleDietFieldChange(['mealPlan', key, 'focus'], event.target.value)}
                            className="mt-2 min-h-[76px] w-full resize-y rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-white px-3 py-2 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                          />
                        </div>
                      </div>
                      <div className="space-y-3">
                        {(section?.options || []).map((option, optionIndex) => (
                          <div key={`${key}-option-${optionIndex}`} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-1)] p-3">
                            <div className="grid gap-3 md:grid-cols-2">
                              <label className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">
                                Meal
                                <input
                                  value={option.meal || ''}
                                  onChange={(event) => handleDietFieldChange(['mealPlan', key, 'options', optionIndex, 'meal'], event.target.value)}
                                  className="mt-2 w-full rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-white px-3 py-2 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                                />
                              </label>
                              <label className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">
                                Portion
                                <input
                                  value={option.portion || ''}
                                  onChange={(event) => handleDietFieldChange(['mealPlan', key, 'options', optionIndex, 'portion'], event.target.value)}
                                  className="mt-2 w-full rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-white px-3 py-2 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                                />
                              </label>
                              <label className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">
                                Calories
                                <input
                                  value={option.approxKcal ?? ''}
                                  onChange={(event) => handleDietFieldChange(['mealPlan', key, 'options', optionIndex, 'approxKcal'], event.target.value === '' ? null : Number(event.target.value))}
                                  className="mt-2 w-full rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-white px-3 py-2 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                                />
                              </label>
                              <label className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">
                                Protein
                                <input
                                  value={option.proteinGrams ?? ''}
                                  onChange={(event) => handleDietFieldChange(['mealPlan', key, 'options', optionIndex, 'proteinGrams'], event.target.value === '' ? null : Number(event.target.value))}
                                  className="mt-2 w-full rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-white px-3 py-2 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                                />
                              </label>
                            </div>
                            <label className="mt-3 block text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">
                              Prep note
                              <textarea
                                value={option.prepNote || ''}
                                onChange={(event) => handleDietFieldChange(['mealPlan', key, 'options', optionIndex, 'prepNote'], event.target.value)}
                                className="mt-2 min-h-[72px] w-full resize-y rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-white px-3 py-2 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                              />
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Surface>
        </div>
      ) : (
        <Surface className="p-5" animated>
          <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
            No active meal plan assigned yet. Use “Prepare Diet Chart” to generate a consultant-assisted draft from the live Fiteatsy nutrition intelligence.
          </div>
        </Surface>
      )}
    </div>
    )
  );

  const renderMedication = () => (
    <div className="space-y-4">
      <Surface className="p-5" animated>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Medication Monitoring</p>
            <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
              Read-only medication adherence from the client&apos;s Fiteatsy medication tracker. Consultants can review, but cannot edit medicine data.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => void refreshMedications()}
              disabled={medicationLoading}
              className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-neutral-foreground-1)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {medicationLoading ? 'Refreshing...' : 'Refresh'}
            </button>
            {typeof onCreateMedicationFollowUp === 'function' ? (
              <button
                onClick={() => onCreateMedicationFollowUp(summaryClient?.id, 'Review medication adherence')}
                className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)]"
              >
                Create follow-up
              </button>
            ) : null}
          </div>
        </div>
        {medicationError ? (
          <div className="mt-4 rounded-[16px] bg-[var(--fluent-color-status-danger-background)] px-4 py-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
            <p className="font-semibold">Unable to load medication monitoring.</p>
            <p className="mt-1">
              {medicationError?.status === 403
                ? 'Medication monitoring is restricted to assigned consultants.'
                : medicationError?.message || 'Try again after the backend connection recovers.'}
            </p>
          </div>
        ) : null}
        {medicationLoading && !medicationMonitoring ? (
          <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {Array.from({ length: 6 }).map((_, index) => <LoadingSkeleton key={index} className="h-20 w-full" />)}
          </div>
        ) : medicationSummary ? (
          <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            <DetailField label="Active" value={`${medicationSummary.activeMedicationCount || 0}`} />
            <DetailField label="Today" value={formatMedicationAdherence(medicationSummary.today)} />
            <DetailField label="7 days" value={formatMedicationAdherencePercent(medicationSummary.sevenDay)} />
            <DetailField label="30 days" value={formatMedicationAdherencePercent(medicationSummary.thirtyDay)} />
            <DetailField label="Missed / skipped" value={`${medicationSummary.sevenDay?.missed || 0} / ${medicationSummary.sevenDay?.skipped || 0}`} />
            <DetailField label="Next dose" value={formatNextMedicationDose(medicationSummary.nextDose)} />
          </div>
        ) : (
          <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
            No medication data has synced for this client yet.
          </div>
        )}
      </Surface>

      <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Today&apos;s Medication</p>
          <div className="mt-4 space-y-3">
            {todaysMedicationDoses.length ? todaysMedicationDoses.map((dose) => (
              <div key={`${dose.medicationId}-${dose.scheduledFor}`} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{dose.scheduledTime || 'Time pending'} · {dose.medicationName}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                      {[dose.dosage, dose.type, dose.foodRelationLabel].filter(Boolean).join(' · ') || 'Dose details not available'}
                    </p>
                    {dose.actionedAt ? (
                      <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Actioned {formatMedicationDateTime(dose.actionedAt)}</p>
                    ) : null}
                    {dose.snoozedUntil ? (
                      <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Snoozed until {formatMedicationDateTime(dose.snoozedUntil)}</p>
                    ) : null}
                    {dose.skipReason ? (
                      <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Skip reason: {dose.skipReason}</p>
                    ) : null}
                  </div>
                  <span className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-medium ${medicationStatusTone(dose.status)}`}>
                    {formatMedicationStatus(dose.status)}
                  </span>
                </div>
              </div>
            )) : (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No medication doses are scheduled for today.
              </div>
            )}
          </div>
        </Surface>

        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Active Medications</p>
          <div className="mt-4 space-y-3">
            {activeMedications.length ? activeMedications.map((medication) => (
              <button
                key={medication.id}
                onClick={() => setSelectedMedicationId(medication.id)}
                className={`w-full rounded-[18px] border p-4 text-left transition ${
                  selectedMedication?.id === medication.id
                    ? 'border-[var(--fluent-color-brand-stroke-1)] bg-[rgba(99,124,239,0.12)]'
                    : 'border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] hover:border-[var(--fluent-color-neutral-stroke-2)]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{medication.name}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{[medication.dosage, medication.type].filter(Boolean).join(' · ') || 'Dose details not available'}</p>
                    <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                      {formatMedicationFrequency(medication.frequency)} · {(medication.scheduledTimes || []).map((slot) => slot.displayTime).join(', ') || 'No schedule'}
                    </p>
                  </div>
                  <StatusChip status={medication.reminderEnabled ? 'stable' : 'pending'}>
                    Reminder {medication.reminderEnabled ? 'on' : 'off'}
                  </StatusChip>
                </div>
              </button>
            )) : (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No active medications are synced for this client.
              </div>
            )}
          </div>
        </Surface>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Medication Detail</p>
          {selectedMedication ? (
            <div className="mt-4 space-y-4">
              <div>
                <p className="text-[24px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">{selectedMedication.name}</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{[selectedMedication.dosage, selectedMedication.type].filter(Boolean).join(' · ')}</p>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <DetailField label="Frequency" value={formatMedicationFrequency(selectedMedication.frequency)} />
                <DetailField label="Scheduled times" value={(selectedMedication.scheduledTimes || []).map((slot) => slot.displayTime).join(', ') || 'Not available'} />
                <DetailField label="Food relation" value={(selectedMedication.scheduledTimes || []).map((slot) => slot.mealRelationLabel).filter(Boolean).join(', ') || 'Not available'} />
                <DetailField label="Duration" value={formatMedicationDuration(selectedMedication.duration)} />
                <DetailField label="Reminder" value={selectedMedication.reminderEnabled ? 'Enabled' : 'Disabled'} />
                <DetailField label="7-day adherence" value={formatMedicationAdherencePercent(selectedMedication.recentAdherence)} />
              </div>
              <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                Consultant access is read-only. Medication changes must be made by the client in Fiteatsy.
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              Select an active medication to view read-only details.
            </div>
          )}
        </Surface>

        <Surface className="p-5" animated>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Dose History</p>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Latest synced dose events across the client&apos;s medication tracker.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusChip status="stable">7D {formatMedicationAdherencePercent(medicationSummary?.sevenDay)}</StatusChip>
              <StatusChip status="stable">30D {formatMedicationAdherencePercent(medicationSummary?.thirtyDay)}</StatusChip>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {medicationHistory.length ? medicationHistory.slice(0, 24).map((event) => (
              <div key={event.id || `${event.medicationId}-${event.scheduledFor}`} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{event.scheduledTime || formatMedicationDateTime(event.scheduledFor)} · {event.medicationName}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                      Scheduled {formatMedicationDateTime(event.scheduledFor)}{event.dosage ? ` · ${event.dosage}` : ''}
                    </p>
                    {event.actionedAt ? (
                      <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Actioned {formatMedicationDateTime(event.actionedAt)}</p>
                    ) : null}
                    {event.skipReason ? (
                      <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Skip reason: {event.skipReason}</p>
                    ) : null}
                  </div>
                  <span className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-medium ${medicationStatusTone(event.status)}`}>
                    {formatMedicationStatus(event.status)}
                  </span>
                </div>
              </div>
            )) : (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No medication dose history has synced yet.
              </div>
            )}
          </div>
        </Surface>
      </div>
    </div>
  );

  const renderStress = () => {
    const latest = stressAssessment?.latest || null;
    const previous = stressAssessment?.previous || null;
    const history = Array.isArray(stressAssessment?.history) ? stressAssessment.history : [];
    const change = stressAssessment?.change;
    const changeLabel = change == null ? (previous ? 'No change' : 'First assessment') : `${change < 0 ? '↓' : change > 0 ? '↑' : ''} ${Math.abs(change)} pts`.trim();

    return (
      <div className="space-y-4">
        <Surface className="p-5" animated>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Perceived Stress</p>
              <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">Completed Stress Test results from the client record. This view is non-diagnostic and read-only.</p>
            </div>
            {typeof onCreateFollowUp === 'function' ? (
              <button type="button" onClick={() => onCreateFollowUp(summaryClient?.id, latest ? `Review latest perceived-stress assessment (${latest.rawScore}/${latest.maxScore})` : 'Review perceived-stress assessment')} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)]">
                Create follow-up
              </button>
            ) : null}
          </div>
          {latest ? (
            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <DetailField label="Latest" value={`${latest.rawScore} / ${latest.maxScore}`} />
              <DetailField label="Interpretation" value={latest.interpretationLabel} />
              <DetailField label="Last assessed" value={formatDateLabel(latest.completedAtISO)} />
              <DetailField label="Change" value={changeLabel} />
            </div>
          ) : (
            <div className="mt-5 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No completed perceived-stress assessment yet.</div>
          )}
        </Surface>
        <Surface className="p-5" animated>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Trend</p>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Periodic completed assessments only. No values are interpolated.</p>
            </div>
            <TrendingUp size={18} className="text-[var(--fluent-color-brand-foreground-link)]" />
          </div>
          {history.length > 1 ? (
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {history.slice().reverse().map((item) => (
                <div key={item.id} className="rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-2xl font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.rawScore}/{item.maxScore}</span>
                    <span className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{formatDateLabel(item.completedAtISO)}</span>
                  </div>
                  <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.interpretationLabel}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4 rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Insufficient history for a trend. A second completed assessment will appear here when available.</div>
          )}
        </Surface>
        <Surface className="p-5" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Assessment History</p>
          <div className="mt-4 divide-y divide-[var(--fluent-color-neutral-stroke-1)]">
            {history.length ? history.map((item) => (
              <div key={item.id} className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{formatDateLabel(item.completedAtISO)}</p>
                  <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.interpretationLabel}</p>
                </div>
                <div className="text-left sm:text-right">
                  <p className="text-base font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.rawScore} / {item.maxScore}</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{item.instrumentVersion} · {item.scoringVersion}</p>
                </div>
              </div>
            )) : <p className="py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No completed assessment history yet.</p>}
          </div>
        </Surface>
      </div>
    );
  };

  const renderActivity = () => (
    <Surface className="p-5" animated>
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Activity</p>
      {wearableSummary?.connected ? (
        <div className="mt-4 space-y-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <DetailField label="Connected sources" value={formatDisplayValue(wearableSummary?.dataSources)} />
            <DetailField label="Records synced" value={wearableSummary?.recordsCount != null ? `${wearableSummary.recordsCount}` : 'Not available'} />
            <DetailField label="Last sync" value={formatDateLabel(wearableSummary?.lastSyncedAt)} />
            <DetailField label="Latest metric" value={wearableSummary?.latestMetrics?.[0] ? `${wearableSummary.latestMetrics[0].metricType} • ${wearableSummary.latestMetrics[0].latestValue} ${wearableSummary.latestMetrics[0].unit}` : 'Not available'} />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {(wearableSummary?.latestMetrics || []).slice(0, 6).map((metric) => (
              <div key={`${metric.metricType}-${metric.measuredAt}`} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{metric.metricType}</p>
                <p className="mt-2 text-[22px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">{`${metric.latestValue} ${metric.unit}`.trim()}</p>
                <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{metric.sourceProvider} • {formatDateLabel(metric.measuredAt)}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
          No wearable summary is available yet. The client can still continue using manual health profile, reports, and onboarding flows.
        </div>
      )}
    </Surface>
  );

  const renderTimeline = () => (
    <Surface className="p-5" animated>
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Timeline</p>
      <div className="mt-4 space-y-3">
        {timeline.length ? timeline.map((event) => (
          <div key={event.id || `${event.type}-${event.timestamp || 'unknown'}`} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3">
            <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{event.title || event.type}</p>
            <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{event.detail || 'Client activity synchronized.'}</p>
            <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
              {formatDateLabel(event.timestamp || event.createdAt)}{event.source ? ` • ${String(event.source).replace(/_/g, ' ')}` : ''}
            </p>
          </div>
        )) : (
          <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
            No synced client timeline events yet.
          </div>
        )}
      </div>
    </Surface>
  );

  const tabContent = {
    Overview: renderOverview,
    'Health Profile': renderHealthProfile,
    Lifestyle: renderLifestyle,
    Reports: renderReports,
    Biomarkers: renderBiomarkers,
    Medication: renderMedication,
    Stress: renderStress,
    'Nutrition Plan': renderNutrition,
    Activity: renderActivity,
    Timeline: renderTimeline,
  }[activeWorkspaceTab] || renderOverview;

  return (
    <AnimatePresence>
      {isOpen ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[72] bg-[rgba(15,23,42,0.18)] backdrop-blur-[2px]"
          onClick={onClose}
        >
          <motion.aside
            initial={{ x: 32, opacity: 0.98 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 24, opacity: 0.98 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            onClick={(event) => event.stopPropagation()}
            className="absolute right-0 top-0 h-full w-full max-w-[920px] overflow-hidden bg-[var(--fluent-color-neutral-background-canvas)] shadow-[-18px_0_42px_rgba(15,23,42,0.16)]"
          >
            <div className="flex h-full flex-col">
              <div className="border-b border-[var(--fluent-color-neutral-stroke-1)] bg-[rgba(255,255,255,0.94)] px-5 py-4 backdrop-blur">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Client Command Center</p>
                    <h2 className="mt-2 text-[28px] font-semibold tracking-[-0.03em] text-[var(--fluent-color-neutral-foreground-1)]">
                      {client?.name || summaryClient?.name || 'Client'}
                    </h2>
                    <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                      {goalLabel === 'Not assigned' ? 'Recovery Program not assigned' : `${goalLabel} Recovery Program`}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-[var(--fluent-color-neutral-foreground-2)]">
                      <span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5">
                        Status: {healthStatus.label}
                      </span>
                      <span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5">
                        Profile completeness {profileStrength != null ? `${profileStrength}%` : 'pending'}
                      </span>
                      <span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5">
                        Last synced: {formatDateLabel(lastSynced)}
                      </span>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {canManageNutrition ? (
                      <button
                        onClick={handleGenerateDietPlan}
                        disabled={nutritionActionLoading}
                        className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {nutritionActionLoading && !dietPlanState ? 'Preparing...' : 'Generate Diet Plan'}
                      </button>
                    ) : null}
                    <button className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-neutral-foreground-1)]">
                      Message Client
                    </button>
                    <button
                      onClick={onClose}
                      className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-2 text-[var(--fluent-color-neutral-foreground-2)] transition hover:bg-[var(--fluent-color-neutral-background-2)]"
                      aria-label="Close client profile"
                    >
                      <X size={18} />
                    </button>
                  </div>
                </div>
                <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
                  {groupedWorkspaceTabs.map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveWorkspaceTab(tab.key)}
                      className={`whitespace-nowrap rounded-full px-3 py-2 text-xs font-semibold transition ${
                        activeWorkspaceTab === tab.key
                          ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]'
                          : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-2)] hover:text-[var(--fluent-color-neutral-foreground-1)]'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex-1 overflow-y-auto px-5 py-5">
                {loading ? (
                  <div className="space-y-4">
                    <LoadingSkeleton className="h-28 w-full" />
                    <div className="grid gap-4 md:grid-cols-2">
                      <LoadingSkeleton className="h-36 w-full" />
                      <LoadingSkeleton className="h-36 w-full" />
                    </div>
                    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                      {Array.from({ length: 6 }).map((_, index) => <LoadingSkeleton key={index} className="h-32 w-full" />)}
                    </div>
                    <LoadingSkeleton className="h-56 w-full" />
                  </div>
                ) : message ? (
                  <Surface className="border-[var(--fluent-color-status-danger-foreground)] bg-[var(--fluent-color-status-danger-background)] p-5">
                    <p className="text-sm font-semibold text-[var(--fluent-color-status-danger-foreground)]">{message}</p>
                  </Surface>
                ) : (
                  tabContent()
                )}
              </div>
            </div>
          </motion.aside>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

function ProgressTrack({ value, tone = '#1E88E5' }) {
  return (
    <div className="h-2 rounded-full bg-[var(--fluent-color-neutral-background-3)]">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="h-2 rounded-full"
        style={{ backgroundColor: tone }}
      />
    </div>
  );
}

function SparklineBars({ values, color = '#1E88E5' }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const width = 132;
  const height = 36;
  const padding = 4;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const labels = values.map((_, index) => (index === values.length - 1 ? 'Today' : `Day ${index + 1}`));
  const points = values.map((value, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(values.length - 1, 1);
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return [x, y, value, labels[index]];
  });
  const linePath = points.map(([x, y]) => `${x},${y}`).join(' ');
  const areaPath = `${padding},${height - padding} ${linePath} ${width - padding},${height - padding}`;
  const lastPoint = points[points.length - 1];
  const hoveredPoint = hoveredIndex !== null ? points[hoveredIndex] : null;

  return (
    <div className="relative">
      {hoveredPoint ? (
        <div className="pointer-events-none absolute -top-11 left-1/2 z-10 -translate-x-1/2 rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[rgba(255,255,255,0.96)] px-2.5 py-1.5 text-center shadow-[0_8px_18px_rgba(15,23,42,0.10)]">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{hoveredPoint[3]}</p>
          <p className="mt-0.5 text-xs font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{hoveredPoint[2]}</p>
        </div>
      ) : null}
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-10 w-full"
        role="img"
        aria-label="Trend sparkline"
        preserveAspectRatio="none"
      >
        <polyline
          points={areaPath}
          fill={color}
          fillOpacity="0.1"
          stroke="none"
        />
        <polyline
          points={linePath}
          fill="none"
          stroke={color}
          strokeWidth="2.25"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {points.map(([x, y, value, label], index) => {
          const isHovered = hoveredIndex === index;
          return (
            <g key={`${label}-${value}`}>
              <title>{`${label}: ${value}`}</title>
              <circle
                cx={x}
                cy={y}
                r={isHovered ? 3.75 : index === values.length - 1 ? 3 : 2.4}
                fill={isHovered ? color : '#ffffff'}
                stroke={color}
                strokeWidth={isHovered ? 2.5 : 1.8}
              />
              <circle
                cx={x}
                cy={y}
                r="8"
                fill="transparent"
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
              />
            </g>
          );
        })}
        {lastPoint && hoveredIndex === null ? (
          <circle cx={lastPoint[0]} cy={lastPoint[1]} r="3.2" fill={color} />
        ) : null}
      </svg>
    </div>
  );
}

function TopAppBar({ roleName, timeframe, setTimeframe, search, setSearch, onSearchOpen, user, logout, onQuickAction, onResumeWorkspace, resumeLabel }) {
  return (
    <div className="sticky top-0 z-40 border-b border-[var(--fluent-color-neutral-stroke-1)] bg-[rgba(255,255,255,0.94)] backdrop-blur">
      <div className="mx-auto flex max-w-[1480px] items-center gap-3 px-4 py-3 md:px-6 lg:px-8">
        <div className="min-w-0 shrink-0">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Nuetra + Fiteatsy</p>
          <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{roleName}</p>
        </div>
        <div
          onClick={onSearchOpen}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') onSearchOpen();
          }}
          className="mx-auto flex min-w-0 max-w-[640px] flex-1 items-center gap-3 rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-left shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)]"
        >
          <Search className="h-4 w-4 text-[var(--fluent-color-neutral-foreground-3)]" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            onFocus={onSearchOpen}
            placeholder="Search clients, biomarkers, reports, plans..."
            className="w-full bg-transparent text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none placeholder:text-[var(--fluent-color-neutral-foreground-3)]"
          />
          <span className="hidden items-center gap-1 rounded-full bg-[var(--fluent-color-neutral-background-inset)] px-2 py-1 text-[11px] text-[var(--fluent-color-neutral-foreground-3)] md:inline-flex">
            <Command className="h-3 w-3" />K
          </span>
        </div>
        <div className="flex items-center gap-2">
          {resumeLabel && onResumeWorkspace ? (
            <motion.button {...hoverLift} onClick={onResumeWorkspace} className="hidden rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)] shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)] lg:inline-flex">
              Resume workspace - {resumeLabel}
            </motion.button>
          ) : null}
          <motion.button {...hoverLift} onClick={onQuickAction} className="hidden rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)] shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)] md:inline-flex">
            Quick AI actions
          </motion.button>
          <select
            value={timeframe}
            onChange={(event) => setTimeframe(event.target.value)}
            className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-sm text-[var(--fluent-color-neutral-foreground-1)] shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)] outline-none"
          >
            {timeframeOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <motion.button {...hoverLift} className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-2.5 text-[var(--fluent-color-neutral-foreground-2)] shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)]"><Bell className="h-4 w-4" /></motion.button>
          <motion.button {...hoverLift} className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-2.5 text-[var(--fluent-color-neutral-foreground-2)] shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)]"><Settings className="h-4 w-4" /></motion.button>
          <motion.button {...hoverLift} onClick={logout} className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)] shadow-[0_2px_8px_var(--fluent-shadow-ambient),0_12px_28px_var(--fluent-shadow-key)]">
            {user?.avatar || 'NU'}
          </motion.button>
        </div>
      </div>
    </div>
  );
}

function OperationalTopNav({ items, active, onChange, brandView, setBrandView, roleKind }) {
  return (
    <div className="sticky top-[72px] z-30 border-b border-[var(--fluent-color-neutral-stroke-1)] bg-[rgba(250,250,250,0.94)] backdrop-blur">
      <div className="mx-auto flex max-w-[1480px] flex-col gap-3 px-4 py-3 md:px-6 lg:px-8 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex rounded-full bg-[var(--fluent-color-neutral-background-2)] p-1">
            {['All Brands', 'Nuetra', 'Fiteatsy'].map((brand) => (
              <button
                key={brand}
                onClick={() => setBrandView(brand)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                  brandView === brand ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]' : 'text-[var(--fluent-color-neutral-foreground-2)]'
                }`}
              >
                {brand}
              </button>
            ))}
          </div>
          <span className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-inset)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">
            {roleKind === 'consultant' ? 'Intervention Mode' : roleKind === 'mentor' ? 'Support Mode' : brandView === 'Fiteatsy' ? 'User Intelligence Mode' : 'Organization Mode'}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1 rounded-full bg-[var(--fluent-color-neutral-background-2)] p-1">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => onChange(item.id)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                active === item.id ? 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-1)] shadow-[inset_0_0_0_1px_var(--fluent-color-neutral-stroke-1)]' : 'text-[var(--fluent-color-neutral-foreground-2)] hover:text-[var(--fluent-color-neutral-foreground-1)]'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Sidebar({ items, active, onChange, groups }) {
  const sections = groups?.length
    ? groups.map((group) => ({
        ...group,
        items: group.items.map((id) => items.find((item) => item.id === id)).filter(Boolean),
      }))
    : [{ label: null, items }];

  return (
    <div className="sticky top-[76px] self-start">
      <Surface className="p-3">
        <nav className="space-y-4">
          {sections.map((section, index) => (
            <div key={section.label || `section-${index}`}>
              {section.label ? <p className="px-3 pb-2 text-[11px] font-medium uppercase tracking-[0.16em] text-[var(--fluent-color-neutral-foreground-3)]">{section.label}</p> : null}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = item.id === active;
                  return (
                    <motion.button
                      key={item.id}
                      onClick={() => onChange(item.id)}
                      {...hoverLift}
                      className={`flex w-full items-center gap-3 rounded-[14px] px-3 py-2.5 text-left text-sm font-medium transition ${
                        isActive ? 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)]' : 'text-[var(--fluent-color-neutral-foreground-2)] hover:bg-[#F6F8FB] hover:text-[var(--fluent-color-neutral-foreground-1)]'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                    </motion.button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </Surface>
    </div>
  );
}

function CompactPageHeader({ title, subtitle, actions }) {
  return (
    <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h2 className="text-[20px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">{title}</h2>
        {subtitle ? <p className="mt-0.5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

function SearchOverlay({ isOpen, onClose, search, setSearch, results, onResultSelect }) {
  return (
    <AnimatePresence>
      {isOpen ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[70] bg-[rgba(36,36,36,0.12)] px-4 py-10"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            onClick={(event) => event.stopPropagation()}
            className="mx-auto flex max-h-[78vh] max-w-[920px] flex-col overflow-hidden rounded-[28px] bg-[var(--fluent-color-neutral-background-1)] shadow-[0_8px_24px_var(--fluent-shadow-ambient),0_24px_56px_var(--fluent-shadow-key)]"
          >
            <div className="flex items-center gap-3 border-b border-[var(--fluent-color-neutral-stroke-1)] px-5 py-4">
              <Search className="h-4 w-4 text-[var(--fluent-color-neutral-foreground-3)]" />
              <input
                autoFocus
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search clients, biomarkers, reports, notes, interventions, tasks..."
                className="w-full bg-transparent text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none placeholder:text-[var(--fluent-color-neutral-foreground-3)]"
              />
              <button onClick={onClose} className="rounded-full bg-[var(--fluent-color-neutral-background-3)] p-2 text-[var(--fluent-color-neutral-foreground-2)]">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid min-h-0 flex-1 gap-0 overflow-hidden md:grid-cols-[0.9fr_1.1fr]">
              <div className="border-r border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-[var(--fluent-color-neutral-foreground-3)]">Quick actions</p>
                <div className="mt-3 space-y-2">
                  {[
                    ['Open Workspace', 'client'],
                    ['Generate AI Draft', 'plan'],
                    ['Upload Report', 'report'],
                    ['Add Note', 'note'],
                    ['Start Follow-Up', 'task'],
                    ['Schedule Session', 'task'],
                  ].map(([label, kind]) => (
                    <button
                      key={label}
                      onClick={() => {
                        const target = results.find((group) => group.items.length)?.items[0];
                        if (target) onResultSelect(target, kind === 'plan' ? 'Diet Plan' : kind === 'report' ? 'Reports' : kind === 'note' ? 'Notes' : 'Overview');
                      }}
                      className="flex w-full items-center justify-between rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3 text-left text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]"
                    >
                      {label}
                      <ChevronRight className="h-4 w-4 text-[var(--fluent-color-neutral-foreground-3)]" />
                    </button>
                  ))}
                </div>
              </div>
              <div className="min-h-0 overflow-y-auto px-4 py-4">
                {results.map((group) => (
                  <div key={group.label} className="mb-5 last:mb-0">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-xs font-medium uppercase tracking-[0.16em] text-[var(--fluent-color-neutral-foreground-3)]">{group.label}</p>
                      <span className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{group.items.length}</span>
                    </div>
                    <div className="space-y-2">
                      {group.items.length ? group.items.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => onResultSelect(item, item.targetTab)}
                          className="flex w-full items-start justify-between rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left transition hover:bg-[#f7f9fc]"
                        >
                          <div>
                            <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                            <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.subtitle}</p>
                          </div>
                          <StatusChip status={item.status || 'medium'}>{item.meta}</StatusChip>
                        </button>
                      )) : (
                        <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No matching {group.label.toLowerCase()}.</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

function ConsultantHome({
  briefingMeta,
  dailySummary,
  priorityQueue,
  clusters,
  healthMovement,
  alerts,
  recommendedActions,
  trendSignals,
  organizationSignals,
  uploadPipeline,
  reviewPipeline,
  onClientOpen,
}) {
  const [intelligenceTab, setIntelligenceTab] = useState('Trends');
  const [densityMode, setDensityMode] = useState('compact');
  const [operationalMode, setOperationalMode] = useState('Operations Mode');
  const [selectedQueueClientId, setSelectedQueueClientId] = useState(null);
  const compactMode = densityMode === 'compact';
  const scopedQueue = useMemo(() => {
    if (operationalMode === 'Focus Mode') {
      return priorityQueue.filter((item) => item.risk === 'critical' || item.risk === 'high').slice(0, 7);
    }
    if (operationalMode === 'Review Mode') {
      return priorityQueue.filter((item) => item.action.toLowerCase().includes('review') || item.action.toLowerCase().includes('publish')).slice(0, 7);
    }
    return priorityQueue.slice(0, 7);
  }, [operationalMode, priorityQueue]);
  const topActions = useMemo(() => {
    if (operationalMode === 'Focus Mode') return recommendedActions.filter((item) => item.detail.toLowerCase().includes('follow') || item.detail.toLowerCase().includes('support')).slice(0, 5);
    if (operationalMode === 'Review Mode') return recommendedActions.filter((item) => item.detail.toLowerCase().includes('review') || item.detail.toLowerCase().includes('approval')).slice(0, 5);
    return recommendedActions.slice(0, 5);
  }, [operationalMode, recommendedActions]);
  const railAlerts = alerts.slice(0, 3);
  const railReviews = reviewPipeline.slice(0, 3);
  const railEscalations = priorityQueue.filter((item) => item.risk === 'critical' || item.risk === 'high').slice(0, 3);
  const lowConfidenceCases = priorityQueue.filter((item) => item.confidence < 70).slice(0, 3);
  const internalTabClass = compactMode ? 'max-h-[520px] overflow-y-auto' : 'max-h-[600px] overflow-y-auto';
  const pulseItems = [
    { label: 'Worsening', value: clusters[0]?.count || 0, delta: '+4 WoW', status: 'critical', spark: [8, 10, 11, 12, 13, 14, clusters[0]?.count || 14] },
    { label: 'Adherence Drops', value: clusters[2]?.count || 0, delta: '+2 WoW', status: 'high', spark: [4, 5, 5, 6, 7, 7, clusters[2]?.count || 7] },
    { label: 'Pending Reviews', value: reviewPipeline.length, delta: '-3 WoW', status: 'pending', spark: [9, 8, 7, 7, 6, 5, reviewPipeline.length] },
    { label: 'Improving', value: Number(healthMovement.items[0]?.value || 0), delta: '+6 WoW', status: 'improving', spark: healthMovement.items[0]?.spark || [16, 19, 24, 28, 35, 39, 42] },
    { label: 'Inactive >14 days', value: alerts.filter((alert) => alert.alert.toLowerCase().includes('requires escalation')).length || 4, delta: '+1 WoW', status: 'medium', spark: [2, 2, 3, 3, 4, 4, alerts.filter((alert) => alert.alert.toLowerCase().includes('requires escalation')).length || 4] },
  ];
  const pipelines = [
    ...uploadPipeline.map((item) => ({
      id: `upload-${item.id}`,
      client: item.employee,
      stage: item.state.replace('...', ''),
      progress: `${item.progress}%`,
      reviewer: 'AI pipeline',
      eta: item.progress === 100 ? 'Ready now' : item.progress > 70 ? '18 min' : '42 min',
      onOpen: () => onClientOpen(clientsByName(priorityQueue, item.employee)),
    })),
    ...reviewPipeline.map((item) => ({
      id: `review-${item.employeeName}`,
      client: item.employeeName,
      stage: item.stateLabel,
      progress: item.state === 'senior_review' ? '88%' : item.state === 'consultant_modified' ? '72%' : '61%',
      reviewer: item.state === 'senior_review' ? 'Dr. Rohan Mehta' : 'Dr. Aditi Kulkarni',
      eta: item.state === 'senior_review' ? 'Today' : '4 hrs',
      onOpen: () => onClientOpen(clientsByName(priorityQueue, item.employeeName)),
    })),
  ].slice(0, 10);

  function clientsByName(queue, name) {
    return queue.find((item) => item.name === name)?.clientId;
  }

  function openCluster(cluster) {
    const match = priorityQueue.find((item) => {
      if (cluster.title.includes('HbA1c')) return item.title.toLowerCase().includes('hba1c');
      if (cluster.title.includes('Burnout')) return item.title.toLowerCase().includes('burnout') || item.why.toLowerCase().includes('sleep inconsistency');
      if (cluster.title.includes('Adherence')) return item.why.toLowerCase().includes('adherence');
      if (cluster.title.includes('Sleep')) return item.why.toLowerCase().includes('sleep');
      return false;
    });
    if (match?.clientId) onClientOpen(match.clientId);
  }

  useEffect(() => {
    if (!scopedQueue.length) return;
    if (!selectedQueueClientId || !scopedQueue.some((item) => item.clientId === selectedQueueClientId)) {
      setSelectedQueueClientId(scopedQueue[0].clientId);
    }
  }, [scopedQueue, selectedQueueClientId]);

  const selectedQueueItem = scopedQueue.find((item) => item.clientId === selectedQueueClientId) || scopedQueue[0];

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="space-y-4">
        <Surface className={`${compactMode ? 'p-3' : 'p-4'}`} animated>
          <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Consultant command center</p>
              <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{briefingMeta}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {['Focus Mode', 'Operations Mode', 'Review Mode'].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setOperationalMode(mode)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${operationalMode === mode ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]' : 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-2)]'}`}
                >
                  {mode}
                </button>
              ))}
              {['compact', 'comfortable'].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setDensityMode(mode)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${densityMode === mode ? 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)]' : 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-2)]'}`}
                >
                  {formatStatusLabel(mode)}
                </button>
              ))}
            </div>
          </div>
          <div className="mt-3 grid gap-2 xl:grid-cols-5">
            {pulseItems.map((item) => (
              <motion.button key={item.label} {...hoverLift} className="rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-left">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{item.label}</p>
                    <p className="mt-1 text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.value}</p>
                    <p className="mt-1 text-[11px] text-[var(--fluent-color-neutral-foreground-2)]">{item.delta}</p>
                  </div>
                  <StatusChip status={item.status}>{item.delta}</StatusChip>
                </div>
                <div className="mt-2">
                  <SparklineBars values={item.spark} color={item.status === 'critical' ? '#E53935' : item.status === 'improving' ? '#43A047' : item.status === 'pending' ? '#5C6BC0' : '#FB8C00'} />
                </div>
              </motion.button>
            ))}
          </div>
        </Surface>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(280px,0.7fr)]">
          <Surface className={`${compactMode ? 'p-3' : 'p-4'} max-h-[720px] min-h-[650px] overflow-hidden`} animated>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Exception queue</p>
                <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{operationalMode} • signal-first clinical review</p>
              </div>
              <span className="text-xs text-[var(--fluent-color-neutral-foreground-2)]">{scopedQueue.length} active cases</span>
            </div>
            <div className="mt-3 overflow-auto">
              <div className="min-w-[1060px]">
                <div className="grid grid-cols-[1.5fr_0.7fr_1.1fr_1fr_0.7fr_0.7fr_0.9fr_0.9fr_1.2fr] gap-2 border-b border-[var(--fluent-color-neutral-stroke-1)] px-3 py-2 text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">
                  <div>Client</div>
                  <div>Risk</div>
                  <div>Drift</div>
                  <div>Cause</div>
                  <div>Adherence</div>
                  <div>Confidence</div>
                  <div>Last activity</div>
                  <div>Assigned</div>
                  <div>Next action</div>
                </div>
                <div className="max-h-[340px] space-y-2 overflow-y-auto pr-1 pt-2">
                  {scopedQueue.map((item) => (
                    <motion.button
                      key={item.clientId}
                      layout
                      onClick={() => setSelectedQueueClientId(item.clientId)}
                      className={`w-full rounded-[14px] border px-3 py-3 text-left transition ${
                        selectedQueueClientId === item.clientId ? 'border-[#C6DAFC] bg-[#EEF4FF]' : 'border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] hover:bg-[#F2F6FC]'
                      }`}
                    >
                      <div className="grid grid-cols-[1.5fr_0.7fr_1.1fr_1fr_0.7fr_0.7fr_0.9fr_0.9fr_1.2fr] gap-2 text-sm">
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {item.drivers.slice(0, 2).map((driver) => (
                              <span key={driver} className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-2 py-1 text-[11px] text-[var(--fluent-color-neutral-foreground-2)]">
                                {driver}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div><StatusChip status={item.risk}>{item.risk}</StatusChip></div>
                        <div className="text-[var(--fluent-color-neutral-foreground-1)]">{item.title.replace(item.name, '').trim()}</div>
                        <div className="text-[var(--fluent-color-neutral-foreground-2)]">{item.drivers[0]}</div>
                        <div className="text-[var(--fluent-color-neutral-foreground-1)]">{item.adherenceScore}%</div>
                        <div className="text-[var(--fluent-color-neutral-foreground-1)]">{item.confidence}%</div>
                        <div className="text-[var(--fluent-color-neutral-foreground-2)]">{item.lastActivity}</div>
                        <div className="text-[var(--fluent-color-neutral-foreground-2)]">{item.owner}</div>
                        <div className="flex items-center justify-between gap-2">
                          <span className="truncate text-[var(--fluent-color-neutral-foreground-1)]">{item.action}</span>
                          <ChevronRight className="h-4 w-4 shrink-0 text-[var(--fluent-color-neutral-foreground-3)]" />
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>
            </div>
            {selectedQueueItem ? (
              <div className="mt-4 rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-base font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{selectedQueueItem.name}</p>
                      <StatusChip status={selectedQueueItem.risk}>{selectedQueueItem.risk}</StatusChip>
                      <StatusChip status={selectedQueueItem.momentum.status}>{selectedQueueItem.momentum.label}</StatusChip>
                    </div>
                    <p className="mt-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{selectedQueueItem.title}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{selectedQueueItem.why}</p>
                  </div>
                  <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                    <p className="font-medium text-[var(--fluent-color-neutral-foreground-1)]">Confidence {selectedQueueItem.confidence}%</p>
                    <p className="mt-1 text-xs">Evidence: {selectedQueueItem.evidence.reports} reports</p>
                    <p className="mt-1 text-xs">{selectedQueueItem.evidence.adherence}</p>
                  </div>
                </div>
                <div className="mt-4 grid gap-3 lg:grid-cols-[1.2fr_1fr]">
                  <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] p-3">
                    <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Likely Drivers</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selectedQueueItem.drivers.map((driver) => (
                        <span key={driver} className="rounded-full bg-[#F6F8FB] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{driver}</span>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] p-3">
                    <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Recommended Action</p>
                    <p className="mt-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{selectedQueueItem.action}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {['Open workspace', 'Add note', 'Generate AI draft', 'Mark reviewed', 'Escalate'].map((action) => (
                        <button key={action} onClick={() => onClientOpen(selectedQueueItem.clientId)} className="rounded-full bg-[#F6F8FB] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">
                          {action}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </Surface>

          <div className="space-y-4">
            <Surface className={`${compactMode ? 'p-3' : 'p-4'}`} animated>
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Priority clusters</p>
              <div className="mt-3 space-y-2">
                {clusters.map((cluster) => (
                  <motion.button key={cluster.title} onClick={() => openCluster(cluster)} {...hoverLift} className="flex w-full items-center justify-between rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                    <div>
                      <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{cluster.title}</p>
                      <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{cluster.count} cases • {cluster.subtitle.includes('Worsening') ? 'Down' : 'Active'} trend</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <StatusChip status={cluster.status}>{formatStatusLabel(cluster.status)}</StatusChip>
                      <span className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{cluster.count}</span>
                    </div>
                  </motion.button>
                ))}
              </div>
            </Surface>

            <Surface className={`${compactMode ? 'p-3' : 'p-4'}`} animated>
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Recommended actions</p>
              <div className="mt-3 space-y-2">
                {topActions.map((item) => {
                  const reason = priorityQueue.find((queueItem) => queueItem.clientId === item.clientId)?.title || item.detail;
                  return (
                    <motion.button key={item.title} onClick={() => onClientOpen(item.clientId)} {...hoverLift} className="flex w-full items-start justify-between rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                        <p className="mt-1 truncate text-xs text-[var(--fluent-color-neutral-foreground-2)]">Reason: {reason}</p>
                        <p className="mt-1 truncate text-xs text-[var(--fluent-color-neutral-foreground-1)]">Action: {item.detail}</p>
                      </div>
                      <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-[var(--fluent-color-neutral-foreground-3)]" />
                    </motion.button>
                  );
                })}
              </div>
            </Surface>
          </div>
        </div>

        <Surface className={`${compactMode ? 'p-3' : 'p-4'}`} animated>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              {['Trends', 'Pipelines', 'Alerts', 'Organizations'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setIntelligenceTab(tab)}
                  className={`rounded-full px-3 py-2 text-sm font-medium transition ${intelligenceTab === tab ? 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)]' : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-2)]'}`}
                >
                  {tab}
                </button>
              ))}
            </div>
            <p className="text-xs text-[var(--fluent-color-neutral-foreground-2)]">Only active intelligence is rendered</p>
          </div>

          <div className="mt-3">
            {intelligenceTab === 'Trends' ? (
              <div className={`space-y-2 ${internalTabClass}`}>
                {trendSignals.map((signal) => (
                  <motion.button key={signal.title} onClick={() => onClientOpen(priorityQueue.find((item) => item.title === signal.title)?.clientId || priorityQueue[0]?.clientId)} {...hoverLift} className="flex w-full items-start justify-between rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                    <div>
                      <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{signal.title}</p>
                      <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{signal.detail}</p>
                      <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-1)]">Likely cause: {signal.drivers[0]}</p>
                    </div>
                    <StatusChip status={signal.status}>{signal.status}</StatusChip>
                  </motion.button>
                ))}
              </div>
            ) : null}

            {intelligenceTab === 'Pipelines' ? (
              <div className={`overflow-auto ${internalTabClass}`}>
                <table className="w-full border-separate border-spacing-y-2 text-left">
                  <thead>
                    <tr className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">
                      <th className="px-3 py-1 font-medium">Client</th>
                      <th className="px-3 py-1 font-medium">Stage</th>
                      <th className="px-3 py-1 font-medium">Progress</th>
                      <th className="px-3 py-1 font-medium">Reviewer</th>
                      <th className="px-3 py-1 font-medium">ETA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pipelines.map((row) => (
                      <tr key={row.id} className="rounded-[14px] bg-[var(--fluent-color-neutral-background-2)]">
                        <td className="rounded-l-[14px] px-3 py-3 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{row.client}</td>
                        <td className="px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{row.stage}</td>
                        <td className="px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)]">{row.progress}</td>
                        <td className="px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{row.reviewer}</td>
                        <td className="rounded-r-[14px] px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{row.eta}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {intelligenceTab === 'Alerts' ? (
              <div className={`grid gap-4 md:grid-cols-3 ${internalTabClass}`}>
                {['critical', 'declining', 'medium'].map((level) => (
                  <div key={level}>
                    <p className="mb-2 text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{level === 'declining' ? 'High' : formatStatusLabel(level)}</p>
                    <div className="space-y-2">
                      {alerts.filter((alert) => (level === 'declining' ? alert.trend === 'declining' : alert.trend === level)).slice(0, 4).map((alert) => (
                        <motion.button key={alert.id} onClick={() => onClientOpen(alert.employeeId)} {...hoverLift} className="w-full rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                          <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{alert.employeeName}</p>
                          <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{alert.alert}</p>
                        </motion.button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}

            {intelligenceTab === 'Organizations' ? (
              <div className={`overflow-auto ${internalTabClass}`}>
                <table className="w-full border-separate border-spacing-y-2 text-left">
                  <thead>
                    <tr className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">
                      <th className="px-3 py-1 font-medium">Organization</th>
                      <th className="px-3 py-1 font-medium">High Risk Employees</th>
                      <th className="px-3 py-1 font-medium">Burnout Trend</th>
                      <th className="px-3 py-1 font-medium">Sleep Trend</th>
                      <th className="px-3 py-1 font-medium">Hydration Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {organizationSignals.map((org) => (
                      <tr key={org.name} className="bg-[var(--fluent-color-neutral-background-2)]">
                        <td className="rounded-l-[14px] px-3 py-3 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{org.name}</td>
                        <td className="px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)]">{org.highRisk}</td>
                        <td className="px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{org.signals[0]?.delta}</td>
                        <td className="px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{org.signals[1]?.delta}</td>
                        <td className="rounded-r-[14px] px-3 py-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{org.signals[2]?.delta}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        </Surface>
      </div>

      <div className="sticky top-[92px] self-start">
        <Surface className={`${compactMode ? 'p-3' : 'p-4'}`} animated>
          <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Intelligence rail</p>
          <div className="mt-3 space-y-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Critical Alerts</p>
              <div className="mt-2 space-y-2">
                {railAlerts.map((alert) => (
                  <motion.button key={alert.id} onClick={() => onClientOpen(alert.employeeId)} {...hoverLift} className="w-full rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{alert.employeeName}</p>
                    <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{alert.alert}</p>
                    <p className="mt-1 text-[11px] text-[var(--fluent-color-neutral-foreground-3)]">Now • {alert.recommendation}</p>
                  </motion.button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Escalations</p>
              <div className="mt-2 space-y-2">
                {railEscalations.map((item) => (
                  <motion.button key={item.clientId} onClick={() => onClientOpen(item.clientId)} {...hoverLift} className="w-full rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                    <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{item.action}</p>
                    <p className="mt-1 text-[11px] text-[var(--fluent-color-neutral-foreground-3)]">{item.confidence}% confidence</p>
                  </motion.button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">AI Pattern Detection</p>
              <div className="mt-2 space-y-2">
                <div className="rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                  <p className="text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Late dinner timing is clustering</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">Linked with worsening HbA1c and next-day recovery softness across current high-risk cases.</p>
                </div>
                <div className="rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                  <p className="text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Intervention memory surfaced</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">17 similar PCOS profiles improved after simpler breakfast anchors and lower evening complexity.</p>
                </div>
              </div>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Low Confidence AI Cases</p>
              <div className="mt-2 space-y-2">
                {lowConfidenceCases.map((item) => (
                  <motion.button key={item.clientId} onClick={() => onClientOpen(item.clientId)} {...hoverLift} className="w-full rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                    <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{item.title}</p>
                    <p className="mt-1 text-[11px] text-[var(--fluent-color-neutral-foreground-3)]">Confidence {item.confidence}% • review before publish</p>
                  </motion.button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Today's Reviews</p>
              <div className="mt-2 space-y-2">
                {railReviews.map((item) => (
                  <div key={item.employeeName} className="rounded-[14px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.employeeName}</p>
                    <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{item.stateLabel}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Surface>
      </div>
    </div>
  );
}

function SmartClientQueues({ queueViews, activeQueue, setActiveQueue, filteredClients, onClientOpen, onQueueOpen, loading = false, error = null, isRealFiteatsy = false }) {
  const errorMessage = getFiteatsyClientsErrorMessage(error);

  return (
    <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
      <Surface className="p-4" animated>
        <p className="px-2 text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Operational queues</p>
        <div className="mt-3 space-y-2">
          {queueViews.map((view) => (
            <motion.button
              key={view.key}
              onClick={() => {
                setActiveQueue(view.key);
                onQueueOpen?.(view.key);
              }}
              {...hoverLift}
              className={`flex w-full items-center justify-between rounded-[16px] px-4 py-3 text-left text-sm transition ${
                activeQueue === view.key ? 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)]' : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-1)] hover:bg-[#f7f9fc]'
              }`}
            >
              <div>
                <p className="font-medium">{view.title}</p>
                <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{view.subtitle}</p>
              </div>
              <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${toneForStatus(view.tone)}`}>{view.count}</span>
            </motion.button>
          ))}
        </div>
      </Surface>
      <Surface className="p-3">
        <div className="divide-y divide-[#EEF2F6]">
          {loading ? (
            <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading Fiteatsy clients...</div>
          ) : errorMessage ? (
            <div className="rounded-[16px] bg-[var(--fluent-color-status-danger-background)] px-4 py-5 text-sm font-medium text-[var(--fluent-color-status-danger-foreground)]">{errorMessage}</div>
          ) : filteredClients.length ? filteredClients.map((client) => (
            <motion.button
              key={client.id}
              onClick={() => onClientOpen(client.id)}
              {...hoverLift}
              className="grid w-full gap-3 px-4 py-4 text-left transition hover:bg-[var(--fluent-color-neutral-background-2)] lg:grid-cols-[1.5fr_0.7fr_0.7fr_1fr_1fr] lg:items-center"
            >
              <div>
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.brand} · {client.packageLabel} · {client.brand === 'Nuetra' ? client.organization : client.recoveryStage}</p>
              </div>
              <div><StatusChip status={isRealFiteatsy ? client.planStatus : client.riskLevel}>{isRealFiteatsy ? client.recoveryStage : client.riskLevel}</StatusChip></div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-1)]">{isRealFiteatsy ? 'Not available' : `${client.adherenceScore}%`}</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{isRealFiteatsy ? client.lastActivity : client.mentorName}</div>
              <div><StatusChip status={client.planStatus}>{isRealFiteatsy ? 'No action assigned' : formatStatusLabel(client.planStatus)}</StatusChip></div>
            </motion.button>
          )) : (
            <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              No Fiteatsy clients registered yet. New users will appear here automatically after they register in Fiteatsy.
            </div>
          )}
        </div>
      </Surface>
    </div>
  );
}

function QueueBottomSheet({ isOpen, onClose, queueViews, activeQueue, setActiveQueue, filteredClients, onClientOpen, loading = false, error = null, isRealFiteatsy = false }) {
  const errorMessage = getFiteatsyClientsErrorMessage(error);

  return (
    <AnimatePresence>
      {isOpen ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 z-[65] bg-[rgba(36,36,36,0.12)]"
        >
          <motion.div
            initial={{ y: 42, opacity: 0.98 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 32, opacity: 0.98 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            onClick={(event) => event.stopPropagation()}
            className="absolute bottom-0 left-0 right-0 mx-auto max-h-[76vh] w-full max-w-[1360px] rounded-t-[28px] bg-[var(--fluent-color-neutral-background-1)] shadow-[0_-18px_48px_rgba(16,24,40,0.16)]"
          >
            <div className="flex items-center justify-between gap-3 border-b border-[var(--fluent-color-neutral-stroke-1)] px-5 py-4">
              <div>
                <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Operational queue</p>
                <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">Queue-first triage with quick actions and context-preserving review.</p>
              </div>
              <button onClick={onClose} className="rounded-full bg-[#F6F8FB] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Close</button>
            </div>
            <div className="grid min-h-0 gap-0 md:grid-cols-[300px_minmax(0,1fr)]">
              <div className="border-r border-[var(--fluent-color-neutral-stroke-1)] p-4">
                <div className="space-y-2">
                  {queueViews.map((view) => (
                    <button
                      key={view.key}
                      onClick={() => setActiveQueue(view.key)}
                      className={`flex w-full items-center justify-between rounded-[16px] px-3 py-3 text-left ${activeQueue === view.key ? 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)]' : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-1)]'}`}
                    >
                      <div>
                        <p className="text-sm font-medium">{view.title}</p>
                        <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{view.subtitle}</p>
                      </div>
                      <StatusChip status={view.tone}>{view.count}</StatusChip>
                    </button>
                  ))}
                </div>
              </div>
              <div className="min-h-0 overflow-y-auto p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Matching clients</p>
                  <div className="flex flex-wrap gap-2">
                    {['Generate AI Draft', 'Add Note', 'Message Client'].map((action) => (
                      <button key={action} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">{action}</button>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  {loading ? (
                    <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading Fiteatsy clients...</div>
                  ) : errorMessage ? (
                    <div className="rounded-[16px] bg-[var(--fluent-color-status-danger-background)] px-4 py-4 text-sm font-medium text-[var(--fluent-color-status-danger-foreground)]">{errorMessage}</div>
                  ) : filteredClients.length ? filteredClients.map((client) => (
                    <button
                      key={client.id}
                      onClick={() => {
                        onClientOpen(client.id);
                        onClose();
                      }}
                      className="flex w-full items-center justify-between rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-left transition hover:bg-[#f7f9fc]"
                    >
                      <div>
                        <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                        <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.trendSummary.title}</p>
                        <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                          {isRealFiteatsy ? `${client.brand} • ${client.packageLabel} • ${client.lastActivity} • adherence not available` : `${client.brand} • ${client.packageLabel} • ${client.mentorName} • ${client.adherenceScore}% adherence`}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <StatusChip status={isRealFiteatsy ? client.planStatus : client.riskLevel}>{isRealFiteatsy ? client.recoveryStage : client.riskLevel}</StatusChip>
                        <StatusChip status={client.planStatus}>{formatStatusLabel(client.planStatus)}</StatusChip>
                      </div>
                    </button>
                  )) : (
                    <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                      {isRealFiteatsy ? 'No Fiteatsy clients registered yet. Clients will appear here after users complete Fiteatsy onboarding.' : 'No clients match this queue and filter combination.'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

function ClientIntelligenceDrawer({
  isOpen,
  onClose,
  employee,
  plan,
  activeTab,
  setActiveTab,
  noteDraft,
  setNoteDraft,
  noteType,
  setNoteType,
  noteSeverity,
  setNoteSeverity,
  onAddNote,
  onEditPlan,
  onGenerateDraft,
  onRegenerateBlock,
  onPlanStateChange,
  onExportDocx,
  onDietCellChange,
}) {
  return (
    <AnimatePresence>
      {isOpen && employee ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="fixed inset-0 z-50 bg-[rgba(36,36,36,0.10)]"
          onClick={onClose}
        >
          <motion.div
            initial={{ x: 36, opacity: 0.98 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 28, opacity: 0.98 }}
            transition={{ duration: 0.24, ease: 'easeOut' }}
            className="ml-auto h-full w-[80vw] min-w-[320px] max-w-[1200px] border-l border-[var(--fluent-color-neutral-stroke-1)] bg-[#F6F8FB] shadow-[-8px_0_24px_var(--fluent-shadow-ambient)]"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex h-full flex-col">
          <div className="sticky top-0 z-20 border-b border-[var(--fluent-color-neutral-stroke-1)] bg-[rgba(255,255,255,0.94)] px-4 py-3 backdrop-blur">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-2)]">Client intelligence</p>
                <p className="mt-1 text-lg font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{employee.name}</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{employee.brand} • {employee.packageLabel || employee.packageName} • {employee.packageDuration}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <motion.button {...hoverLift} onClick={onGenerateDraft} className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Generate AI Draft</motion.button>
                <motion.button {...hoverLift} className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Save</motion.button>
                <motion.button {...hoverLift} onClick={() => onPlanStateChange('published')} className="rounded-full bg-[var(--fluent-color-brand-background)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-brand-foreground)]">Publish</motion.button>
                <motion.button {...hoverLift} onClick={onExportDocx} className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Export DOCX</motion.button>
                <motion.button {...hoverLift} className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Share to Client</motion.button>
                <motion.button {...hoverLift} onClick={onClose} className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Close</motion.button>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-7">
              {[
                ['Risk', employee.riskLevel],
                ['Adherence', `${employee.adherenceScore}%`],
                ['Recovery', `${employee.recoveryMomentum.label}`],
                ['Package', employee.packageLabel || employee.packageName],
                ['Stage', employee.recoveryStage],
                ['Last activity', employee.lastActivity],
                ['Confidence', `${employee.confidence}%`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-[14px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{label}</p>
                  <p className="mt-1 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{value}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
            <ClientWorkspace
              employee={employee}
              plan={plan}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              noteDraft={noteDraft}
              setNoteDraft={setNoteDraft}
              noteType={noteType}
              setNoteType={setNoteType}
              noteSeverity={noteSeverity}
              setNoteSeverity={setNoteSeverity}
              onAddNote={onAddNote}
              onEditPlan={onEditPlan}
              onGenerateDraft={onGenerateDraft}
              onRegenerateBlock={onRegenerateBlock}
              onPlanStateChange={onPlanStateChange}
              onExportDocx={onExportDocx}
              onDietCellChange={onDietCellChange}
            />
          </div>
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

function QueueConsole({ mode, setMode, queueViews, activeQueue, setActiveQueue, filteredClients, onClientOpen }) {
  const isClosed = mode === 'closed';
  return (
    <div className="fixed bottom-4 right-4 z-40">
      <AnimatePresence initial={false}>
      {isClosed ? (
        <motion.button initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} onClick={() => setMode('compact')} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-3 text-sm font-medium text-[var(--fluent-color-brand-foreground)] shadow-[0_8px_24px_var(--fluent-shadow-ambient),0_24px_56px_var(--fluent-shadow-key)]">
          Open Operational Queue
        </motion.button>
      ) : (
        <motion.div initial={{ opacity: 0, y: 12, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 12, scale: 0.98 }} transition={{ duration: 0.2, ease: 'easeOut' }} className={`rounded-[20px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] shadow-[0_8px_24px_var(--fluent-shadow-ambient),0_24px_56px_var(--fluent-shadow-key)] ${mode === 'expanded' ? 'w-[440px]' : 'w-[320px]'}`}>
          <div className="flex items-center justify-between gap-3 border-b border-[var(--fluent-color-neutral-stroke-1)] px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Operational queue</p>
              <p className="text-xs text-[var(--fluent-color-neutral-foreground-2)]">{mode === 'expanded' ? 'Expanded triage' : 'Compact summary'}</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setMode(mode === 'compact' ? 'expanded' : 'compact')} className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">
                {mode === 'compact' ? 'Expand' : 'Compact'}
              </button>
              <button onClick={() => setMode('closed')} className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Close</button>
            </div>
          </div>
          <div className="max-h-[60vh] overflow-y-auto p-3">
            {mode === 'compact' ? (
              <div className="space-y-2">
                {queueViews.slice(0, 5).map((view) => (
                  <button key={view.key} onClick={() => { setActiveQueue(view.key); }} className="flex w-full items-center justify-between rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                    <span className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{view.title}</span>
                    <StatusChip status={view.tone}>{view.count}</StatusChip>
                  </button>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="space-y-2">
                  {queueViews.map((view) => (
                    <button key={view.key} onClick={() => setActiveQueue(view.key)} className={`flex w-full items-center justify-between rounded-[14px] px-3 py-3 text-left ${activeQueue === view.key ? 'bg-[rgba(59,130,246,0.10)]' : 'bg-[var(--fluent-color-neutral-background-2)]'}`}>
                      <div>
                        <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{view.title}</p>
                        <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{view.subtitle}</p>
                      </div>
                      <StatusChip status={view.tone}>{view.count}</StatusChip>
                    </button>
                  ))}
                </div>
                <div className="border-t border-[var(--fluent-color-neutral-stroke-1)] pt-3">
                  <p className="mb-2 text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Active queue preview</p>
                  <div className="space-y-2">
                    {filteredClients.slice(0, 5).map((client) => (
                      <button key={client.id} onClick={() => onClientOpen(client.id)} className="flex w-full items-center justify-between rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3 text-left">
                        <div>
                          <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                          <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{client.trendSummary.title}</p>
                        </div>
                        <StatusChip status={client.riskLevel}>{client.riskLevel}</StatusChip>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
      </AnimatePresence>
    </div>
  );
}

function AIDraftProgressModal({
  isOpen,
  onClose,
  status,
  progress,
  stageLabel,
  clientName,
  onDownload,
  onShareEmail,
  onShareWhatsapp,
}) {
  return (
    <AnimatePresence>
      {isOpen ? (
        <motion.div
          className="fixed inset-0 z-[90] flex items-center justify-center bg-[rgba(15,23,42,0.32)] p-4 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { duration: 0.2 } }}
          exit={{ opacity: 0, transition: { duration: 0.16 } }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-[560px] rounded-[28px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-6 shadow-[0_28px_64px_rgba(15,23,42,0.18)]"
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1, transition: { duration: 0.22, ease: [0.16, 1, 0.3, 1] } }}
            exit={{ opacity: 0, y: 10, scale: 0.98, transition: { duration: 0.16 } }}
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">AI Diet Plan Generator</p>
                <h3 className="mt-2 text-[28px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">
                  {status === 'complete' ? 'Plan is generated' : 'Generating the diet plan'}
                </h3>
                <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
                  {clientName ? `Preparing a consultant-ready recovery plan for ${clientName}.` : 'Preparing the consultant-ready recovery plan.'}
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full bg-[var(--fluent-color-neutral-background-2)] p-2 text-[var(--fluent-color-neutral-foreground-2)] transition hover:bg-[var(--fluent-color-neutral-background-3)] hover:text-[var(--fluent-color-neutral-foreground-1)]"
                aria-label="Close AI draft modal"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-6 rounded-[22px] bg-[var(--fluent-color-neutral-background-2)] p-5">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{stageLabel}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">
                    {status === 'complete' ? 'Ready for download and sharing' : 'Adaptive generation in progress'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[32px] font-semibold leading-none text-[var(--fluent-color-neutral-foreground-1)]">{progress}%</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{status === 'complete' ? 'Completed' : 'Processing'}</p>
                </div>
              </div>

              <div className="mt-5 h-3 overflow-hidden rounded-full bg-[var(--fluent-color-neutral-background-3)]">
                <motion.div
                  className="h-full rounded-full bg-[linear-gradient(90deg,#0f6cbd_0%,#5b8def_100%)]"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                {[
                  ['Data sources', 'Reports, biomarkers, adherence history'],
                  ['Plan style', 'Regional, condition-aware, intervention-led'],
                  ['Output', status === 'complete' ? 'Ready to review, download, and share' : 'Draft assembling in consultant format'],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-[18px] bg-[var(--fluent-color-neutral-background-1)] px-4 py-4">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{label}</p>
                    <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">{value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              {status === 'complete' ? (
                <>
                  <button
                    type="button"
                    onClick={onDownload}
                    className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]"
                  >
                    Download
                  </button>
                  <button
                    type="button"
                    onClick={onShareEmail}
                    className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]"
                  >
                    Share via Email
                  </button>
                  <button
                    type="button"
                    onClick={onShareWhatsapp}
                    className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]"
                  >
                    Share via WhatsApp
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  disabled
                  className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-neutral-foreground-3)]"
                >
                  Generating...
                </button>
              )}
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

function ClientWorkspace({
  employee,
  plan,
  activeTab,
  setActiveTab,
  noteDraft,
  setNoteDraft,
  noteType,
  setNoteType,
  noteSeverity,
  setNoteSeverity,
  onAddNote,
  onEditPlan,
  onGenerateDraft,
  onRegenerateBlock,
  onPlanStateChange,
  onDietCellChange,
}) {
  const confidence = employee.confidence;
  const condition = employee.conditionFocus;
  const summary = employee.trendSummary;
  const internalNotes = buildInternalNotes(employee);
  const sharedClientNotes = buildSharedClientNotes(employee);
  const chatMessages = buildChatMessages(employee, plan);
  const timelineEvents = buildTimelineEvents(employee, plan);
  const dietModules = buildDietProtocolModules(employee, plan);
  const nutritionProfile = buildNutritionProfileSnapshot(employee);
  const [openDietModule, setOpenDietModule] = useState(dietModules[0]?.id || null);
  const communicationStream = [...chatMessages, ...sharedClientNotes.map((note) => ({ ...note, sender: note.author, type: note.type, text: note.text }))]
    .sort((a, b) => String(b.time).localeCompare(String(a.time)));
  const groupedBiomarkers = useMemo(() => {
    return employee.biomarkers.reduce((acc, biomarker) => {
      const domain = getBiomarkerDomain(biomarker.name);
      if (!acc[domain]) acc[domain] = [];
      acc[domain].push(biomarker);
      return acc;
    }, {});
  }, [employee.biomarkers]);

  const workspaceHeaderStats = [
    ['Program', employee.packageLabel || employee.packageName],
    ['Risk', employee.riskLevel],
    ['Adherence', `${employee.adherenceScore}%`],
    ['Phase', employee.recoveryStage],
    ['Last interaction', employee.lastActivity],
    ['Mentor', employee.mentorName],
  ];

  function renderOverviewTab() {
    return (
      <div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr_0.9fr]">
        <div className="space-y-4">
          <Surface className="p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Client health state</p>
            <div className="mt-4 space-y-3">
              {[
                ['Readiness', `${employee.readiness}%`],
                ['Recovery', `${employee.recovery}%`],
                ['Hydration', `${employee.hydration}%`],
                ['Sleep', `${employee.sleepQuality}%`],
                ['Stress', `${employee.stress}%`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{label}</p>
                    <span className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{value}</span>
                  </div>
                </div>
              ))}
            </div>
          </Surface>

          <Surface className="p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Active issues</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {employee.biomarkers.filter((item) => item.status !== 'stable').map((item) => (
                <StatusChip key={item.name} status={item.status}>{item.name}</StatusChip>
              ))}
              <StatusChip status={employee.riskLevel}>{employee.recoveryMomentum.label}</StatusChip>
              <StatusChip status={employee.burnoutRisk === 'critical' ? 'critical' : 'medium'}>{employee.burnoutRisk} burnout risk</StatusChip>
            </div>
          </Surface>
        </div>

        <div className="space-y-4">
          <Surface className="p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Nutrition Profile</p>
                <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Shared health profile summary for consultant-ready diet planning.</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{nutritionProfile.completionPercent}% complete</p>
                <p className={`mt-1 text-xs font-medium ${nutritionProfile.aiReady ? 'text-[#107c10]' : 'text-[#bc4b09]'}`}>
                  {nutritionProfile.aiReady ? `AI ready ${nutritionProfile.readinessPercent}%` : `Pending ${nutritionProfile.readinessPercent}%`}
                </p>
              </div>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Missing information</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {nutritionProfile.missing.length ? nutritionProfile.missing.map((item) => (
                    <StatusChip key={item} status="high">{item}</StatusChip>
                  )) : <StatusChip status="improving">Profile complete</StatusChip>}
                </div>
              </div>
              <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Latest blood report</p>
                <p className="mt-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{nutritionProfile.latestReport?.name || 'No report uploaded'}</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{nutritionProfile.latestReport?.lab || 'Awaiting upload'} • {nutritionProfile.latestReport?.uploadedAt || 'No upload date'}</p>
              </div>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {[
                ['Body composition', nutritionProfile.bodyComposition],
                ['Lifestyle summary', nutritionProfile.lifestyle],
                ['Meal behaviour', nutritionProfile.mealBehaviour],
              ].map(([title, items]) => (
                <div key={title} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                  <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{title}</p>
                  <div className="mt-3 space-y-2">
                    {items.map(([label, value]) => (
                      <div key={label} className="flex items-center justify-between gap-3 text-sm">
                        <span className="text-[var(--fluent-color-neutral-foreground-3)]">{label}</span>
                        <span className="text-right font-medium text-[var(--fluent-color-neutral-foreground-1)]">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Surface>

          <Surface className="p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">What changed</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {employee.biomarkers.filter((item) => item.status !== 'stable').slice(0, 4).map((item) => (
                <div key={item.name} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                    <StatusChip status={item.status}>{item.current}</StatusChip>
                  </div>
                  <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.previous} {'->'} {item.current}</p>
                  <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{condition.drivers.slice(0, 2).join(' • ')}</p>
                </div>
              ))}
            </div>
          </Surface>

          <Surface className="p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Intervention plan + AI guidance</p>
              <button onClick={onGenerateDraft} className="rounded-full bg-[var(--fluent-color-brand-background)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-brand-foreground)]">Generate adaptation</button>
            </div>
            <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
              <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">Next best action</p>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{summary.action}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {condition.drivers.slice(0, 3).map((driver) => (
                  <span key={driver} className="rounded-full bg-[var(--fluent-color-neutral-background-inset)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{driver}</span>
                ))}
              </div>
            </div>
            <div className="mt-4 space-y-3">
              {dietModules.slice(0, 3).map((module) => (
                <div key={module.id} className="rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{module.title}</p>
                    <StatusChip status="medium">{module.options.length} options</StatusChip>
                  </div>
                  <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{module.summary}</p>
                </div>
              ))}
            </div>
          </Surface>
        </div>

        <div className="space-y-4">
          <Surface className="p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Communication + notes + activity</p>
            <div className="mt-4 space-y-3">
              {communicationStream.slice(0, 4).map((entry, index) => (
                <div key={`${entry.id || entry.time}-${index}`} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{entry.sender}</p>
                    <p className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{entry.time}</p>
                  </div>
                  <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{entry.text}</p>
                </div>
              ))}
            </div>
          </Surface>

          <Surface className="p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Nutrition Profile Timeline</p>
            <div className="mt-4 space-y-3">
              {nutritionProfile.timeline.map((event) => (
                <div key={event.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{event.title}</p>
                    <p className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{event.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </Surface>
        </div>
      </div>
    );
  }

  function renderBiomarkersTab() {
    return (
      <div className="space-y-4">
        {Object.entries(groupedBiomarkers).map(([group, items]) => (
          <Surface key={group} className="p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{group}</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {items.map((item) => (
                <div key={item.name} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                    <StatusChip status={item.status}>{item.status}</StatusChip>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Current</p>
                      <p className="mt-1 text-[var(--fluent-color-neutral-foreground-2)]">{item.current}</p>
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Previous</p>
                      <p className="mt-1 text-[var(--fluent-color-neutral-foreground-2)]">{item.previous}</p>
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Delta</p>
                      <p className="mt-1 text-[var(--fluent-color-neutral-foreground-2)]">{(item.current - item.previous).toFixed(1)}</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <SparklineBars values={item.values} color={item.status === 'declining' || item.status === 'critical' ? '#d13438' : item.status === 'improving' ? '#107c10' : '#0f6cbd'} />
                  </div>
                </div>
              ))}
            </div>
          </Surface>
        ))}
      </div>
    );
  }

  function renderBehaviorsTab() {
    const behaviors = [
      ['Hydration', employee.hydration, 'anchor reminders active'],
      ['Sleep', employee.sleepQuality, 'sleep debt needs monitoring'],
      ['Stress', employee.stress, 'stress variability elevated'],
      ['Recovery', employee.recovery, 'recovery direction tied to consistency'],
      ['Adherence', employee.adherenceScore, 'meal timing and travel friction'],
    ];

    return (
      <div className="grid gap-4 lg:grid-cols-2">
        {behaviors.map(([label, value, note]) => (
          <Surface key={label} className="p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{label}</p>
              <span className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{value}%</span>
            </div>
            <div className="mt-3">
              <ProgressTrack value={value} tone={label === 'Stress' ? '#d13438' : '#0f6cbd'} />
            </div>
            <p className="mt-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{note}</p>
          </Surface>
        ))}
      </div>
    );
  }

  function renderDietPlanTab() {
    return (
      <div className="space-y-3">
        {dietModules.map((module) => {
          const isOpen = openDietModule === module.id;
          return (
            <Surface key={module.id} className="overflow-hidden">
              <button onClick={() => setOpenDietModule(isOpen ? null : module.id)} className="flex w-full items-start justify-between gap-3 px-4 py-4 text-left">
                <div>
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{module.title}</p>
                  <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{module.summary}</p>
                </div>
                <StatusChip status="medium">{module.options.length} options</StatusChip>
              </button>
              {isOpen ? (
                <div className="border-t border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                  <p className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{module.rationale}</p>
                  <div className="mt-4 space-y-3">
                    {module.options.map((option) => (
                      <div key={option.name} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-1)] px-4 py-4">
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                          <div>
                            <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{option.name}</p>
                            <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{option.biomarkerLinkage} • {option.prepTime}</p>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <button className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">AI optimize</button>
                            <button className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Edit block</button>
                            <button className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">Compare version</button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </Surface>
          );
        })}
      </div>
    );
  }

  function renderReportsTab() {
    return (
      <div className="space-y-3">
        {employee.reports.map((report) => (
          <Surface key={report.id} className="p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{report.name}</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{report.lab} • {report.uploadedAt}</p>
              </div>
              <StatusChip status={report.ocrState === 'complete' ? 'improving' : 'medium'}>{report.ocrState}</StatusChip>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3">
              <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Confidence</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{report.extractionConfidence}%</p>
              </div>
              <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">OCR</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{report.ocrState}</p>
              </div>
              <div className="rounded-[14px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Biomarkers</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{report.detectedBiomarkers.length}</p>
              </div>
            </div>
          </Surface>
        ))}
      </div>
    );
  }

  function renderNotesTab() {
    return (
      <div className="grid gap-4 xl:grid-cols-2">
        <Surface className="p-4">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Consultant Notes</p>
          <div className="mt-4 space-y-3">
            {internalNotes.slice(0, 6).map((note) => (
              <div key={note.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{note.type}</p>
                  <StatusChip status={note.severity}>{note.severity}</StatusChip>
                </div>
                <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{note.text}</p>
              </div>
            ))}
          </div>
        </Surface>
        <Surface className="p-4">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Add Note</p>
          <div className="mt-4 space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <select value={noteType} onChange={(event) => setNoteType(event.target.value)} className="fluent-input rounded-[16px] px-3 py-3 text-sm outline-none">
                {noteTypeOptions.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
              <select value={noteSeverity} onChange={(event) => setNoteSeverity(event.target.value)} className="fluent-input rounded-[16px] px-3 py-3 text-sm outline-none">
                {noteSeverityOptions.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </div>
            <textarea value={noteDraft} onChange={(event) => setNoteDraft(event.target.value)} rows={6} className="fluent-input w-full rounded-[16px] px-3 py-3 text-sm outline-none" placeholder="Capture observation, adherence concern, or intervention outcome" />
            <button onClick={onAddNote} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Save note</button>
          </div>
        </Surface>
      </div>
    );
  }

  function renderChatTab() {
    return (
      <Surface className="p-4">
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Communication Stream</p>
        <div className="mt-4 space-y-3">
          {communicationStream.map((entry, index) => (
            <div key={`${entry.id || entry.time}-${index}`} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{entry.sender}</p>
                  <StatusChip status={entry.role === 'ai' ? 'medium' : entry.role === 'consultant' ? 'pending' : 'stable'}>{entry.type}</StatusChip>
                </div>
                <p className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{entry.time}</p>
              </div>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{entry.text}</p>
            </div>
          ))}
        </div>
      </Surface>
    );
  }

  function renderTimelineTab() {
    return (
      <Surface className="p-4">
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Intervention Timeline</p>
        <div className="mt-4 space-y-3">
          {timelineEvents.map((event) => (
            <div key={event.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{event.title}</p>
                <p className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{event.time}</p>
              </div>
              <p className="mt-1 text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{event.kind}</p>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{event.detail}</p>
            </div>
          ))}
        </div>
      </Surface>
    );
  }

  return (
    <div className="space-y-4">
      <Surface className="p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Adaptive intervention cockpit</p>
            <h3 className="mt-2 text-[28px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">{employee.name}</h3>
            <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              {employee.brand === 'Nuetra'
                ? `${employee.organization} · ${employee.department} · ${employee.workSchedule}`
                : `${employee.packageName} · ${employee.recoveryStage} · ${employee.region}`}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={onGenerateDraft} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Generate Adaptation</button>
            <button className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">Schedule Follow-up</button>
            <button className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">Send Check-in</button>
          </div>
        </div>

        <div className="mt-5 grid gap-3 lg:grid-cols-6">
          {workspaceHeaderStats.map(([label, value]) => (
            <div key={label} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{label}</p>
              <p className="mt-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{value}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {clientWorkspaceTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-3 py-2 text-sm font-medium transition ${
                activeTab === tab
                  ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]'
                  : 'bg-[var(--fluent-color-neutral-background-3)] text-[var(--fluent-color-neutral-foreground-2)]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </Surface>

      {activeTab === 'Overview' ? renderOverviewTab() : null}
      {activeTab === 'Biomarkers' ? renderBiomarkersTab() : null}
      {activeTab === 'Behaviors' ? renderBehaviorsTab() : null}
      {activeTab === 'Diet Plan' ? renderDietPlanTab() : null}
      {activeTab === 'Reports' ? renderReportsTab() : null}
      {activeTab === 'Notes' ? renderNotesTab() : null}
      {activeTab === 'Chat' ? renderChatTab() : null}
      {activeTab === 'Timeline' ? renderTimelineTab() : null}
    </div>
  );
}

function MentorHome({ clients, sessions, tasks }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Surface className="p-5">
        <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Clients needing support</p>
        <div className="mt-4 space-y-3">
          {clients.filter((client) => client.riskLevel !== 'stable').map((client) => (
            <div key={client.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                  <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.goals[0]}</p>
                </div>
                <StatusChip status={client.riskLevel}>{client.riskLevel}</StatusChip>
              </div>
            </div>
          ))}
        </div>
      </Surface>
      <Surface className="p-5">
        <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Today’s sessions</p>
        <div className="mt-4 space-y-3">
          {sessions.map((session) => (
            <div key={session.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{session.employee}</p>
              <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{session.type} · {session.when}</p>
            </div>
          ))}
          {tasks.slice(0, 2).map((task) => (
            <div key={task.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{task.title}</p>
              <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{task.due}</p>
            </div>
          ))}
        </div>
      </Surface>
    </div>
  );
}

function AdminOverview({ billing, revenue, quality }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Surface className="p-5">
        <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Organization accounts</p>
        <div className="mt-4 space-y-3">
          {billing.map((item) => (
            <div key={item.organization} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.organization}</p>
                  <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.subscription} · {item.employees} employees</p>
                </div>
                <span className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.invoice}</span>
              </div>
            </div>
          ))}
        </div>
      </Surface>
      <Surface className="p-5">
        <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Revenue and quality</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {revenue.map((item) => (
            <div key={item.label} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <p className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.label}</p>
              <p className="mt-2 text-2xl font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.value}</p>
            </div>
          ))}
          {quality.slice(0, 2).map((item) => (
            <div key={item.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] p-4">
              <p className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.label}</p>
              <p className="mt-2 text-2xl font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.count}</p>
            </div>
          ))}
        </div>
      </Surface>
    </div>
  );
}

function SuperAdminPeoplePage() {
  const [people, setPeople] = useState([]);
  const [peopleLoading, setPeopleLoading] = useState(true);
  const [peopleError, setPeopleError] = useState('');
  const [authorityOptions, setAuthorityOptions] = useState(defaultAuthorityOptions);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingPerson, setEditingPerson] = useState(null);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    role: 'mentor',
    specialization: '',
    authorities: [],
  });
  const [editAuthorities, setEditAuthorities] = useState([]);

  useEffect(() => {
    let active = true;

    Promise.allSettled([corporateAPI.people(), corporateAPI.authorityOptions()])
      .then(([peopleResult, optionsResult]) => {
        if (!active) return;

        if (peopleResult.status === 'fulfilled') {
          setPeople(Array.isArray(peopleResult.value) ? peopleResult.value : []);
        } else {
          setPeopleError(peopleResult.reason?.message || 'Unable to load workspace people.');
        }

        if (optionsResult.status === 'fulfilled' && Array.isArray(optionsResult.value)) {
          setAuthorityOptions(optionsResult.value);
        }
      })
      .finally(() => {
        if (active) {
          setPeopleLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const grouped = useMemo(() => groupManagedPeople(people), [people]);
  const visibleAuthorityOptions = useMemo(() => {
    const audience = getAuthorityAudience(form.role);
    return authorityOptions.filter((item) => item.audience === 'all' || item.audience === audience);
  }, [authorityOptions, form.role]);
  const editableAuthorityOptions = useMemo(() => {
    const audience = editingPerson ? getAuthorityAudience(editingPerson.role) : 'consultant';
    return authorityOptions.filter((item) => item.audience === 'all' || item.audience === audience);
  }, [authorityOptions, editingPerson]);

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setSubmitError('');
  }

  function toggleAuthority(value) {
    setForm((current) => ({
      ...current,
      authorities: current.authorities.includes(value)
        ? current.authorities.filter((item) => item !== value)
        : [...current.authorities, value],
    }));
  }

  function toggleEditAuthority(value) {
    setEditAuthorities((current) => (
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value]
    ));
  }

  async function handleCreate(event) {
    event.preventDefault();
    setSubmitting(true);
    setSubmitError('');

    try {
      const response = await corporateAPI.createPerson(form);
      const createdPerson = response?.person;
      if (createdPerson) {
        setPeople((current) => [createdPerson, ...current]);
      }
      setSubmitSuccess(response);
      setCreateOpen(false);
      setForm({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        role: 'mentor',
        specialization: '',
        authorities: [],
      });
    } catch (nextError) {
      setSubmitError(nextError?.message || 'Unable to create workspace account.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAuthoritySave(event) {
    event.preventDefault();
    if (!editingPerson) return;
    setSubmitting(true);
    setSubmitError('');

    try {
      const response = await corporateAPI.updatePersonAuthorities(editingPerson.id, editAuthorities);
      setPeople((current) => current.map((item) => (item.id === response.id ? response : item)));
      setEditingPerson(null);
    } catch (nextError) {
      setSubmitError(nextError?.message || 'Unable to update authorities.');
    } finally {
      setSubmitting(false);
    }
  }

  const sections = [
    { id: 'mentors', title: 'Mentors', subtitle: 'Supervision, escalations, and recovery oversight.', items: grouped.mentors },
    { id: 'consultants', title: 'Consultants', subtitle: 'Practitioner delivery roles and specialist reviewers.', items: grouped.consultants },
    { id: 'admins', title: 'Admins', subtitle: 'Operational owners with platform and organization controls.', items: grouped.admins },
  ];

  return (
    <div className="space-y-4">
      <Surface className="p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">People and authorities</p>
            <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Super admins can create mentor, consultant, and admin accounts, then assign only the authorities they need.</p>
          </div>
          <button
            type="button"
            onClick={() => {
              setSubmitError('');
              setCreateOpen(true);
            }}
            className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-brand-foreground)]"
          >
            Add workspace user
          </button>
        </div>

        {submitSuccess?.temporaryPassword || submitSuccess?.tempPassword ? (
          <div className="mt-4 rounded-[18px] border border-[var(--fluent-color-status-success-border)] bg-[var(--fluent-color-status-success-background)] p-4">
            <p className="text-sm font-medium text-[var(--fluent-color-status-success-foreground)]">
              {submitSuccess?.person?.firstName || 'Workspace user'} account created.
            </p>
            <p className="mt-1 text-sm text-[var(--fluent-color-status-success-foreground)]">
              Temporary password:{" "}
              <span className="font-semibold">{submitSuccess.temporaryPassword || submitSuccess.tempPassword}</span>
            </p>
          </div>
        ) : null}

        {peopleError ? (
          <div className="mt-4 rounded-[16px] border border-[var(--fluent-color-status-danger-border)] bg-[var(--fluent-color-status-danger-background)] p-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
            {peopleError}
          </div>
        ) : null}
      </Surface>

      <div className="grid gap-4 xl:grid-cols-3">
        {sections.map((section) => (
          <Surface key={section.id} className="p-5">
            <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{section.title}</p>
            <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{section.subtitle}</p>
            <div className="mt-4 space-y-3">
              {peopleLoading ? (
                <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading {section.title.toLowerCase()}...</div>
              ) : null}
              {!peopleLoading && !section.items.length ? (
                <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No {section.title.toLowerCase()} created yet.</div>
              ) : null}
              {section.items.map((person) => (
                <div key={person.id} className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">
                        {[person.firstName, person.lastName].filter(Boolean).join(' ') || person.email}
                      </p>
                      <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{person.email}</p>
                      <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                        {formatStatusLabel(person.role)}{person.specialization ? ` · ${person.specialization}` : ''}{person.phone ? ` · ${person.phone}` : ''}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setSubmitError('');
                        setEditingPerson(person);
                        setEditAuthorities(person.authorities || []);
                      }}
                      className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-1.5 text-xs font-medium text-[var(--fluent-color-neutral-foreground-2)]"
                    >
                      Edit authorities
                    </button>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(person.authorities || []).map((authority) => (
                      <span key={`${person.id}-${authority}`} className="rounded-full bg-[rgba(54,88,212,0.12)] px-2.5 py-1 text-[11px] text-[#3658d4]">
                        {authority.replace(/_/g, ' ')}
                      </span>
                    ))}
                    {!person.authorities?.length ? (
                      <span className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-2.5 py-1 text-[11px] text-[var(--fluent-color-neutral-foreground-3)]">
                        No custom authorities
                      </span>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </Surface>
        ))}
      </div>

      {createOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(15,23,42,0.42)] p-4">
          <div className="w-full max-w-2xl rounded-[28px] bg-[var(--fluent-color-neutral-background-1)] p-6 shadow-[0_24px_80px_rgba(15,23,42,0.24)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-lg font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Create workspace account</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Create a mentor, consultant, or admin and define the authorities they should receive from day one.</p>
              </div>
              <button
                type="button"
                onClick={() => setCreateOpen(false)}
                className="rounded-full bg-[var(--fluent-color-neutral-background-2)] p-2 text-[var(--fluent-color-neutral-foreground-2)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="mt-5 space-y-4">
              {submitError ? (
                <div className="rounded-[16px] border border-[var(--fluent-color-status-danger-border)] bg-[var(--fluent-color-status-danger-background)] p-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
                  {submitError}
                </div>
              ) : null}

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">First name</span>
                  <input type="text" required value={form.firstName} onChange={(event) => updateForm('firstName', event.target.value)} className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none" />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Last name</span>
                  <input type="text" required value={form.lastName} onChange={(event) => updateForm('lastName', event.target.value)} className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none" />
                </label>
              </div>

              <label className="block">
                <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Email</span>
                <input type="email" required value={form.email} onChange={(event) => updateForm('email', event.target.value)} className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none" />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Phone</span>
                  <input type="text" value={form.phone} onChange={(event) => updateForm('phone', event.target.value)} className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none" />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Role</span>
                  <select value={form.role} onChange={(event) => updateForm('role', event.target.value)} className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none">
                    {managedRoleOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="block">
                <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Specialization / context</span>
                <input type="text" value={form.specialization} onChange={(event) => updateForm('specialization', event.target.value)} placeholder="PCOS, operations, women’s health, mentor oversight" className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none" />
              </label>

              <div className="rounded-[22px] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Authorities</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Choose the exact access this role should receive.</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {visibleAuthorityOptions.map((authority) => (
                    <label key={authority.id} className="flex cursor-pointer items-start gap-3 rounded-[18px] bg-[var(--fluent-color-neutral-background-1)] p-3">
                      <input
                        type="checkbox"
                        checked={form.authorities.includes(authority.id)}
                        onChange={() => toggleAuthority(authority.id)}
                        className="mt-1 h-4 w-4 accent-[var(--fluent-color-brand-background)]"
                      />
                      <div>
                        <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{authority.label}</p>
                        <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{authority.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button type="button" onClick={() => setCreateOpen(false)} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Cancel</button>
                <button type="submit" disabled={submitting} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-brand-foreground)] disabled:opacity-70">
                  {submitting ? 'Creating...' : 'Create user'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {editingPerson ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(15,23,42,0.42)] p-4">
          <div className="w-full max-w-xl rounded-[28px] bg-[var(--fluent-color-neutral-background-1)] p-6 shadow-[0_24px_80px_rgba(15,23,42,0.24)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-lg font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Edit authorities</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                  {[editingPerson.firstName, editingPerson.lastName].filter(Boolean).join(' ') || editingPerson.email} · {formatStatusLabel(editingPerson.role)}
                </p>
              </div>
              <button type="button" onClick={() => setEditingPerson(null)} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] p-2 text-[var(--fluent-color-neutral-foreground-2)]">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleAuthoritySave} className="mt-5 space-y-4">
              {submitError ? (
                <div className="rounded-[16px] border border-[var(--fluent-color-status-danger-border)] bg-[var(--fluent-color-status-danger-background)] p-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
                  {submitError}
                </div>
              ) : null}

              <div className="grid gap-3">
                {editableAuthorityOptions.map((authority) => (
                  <label key={authority.id} className="flex cursor-pointer items-start gap-3 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-3">
                    <input
                      type="checkbox"
                      checked={editAuthorities.includes(authority.id)}
                      onChange={() => toggleEditAuthority(authority.id)}
                      className="mt-1 h-4 w-4 accent-[var(--fluent-color-brand-background)]"
                    />
                    <div>
                      <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{authority.label}</p>
                      <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{authority.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button type="button" onClick={() => setEditingPerson(null)} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Cancel</button>
                <button type="submit" disabled={submitting} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-brand-foreground)] disabled:opacity-70">
                  {submitting ? 'Saving...' : 'Save authorities'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function FiteatsyAdminHome() {
  const [range, setRange] = useState('month');
  const [customStart, setCustomStart] = useState('2026-06-01');
  const [customEnd, setCustomEnd] = useState('2026-06-03');
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [consultants, setConsultants] = useState([]);
  const [consultantsLoading, setConsultantsLoading] = useState(true);
  const [consultantsError, setConsultantsError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    role: 'consultant',
    specialization: '',
  });

  useEffect(() => {
    if (range === 'custom' && (!customStart || !customEnd)) {
      return undefined;
    }

    const controller = new AbortController();
    const params = new URLSearchParams({ range });
    if (range === 'custom') {
      params.set('start', customStart);
      params.set('end', customEnd);
    }

    setLoading(true);
    setError('');

    fetch(`/api/intelligence/fiteatsy?${params.toString()}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Unable to load Fiteatsy intelligence');
        }
        return response.json();
      })
      .then((nextPayload) => {
        setPayload(nextPayload);
        if (nextPayload?.window?.startDate && nextPayload?.window?.endDate && range !== 'custom') {
          setCustomStart((current) => current || nextPayload.window.startDate);
          setCustomEnd((current) => current || nextPayload.window.endDate);
        }
      })
      .catch((fetchError) => {
        if (fetchError.name !== 'AbortError') {
          setError(fetchError.message || 'Unable to load Fiteatsy intelligence');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [range, customEnd, customStart]);

  useEffect(() => {
    let active = true;
    setConsultantsLoading(true);
    setConsultantsError('');

    corporateAPI
      .consultants()
      .then((data) => {
        if (active) {
          setConsultants(Array.isArray(data) ? data : []);
        }
      })
      .catch((nextError) => {
        if (active) {
          setConsultantsError(nextError?.message || 'Unable to load consultants.');
        }
      })
      .finally(() => {
        if (active) {
          setConsultantsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const clients = payload?.clients || [];
  const revenue = payload?.metrics?.revenue || [];
  const quality = payload?.metrics?.quality || [];

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setSubmitError('');
  }

  async function handleConsultantCreate(event) {
    event.preventDefault();
    setSubmitting(true);
    setSubmitError('');

    try {
      const response = await corporateAPI.createConsultant(form);
      const createdConsultant = response?.consultant;
      if (createdConsultant) {
        setConsultants((current) => [createdConsultant, ...current]);
      }
      setSubmitSuccess(response);
      setCreateOpen(false);
      setForm({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        role: 'consultant',
        specialization: '',
      });
    } catch (nextError) {
      setSubmitError(nextError?.message || 'Unable to create consultant.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1.3fr_0.9fr]">
      <Surface className="p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Clients and plans</p>
            <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              {payload?.window?.label ? `Showing Fiteatsy clients for ${payload.window.label}.` : 'Loading Fiteatsy client intelligence.'}
            </p>
          </div>
          <div className="flex flex-col gap-3 xl:items-end">
            <div className="flex flex-wrap items-center gap-2">
              {intelligenceRangeOptions.map((option) => (
                <button
                  key={option.id}
                  onClick={() => setRange(option.id)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                    range === option.id
                      ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]'
                      : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-2)]'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            {range === 'custom' ? (
              <div className="flex flex-wrap items-center gap-2">
                <label className="inline-flex items-center gap-2 rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-xs text-[var(--fluent-color-neutral-foreground-2)]">
                  <CalendarDays className="h-4 w-4" />
                  <input
                    type="date"
                    value={customStart}
                    onChange={(event) => setCustomStart(event.target.value)}
                    className="bg-transparent text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                  />
                </label>
                <label className="inline-flex items-center gap-2 rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-xs text-[var(--fluent-color-neutral-foreground-2)]">
                  <CalendarDays className="h-4 w-4" />
                  <input
                    type="date"
                    value={customEnd}
                    onChange={(event) => setCustomEnd(event.target.value)}
                    className="bg-transparent text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                  />
                </label>
              </div>
            ) : null}
          </div>
        </div>

        {error ? (
          <div className="mt-4 rounded-[16px] border border-[var(--fluent-color-status-danger-border)] bg-[var(--fluent-color-status-danger-background)] p-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
            {error}
          </div>
        ) : null}

        <div className="mt-4 grid gap-3">
          {loading && !payload ? (
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading Fiteatsy clients...</div>
          ) : null}

          {!loading && !clients.length ? (
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No Fiteatsy clients found for the selected range.</div>
          ) : null}

          {clients.map((client) => (
            <div key={client.id} className="rounded-[20px] bg-[var(--fluent-color-neutral-background-2)] p-4 shadow-[0_10px_32px_rgba(15,23,42,0.08)]">
              <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                    <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${toneForStatus(client.planStatus)}`}>
                      {client.planStatus.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.planName} · {client.planDuration} · {client.recoveryStage}</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.city} · Last activity {client.latestActivity}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm xl:min-w-[220px]">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Readiness</p>
                    <p className="mt-1 font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{client.readiness}%</p>
                  </div>
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Adherence</p>
                    <p className="mt-1 font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{client.adherenceScore}%</p>
                  </div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {client.goals.slice(0, 3).map((goal) => (
                  <span key={`${client.id}-${goal}`} className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-2.5 py-1 text-[11px] text-[var(--fluent-color-neutral-foreground-2)]">
                    {goal}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Surface>

      <div className="space-y-4">
        <Surface className="p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Consultant accounts</p>
              <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Create and manage Fiteatsy consultant access from the admin workspace.</p>
            </div>
            <button
              type="button"
              onClick={() => {
                setSubmitError('');
                setCreateOpen(true);
              }}
              className="rounded-full bg-[var(--fluent-color-brand-background)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-brand-foreground)]"
            >
              Create consultant
            </button>
          </div>

          {submitSuccess?.temporaryPassword || submitSuccess?.tempPassword ? (
            <div className="mt-4 rounded-[18px] border border-[var(--fluent-color-status-success-border)] bg-[var(--fluent-color-status-success-background)] p-4">
              <p className="text-sm font-medium text-[var(--fluent-color-status-success-foreground)]">
                {submitSuccess?.consultant?.firstName || 'Consultant'} account created.
              </p>
              <p className="mt-1 text-sm text-[var(--fluent-color-status-success-foreground)]">
                Temporary password:{" "}
                <span className="font-semibold">{submitSuccess.temporaryPassword || submitSuccess.tempPassword}</span>
              </p>
            </div>
          ) : null}

          {consultantsError ? (
            <div className="mt-4 rounded-[16px] border border-[var(--fluent-color-status-danger-border)] bg-[var(--fluent-color-status-danger-background)] p-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
              {consultantsError}
            </div>
          ) : null}

          <div className="mt-4 space-y-3">
            {consultantsLoading ? (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading consultant directory...</div>
            ) : null}

            {!consultantsLoading && !consultants.length ? (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No consultants have been created for this organization yet.</div>
            ) : null}

            {consultants.map((consultant) => (
              <div key={consultant.id} className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">
                      {[consultant.firstName, consultant.lastName].filter(Boolean).join(' ') || consultant.email}
                    </p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{consultant.email}</p>
                    <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                      {consultant.specialization || 'General consultant'}{consultant.phone ? ` · ${consultant.phone}` : ''}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-2.5 py-1 text-[11px] text-[var(--fluent-color-neutral-foreground-2)]">
                      {formatStatusLabel(consultant.role)}
                    </span>
                    <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                      Added {new Date(consultant.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Surface>

        <Surface className="p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Revenue and quality</p>
              <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Metrics update from the same selected client date window.</p>
            </div>
            {loading ? <span className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">Refreshing...</span> : null}
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {revenue.map((item) => (
              <div key={item.label} className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <p className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.label}</p>
                <p className="mt-2 text-2xl font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.value}</p>
                <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{item.delta}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 space-y-3">
            {quality.map((item) => (
              <div key={item.id} className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.label}</p>
                    <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{item.detail}</p>
                  </div>
                  <span className="text-lg font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </Surface>
      </div>

      {createOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(15,23,42,0.42)] p-4">
          <div className="w-full max-w-xl rounded-[28px] bg-[var(--fluent-color-neutral-background-1)] p-6 shadow-[0_24px_80px_rgba(15,23,42,0.24)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-lg font-semibold text-[var(--fluent-color-neutral-foreground-1)]">Create consultant account</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">The consultant will receive a temporary password and can sign in immediately after creation.</p>
              </div>
              <button
                type="button"
                onClick={() => setCreateOpen(false)}
                className="rounded-full bg-[var(--fluent-color-neutral-background-2)] p-2 text-[var(--fluent-color-neutral-foreground-2)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleConsultantCreate} className="mt-5 space-y-4">
              {submitError ? (
                <div className="rounded-[16px] border border-[var(--fluent-color-status-danger-border)] bg-[var(--fluent-color-status-danger-background)] p-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
                  {submitError}
                </div>
              ) : null}

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">First name</span>
                  <input
                    type="text"
                    required
                    value={form.firstName}
                    onChange={(event) => updateForm('firstName', event.target.value)}
                    className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Last name</span>
                  <input
                    type="text"
                    required
                    value={form.lastName}
                    onChange={(event) => updateForm('lastName', event.target.value)}
                    className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                  />
                </label>
              </div>

              <label className="block">
                <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Email</span>
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={(event) => updateForm('email', event.target.value)}
                  className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Phone</span>
                  <input
                    type="text"
                    value={form.phone}
                    onChange={(event) => updateForm('phone', event.target.value)}
                    className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Role</span>
                  <select
                    value={form.role}
                    onChange={(event) => updateForm('role', event.target.value)}
                    className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                  >
                    <option value="consultant">Consultant</option>
                    <option value="provider">Provider</option>
                    <option value="dietician">Dietician</option>
                    <option value="senior_consultant">Senior Consultant</option>
                  </select>
                </label>
              </div>

              <label className="block">
                <span className="mb-2 block text-sm text-[var(--fluent-color-neutral-foreground-2)]">Specialization</span>
                <input
                  type="text"
                  value={form.specialization}
                  onChange={(event) => updateForm('specialization', event.target.value)}
                  placeholder="PCOS, metabolism, thyroid, women’s health"
                  className="w-full rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none"
                />
              </label>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-brand-foreground)] disabled:opacity-70"
                >
                  {submitting ? 'Creating...' : 'Create consultant'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function AdminHome({ billing, revenue, quality, brandView }) {
  if (brandView === 'Fiteatsy') {
    return <FiteatsyAdminHome />;
  }

  return <AdminOverview billing={billing} revenue={revenue} quality={quality} />;
}

function MedicationAttentionSection({
  feed,
  loading,
  error,
  onRefresh,
  onClientOpen,
  onCreateFollowUp,
  onAcknowledge,
  acknowledgingId,
}) {
  const summary = feed?.summary || {};
  const exceptions = Array.isArray(feed?.exceptions) ? feed.exceptions : [];
  const byType = summary.byType || {};
  const typeItems = Object.entries(byType).filter(([, count]) => Number(count) > 0);

  return (
    <Surface className="border border-[rgba(245,158,11,0.28)] bg-[linear-gradient(135deg,rgba(245,158,11,0.10),rgba(15,23,42,0.02))] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[#B45309]">Medication Attention</p>
          <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.02em]">Operational medication exceptions</h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">
            Deterministic adherence signals from assigned Fiteatsy clients. These are workflow prompts, not diagnostic or prescribing recommendations.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip status={exceptions.length ? 'high' : 'stable'}>
            {summary.activeExceptionCount || 0} active
          </StatusChip>
          <StatusChip status={summary.clientsRequiringAttention ? 'medium' : 'stable'}>
            {summary.clientsRequiringAttention || 0} clients
          </StatusChip>
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] px-3 py-1.5 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)] disabled:opacity-60"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {typeItems.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {typeItems.map(([type, count]) => (
            <span key={type} className="rounded-full bg-[rgba(245,158,11,0.12)] px-3 py-1.5 text-xs font-medium text-[#92400E]">
              {formatStatusLabel(type)} · {count}
            </span>
          ))}
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-[18px] border border-[var(--fluent-color-status-danger-border)] bg-[var(--fluent-color-status-danger-background)] p-4 text-sm text-[var(--fluent-color-status-danger-foreground)]">
          Unable to load medication attention right now. {error?.message || 'Try refreshing the command center.'}
        </div>
      ) : null}

      {loading && !exceptions.length ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          <LoadingSkeleton className="h-32" />
          <LoadingSkeleton className="h-32" />
        </div>
      ) : exceptions.length ? (
        <div className="mt-4 grid gap-3 xl:grid-cols-2">
          {exceptions.slice(0, 6).map((exception) => (
            <div key={exception.id} className="rounded-[20px] border border-[rgba(245,158,11,0.22)] bg-[var(--fluent-color-neutral-background-1)] p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">
                    {exception.clientName || 'Assigned client'}
                  </p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                    {exception.typeLabel || formatStatusLabel(exception.type)} · {exception.status || 'OPEN'}
                  </p>
                </div>
                <StatusChip status={exception.status === 'ACKNOWLEDGED' ? 'pending' : 'high'}>
                  {exception.status === 'ACKNOWLEDGED' ? 'Acknowledged' : 'Open'}
                </StatusChip>
              </div>
              <p className="mt-3 text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{exception.title}</p>
              <p className="mt-2 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">{exception.summary}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => onClientOpen(exception.clientId)}
                  className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-1.5 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]"
                >
                  View medication
                </button>
                <button
                  type="button"
                  onClick={() => onCreateFollowUp(exception.clientId, exception.summary)}
                  className="rounded-full border border-[rgba(245,158,11,0.32)] bg-[rgba(245,158,11,0.10)] px-3 py-1.5 text-xs font-medium text-[#92400E]"
                >
                  Create follow-up
                </button>
                <button
                  type="button"
                  onClick={() => onAcknowledge(exception.id)}
                  disabled={exception.status === 'ACKNOWLEDGED' || acknowledgingId === exception.id}
                  className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] px-3 py-1.5 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)] disabled:opacity-50"
                >
                  {acknowledgingId === exception.id ? 'Saving...' : exception.status === 'ACKNOWLEDGED' ? 'Acknowledged' : 'Acknowledge'}
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-4 rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] p-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
          No medication exceptions are open for assigned clients right now.
        </div>
      )}
    </Surface>
  );
}

function CommandCenterPage({
  briefingMeta,
  pulseItems,
  priorityQueue,
  workloadItems,
  memoryItems,
  railItems,
  medicationExceptionFeed,
  medicationExceptionsLoading,
  medicationExceptionsError,
  onMedicationExceptionsRefresh,
  onMedicationExceptionAcknowledge,
  medicationExceptionAcknowledgingId,
  onClientOpen,
  onCreateFollowUp,
  onPulseSelect,
}) {
  const [selectedClientId, setSelectedClientId] = useState(priorityQueue[0]?.clientId || null);

  useEffect(() => {
    if (!priorityQueue.length) return;
    if (!selectedClientId || !priorityQueue.some((item) => item.clientId === selectedClientId)) {
      setSelectedClientId(priorityQueue[0].clientId);
    }
  }, [priorityQueue, selectedClientId]);

  const selectedItem = priorityQueue.find((item) => item.clientId === selectedClientId) || priorityQueue[0];
  const railGroups = {
    'Critical Alerts': railItems.filter((item) => item.status === 'critical').slice(0, 2),
    'Emerging Patterns': railItems.filter((item) => item.badge === 'Pattern').slice(0, 2),
    'AI Learnings': memoryItems.slice(0, 2).map((item) => ({ ...item, badge: 'Learning', status: 'medium' })),
    'Mentor Escalations': priorityQueue.filter((item) => item.risk === 'critical' || item.risk === 'high').slice(0, 2).map((item) => ({
      title: item.name,
      detail: `${item.momentum.label} • last touch ${item.lastActivity}`,
      badge: 'Escalate',
      status: item.risk,
    })),
    'Intervention Memory': memoryItems.slice(1, 3).map((item) => ({ ...item, badge: 'Memory', status: 'stable' })),
  };

  const compactRows = priorityQueue.map((item) => ({
    ...item,
    primaryIssue: item.title.replace('worsening', '').replace('improving', '').trim(),
    temporalState: String(item.lastActivity).toLowerCase().includes('today') ? 'active today' : 'follow-up pending',
    nextAction: item.action.split('. ')[0],
  }));

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-4">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
          <div className="grid gap-4 xl:grid-cols-[minmax(280px,340px)_minmax(0,1fr)] xl:items-stretch">
            <div className="flex flex-col justify-between rounded-[24px] bg-[var(--fluent-color-neutral-background-2)] px-5 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Command Center</p>
              <div className="mt-3">
                <h2 className="text-[22px] font-semibold tracking-[-0.02em]">Adaptive recovery mission control</h2>
                <p className="mt-2 max-w-[26ch] text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">{briefingMeta}</p>
              </div>
              <p className="mt-4 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Click a signal to open its working list</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
              {pulseItems.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => onPulseSelect(item)}
                  className="group flex min-h-[136px] flex-col justify-between rounded-[24px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] px-4 py-3.5 text-left shadow-[0_8px_24px_rgba(15,23,42,0.05)] transition duration-200 hover:-translate-y-[1px] hover:border-[var(--fluent-color-brand-stroke-1)] hover:bg-[var(--fluent-color-neutral-background-1)] hover:shadow-[0_12px_28px_rgba(15,23,42,0.08)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fluent-color-brand-stroke-1)] focus-visible:ring-offset-2"
                  aria-label={`Open ${item.label} list`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{item.label}</p>
                      <StatusChip status={item.status}>{item.delta}</StatusChip>
                    </div>
                    <div className="mt-3 flex items-end justify-between gap-3">
                      <p className="text-[36px] font-semibold leading-none text-[var(--fluent-color-neutral-foreground-1)]">{item.value}</p>
                      <span className="text-xs font-medium text-[var(--fluent-color-brand-foreground-link)] opacity-0 transition group-hover:opacity-100">Open list</span>
                    </div>
                  </div>
                  <div className="mt-3">
                    <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-2.5">
                      <SparklineBars values={item.spark} color={item.color} />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </Surface>

        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Attention Queue</p>
              <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Scan the active intervention queue, select a case, and move into workspace only when ready to act.</p>
            </div>
            <span className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{priorityQueue.length} active cases</span>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <div className="overflow-hidden rounded-[20px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)]">
              <div className="grid grid-cols-[1.2fr_0.9fr_1fr_0.9fr_0.9fr_0.9fr_1fr_0.9fr] gap-3 border-b border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-inset)] px-4 py-3 text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">
                <span>Client</span>
                <span>Risk</span>
                <span>Primary Issue</span>
                <span>Recovery</span>
                <span>Last Touch</span>
                <span>Adherence</span>
                <span>Confidence</span>
                <span>Action</span>
              </div>
              <div className="divide-y divide-[var(--fluent-color-neutral-stroke-1)]">
                {compactRows.map((item) => {
                  const isSelected = item.clientId === selectedClientId;
                  return (
                    <button
                      key={item.clientId}
                      onClick={() => setSelectedClientId(item.clientId)}
                      className={`grid w-full grid-cols-[1.2fr_0.9fr_1fr_0.9fr_0.9fr_0.9fr_1fr_0.9fr] gap-3 px-4 py-4 text-left transition ${
                        isSelected
                          ? 'bg-[rgba(59,130,246,0.08)]'
                          : 'bg-[var(--fluent-color-neutral-background-1)] hover:bg-[#f7f9fc]'
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                        <p className="mt-1 truncate text-xs text-[var(--fluent-color-neutral-foreground-3)]">{item.owner}</p>
                      </div>
                      <div className="min-w-0">
                        <StatusChip status={item.risk}>{item.risk}</StatusChip>
                      </div>
                      <div className="min-w-0 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.primaryIssue}</div>
                      <div className="min-w-0 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.momentum.label}</div>
                      <div className="min-w-0 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.lastActivity}</div>
                      <div className="min-w-0 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.adherenceScore}%</div>
                      <div className="min-w-0 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.confidence}%</div>
                      <div className="min-w-0">
                        <span className="rounded-full bg-[var(--fluent-color-neutral-background-3)] px-3 py-1.5 text-xs font-medium text-[var(--fluent-color-neutral-foreground-1)]">
                          Open Workspace
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {selectedItem ? (
              <div className="rounded-[20px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Selected Client Preview</p>
                    <h3 className="mt-2 text-xl font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{selectedItem.name}</h3>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{selectedItem.title}</p>
                  </div>
                  <StatusChip status={selectedItem.risk}>{selectedItem.risk}</StatusChip>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Why AI flagged this</p>
                    <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{selectedItem.drivers.slice(0, 2).join(' • ')}</p>
                  </div>
                  <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Recovery direction</p>
                    <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{selectedItem.momentum.label}</p>
                  </div>
                  <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Suggested intervention</p>
                    <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{selectedItem.action}</p>
                  </div>
                  <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-1)] px-3 py-3">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Temporal state</p>
                    <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Last touched {selectedItem.lastActivity} • {selectedItem.temporalState}</p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full bg-[var(--fluent-color-neutral-background-inset)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">Adherence {selectedItem.adherenceScore}%</span>
                  <span className="rounded-full bg-[var(--fluent-color-neutral-background-inset)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">Confidence {selectedItem.confidence}%</span>
                  <span className="rounded-full bg-[var(--fluent-color-neutral-background-inset)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{selectedItem.evidence.reports} reports</span>
                  <span className="rounded-full bg-[var(--fluent-color-neutral-background-inset)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{selectedItem.evidence.adherence}</span>
                </div>

                <div className="mt-4">
                  <button
                    onClick={() => onClientOpen(selectedItem.clientId)}
                    className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]"
                  >
                    Open Workspace
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </Surface>

        <MedicationAttentionSection
          feed={medicationExceptionFeed}
          loading={medicationExceptionsLoading}
          error={medicationExceptionsError}
          onRefresh={onMedicationExceptionsRefresh}
          onClientOpen={onClientOpen}
          onCreateFollowUp={onCreateFollowUp}
          onAcknowledge={onMedicationExceptionAcknowledge}
          acknowledgingId={medicationExceptionAcknowledgingId}
        />

        <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Recovery Momentum</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {workloadItems.map((item) => (
                <button key={item.label} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-left transition hover:border-[var(--fluent-color-neutral-stroke-2)] hover:bg-[#f7f9fc]">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.label}</p>
                    <StatusChip status={item.status}>{item.value}</StatusChip>
                  </div>
                  <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
                </button>
              ))}
            </div>
          </Surface>

          <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Operational Memory</p>
            <div className="mt-4 space-y-3">
              {memoryItems.map((item) => (
                <div key={item.title} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                  <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                  <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
                </div>
              ))}
            </div>
          </Surface>
        </div>
      </div>

      <div className="space-y-4 xl:sticky xl:top-[150px] xl:self-start">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Live Intelligence Rail</p>
          <div className="mt-4 space-y-4">
            {Object.entries(railGroups).map(([label, items]) => (
              <div key={label}>
                <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{label}</p>
                <div className="space-y-2">
                  {items.map((item) => (
                    <div key={`${label}-${item.title}`} className="rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                          <p className="mt-1 line-clamp-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
                        </div>
                        <StatusChip status={item.status}>{item.badge}</StatusChip>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Surface>
      </div>
    </div>
  );
}

function ClientDirectoryPage({ queueViews, activeQueue, setActiveQueue, filteredClients, totalCount = 0, onClientOpen, loading = false, error = null, isRealFiteatsy = false, isAdminDirectory = false, canManageAssignments = false, onAssignClient }) {
  const errorMessage = getFiteatsyClientsErrorMessage(error);
  const [assignmentFilter, setAssignmentFilter] = useState('all');
  const visibleClients = isAdminDirectory && assignmentFilter !== 'all'
    ? filteredClients.filter((client) => client.assignmentStatus === assignmentFilter)
    : filteredClients;

  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{isAdminDirectory ? 'Registered Client Directory' : 'My Clients'}</p>
            <h2 className="mt-2 text-[24px] font-semibold tracking-[-0.02em]">Healthcare operating roster</h2>
            <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              {isRealFiteatsy
                ? (isAdminDirectory ? `${totalCount} registered Fiteatsy clients. Assignment and subscription are tracked independently.` : `${totalCount} clients assigned to your consultant workspace.`)
                : 'Filter the client population by risk, momentum, inactivity, and intervention stage before opening the workspace.'}
            </p>
            {isRealFiteatsy && !isAdminDirectory && !canManageAssignments ? (
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-3)]">
                Client assignment is managed by authorised operations. Assigned clients will appear here automatically.
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            {isRealFiteatsy && canManageAssignments && typeof onAssignClient === 'function' ? (
              <button type="button" onClick={onAssignClient} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)]">
                Assign Client
              </button>
            ) : null}
            {isRealFiteatsy ? (
              isAdminDirectory ? (
                <span className="rounded-full bg-[var(--fluent-color-status-info-background)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-status-info-foreground)]">
                  Registered clients · {totalCount}
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => setActiveQueue('assigned')}
                  aria-label={`Show all assigned clients (${totalCount})`}
                  aria-pressed={activeQueue === 'assigned'}
                  className={`rounded-full px-3 py-2 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fluent-color-brand-stroke-1)] focus-visible:ring-offset-2 ${
                    activeQueue === 'assigned'
                      ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]'
                      : 'bg-[var(--fluent-color-status-info-background)] text-[var(--fluent-color-status-info-foreground)] hover:bg-[var(--fluent-color-neutral-background-2)]'
                  }`}
                >
                  Assigned clients · {totalCount}
                </button>
              )
            ) : null}
            {isAdminDirectory ? (
              <select value={assignmentFilter} onChange={(event) => setAssignmentFilter(event.target.value)} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-xs font-medium text-[var(--fluent-color-neutral-foreground-2)] outline-none">
                <option value="all">All clients</option>
                <option value="assigned">Assigned</option>
                <option value="unassigned">Unassigned</option>
              </select>
            ) : null}
            {queueViews.slice(0, isRealFiteatsy ? 6 : 5).map((view) => (
              <button
                key={view.key}
                onClick={() => setActiveQueue(view.key)}
                className={`rounded-full px-3 py-2 text-xs font-medium transition ${
                  activeQueue === view.key ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]' : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-2)]'
                }`}
              >
                {view.title} · {view.count}
              </button>
            ))}
          </div>
        </div>
      </Surface>

      <Surface className="overflow-hidden border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <div className="grid grid-cols-[1.3fr_0.9fr_1fr_0.8fr_1fr_0.9fr_1.1fr] gap-3 border-b border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-inset)] px-4 py-3 text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">
          <span>Client</span>
          <span>Program</span>
          <span>Momentum</span>
          <span>Adherence</span>
          <span>Protocol Stage</span>
          <span>Last activity</span>
          <span>Next action</span>
        </div>
        <div className="divide-y divide-[var(--fluent-color-neutral-stroke-1)]">
          {loading ? (
            <div className="px-4 py-8 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading Fiteatsy clients...</div>
          ) : errorMessage ? (
            <div className="px-4 py-8 text-sm font-medium text-[var(--fluent-color-status-danger-foreground)]">{errorMessage}</div>
          ) : visibleClients.length ? visibleClients.map((client) => (
            <button
              key={client.id}
              onClick={() => onClientOpen(client.id)}
              className="grid w-full grid-cols-[1.3fr_0.9fr_1fr_0.8fr_1fr_0.9fr_1.1fr] gap-3 px-4 py-4 text-left transition hover:bg-[var(--fluent-color-neutral-background-2)]"
            >
              <div>
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                  {isRealFiteatsy
                    ? [client.email, client.mobile || client.mobileNumberMasked].filter(Boolean).join(' · ') || 'Contact not available'
                    : `${client.brand} · ${client.organization}`}
                </p>
              </div>
              <div className="min-w-0 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.packageLabel}</div>
              <div className="min-w-0">
                <StatusChip status={isRealFiteatsy ? 'pending' : client.recoveryMomentum.status}>{isRealFiteatsy ? 'Not available' : client.recoveryMomentum.label}</StatusChip>
                <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.trendSummary.title}</p>
              </div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{isRealFiteatsy ? 'Not available' : `${client.adherenceScore}%`}</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{formatStatusLabel(client.planStatus)}</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.lastActivity}</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{isRealFiteatsy ? 'No action assigned' : client.conditionFocus.action.split('.')[0]}</div>
            </button>
          )) : (
            <div className="px-4 py-8 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              <p>{isAdminDirectory ? 'No registered Fiteatsy clients found.' : 'No clients are assigned to you yet.'}</p>
              {isRealFiteatsy && canManageAssignments && typeof onAssignClient === 'function' ? (
                <button type="button" onClick={onAssignClient} className="mt-4 rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)]">
                  Assign Client
                </button>
              ) : null}
            </div>
          )}
        </div>
      </Surface>
    </div>
  );
}

function ProfessionalAssignmentPage() {
  const [query, setQuery] = useState('');
  const [clients, setClients] = useState([]);
  const [professionals, setProfessionals] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [clientUserId, setClientUserId] = useState('');
  const [professionalUserId, setProfessionalUserId] = useState('');
  const [professionalType, setProfessionalType] = useState('CONSULTANT');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    const [nextProfessionals, nextAssignments] = await Promise.all([
      listFiteatsyAssignmentProfessionals(professionalType),
      listFiteatsyProfessionalAssignments(),
    ]);
    setProfessionals(nextProfessionals);
    setAssignments(nextAssignments);
  }, [professionalType]);

  useEffect(() => { refresh().catch((nextError) => setError(nextError.message)); }, [refresh]);

  const search = async () => {
    try { setError(''); setClients(await searchFiteatsyAssignmentClients(query)); }
    catch (nextError) { setError(nextError.message); }
  };

  const assign = async () => {
    if (!clientUserId || !professionalUserId) return;
    try {
      setError('');
      await createFiteatsyProfessionalAssignment({ clientUserId, professionalUserId, professionalType, relationshipType: professionalType === 'MENTOR' ? 'MENTORSHIP' : 'CLIENT_CARE', reason: 'Operational client assignment' });
      setMessage('Assignment created');
      await refresh();
    } catch (nextError) { setError(nextError.message); }
  };

  const revoke = async (assignmentId) => {
    try { await revokeFiteatsyProfessionalAssignment(assignmentId, 'Operational assignment change'); setMessage('Assignment revoked'); await refresh(); }
    catch (nextError) { setError(nextError.message); }
  };

  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-5">
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Client Assignments</p>
        <h2 className="mt-2 text-[24px] font-semibold">Assign a Fiteatsy client</h2>
        <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Assign registered Fiteatsy clients to yourself or to an active Consultant. Food Preferences and subscription do not affect eligibility.</p>
        <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_180px_1fr_auto]">
          <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && search()} placeholder="Search registered clients" className="rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3 py-2 text-sm" />
          <select value={professionalType} onChange={(event) => { setProfessionalType(event.target.value); setProfessionalUserId(''); }} className="rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3 py-2 text-sm"><option value="CONSULTANT">Consultant</option><option value="PRACTITIONER">Practitioner</option><option value="MENTOR">Mentor</option></select>
          <select value={professionalUserId} onChange={(event) => setProfessionalUserId(event.target.value)} className="rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3 py-2 text-sm"><option value="">Select professional</option>{professionals.map((professional) => <option key={professional.userId} value={professional.userId}>{professional.name}</option>)}</select>
          <button type="button" onClick={search} className="rounded-[12px] bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-[var(--fluent-color-brand-foreground)]">Search</button>
        </div>
        {error ? <p className="mt-3 text-sm text-[var(--fluent-color-status-danger-foreground)]">{error}</p> : null}
        {message ? <p className="mt-3 text-sm text-[var(--fluent-color-status-success-foreground)]">{message}</p> : null}
        <div className="mt-4 space-y-2">{clients.map((client) => <div key={client.userId} className="flex items-center justify-between gap-3 rounded-[12px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3"><div><p className="text-sm font-medium">{client.name}</p><p className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.clientId} · {client.assignmentStatus}</p></div><button type="button" onClick={() => { setClientUserId(client.userId); }} className="rounded-[10px] bg-[var(--fluent-color-neutral-background-3)] px-3 py-2 text-xs font-semibold">Select</button></div>)}</div>
        <button type="button" disabled={!clientUserId || !professionalUserId} onClick={assign} className="mt-4 rounded-[12px] bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-[var(--fluent-color-brand-foreground)] disabled:opacity-40">Assign selected client</button>
      </Surface>
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-5"><h3 className="text-lg font-semibold">Active and historical assignments</h3><div className="mt-3 space-y-2">{assignments.map((assignment) => <div key={assignment.id} className="flex items-center justify-between gap-3 rounded-[12px] bg-[var(--fluent-color-neutral-background-2)] px-3 py-3"><div><p className="text-sm font-medium">{assignment.client_name} · {assignment.professional_name}</p><p className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{assignment.professional_type} · {assignment.status}</p></div>{assignment.status === 'active' ? <button type="button" onClick={() => revoke(assignment.id)} className="rounded-[10px] bg-[var(--fluent-color-status-danger-background)] px-3 py-2 text-xs font-semibold">Revoke</button> : null}</div>)}</div></Surface>
    </div>
  );
}

function SeniorConsultantClientAllocationPage({ currentUserId }) {
  const [view, setView] = useState('all');
  const [query, setQuery] = useState('');
  const [clients, setClients] = useState([]);
  const [professionals, setProfessionals] = useState([]);
  const [counts, setCounts] = useState({ all: 0, unassigned: 0, mine: 0, assigned: 0 });
  const [selectedClient, setSelectedClient] = useState(null);
  const [professionalUserId, setProfessionalUserId] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [nextClients, allClients, nextProfessionals] = await Promise.all([
        listFiteatsyClientAllocationPool({ query, assignment: view }),
        listFiteatsyClientAllocationPool({ query, assignment: 'all' }),
        listFiteatsyAssignmentProfessionals('CONSULTANT'),
      ]);
      setClients(nextClients);
      setCounts({
        all: allClients.length,
        unassigned: allClients.filter((client) => client.assignmentStatus === 'UNASSIGNED').length,
        mine: allClients.filter((client) => client.assignedToMe).length,
        assigned: allClients.filter((client) => client.assignmentStatus === 'ASSIGNED').length,
      });
      setProfessionals(nextProfessionals.filter((professional) => professional.role !== 'senior_consultant'));
    } catch (nextError) {
      setError(nextError.message || 'Unable to load the Client Pool.');
    } finally {
      setLoading(false);
    }
  }, [query, view]);

  useEffect(() => { void refresh(); }, [refresh]);

  const assign = async () => {
    if (!selectedClient?.userId || !professionalUserId) return;
    try {
      setError('');
      await createFiteatsyProfessionalAssignment({ clientUserId: selectedClient.userId, professionalUserId, professionalType: 'CONSULTANT', relationshipType: 'CLIENT_CARE', reason: 'Senior Consultant client allocation' });
      setMessage('Client assignment updated.');
      setSelectedClient(null);
      setProfessionalUserId('');
      await refresh();
    } catch (nextError) { setError(nextError.message || 'Unable to update the assignment.'); }
  };

  const endAssignment = async (client) => {
    if (!client?.assignmentId) return;
    try {
      setError('');
      await revokeFiteatsyProfessionalAssignment(client.assignmentId, 'Senior Consultant returned client to pool');
      setMessage('Client returned to the Client Pool.');
      await refresh();
    } catch (nextError) { setError(nextError.message || 'Unable to end the assignment.'); }
  };

  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-5" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Senior Consultant</p>
        <h2 className="mt-2 text-[24px] font-semibold">Client allocation</h2>
        <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Allocate registered Fiteatsy Clients without requiring Food Preferences or a subscription.</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {[['all', 'All Clients'], ['mine', 'Assigned to Me'], ['assigned', 'Assigned to Consultants'], ['unassigned', 'Unassigned']].map(([value, label]) => (
            <button key={value} type="button" onClick={() => setView(value)} className={`rounded-full px-4 py-2 text-xs font-semibold ${view === value ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]' : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-2)]'}`}>{label} · {counts[value]}</button>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && refresh()} placeholder="Search registered Clients" className="min-w-[260px] flex-1 rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3 py-2 text-sm" />
          <button type="button" onClick={() => void refresh()} className="rounded-[12px] bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-[var(--fluent-color-brand-foreground)]">Search</button>
        </div>
      </Surface>
      {error ? <p className="rounded-[16px] bg-[var(--fluent-color-status-danger-background)] px-4 py-3 text-sm text-[var(--fluent-color-status-danger-foreground)]">{error}</p> : null}
      {message ? <p className="rounded-[16px] bg-[var(--fluent-color-status-success-background)] px-4 py-3 text-sm text-[var(--fluent-color-status-success-foreground)]">{message}</p> : null}
      <Surface className="overflow-hidden border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)]" animated>
        {loading ? <p className="p-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading Client Pool...</p> : clients.length ? (
          <div className="divide-y divide-[var(--fluent-color-neutral-stroke-1)]">
            {clients.map((client) => (
              <div key={client.userId} className="flex flex-wrap items-center justify-between gap-4 p-4">
                <div className="min-w-[220px] flex-1">
                  <p className="text-sm font-semibold">{client.name}</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Registered {client.registrationDateISO ? new Date(client.registrationDateISO).toLocaleDateString() : '—'} · Food Preferences: {client.foodPreferenceStatus === 'AVAILABLE' ? 'Available' : 'Not provided'} · Subscription: {client.subscriptionStatus === 'NONE' ? 'None' : client.subscriptionStatus}</p>
                </div>
                <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.assignedProfessional ? `Assigned to ${client.assignedProfessional.name}` : 'Unassigned'}</div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => { setSelectedClient(client); setProfessionalUserId(client.assignedToMe ? currentUserId : ''); }} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)]">{client.assignmentStatus === 'ASSIGNED' ? 'Reassign' : 'Assign'}</button>
                  {client.assignmentStatus === 'ASSIGNED' ? <button type="button" onClick={() => void endAssignment(client)} className="rounded-full border border-[var(--fluent-color-status-danger-border)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-status-danger-foreground)]">End Assignment</button> : null}
                </div>
              </div>
            ))}
          </div>
        ) : <p className="p-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No registered Clients match this view.</p>}
      </Surface>
      {selectedClient ? (
        <Surface className="border border-[var(--fluent-color-brand-background)] bg-[var(--fluent-color-neutral-background-1)] p-5" animated>
          <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Assign Client</p><h3 className="mt-1 text-lg font-semibold">{selectedClient.name}</h3></div><button type="button" onClick={() => setSelectedClient(null)} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-2 text-xs font-semibold">Cancel</button></div>
          <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto] md:items-end"><label className="text-sm font-medium">Assign to me or Consultant<select value={professionalUserId} onChange={(event) => setProfessionalUserId(event.target.value)} className="mt-2 w-full rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3 py-2 text-sm"><option value="">Select assignment target</option><option value={currentUserId}>Assign to Me</option>{professionals.map((professional) => <option key={professional.userId} value={professional.userId}>{professional.name}</option>)}</select></label><button type="button" disabled={!professionalUserId} onClick={() => void assign()} className="rounded-[12px] bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-semibold text-[var(--fluent-color-brand-foreground)] disabled:opacity-40">Confirm Assignment</button></div>
        </Surface>
      ) : null}
    </div>
  );
}

function DietPlanReviewQueuePage() {
  const [reviews, setReviews] = useState([]);
  const [comments, setComments] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setReviews(await listFiteatsyDietPlanReviews());
    } catch (nextError) {
      setError(nextError.message || 'Unable to load diet plan reviews.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const approve = async (review) => {
    try {
      await approveFiteatsyConsultantDietPlan(review.clientUserId, review.dietPlanId);
      await refresh();
    } catch (nextError) {
      setError(nextError.message || 'Unable to approve this diet plan.');
    }
  };

  const requestChanges = async (review) => {
    const comment = String(comments[review.dietPlanId] || '').trim();
    if (!comment) {
      setError('A review comment is required when requesting changes.');
      return;
    }
    try {
      await requestFiteatsyConsultantDietPlanChanges(review.clientUserId, review.dietPlanId, comment);
      setComments((current) => ({ ...current, [review.dietPlanId]: '' }));
      await refresh();
    } catch (nextError) {
      setError(nextError.message || 'Unable to request changes.');
    }
  };

  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-5" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Diet Plan Reviews</p>
        <h2 className="mt-2 text-[24px] font-semibold">Senior Consultant review queue</h2>
        <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Review submitted Consultant plans, request focused corrections, or approve the submitted version.</p>
      </Surface>
      {error ? <p className="rounded-[16px] bg-[var(--fluent-color-status-danger-background)] px-4 py-3 text-sm text-[var(--fluent-color-status-danger-foreground)]">{error}</p> : null}
      <Surface className="overflow-hidden border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)]" animated>
        {loading ? <p className="p-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Loading review queue...</p> : reviews.length ? (
          <div className="divide-y divide-[var(--fluent-color-neutral-stroke-1)]">
            {reviews.map((review) => (
              <div key={review.dietPlanId} className="space-y-3 p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{review.clientName}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Consultant: {review.consultantName || 'Assigned Consultant'} · Version {review.version?.versionNumber || '—'}</p>
                  </div>
                  <StatusChip status={review.planStatus === 'changes_requested' ? 'high' : 'pending'}>{review.planStatus === 'changes_requested' ? 'Changes Requested' : 'Pending Review'}</StatusChip>
                </div>
                {review.reviewComment ? <p className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">Previous comment: {review.reviewComment}</p> : null}
                <textarea value={comments[review.dietPlanId] || ''} onChange={(event) => setComments((current) => ({ ...current, [review.dietPlanId]: event.target.value }))} placeholder="Required only when requesting changes" className="min-h-[84px] w-full rounded-[12px] border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3 py-2 text-sm" />
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => void requestChanges(review)} className="rounded-full border border-[var(--fluent-color-status-danger-border)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-status-danger-foreground)]">Request Changes</button>
                  <button type="button" onClick={() => void approve(review)} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-xs font-semibold text-[var(--fluent-color-brand-foreground)]">Approve</button>
                </div>
              </div>
            ))}
          </div>
        ) : <p className="p-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No diet plans are waiting for review.</p>}
      </Surface>
    </div>
  );
}

function ConsultantOperationalOverview({
  metrics,
  appointmentsToday,
  pendingReviews,
  overdueFollowUps,
  attentionClients,
  recentActivity,
  onOpenClient,
  onNavigate,
}) {
  const statCards = [
    { label: 'Today’s appointments', value: appointmentsToday.length, detail: appointmentsToday.length ? `${appointmentsToday[0].clientName} next` : 'No sessions scheduled', tone: appointmentsToday.length ? 'pending' : 'stable' },
    { label: 'Pending plan reviews', value: pendingReviews.length, detail: pendingReviews.length ? 'Drafts are waiting for consultant action' : 'No draft reviews pending', tone: pendingReviews.length ? 'medium' : 'stable' },
    { label: 'Overdue follow-ups', value: overdueFollowUps.length, detail: overdueFollowUps.length ? 'Needs same-cycle follow-through' : 'No overdue follow-ups', tone: overdueFollowUps.length ? 'critical' : 'stable' },
    { label: 'Clients requiring attention', value: attentionClients.length, detail: attentionClients.length ? attentionClients[0].title : 'No urgent attention flags', tone: attentionClients.length ? 'high' : 'stable' },
  ];

  return (
    <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Consultant command center</p>
            <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">Today’s operating picture</h3>
            <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Appointments, reviews, follow-ups, and live client attention signals in one place.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => onNavigate('consultations')} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Open consultations</button>
            <button onClick={() => onNavigate('operations')} className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">View work queue</button>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {statCards.map((item) => (
            <div key={item.label} className="rounded-[20px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
              <div className="flex items-start justify-between gap-3">
                <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">{item.label}</p>
                <StatusChip status={item.tone}>{item.tone === 'stable' ? 'Ready' : formatStatusLabel(item.tone)}</StatusChip>
              </div>
              <p className="mt-4 text-[30px] font-semibold leading-none text-[var(--fluent-color-neutral-foreground-1)]">{item.value}</p>
              <p className="mt-3 text-sm leading-6 text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
            </div>
          ))}
        </div>
      </Surface>

      <div className="grid gap-4">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Quick actions</p>
            <span className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">Action without context switching</span>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {metrics.map((metric) => (
              <button
                key={metric.label}
                onClick={() => metric.target ? onNavigate(metric.target) : undefined}
                className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-left transition hover:border-[var(--fluent-color-brand-stroke-1)]"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{metric.label}</p>
                  <StatusChip status={metric.tone}>{metric.badge}</StatusChip>
                </div>
                <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{metric.detail}</p>
              </button>
            ))}
          </div>
        </Surface>

        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Recent activity</p>
            <button onClick={() => onNavigate('operations')} className="text-sm font-medium text-[var(--fluent-color-brand-foreground-link)]">View full timeline</button>
          </div>
          <div className="mt-4 space-y-3">
            {recentActivity.length ? recentActivity.slice(0, 4).map((item) => (
              <div key={item.id} className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
                  </div>
                  <StatusChip status={item.tone || 'stable'}>{formatDateLabel(item.createdAt)}</StatusChip>
                </div>
              </div>
            )) : (
              <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No recent workflow activity yet. Your appointment, notes, and follow-up actions will appear here.
              </div>
            )}
          </div>
        </Surface>
      </div>

      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 xl:col-span-2" animated>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Clients requiring attention</p>
            <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Live Fiteatsy clients surfaced from profile completion, reports, biomarker status, and recent activity.</p>
          </div>
          <button onClick={() => onNavigate('clients')} className="text-sm font-medium text-[var(--fluent-color-brand-foreground-link)]">Open client directory</button>
        </div>
        <div className="mt-4 grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
          {attentionClients.length ? attentionClients.slice(0, 4).map((client) => (
            <button key={client.clientId} onClick={() => onOpenClient(client.clientId)} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-left transition hover:border-[var(--fluent-color-brand-stroke-1)]">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.goal}</p>
                </div>
                <StatusChip status={client.tone}>{formatStatusLabel(client.tone)}</StatusChip>
              </div>
              <p className="mt-3 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.title}</p>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.reason}</p>
              <p className="mt-3 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Last touch: {client.lastTouch}</p>
            </button>
          )) : (
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)] xl:col-span-4">
              No active attention signals yet. The live Fiteatsy client roster is stable right now.
            </div>
          )}
        </div>
      </Surface>
    </div>
  );
}

function ConsultationManagementPage({
  appointments,
  consultationNotes,
  clients,
  onCreateAppointment,
  onSaveNotes,
  onCompleteAppointment,
  onCreateFollowUp,
  onOpenClient,
}) {
  const [selectedAppointmentId, setSelectedAppointmentId] = useState(appointments[0]?.id || null);
  const [draft, setDraft] = useState({ clientId: clients[0]?.id || '', date: getTodayDateKey(), time: '11:00', mode: 'Video', objective: '' });
  const [noteDraft, setNoteDraft] = useState({ subjective: '', objective: '', assessment: '', actions: '', followUpPlan: '' });

  useEffect(() => {
    if (!appointments.length) {
      setSelectedAppointmentId(null);
      return;
    }
    if (!selectedAppointmentId || !appointments.some((item) => item.id === selectedAppointmentId)) {
      setSelectedAppointmentId(appointments[0].id);
    }
  }, [appointments, selectedAppointmentId]);

  const selectedAppointment = appointments.find((item) => item.id === selectedAppointmentId) || appointments[0];
  const selectedNote = selectedAppointment ? consultationNotes[selectedAppointment.clientId] : null;

  useEffect(() => {
    setNoteDraft({
      subjective: selectedNote?.subjective || '',
      objective: selectedNote?.objective || '',
      assessment: selectedNote?.assessment || '',
      actions: selectedNote?.actions || '',
      followUpPlan: selectedNote?.followUpPlan || '',
    });
  }, [selectedNote?.actions, selectedNote?.assessment, selectedNote?.followUpPlan, selectedNote?.objective, selectedNote?.subjective]);

  function submitAppointment(event) {
    event.preventDefault();
    if (!draft.clientId || !draft.date || !draft.time) return;
    onCreateAppointment(draft);
    setDraft((current) => ({ ...current, objective: '' }));
  }

  function submitNotes(event) {
    event.preventDefault();
    if (!selectedAppointment?.clientId) return;
    onSaveNotes(selectedAppointment.clientId, noteDraft);
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.78fr_1.22fr]">
      <div className="space-y-4">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Consultations</p>
              <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">Preparation, notes, and follow-through</h3>
            </div>
            <StatusChip status={appointments.length ? 'pending' : 'stable'}>{appointments.length} open</StatusChip>
          </div>
          <div className="mt-4 space-y-3">
            {appointments.length ? appointments.map((appointment) => (
              <button
                key={appointment.id}
                onClick={() => setSelectedAppointmentId(appointment.id)}
                className={`w-full rounded-[18px] border px-4 py-4 text-left transition ${
                  appointment.id === selectedAppointmentId
                    ? 'border-[var(--fluent-color-brand-stroke-1)] bg-[rgba(59,130,246,0.08)]'
                    : 'border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{appointment.clientName}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{appointment.objective || 'Consultation objective not set yet.'}</p>
                  </div>
                  <StatusChip status={appointment.status}>{appointment.mode}</StatusChip>
                </div>
                <p className="mt-3 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{formatDateLabel(appointment.date)} • {formatTimeLabel(appointment.time)}</p>
              </button>
            )) : (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No consultation appointments are scheduled yet.
              </div>
            )}
          </div>
        </Surface>

        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Schedule consultation</p>
          <form onSubmit={submitAppointment} className="mt-4 space-y-3">
            <select value={draft.clientId} onChange={(event) => setDraft((current) => ({ ...current, clientId: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none">
              <option value="">Select client</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>{client.name}</option>
              ))}
            </select>
            <div className="grid gap-3 sm:grid-cols-2">
              <input type="date" value={draft.date} onChange={(event) => setDraft((current) => ({ ...current, date: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
              <input type="time" value={draft.time} onChange={(event) => setDraft((current) => ({ ...current, time: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <select value={draft.mode} onChange={(event) => setDraft((current) => ({ ...current, mode: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none">
                <option>Video</option>
                <option>Call</option>
                <option>In-person</option>
              </select>
              <input type="text" value={draft.objective} onChange={(event) => setDraft((current) => ({ ...current, objective: event.target.value }))} placeholder="Objective: report review, plan check-in, follow-up" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
            </div>
            <button type="submit" className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Create appointment</button>
          </form>
        </Surface>
      </div>

      <div className="space-y-4">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          {selectedAppointment ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Consultation workspace</p>
                  <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">{selectedAppointment.clientName}</h3>
                  <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{selectedAppointment.objective || 'Structured consultation capture for this client.'}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => onOpenClient(selectedAppointment.clientId)} className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">Open client</button>
                  <button onClick={() => onCompleteAppointment(selectedAppointment.id)} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Mark complete</button>
                </div>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <DetailField label="Date" value={formatDateLabel(selectedAppointment.date)} />
                <DetailField label="Time" value={formatTimeLabel(selectedAppointment.time)} />
                <DetailField label="Mode" value={selectedAppointment.mode} />
                <DetailField label="Status" value={formatStatusLabel(selectedAppointment.status)} />
              </div>
              <form onSubmit={submitNotes} className="mt-4 grid gap-3 lg:grid-cols-2">
                {[
                  ['subjective', 'Subjective'],
                  ['objective', 'Objective'],
                  ['assessment', 'Assessment'],
                  ['actions', 'Actions'],
                ].map(([key, label]) => (
                  <label key={key} className="block">
                    <span className="mb-2 block text-xs font-medium uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">{label}</span>
                    <textarea value={noteDraft[key]} onChange={(event) => setNoteDraft((current) => ({ ...current, [key]: event.target.value }))} className="min-h-[124px] w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none" />
                  </label>
                ))}
                <label className="block lg:col-span-2">
                  <span className="mb-2 block text-xs font-medium uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Next follow-up</span>
                  <textarea value={noteDraft.followUpPlan} onChange={(event) => setNoteDraft((current) => ({ ...current, followUpPlan: event.target.value }))} className="min-h-[84px] w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm text-[var(--fluent-color-neutral-foreground-1)] outline-none" />
                </label>
                <div className="flex flex-wrap gap-2 lg:col-span-2">
                  <button type="submit" className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Save notes</button>
                  <button type="button" onClick={() => onCreateFollowUp(selectedAppointment.clientId, noteDraft.followUpPlan || 'Follow-up required after consultation.')} className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">Create follow-up</button>
                </div>
              </form>
            </>
          ) : (
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-5 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
              Select or create a consultation to open the structured workspace.
            </div>
          )}
        </Surface>
      </div>
    </div>
  );
}

function TasksTimelinePage({ tasks, followUps, recentActivity, onToggleTask, onResolveFollowUp, onCreateTask, clients, onOpenClient }) {
  const [draft, setDraft] = useState({ clientId: clients[0]?.id || '', title: '', dueDate: getTodayDateKey(), category: 'Follow-up' });

  function submitTask(event) {
    event.preventDefault();
    if (!draft.clientId || !draft.title) return;
    onCreateTask(draft);
    setDraft((current) => ({ ...current, title: '' }));
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-4">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Operational queue</p>
              <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">Tasks and follow-ups</h3>
            </div>
            <StatusChip status={followUps.some((item) => item.status === 'overdue') ? 'critical' : 'stable'}>
              {tasks.length + followUps.length} open items
            </StatusChip>
          </div>
          <div className="mt-4 space-y-3">
            {[...tasks, ...followUps].length ? [...tasks, ...followUps].map((item) => (
              <div key={item.id} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.title || item.reason}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.clientName}</p>
                  </div>
                  <StatusChip status={item.status}>{formatStatusLabel(item.status)}</StatusChip>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">
                  <span className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-3 py-1.5">{item.category || 'Follow-up'}</span>
                  <span className="rounded-full bg-[var(--fluent-color-neutral-background-1)] px-3 py-1.5">Due {formatDateLabel(item.dueDate)}</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button onClick={() => onOpenClient(item.clientId)} className="rounded-full border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] px-3 py-2 text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">Open client</button>
                  <button onClick={() => ('reason' in item ? onResolveFollowUp(item.id) : onToggleTask(item.id))} className="rounded-full bg-[var(--fluent-color-brand-background)] px-3 py-2 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">
                    {'reason' in item ? 'Resolve follow-up' : item.status === 'done' ? 'Reopen task' : 'Mark done'}
                  </button>
                </div>
              </div>
            )) : (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">
                No consultant tasks or follow-ups are open right now.
              </div>
            )}
          </div>
        </Surface>

        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Create task</p>
          <form onSubmit={submitTask} className="mt-4 space-y-3">
            <select value={draft.clientId} onChange={(event) => setDraft((current) => ({ ...current, clientId: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none">
              <option value="">Select client</option>
              {clients.map((client) => <option key={client.id} value={client.id}>{client.name}</option>)}
            </select>
            <input type="text" value={draft.title} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} placeholder="Task title" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
            <div className="grid gap-3 sm:grid-cols-2">
              <input type="date" value={draft.dueDate} onChange={(event) => setDraft((current) => ({ ...current, dueDate: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
              <input type="text" value={draft.category} onChange={(event) => setDraft((current) => ({ ...current, category: event.target.value }))} placeholder="Category" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
            </div>
            <button type="submit" className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Add task</button>
          </form>
        </Surface>
      </div>

      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Unified client timeline</p>
            <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Consultation activity, manual follow-through, and system milestones together.</p>
          </div>
          <StatusChip status="stable">{recentActivity.length} events</StatusChip>
        </div>
        <div className="mt-4 space-y-3">
          {recentActivity.length ? recentActivity.map((item) => (
            <div key={item.id} className="rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.title}</p>
                  <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.detail}</p>
                  {item.clientName ? <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{item.clientName}</p> : null}
                </div>
                <StatusChip status={item.tone || 'stable'}>{formatDateLabel(item.createdAt)}</StatusChip>
              </div>
            </div>
          )) : (
            <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No timeline events yet.</div>
          )}
        </div>
      </Surface>
    </div>
  );
}

function GoalsProgressPage({ clients, attentionClients, onOpenClient }) {
  const aggregate = {
    total: clients.length,
    completed: clients.filter((client) => client.profileCompleted).length,
    reports: clients.reduce((sum, client) => sum + (client.reportsCount || 0), 0),
    activeGoals: clients.filter((client) => client.goal).length,
  };

  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Goals and progress intelligence</p>
            <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.02em] text-[var(--fluent-color-neutral-foreground-1)]">Baseline, current state, and attention signals</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">Profiles complete {aggregate.completed}/{aggregate.total}</span>
            <span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">Reports {aggregate.reports}</span>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Registered clients</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{aggregate.total}</p></div>
          <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Goals captured</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{aggregate.activeGoals}</p></div>
          <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Need profile completion</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{aggregate.total - aggregate.completed}</p></div>
          <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Attention signals</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{attentionClients.length}</p></div>
        </div>
      </Surface>
      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Client progress scan</p>
          <div className="mt-4 space-y-3">
            {clients.length ? clients.slice(0, 8).map((client) => (
              <button key={client.id} onClick={() => onOpenClient(client.id)} className="grid w-full gap-3 rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-left transition hover:border-[var(--fluent-color-brand-stroke-1)] md:grid-cols-[1fr_0.9fr_0.9fr_0.8fr]">
                <div>
                  <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                  <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.goal || 'Goal not captured yet'}</p>
                </div>
                <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">Baseline: {client.profileCompleted ? 'Profile complete' : 'Registration only'}</div>
                <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">Current: {client.reportsCount ? `${client.reportsCount} report${client.reportsCount === 1 ? '' : 's'}` : 'No reports yet'}</div>
                <div><StatusChip status={client.profileCompleted ? 'improving' : 'medium'}>{client.profileCompleted ? 'Profile ready' : 'Needs profile'}</StatusChip></div>
              </button>
            )) : (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No client progress data available yet.</div>
            )}
          </div>
        </Surface>
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Attention signals</p>
          <div className="mt-4 space-y-3">
            {attentionClients.length ? attentionClients.map((item) => (
              <button key={item.clientId} onClick={() => onOpenClient(item.clientId)} className="w-full rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-left transition hover:border-[var(--fluent-color-brand-stroke-1)]">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{item.name}</p>
                    <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.title}</p>
                  </div>
                  <StatusChip status={item.tone}>{formatStatusLabel(item.tone)}</StatusChip>
                </div>
                <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.reason}</p>
              </button>
            )) : (
              <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No active attention signals right now.</div>
            )}
          </div>
        </Surface>
      </div>
    </div>
  );
}

function ConsultantPracticePage({
  clients,
  consultantProfile,
  consultantAvailability,
  onProfileSave,
  onAvailabilitySave,
}) {
  const [profileDraft, setProfileDraft] = useState(consultantProfile);
  const [availabilityDraft, setAvailabilityDraft] = useState(consultantAvailability);

  useEffect(() => {
    setProfileDraft(consultantProfile);
  }, [consultantProfile]);

  useEffect(() => {
    setAvailabilityDraft(consultantAvailability);
  }, [consultantAvailability]);

  const completionRate = clients.length ? Math.round((clients.filter((client) => client.profileCompleted).length / clients.length) * 100) : 0;
  const reportCoverage = clients.length ? Math.round((clients.filter((client) => (client.reportsCount || 0) > 0).length / clients.length) * 100) : 0;

  return (
    <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="space-y-4">
        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Consultant reports</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Portfolio size</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{clients.length}</p></div>
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Profile completion</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{completionRate}%</p></div>
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Report coverage</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{reportCoverage}%</p></div>
            <div className="rounded-[18px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4"><p className="text-xs uppercase tracking-[0.12em] text-[var(--fluent-color-neutral-foreground-3)]">Open diet workflows</p><p className="mt-3 text-[30px] font-semibold text-[var(--fluent-color-neutral-foreground-1)]">{clients.filter((client) => client.profileCompleted).length}</p></div>
          </div>
        </Surface>

        <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Availability</p>
          <div className="mt-4 space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <input type="time" value={availabilityDraft.startTime} onChange={(event) => setAvailabilityDraft((current) => ({ ...current, startTime: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
              <input type="time" value={availabilityDraft.endTime} onChange={(event) => setAvailabilityDraft((current) => ({ ...current, endTime: event.target.value }))} className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
            </div>
            <input type="text" value={availabilityDraft.breakBufferMinutes} onChange={(event) => setAvailabilityDraft((current) => ({ ...current, breakBufferMinutes: event.target.value }))} placeholder="Break buffer (minutes)" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
            <div className="flex flex-wrap gap-2">
              {weekdayLabels.map((day) => {
                const selected = availabilityDraft.workingDays.includes(day);
                return (
                  <button key={day} type="button" onClick={() => setAvailabilityDraft((current) => ({
                    ...current,
                    workingDays: selected ? current.workingDays.filter((item) => item !== day) : [...current.workingDays, day],
                  }))} className={`rounded-full px-3 py-2 text-sm font-medium ${selected ? 'bg-[var(--fluent-color-brand-background)] text-[var(--fluent-color-brand-foreground)]' : 'bg-[var(--fluent-color-neutral-background-2)] text-[var(--fluent-color-neutral-foreground-2)]'}`}>
                    {day}
                  </button>
                );
              })}
            </div>
            <button onClick={() => onAvailabilitySave(availabilityDraft)} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Save availability</button>
          </div>
        </Surface>
      </div>

      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Consultant profile</p>
        <div className="mt-4 space-y-3">
          <input type="text" value={profileDraft.specialisation} onChange={(event) => setProfileDraft((current) => ({ ...current, specialisation: event.target.value }))} placeholder="Specialisation" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
          <input type="text" value={profileDraft.consultationStyle} onChange={(event) => setProfileDraft((current) => ({ ...current, consultationStyle: event.target.value }))} placeholder="Consultation style" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
          <input type="text" value={profileDraft.responseWindow} onChange={(event) => setProfileDraft((current) => ({ ...current, responseWindow: event.target.value }))} placeholder="Response window" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
          <input type="text" value={profileDraft.consultationCadence} onChange={(event) => setProfileDraft((current) => ({ ...current, consultationCadence: event.target.value }))} placeholder="Typical follow-up cadence" className="w-full rounded-[16px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-3 text-sm outline-none" />
          <button onClick={() => onProfileSave(profileDraft)} className="rounded-full bg-[var(--fluent-color-brand-background)] px-4 py-2.5 text-sm font-medium text-[var(--fluent-color-brand-foreground)]">Save profile</button>
        </div>
      </Surface>
    </div>
  );
}

function ProtocolLibraryPage({ clients }) {
  const protocols = [
    { title: 'PCOS Stabilization', useCases: 'Cycle irregularity, insulin resistance, inflammatory cravings', outcomes: 'Stabilize energy, reduce symptom volatility, protect adherence' },
    { title: 'Burnout Recovery', useCases: 'Sleep debt, work overload, meal timing disruption', outcomes: 'Reduce decision fatigue and rebuild recovery cadence' },
    { title: 'Late Dinner Correction', useCases: 'HbA1c drift, rebound hunger, post-travel disruption', outcomes: 'Move carb density earlier and simplify evenings' },
    { title: 'Thyroid Recovery', useCases: 'Fatigue persistence, recovery lag, routine inconsistency', outcomes: 'Protect morning anchors and reduce long fasting gaps' },
  ];

  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Protocol Library</p>
        <h2 className="mt-2 text-[24px] font-semibold tracking-[-0.02em]">Reusable intervention systems</h2>
        <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Protocol blocks keep adaptations structured, measurable, and easier to reuse across similar recovery patterns.</p>
      </Surface>

      <div className="grid gap-4 xl:grid-cols-2">
        {protocols.map((protocol, index) => (
          <Surface key={protocol.title} className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
            <div className="flex items-center justify-between gap-3">
              <p className="text-lg font-semibold">{protocol.title}</p>
              <StatusChip status={index % 2 === 0 ? 'medium' : 'improving'}>{index % 2 === 0 ? 'Adaptive' : 'Stable'}</StatusChip>
            </div>
            <p className="mt-3 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Use cases: {protocol.useCases}</p>
            <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Expected outcomes: {protocol.outcomes}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {clients.slice(index * 2, index * 2 + 3).map((client) => (
                <span key={client.id} className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1.5 text-xs text-[var(--fluent-color-neutral-foreground-2)]">{client.name}</span>
              ))}
            </div>
          </Surface>
        ))}
      </div>
    </div>
  );
}

function CommunicationHubPage({ clients, threads, onClientOpen }) {
  const feed = clients.slice(0, 5).flatMap((client) =>
    buildChatMessages(client).slice(0, 2).map((message) => ({
      ...message,
      clientName: client.name,
      clientId: client.id,
    }))
  );

  return (
    <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Communication Hub</p>
        <h2 className="mt-2 text-[24px] font-semibold tracking-[-0.02em]">Unified communication stream</h2>
        <div className="mt-4 space-y-3">
          {feed.map((item) => (
            <button key={item.id} onClick={() => onClientOpen(item.clientId)} className="w-full rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-left transition hover:border-[var(--fluent-color-neutral-stroke-2)] hover:bg-[#f7f9fc]">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{item.clientName}</p>
                  <StatusChip status={item.role === 'ai' ? 'medium' : item.role === 'consultant' ? 'pending' : 'stable'}>{item.type}</StatusChip>
                </div>
                <p className="text-xs text-[var(--fluent-color-neutral-foreground-3)]">{item.time}</p>
              </div>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{item.text}</p>
            </button>
          ))}
        </div>
      </Surface>

      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Operational Threads</p>
        <div className="mt-4 space-y-3">
          {threads.map((thread) => (
            <div key={thread.id} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{thread.title}</p>
                <StatusChip status={thread.unread ? 'high' : 'stable'}>{thread.unread} unread</StatusChip>
              </div>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{thread.latest}</p>
              <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{thread.participants.join(' • ')}</p>
            </div>
          ))}
        </div>
      </Surface>
    </div>
  );
}

function IntelligencePage({ clients, organizationSignals }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Intervention Intelligence</p>
        <div className="mt-4 space-y-3">
          {clients.slice(0, 5).map((client) => (
            <div key={client.id} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
              <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
              <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.behavioralCorrelation}</p>
              <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Historical memory: {client.conditionFocus.action}</p>
            </div>
          ))}
        </div>
      </Surface>

      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Organizational Intelligence</p>
        <div className="mt-4 space-y-3">
          {organizationSignals.map((org) => (
            <div key={org.name} className="rounded-[18px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{org.name}</p>
                <StatusChip status={org.highRisk > 20 ? 'critical' : org.highRisk > 10 ? 'high' : 'medium'}>{org.highRisk} high-risk</StatusChip>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {org.signals.map((signal) => (
                  <StatusChip key={signal.label} status={signal.status}>{signal.label} {signal.delta}</StatusChip>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Surface>
    </div>
  );
}

function OrganizationsPage({ organizationSignals }) {
  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Organizations</p>
        <h2 className="mt-2 text-[24px] font-semibold tracking-[-0.02em]">Population recovery operations</h2>
        <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Watch organization-level recovery drift, escalation density, and adherence direction without exposing deep individual clinical detail.</p>
      </Surface>

      <Surface className="overflow-hidden border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <div className="grid grid-cols-[1.2fr_0.8fr_0.9fr_0.9fr_0.9fr] gap-3 border-b border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-inset)] px-4 py-3 text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">
          <span>Organization</span>
          <span>High Risk</span>
          <span>Burnout</span>
          <span>Sleep</span>
          <span>Hydration</span>
        </div>
        <div className="divide-y divide-[var(--fluent-color-neutral-stroke-1)]">
          {organizationSignals.map((org) => (
            <div key={org.name} className="grid grid-cols-[1.2fr_0.8fr_0.9fr_0.9fr_0.9fr] gap-3 px-4 py-4">
              <div>
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{org.name}</p>
                <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">Recovery cluster summary</p>
              </div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{org.highRisk}</div>
              <div><StatusChip status={org.signals[0]?.status}>{org.signals[0]?.delta}</StatusChip></div>
              <div><StatusChip status={org.signals[1]?.status}>{org.signals[1]?.delta}</StatusChip></div>
              <div><StatusChip status={org.signals[2]?.status}>{org.signals[2]?.delta}</StatusChip></div>
            </div>
          ))}
        </div>
      </Surface>
    </div>
  );
}

function PlatformWorkspace({ forcedRole }) {
  const { user, logout } = useAuth();
  const resolvedRole = forcedRole || user?.role || 'consultant';
  const roleKind = getRoleKind(resolvedRole);
  const isSeniorConsultant = String(resolvedRole).toLowerCase() === 'senior_consultant';
  const isSuperAdmin = superAdminRoles.has(String(resolvedRole).toLowerCase());
  const canManageProfessionalAssignments = assignmentManagerRoles.has(String(resolvedRole).toLowerCase());
  const canManageConsultantNutrition = roleKind === 'consultant' && consultantNutritionRoles.has(String(resolvedRole).toLowerCase());
  const [brandView, setBrandView] = useState('All Brands');
  const usesRealFiteatsyClients = roleKind === 'consultant' || brandView === 'Fiteatsy';
  const [state, setState] = useState(() => {
    if (usesRealFiteatsyClients) return buildEmptyPlatformState();

    const initial = buildInitialPlatformState();
    return {
      ...initial,
      plans: initial.plans.map((plan) => {
        const employee = initial.employees.find((item) => item.id === plan.employeeId);
        return {
          ...plan,
          dietRows: buildDietSheetRows(employee, plan),
        };
      }),
    };
  });
  const [nav, setNav] = useState(() => (roleKind === 'consultant' ? 'command-center' : usesRealFiteatsyClients ? 'clients' : 'command-center'));
  const [timeframe, setTimeframe] = useState('Week');
  const [globalSearch, setGlobalSearch] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeQueue, setActiveQueue] = useState('assigned');
  const [selectedClientId, setSelectedClientId] = useState('emp-1');
  const [clientWorkspaceTab, setClientWorkspaceTab] = useState('Overview');
  const [clientDrawerOpen, setClientDrawerOpen] = useState(false);
  const [queueConsoleMode, setQueueConsoleMode] = useState('closed');
  const [queueSheetOpen, setQueueSheetOpen] = useState(false);
  const [noteDraft, setNoteDraft] = useState('');
  const [noteType, setNoteType] = useState(noteTypeOptions[0]);
  const [noteSeverity, setNoteSeverity] = useState('medium');
  const [editingBlockId, setEditingBlockId] = useState(null);
  const [editingBlockText, setEditingBlockText] = useState('');
  const [aiDraftModalOpen, setAiDraftModalOpen] = useState(false);
  const [aiDraftStatus, setAiDraftStatus] = useState('idle');
  const [aiDraftProgress, setAiDraftProgress] = useState(0);
  const [aiDraftStageLabel, setAiDraftStageLabel] = useState(aiDraftProgressStages[0].label);
  const [fiteatsyClients, setFiteatsyClients] = useState([]);
  const [fiteatsyClientsLoading, setFiteatsyClientsLoading] = useState(false);
  const [fiteatsyClientsError, setFiteatsyClientsError] = useState(null);
  const [medicationExceptionFeed, setMedicationExceptionFeed] = useState({ summary: null, exceptions: [] });
  const [medicationExceptionsLoading, setMedicationExceptionsLoading] = useState(false);
  const [medicationExceptionsError, setMedicationExceptionsError] = useState(null);
  const [medicationExceptionAcknowledgingId, setMedicationExceptionAcknowledgingId] = useState(null);
  const [realClientDrawerOpen, setRealClientDrawerOpen] = useState(false);
  const [realClientProfile, setRealClientProfile] = useState(null);
  const [realClientProfileLoading, setRealClientProfileLoading] = useState(false);
  const [realClientProfileError, setRealClientProfileError] = useState(null);
  const consultantWorkspaceStorageKey = useMemo(
    () => `${consultantWorkspaceStoragePrefix}${user?.id || user?.email || resolvedRole || 'consultant'}`,
    [resolvedRole, user?.email, user?.id]
  );
  const [consultantWorkspace, setConsultantWorkspace] = useState(() => createDefaultConsultantWorkspaceState());

  useEffect(() => {
    if (roleKind !== 'consultant') return;
    setConsultantWorkspace(readConsultantWorkspaceState(consultantWorkspaceStorageKey));
  }, [consultantWorkspaceStorageKey, roleKind]);

  useEffect(() => {
    if (roleKind !== 'consultant' || typeof window === 'undefined') return;
    window.localStorage.setItem(consultantWorkspaceStorageKey, JSON.stringify(consultantWorkspace));
  }, [consultantWorkspace, consultantWorkspaceStorageKey, roleKind]);

  useEffect(() => {
    if (selectedClientId) {
      window.localStorage.setItem('nuetra:last-active-client', selectedClientId);
    }
  }, [selectedClientId]);

  useEffect(() => {
    const savedClientId = window.localStorage.getItem('nuetra:last-active-client');
    if (savedClientId) setSelectedClientId(savedClientId);
  }, []);

  useEffect(() => {
    function handleKeydown(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === 'Escape') {
        setSearchOpen(false);
      }
    }

    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, []);

  useEffect(() => {
    if (!aiDraftModalOpen || aiDraftStatus !== 'generating') return undefined;

    let index = 0;
    const sequence = aiDraftProgressStages;
    setAiDraftProgress(0);
    setAiDraftStageLabel(sequence[0].label);

    const timer = window.setInterval(() => {
      const nextStage = sequence[index];
      if (!nextStage) {
        window.clearInterval(timer);
        return;
      }

      setAiDraftProgress(nextStage.progress);
      setAiDraftStageLabel(nextStage.label);
      index += 1;

      if (index >= sequence.length) {
        window.clearInterval(timer);
        generateDraft();
        setAiDraftStatus('complete');
      }
    }, 480);

    return () => window.clearInterval(timer);
  }, [aiDraftModalOpen, aiDraftStatus]);

  useEffect(() => {
    if (!usesRealFiteatsyClients) return undefined;

    let cancelled = false;
    setFiteatsyClientsLoading(true);
    setFiteatsyClientsError(null);

    listFiteatsyConsultantClients()
      .then(({ clients: apiClients }) => {
        if (cancelled) return;
        setFiteatsyClients(apiClients);
      })
      .catch((error) => {
        if (cancelled) return;
        setFiteatsyClients([]);
        setFiteatsyClientsError(error);
      })
      .finally(() => {
        if (cancelled) return;
        setFiteatsyClientsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [usesRealFiteatsyClients]);

  const refreshMedicationExceptionFeed = useCallback(async () => {
    setMedicationExceptionsLoading(true);
    setMedicationExceptionsError(null);
    try {
      const payload = await listFiteatsyConsultantMedicationExceptions();
      setMedicationExceptionFeed(payload);
      return payload;
    } catch (error) {
      setMedicationExceptionFeed({ summary: null, exceptions: [] });
      setMedicationExceptionsError(error);
      return null;
    } finally {
      setMedicationExceptionsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!usesRealFiteatsyClients || roleKind !== 'consultant') {
      setMedicationExceptionFeed({ summary: null, exceptions: [] });
      setMedicationExceptionsError(null);
      return undefined;
    }

    let cancelled = false;
    setMedicationExceptionsLoading(true);
    setMedicationExceptionsError(null);

    listFiteatsyConsultantMedicationExceptions()
      .then((payload) => {
        if (cancelled) return;
        setMedicationExceptionFeed(payload);
      })
      .catch((error) => {
        if (cancelled) return;
        setMedicationExceptionFeed({ summary: null, exceptions: [] });
        setMedicationExceptionsError(error);
      })
      .finally(() => {
        if (cancelled) return;
        setMedicationExceptionsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [roleKind, usesRealFiteatsyClients]);

  useEffect(() => {
    const source = usesRealFiteatsyClients ? 'API' : 'MOCK';
    const activeClients = usesRealFiteatsyClients ? fiteatsyClients : state.employees;
    console.info('CLIENT DATA SOURCE:', source);
    console.info('CLIENT COUNT:', activeClients.length);
    console.info('FIRST CLIENT:', activeClients[0]?.name || 'NONE');
  }, [fiteatsyClients, state.employees, usesRealFiteatsyClients]);

  useEffect(() => {
    if (!usesRealFiteatsyClients || !realClientDrawerOpen || !selectedClientId) return undefined;

    let cancelled = false;
    setRealClientProfileLoading(true);
    setRealClientProfileError(null);

    fetchRealClientWorkspace(selectedClientId)
      .then((payload) => {
        if (cancelled) return;
        setRealClientProfile(payload);
      })
      .catch((error) => {
        if (cancelled) return;
        setRealClientProfile(null);
        setRealClientProfileError(error);
      })
      .finally(() => {
        if (cancelled) return;
        setRealClientProfileLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [realClientDrawerOpen, selectedClientId, usesRealFiteatsyClients]);

  const refreshRealClientProfile = useCallback(async (clientId) => {
    const payload = await fetchRealClientWorkspace(clientId);
    setRealClientProfile(payload);
    setRealClientProfileError(null);
    return payload;
  }, []);

  const mockClients = useMemo(() => buildClientRecords(state), [state]);
  const realFiteatsyClients = useMemo(() => buildFiteatsyClientRecords(fiteatsyClients), [fiteatsyClients]);
  const allClients = useMemo(() => (usesRealFiteatsyClients ? realFiteatsyClients : mockClients), [mockClients, realFiteatsyClients, usesRealFiteatsyClients]);
  const clients = useMemo(() => (
    brandView === 'All Brands' ? allClients : allClients.filter((client) => client.brand === brandView)
  ), [allClients, brandView]);
  const selectedClient = useMemo(() => allClients.find((client) => client.id === selectedClientId) || allClients[0], [allClients, selectedClientId]);
  const selectedPlan = useMemo(() => state.plans.find((plan) => plan.employeeId === selectedClient?.id), [selectedClient, state.plans]);
  const roleName = getRoleDisplayName(resolvedRole);
  const topNavItems = roleKind === 'consultant' ? (isSeniorConsultant ? seniorConsultantNav : consultantNav) : roleKind === 'mentor' ? mentorNav : (isSuperAdmin ? adminNav : adminNav.filter((item) => item.id !== 'people'));
  const adminHeader = brandView === 'Fiteatsy'
    ? {
        title: 'User Intelligence',
        subtitle: 'Client-level recovery visibility, plan mix, and quality for Fiteatsy.'
      }
    : {
        title: 'Organization intelligence',
        subtitle: 'Population-level recovery visibility and consultant performance.'
      };

  const consultantAttentionClients = useMemo(
    () => (usesRealFiteatsyClients ? clients.map(buildConsultantAttentionItem).filter((item) => item.tone !== 'stable').slice(0, 8) : []),
    [clients, usesRealFiteatsyClients]
  );

  const consultantAppointmentsToday = useMemo(
    () => consultantWorkspace.appointments.filter((item) => item.date === getTodayDateKey() && item.status !== 'completed'),
    [consultantWorkspace.appointments]
  );

  const consultantPendingReviews = useMemo(
    () => consultantWorkspace.tasks.filter((item) => item.category === 'Plan review' && item.status !== 'done'),
    [consultantWorkspace.tasks]
  );

  const consultantOverdueFollowUps = useMemo(
    () => consultantWorkspace.followUps.filter((item) => item.status === 'overdue' || ((getDaysSince(item.dueDate) || 0) > 0 && item.status !== 'completed')),
    [consultantWorkspace.followUps]
  );

  const consultantRecentActivity = useMemo(() => {
    const liveClientEvents = clients.slice(0, 6).map((client) => ({
      id: `client-${client.id}`,
      title: `${client.name} updated`,
      detail: client.trendSummary?.title || 'Client activity synchronized from Fiteatsy.',
      createdAt: client.lastHealthUpdate || client.lastActiveAt || client.registeredAt,
      clientName: client.name,
      tone: client.profileCompleted ? 'improving' : 'medium',
    }));

    return [...(consultantWorkspace.activityLog || []), ...liveClientEvents]
      .filter((item) => item?.createdAt)
      .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt))
      .slice(0, 12);
  }, [clients, consultantWorkspace.activityLog]);

  const consultantQuickActions = useMemo(() => ([
    { label: 'Prepare consultations', detail: consultantAppointmentsToday.length ? `${consultantAppointmentsToday.length} session${consultantAppointmentsToday.length === 1 ? '' : 's'} scheduled today.` : 'Create your first follow-up slot for today.', badge: 'Consult', tone: consultantAppointmentsToday.length ? 'pending' : 'stable', target: 'consultations' },
    { label: 'Review client queue', detail: consultantAttentionClients.length ? `${consultantAttentionClients.length} live clients need attention.` : 'Client roster is currently stable.', badge: 'Clients', tone: consultantAttentionClients.length ? 'high' : 'stable', target: 'clients' },
    { label: 'Resolve follow-ups', detail: consultantOverdueFollowUps.length ? `${consultantOverdueFollowUps.length} overdue follow-up${consultantOverdueFollowUps.length === 1 ? '' : 's'} need action.` : 'No overdue follow-ups at the moment.', badge: 'Ops', tone: consultantOverdueFollowUps.length ? 'critical' : 'stable', target: 'operations' },
    { label: 'Update practice profile', detail: consultantWorkspace.profile.specialisation ? 'Your consultant profile is already configured.' : 'Add specialisation and availability before the next client round.', badge: 'Profile', tone: consultantWorkspace.profile.specialisation ? 'improving' : 'medium', target: 'practice' },
  ]), [consultantAppointmentsToday.length, consultantAttentionClients.length, consultantOverdueFollowUps.length, consultantWorkspace.profile.specialisation]);

  const consultantProgressClients = useMemo(
    () => (usesRealFiteatsyClients ? clients.filter((client) => client.profileCompleted || client.reportsCount || client.goal) : []),
    [clients, usesRealFiteatsyClients]
  );

  const consultantAvailability = consultantWorkspace.availability;
  const consultantProfile = consultantWorkspace.profile;

  const queueViews = useMemo(() => {
    if (usesRealFiteatsyClients) {
      const pendingReviewClientIds = new Set(consultantPendingReviews.map((item) => item.clientId));
      return [
        { key: 'assigned', title: 'Assigned clients', subtitle: 'All clients assigned to the authenticated Consultant.', tone: 'stable', filter: () => true },
        { key: 'needs_review', title: 'Needs Review', subtitle: 'Profile or report review is needed before the next intervention.', tone: 'medium', filter: (client) => !client.profileCompleted || (client.reportsCount || 0) > 0 },
        { key: 'ai_draft_ready', title: 'AI Draft Ready', subtitle: 'Consultant-created review tasks are waiting in the queue.', tone: 'pending', filter: (client) => pendingReviewClientIds.has(client.id) },
        { key: 'critical_biomarker_drift', title: 'Critical Biomarker Drift', subtitle: 'Biomarker status indicates a clinical review is needed.', tone: 'critical', filter: (client) => client.biomarkerStatus && !['normal', 'stable', 'not_available'].includes(String(client.biomarkerStatus).toLowerCase()) },
        { key: 'adherence_declining', title: 'Adherence Declining', subtitle: 'Recent health activity is cooling and follow-up may be needed.', tone: 'high', filter: (client) => (getDaysSince(client.lastHealthUpdate || client.lastActiveAt || client.registeredAt) || 0) > 14 },
        { key: 'burnout_escalation', title: 'Burnout Escalation', subtitle: 'Compound profile incompleteness and pending report review need intervention.', tone: 'high', filter: (client) => !client.profileCompleted && (client.reportsCount || 0) > 0 },
      ];
    }

    const definitions = [
      {
        key: 'needs_review',
        title: 'Needs Review',
        subtitle: 'Active plan or report decisions waiting on consultant judgment',
        tone: 'pending',
        filter: (client) => ['consultant_review', 'consultant_modified', 'senior_review'].includes(client.planStatus),
      },
      {
        key: 'ai_draft_ready',
        title: 'AI Draft Ready',
        subtitle: 'Draft generated and ready for block-by-block editing',
        tone: 'medium',
        filter: (client) => client.planStatus === 'draft_generated',
      },
      {
        key: 'critical_biomarker_drift',
        title: 'Critical Biomarker Drift',
        subtitle: 'Worsening biomarkers with likely action needed now',
        tone: 'critical',
        filter: (client) => client.biomarkers.some((item) => item.status === 'critical' || item.status === 'declining'),
      },
      {
        key: 'adherence_declining',
        title: 'Adherence Declining',
        subtitle: 'Behavioral consistency is dropping and may affect outcomes',
        tone: 'high',
        filter: (client) => client.adherenceScore < 60,
      },
      {
        key: 'burnout_escalation',
        title: 'Burnout Escalation',
        subtitle: 'Recovery risk is rising and mentor coordination is needed',
        tone: 'critical',
        filter: (client) => client.burnoutRisk === 'critical' || client.burnoutRisk === 'high',
      },
      {
        key: 'pending_senior_review',
        title: 'Pending Senior Review',
        subtitle: 'Consultant work completed and queued for senior approval',
        tone: 'pending',
        filter: (client) => client.planStatus === 'senior_review',
      },
      {
        key: 'inactive_clients',
        title: 'Inactive Clients',
        subtitle: 'Follow-up momentum is cooling and recent activity is low',
        tone: 'medium',
        filter: (client) => String(client.lastActivity).toLowerCase().includes('yesterday'),
      },
      {
        key: 'upload_processing',
        title: 'Upload Processing',
        subtitle: 'Report pipeline is moving and may need review soon',
        tone: 'medium',
        filter: (client) => client.reports.some((report) => report.ocrState !== 'complete'),
      },
      {
        key: 'high_risk_cluster',
        title: 'High-Risk Cluster',
        subtitle: 'Multiple compounding signals across stress, biomarkers, and adherence',
        tone: 'high',
        filter: (client) => client.riskLevel === 'critical' || (client.riskLevel === 'high' && client.adherenceScore < 70),
      },
      {
        key: 'recovery_momentum_improving',
        title: 'Recovery Momentum Improving',
        subtitle: 'Useful benchmark set for intervention memory and similar profiles',
        tone: 'improving',
        filter: (client) => client.recovery > 68 && client.adherenceScore > 70,
      },
    ];

    return definitions.map((definition) => ({
      ...definition,
      count: clients.filter(definition.filter).length,
    }));
  }, [clients, consultantPendingReviews, usesRealFiteatsyClients]);

  useEffect(() => {
    if (queueViews.some((view) => view.key === activeQueue)) return;
    setActiveQueue(usesRealFiteatsyClients ? 'assigned' : 'needs_review');
  }, [activeQueue, queueViews, usesRealFiteatsyClients]);

  const filteredClients = useMemo(() => {
    if (usesRealFiteatsyClients) {
      const activeView = queueViews.find((view) => view.key === activeQueue);
      const query = globalSearch.toLowerCase();
      return clients.filter((client) => {
        const matchesQueue = activeView ? activeView.filter(client) : true;
        const haystack = [
          client.name,
          client.email,
          client.mobile,
          client.mobileNumberMasked,
          client.organization,
          client.recoveryStage,
          client.packageLabel,
          client.lastActivity,
          client.goal,
          client.gender,
          client.accountStatus,
          ...(client.conditions || []),
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return matchesQueue && haystack.includes(query);
      });
    }

    const activeView = queueViews.find((view) => view.key === activeQueue);
    return clients.filter((client) => {
      const matchesQueue = activeView ? activeView.filter(client) : true;
      const haystack = `${client.name} ${client.organization} ${client.region} ${client.conditions.join(' ')} ${client.biomarkers.map((item) => item.name).join(' ')}`.toLowerCase();
      const matchesSearch = haystack.includes(globalSearch.toLowerCase());
      return matchesQueue && matchesSearch;
    });
  }, [activeQueue, clients, globalSearch, queueViews, usesRealFiteatsyClients]);

  const priorityQueue = useMemo(() => {
    if (usesRealFiteatsyClients) {
      return consultantAttentionClients.map((client, index) => ({
        clientId: client.clientId,
        name: client.name,
        title: client.title,
        why: client.reason,
        drivers: [client.title, client.reason].filter(Boolean),
        risk: client.tone,
        action: client.reason,
        confidence: client.tone === 'high' ? 84 : client.tone === 'medium' ? 72 : 60,
        evidence: {
          reports: clients.find((item) => item.id === client.clientId)?.reportsCount || 0,
          adherence: clients.find((item) => item.id === client.clientId)?.profileCompleted ? 'Profile complete' : 'Onboarding pending',
        },
        momentum: { label: index === 0 ? 'Needs action' : 'Review recommended' },
        adherenceScore: clients.find((item) => item.id === client.clientId)?.profileCompleted ? 78 : 46,
        lastActivity: client.lastTouch,
        owner: roleName,
        score: 100 - index * 8,
        temporalState: 'follow-up pending',
      }));
    }

    return clients
      .map((client) => ({
        clientId: client.id,
        name: client.name,
        title: client.trendSummary.title,
        why: client.trendSummary.explanation,
        drivers: client.conditionFocus.drivers.slice(0, 3),
        risk: client.riskLevel,
        action: client.trendSummary.action,
        confidence: client.confidence,
        evidence: {
          reports: client.reports.length,
          adherence: `${client.interventions.length * 7}-day adherence trend`,
        },
        momentum: client.recoveryMomentum,
        adherenceScore: client.adherenceScore,
        lastActivity: client.lastActivity,
        owner: client.mentorName,
        score:
          (client.riskLevel === 'critical' ? 4 : client.riskLevel === 'high' ? 3 : client.riskLevel === 'medium' ? 2 : 1) * 100 +
          (100 - client.adherenceScore) +
          (100 - client.recovery),
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);
  }, [clients, consultantAttentionClients, roleName, usesRealFiteatsyClients]);

  const dailySummary = useMemo(() => {
    if (usesRealFiteatsyClients) {
      return [
        `${clients.length} registered Fiteatsy clients`,
        `${consultantAttentionClients.length} clients need consultant attention`,
        `${consultantAppointmentsToday.length} consultations scheduled today`,
        `${consultantOverdueFollowUps.length} overdue follow-ups need closure`,
      ];
    }

    const worseningGlucose = clients.filter((client) => client.biomarkers.some((item) => item.name === 'HbA1c' && (item.status === 'declining' || item.status === 'critical'))).length;
    const burnoutCluster = clients.filter((client) => client.organization === 'Zenith Forge' && (client.burnoutRisk === 'critical' || client.burnoutRisk === 'high')).length;
    const improvingAdherence = clients.filter((client) => client.adherenceScore >= 70).length;
    const awaitingApproval = state.plans.filter((plan) => ['senior_review', 'consultant_modified'].includes(plan.state)).length;
    return [
      `${worseningGlucose} HbA1c cases worsening`,
      `Burnout cluster detected in Zenith Forge (${burnoutCluster} high-risk employees)`,
      `Adherence improving across ${improvingAdherence} employees`,
      `${awaitingApproval} plans awaiting approval`,
    ];
  }, [clients, consultantAppointmentsToday.length, consultantAttentionClients.length, consultantOverdueFollowUps.length, state.plans, usesRealFiteatsyClients]);

  const healthMovement = useMemo(() => ({
    period: timeframe,
    items: usesRealFiteatsyClients ? [
      { label: 'Clients registered', value: String(clients.length), delta: 'Live API', comparison: 'Registered Fiteatsy clients available in consultant workspace', spark: [0, 0, 0, 0, 0, 0, clients.length], color: '#1E88E5', status: 'stable' },
      { label: 'Programs', value: 'Not available', delta: 'Pending M2', comparison: 'Program assignment will appear after care-plan synchronization', spark: [0, 0, 0, 0, 0, 0, 0], color: '#637CEF', status: 'stable' },
      { label: 'Adherence', value: 'Not available', delta: 'Pending M2', comparison: 'Adherence metrics are not available yet', spark: [0, 0, 0, 0, 0, 0, 0], color: '#1E88E5', status: 'stable' },
      { label: 'Biomarker drift', value: 'Not available', delta: 'Pending M2', comparison: 'Clinical trend intelligence is not available yet', spark: [0, 0, 0, 0, 0, 0, 0], color: '#FB8C00', status: 'stable' },
      { label: 'Burnout risk', value: 'Not available', delta: 'Pending M2', comparison: 'Behavioral recovery risk is not available yet', spark: [0, 0, 0, 0, 0, 0, 0], color: '#5C6BC0', status: 'stable' },
    ] : [
      { label: 'Clients improving', value: '42', delta: '+6 WoW', comparison: 'More clients are moving into recovery gains', spark: [16, 19, 24, 28, 35, 39, 42], color: '#2E7D32', status: 'improving' },
      { label: 'Clients declining', value: '11', delta: '-2 WoW', comparison: 'Fewer clients are sliding backward this week', spark: [18, 16, 15, 14, 12, 12, 11], color: '#EF5350', status: 'declining' },
      { label: 'Adherence', value: '+4%', delta: '+4% WoW', comparison: 'Meal and hydration consistency is trending upward', spark: [48, 49, 51, 52, 53, 54, 56], color: '#1E88E5', status: 'improving' },
      { label: 'Burnout risk', value: '-7%', delta: '-7% WoW', comparison: 'High-risk burnout cases are easing modestly', spark: [22, 21, 20, 19, 18, 17, 15], color: '#FB8C00', status: 'stable' },
      { label: 'Sleep consistency', value: '+5%', delta: '+5% WoW', comparison: 'Routine stability is improving across coached cohorts', spark: [44, 45, 46, 47, 48, 49, 51], color: '#5C6BC0', status: 'improving' },
    ],
  }), [clients.length, timeframe, usesRealFiteatsyClients]);

  const organizationSignals = useMemo(() => {
    if (usesRealFiteatsyClients) {
      return [{
        name: 'Fiteatsy',
        highRisk: 0,
        signals: [
          { label: 'Review intelligence', delta: '0', status: 'stable' },
          { label: 'Adherence trend', delta: '0', status: 'stable' },
          { label: 'Biomarker drift', delta: '0', status: 'stable' },
        ],
      }];
    }

    const byOrg = clients.reduce((acc, client) => {
      if (!acc[client.organization]) acc[client.organization] = [];
      acc[client.organization].push(client);
      return acc;
    }, {});

    return Object.entries(byOrg).map(([name, orgClients]) => ({
      name,
      highRisk: orgClients.filter((client) => client.riskLevel === 'critical' || client.riskLevel === 'high').length,
      signals: [
        { label: 'Burnout Risk', delta: '+12%', status: 'high' },
        { label: 'Sleep Consistency', delta: '-8%', status: 'declining' },
        { label: 'Hydration', delta: '-6%', status: 'declining' },
      ],
    }));
  }, [clients, usesRealFiteatsyClients]);

  const uploadPipeline = useMemo(() => state.reportPipeline.slice(0, 4), [state.reportPipeline]);
  const reviewPipeline = useMemo(() => state.plans.filter((plan) => ['consultant_review', 'consultant_modified', 'senior_review'].includes(plan.state)).slice(0, 4).map((plan) => ({
    employeeName: plan.employeeName,
    state: plan.state,
    stateLabel: formatStatusLabel(plan.state),
  })), [state.plans]);
  const briefingMeta = useMemo(() => {
    if (usesRealFiteatsyClients) {
      return `${clients.length} registered clients • live API data only`;
    }
    return `Last ${timeframe === 'Day' ? '24 hours' : timeframe === 'Week' ? '7 days' : timeframe === 'Month' ? '30 days' : timeframe === 'Quarter' ? '90 days' : 'custom range'} • ${clients.length} active clients monitored`;
  }, [clients.length, timeframe, usesRealFiteatsyClients]);
  const clusters = useMemo(() => {
    if (usesRealFiteatsyClients) {
      return [
        { title: 'Needs Review', subtitle: 'Awaiting backend review intelligence', count: 0, status: 'stable' },
        { title: 'AI Draft Ready', subtitle: 'Awaiting backend AI draft pipeline', count: 0, status: 'stable' },
        { title: 'Critical Biomarker Drift', subtitle: 'Awaiting biomarker timeline synchronization', count: 0, status: 'stable' },
        { title: 'Adherence Declining', subtitle: 'Awaiting adherence synchronization', count: 0, status: 'stable' },
      ];
    }
    return [
      { title: 'HbA1c Risk Cluster', subtitle: 'Worsening glucose movement and low adherence', count: clients.filter((client) => client.biomarkers.some((item) => item.name === 'HbA1c' && (item.status === 'declining' || item.status === 'critical'))).length, status: 'critical' },
      { title: 'Burnout Escalations', subtitle: 'Recovery overload and sleep inconsistency', count: clients.filter((client) => client.burnoutRisk === 'critical' || client.burnoutRisk === 'high').length, status: 'high' },
      { title: 'Adherence Decline >20%', subtitle: 'Behavioral consistency dropped materially', count: clients.filter((client) => client.adherenceScore < 60).length, status: 'medium' },
      { title: 'Sleep Recovery Issues', subtitle: 'Sleep debt affecting stress and recovery', count: clients.filter((client) => client.sleepQuality < 60).length, status: 'medium' },
    ];
  }, [clients, usesRealFiteatsyClients]);

  const searchResults = useMemo(() => {
    const query = globalSearch.trim().toLowerCase();
    const clientMatches = allClients
      .filter((client) => !query || `${client.name} ${client.organization} ${client.brand} ${client.packageLabel} ${client.conditions.join(' ')} ${client.region} ${client.dietaryStyle} ${client.recoveryStage} ${client.department || ''} ${(client.symptomProfile || []).join(' ')}`.toLowerCase().includes(query))
      .slice(0, 5)
      .map((client) => ({
        id: `search-client-${client.id}`,
        kind: 'client',
        title: client.name,
        subtitle: `${client.brand} • ${client.packageLabel} • ${client.trendSummary.title}`,
        status: client.riskLevel,
        meta: client.planStatus,
        targetClientId: client.id,
        targetTab: 'Overview',
      }));

    const reportMatches = allClients.flatMap((client) =>
      client.reports
        .filter((report) => !query || `${report.name} ${report.lab} ${report.ocrState}`.toLowerCase().includes(query))
        .map((report) => ({
          id: `search-report-${report.id}`,
          kind: 'report',
          title: report.name,
          subtitle: `${client.name} • ${report.lab} • ${report.ocrState}`,
          status: report.ocrState === 'complete' ? 'improving' : 'medium',
          meta: `${report.extractionConfidence}%`,
          targetClientId: client.id,
          targetTab: 'Reports',
        }))
    ).slice(0, 5);

    const noteMatches = allClients.flatMap((client) =>
      buildInternalNotes(client)
        .filter((note) => !query || `${note.text} ${note.type} ${note.linkedBiomarker}`.toLowerCase().includes(query))
        .map((note) => ({
          id: `search-note-${note.id}`,
          kind: 'note',
          title: note.type,
          subtitle: `${client.name} • ${note.text}`,
          status: note.severity,
          meta: note.linkedBiomarker,
          targetClientId: client.id,
          targetTab: 'Notes',
        }))
    ).slice(0, 5);

    const taskMatches = state.tasks
      .filter((task) => !query || task.title.toLowerCase().includes(query))
      .slice(0, 5)
      .map((task) => ({
        id: `search-task-${task.id}`,
        kind: 'task',
        title: task.title,
        subtitle: `${task.owner} • due ${task.due}`,
        status: task.status,
        meta: task.owner.split(' ')[0],
        targetClientId: allClients[0]?.id,
        targetTab: 'Overview',
      }));

    const biomarkerMatches = allClients.flatMap((client) =>
      client.biomarkers
        .filter((item) => !query || `${item.name} ${item.current} ${item.status}`.toLowerCase().includes(query))
        .map((item) => ({
          id: `search-bio-${client.id}-${item.name}`,
          kind: 'biomarker',
          title: `${item.name} • ${item.current}`,
          subtitle: `${client.name} • ${item.status}`,
          status: item.status,
          meta: client.brand === 'Nuetra' ? client.organization : client.packageLabel,
          targetClientId: client.id,
          targetTab: 'Biomarkers',
        }))
    ).slice(0, 5);

    return [
      { label: 'Clients', items: clientMatches },
      { label: 'Reports', items: reportMatches },
      { label: 'Biomarkers', items: biomarkerMatches },
      { label: 'Notes', items: noteMatches },
      { label: 'Tasks', items: taskMatches },
    ];
  }, [allClients, globalSearch, state.tasks]);

  const pulseItems = useMemo(() => {
    if (usesRealFiteatsyClients) {
      return [
        { label: 'Needs Review', value: queueViews.find((view) => view.key === 'needs_review')?.count || 0, delta: 'Live roster', status: 'medium', spark: [1, 2, 2, 3, 3, 4, queueViews.find((view) => view.key === 'needs_review')?.count || 0], color: '#637CEF', targetQueue: 'needs_review' },
        { label: 'AI Draft Ready', value: queueViews.find((view) => view.key === 'ai_draft_ready')?.count || 0, delta: 'Consultant queue', status: 'pending', spark: [0, 0, 1, 1, 1, 2, queueViews.find((view) => view.key === 'ai_draft_ready')?.count || 0], color: '#1E88E5', targetQueue: 'ai_draft_ready' },
        { label: 'Critical Biomarker Drift', value: queueViews.find((view) => view.key === 'critical_biomarker_drift')?.count || 0, delta: 'Live biomarker state', status: 'critical', spark: [0, 1, 1, 1, 2, 2, queueViews.find((view) => view.key === 'critical_biomarker_drift')?.count || 0], color: '#D13438', targetQueue: 'critical_biomarker_drift' },
        { label: 'Adherence Declining', value: queueViews.find((view) => view.key === 'adherence_declining')?.count || 0, delta: 'Activity aging', status: 'high', spark: [0, 0, 1, 1, 1, 1, queueViews.find((view) => view.key === 'adherence_declining')?.count || 0], color: '#FFB900', targetQueue: 'adherence_declining' },
        { label: 'Burnout Escalation', value: queueViews.find((view) => view.key === 'burnout_escalation')?.count || 0, delta: 'Compounding profile gaps', status: 'high', spark: [0, 0, 0, 1, 1, 1, queueViews.find((view) => view.key === 'burnout_escalation')?.count || 0], color: '#FF8C00', targetQueue: 'burnout_escalation' },
      ];
    }
    return [
      { label: 'Worsening', value: clusters[0]?.count || 0, delta: '+4 WoW', status: 'critical', spark: [8, 10, 11, 12, 13, 14, clusters[0]?.count || 14], color: '#D13438', targetQueue: 'critical_biomarker_drift' },
      { label: 'Pending Reviews', value: reviewPipeline.length, delta: '-3 WoW', status: 'pending', spark: [9, 8, 7, 7, 6, 5, reviewPipeline.length || 5], color: '#637CEF', targetQueue: 'needs_review' },
      { label: 'Inactive', value: queueViews.find((view) => view.key === 'inactive_clients')?.count || 0, delta: '+1 WoW', status: 'medium', spark: [2, 2, 3, 3, 4, 4, queueViews.find((view) => view.key === 'inactive_clients')?.count || 4], color: '#FFB900', targetQueue: 'inactive_clients' },
      { label: 'Improving', value: clients.filter((client) => client.recoveryMomentum.status === 'improving').length, delta: '+6 WoW', status: 'improving', spark: [16, 19, 24, 28, 35, 39, clients.filter((client) => client.recoveryMomentum.status === 'improving').length || 39], color: '#107C10', targetQueue: 'recovery_momentum_improving' },
      { label: 'Critical Escalations', value: clients.filter((client) => client.riskLevel === 'critical').length, delta: '+2 WoW', status: 'high', spark: [3, 4, 4, 5, 5, 6, clients.filter((client) => client.riskLevel === 'critical').length || 6], color: '#FF8C00', targetQueue: 'burnout_escalation' },
    ];
  }, [clients, clusters, queueViews, reviewPipeline.length, usesRealFiteatsyClients]);

  const workloadItems = useMemo(() => (
    usesRealFiteatsyClients
      ? [
          { label: 'Pending reviews', value: consultantPendingReviews.length, detail: consultantPendingReviews.length ? 'Consultant-created plan review tasks are waiting in the queue.' : 'No consultant-created plan reviews are waiting right now.', status: consultantPendingReviews.length ? 'pending' : 'stable' },
          { label: 'Unresolved escalations', value: consultantAttentionClients.length, detail: consultantAttentionClients.length ? 'Live Fiteatsy clients need consultant judgement before the next care step.' : 'No unresolved live escalations at the moment.', status: consultantAttentionClients.length ? 'high' : 'stable' },
          { label: 'Overdue follow-ups', value: consultantOverdueFollowUps.length, detail: consultantOverdueFollowUps.length ? 'Follow-up commitments are overdue and need closure.' : 'No overdue follow-ups in the consultant queue.', status: consultantOverdueFollowUps.length ? 'critical' : 'stable' },
          { label: 'Today’s appointments', value: consultantAppointmentsToday.length, detail: consultantAppointmentsToday.length ? 'Scheduled sessions are ready for preparation and note capture.' : 'No consultations are scheduled for today yet.', status: consultantAppointmentsToday.length ? 'medium' : 'stable' },
        ]
      : [
          { label: 'Pending reviews', value: reviewPipeline.length, detail: 'Drafts and report interpretations waiting for consultant judgment.', status: 'pending' },
          { label: 'Unresolved escalations', value: clients.filter((client) => client.riskLevel === 'critical').length, detail: 'Critical cases still requiring consultant or mentor follow-through.', status: 'critical' },
          { label: 'Overdue follow-ups', value: clients.filter((client) => client.adherenceScore < 60).length, detail: 'Low adherence cases at risk of slipping further without intervention.', status: 'high' },
          { label: 'Active critical cases', value: priorityQueue.filter((item) => item.risk === 'critical').length, detail: 'Biomarker drift or recovery decline needs same-cycle action.', status: 'critical' },
        ]
  ), [clients, consultantAppointmentsToday.length, consultantAttentionClients.length, consultantOverdueFollowUps.length, consultantPendingReviews.length, priorityQueue, reviewPipeline.length, usesRealFiteatsyClients]);

  const memoryItems = useMemo(() => (
    usesRealFiteatsyClients
      ? [
          { title: 'Client roster', detail: `${clients.length} Fiteatsy clients are available from the live consultant API.` },
          { title: 'Consultation memory', detail: consultantWorkspace.activityLog.length ? `${consultantWorkspace.activityLog.length} consultant workflow events are retained in local operational memory.` : 'Consultation notes, follow-ups, and tasks will accumulate here as you work.' },
          { title: 'Care readiness', detail: consultantAttentionClients.length ? `${consultantAttentionClients.length} clients need a targeted review before the next nutrition move.` : 'No critical consultant attention signals are active right now.' },
        ]
      : [
          { title: 'Emerging pattern', detail: `Late dinner timing is emerging across ${clusters[0]?.count || 0} worsening HbA1c cases.` },
          { title: 'Behavioral learning', detail: 'Hydration-first recovery improved adherence by 18% in similar corporate stress profiles.' },
          { title: 'Fiteatsy learning', detail: 'Hormonal recovery clients respond better when breakfast complexity is reduced before supplement intensification.' },
        ]
  ), [clients.length, clusters, consultantAttentionClients.length, consultantWorkspace.activityLog.length, usesRealFiteatsyClients]);

  const railItems = useMemo(() => {
    if (usesRealFiteatsyClients) {
      return consultantRecentActivity.slice(0, 5).map((item) => ({
        title: item.title,
        detail: item.detail,
        status: item.tone || 'stable',
        badge: item.clientName || 'Live API',
      }));
    }
    const alertItems = state.recoveryAlerts.slice(0, 2).map((alert) => ({
      title: alert.employee,
      detail: alert.alert,
      status: 'critical',
      badge: 'Alert',
    }));
    const escalationItems = priorityQueue.slice(0, 2).map((item) => ({
      title: item.name,
      detail: item.action,
      status: item.risk,
      badge: `${item.confidence}%`,
    }));
    const memory = memoryItems.slice(0, 2).map((item) => ({
      ...item,
      status: 'medium',
      badge: 'Pattern',
    }));
    return [...alertItems, ...escalationItems, ...memory];
  }, [consultantRecentActivity, memoryItems, priorityQueue, state.recoveryAlerts, usesRealFiteatsyClients]);

  function openClient(clientId, targetTab = 'Overview') {
    if (usesRealFiteatsyClients) {
      setSelectedClientId(clientId);
      setRealClientDrawerOpen(true);
      setSearchOpen(false);
      return;
    }
    setSelectedClientId(clientId);
    setClientWorkspaceTab(targetTab);
    setClientDrawerOpen(true);
    setSearchOpen(false);
  }

  function handleSearchResultSelect(item, fallbackTab = 'Overview') {
    if (item.targetClientId) {
      openClient(item.targetClientId, item.targetTab || fallbackTab);
      return;
    }
    setSearchOpen(false);
  }

  function openPulseQueue(item) {
    if (!item?.targetQueue) return;
    setActiveQueue(item.targetQueue);
    setNav('clients');
    setSearchOpen(false);
  }

  function createConsultantAppointment(draft) {
    const client = clients.find((item) => item.id === draft.clientId);
    if (!client) return;
    setConsultantWorkspace((current) =>
      appendConsultantWorkspaceActivity(
        {
          ...current,
          appointments: [
            {
              id: createWorkspaceId('appt'),
              clientId: client.id,
              clientName: client.name,
              date: draft.date,
              time: draft.time,
              mode: draft.mode,
              objective: draft.objective,
              status: 'scheduled',
              createdAt: new Date().toISOString(),
            },
            ...current.appointments,
          ],
        },
        {
          title: `Consultation scheduled for ${client.name}`,
          detail: `${draft.mode} consultation on ${formatDateLabel(draft.date)} at ${formatTimeLabel(draft.time)}.`,
          clientId: client.id,
          clientName: client.name,
          tone: 'pending',
        }
      )
    );
  }

  function saveConsultationNotes(clientId, draft) {
    const client = clients.find((item) => item.id === clientId);
    setConsultantWorkspace((current) =>
      appendConsultantWorkspaceActivity(
        {
          ...current,
          consultationNotes: {
            ...current.consultationNotes,
            [clientId]: {
              ...draft,
              updatedAt: new Date().toISOString(),
            },
          },
        },
        {
          title: `Consultation notes saved for ${client?.name || 'client'}`,
          detail: 'Structured consultation notes are ready for follow-up planning.',
          clientId,
          clientName: client?.name,
          tone: 'improving',
        }
      )
    );
  }

  function completeConsultationAppointment(appointmentId) {
    setConsultantWorkspace((current) => {
      const appointment = current.appointments.find((item) => item.id === appointmentId);
      return appendConsultantWorkspaceActivity(
        {
          ...current,
          appointments: current.appointments.map((item) => (item.id === appointmentId ? { ...item, status: 'completed', completedAt: new Date().toISOString() } : item)),
        },
        {
          title: `${appointment?.clientName || 'Consultation'} completed`,
          detail: 'Consultation marked complete and ready for next follow-up.',
          clientId: appointment?.clientId,
          clientName: appointment?.clientName,
          tone: 'improving',
        }
      );
    });
  }

  function createConsultantFollowUp(clientId, reason) {
    const client = clients.find((item) => item.id === clientId);
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 3);
    setConsultantWorkspace((current) =>
      appendConsultantWorkspaceActivity(
        {
          ...current,
          followUps: [
            {
              id: createWorkspaceId('followup'),
              clientId,
              clientName: client?.name || 'Client',
              reason,
              dueDate: dueDate.toISOString(),
              status: 'scheduled',
              createdAt: new Date().toISOString(),
            },
            ...current.followUps,
          ],
        },
        {
          title: `Follow-up created for ${client?.name || 'client'}`,
          detail: reason || 'Follow-up scheduled from consultant workspace.',
          clientId,
          clientName: client?.name,
          tone: 'pending',
        }
      )
    );
  }

  async function acknowledgeMedicationException(exceptionId) {
    if (!exceptionId) return;
    setMedicationExceptionAcknowledgingId(exceptionId);
    setMedicationExceptionsError(null);
    try {
      await acknowledgeFiteatsyConsultantMedicationException(exceptionId);
      await refreshMedicationExceptionFeed();
    } catch (error) {
      setMedicationExceptionsError(error);
    } finally {
      setMedicationExceptionAcknowledgingId(null);
    }
  }

  function resolveConsultantFollowUp(followUpId) {
    setConsultantWorkspace((current) => {
      const followUp = current.followUps.find((item) => item.id === followUpId);
      return appendConsultantWorkspaceActivity(
        {
          ...current,
          followUps: current.followUps.map((item) => (item.id === followUpId ? { ...item, status: 'completed', completedAt: new Date().toISOString() } : item)),
        },
        {
          title: `Follow-up closed for ${followUp?.clientName || 'client'}`,
          detail: followUp?.reason || 'Follow-up marked complete.',
          clientId: followUp?.clientId,
          clientName: followUp?.clientName,
          tone: 'improving',
        }
      );
    });
  }

  function createConsultantTask(draft) {
    const client = clients.find((item) => item.id === draft.clientId);
    if (!client) return;
    setConsultantWorkspace((current) =>
      appendConsultantWorkspaceActivity(
        {
          ...current,
          tasks: [
            {
              id: createWorkspaceId('task'),
              clientId: client.id,
              clientName: client.name,
              title: draft.title,
              dueDate: draft.dueDate,
              category: draft.category,
              status: 'open',
              createdAt: new Date().toISOString(),
            },
            ...current.tasks,
          ],
        },
        {
          title: `Task created for ${client.name}`,
          detail: draft.title,
          clientId: client.id,
          clientName: client.name,
          tone: 'pending',
        }
      )
    );
  }

  function toggleConsultantTask(taskId) {
    setConsultantWorkspace((current) => {
      const task = current.tasks.find((item) => item.id === taskId);
      const nextStatus = task?.status === 'done' ? 'open' : 'done';
      return appendConsultantWorkspaceActivity(
        {
          ...current,
          tasks: current.tasks.map((item) => (item.id === taskId ? { ...item, status: nextStatus, updatedAt: new Date().toISOString() } : item)),
        },
        {
          title: `${task?.title || 'Task'} ${nextStatus === 'done' ? 'completed' : 'reopened'}`,
          detail: task?.clientName || 'Consultant task updated.',
          clientId: task?.clientId,
          clientName: task?.clientName,
          tone: nextStatus === 'done' ? 'improving' : 'pending',
        }
      );
    });
  }

  function saveConsultantProfile(profile) {
    setConsultantWorkspace((current) =>
      appendConsultantWorkspaceActivity(
        { ...current, profile },
        {
          title: 'Consultant profile updated',
          detail: 'Specialisation and consultation style were saved.',
          tone: 'improving',
        }
      )
    );
  }

  function saveConsultantAvailability(availability) {
    setConsultantWorkspace((current) =>
      appendConsultantWorkspaceActivity(
        { ...current, availability },
        {
          title: 'Consultant availability updated',
          detail: 'Working hours and response windows were saved.',
          tone: 'improving',
        }
      )
    );
  }

  function openGenerateDraftModal() {
    setAiDraftModalOpen(true);
    setAiDraftStatus('generating');
    setAiDraftProgress(0);
    setAiDraftStageLabel(aiDraftProgressStages[0].label);
  }

  function closeGenerateDraftModal() {
    setAiDraftModalOpen(false);
    setAiDraftStatus('idle');
    setAiDraftProgress(0);
    setAiDraftStageLabel(aiDraftProgressStages[0].label);
  }

  function updateSelectedPlan(mutator) {
    if (!selectedPlan) return;
    setState((current) => ({
      ...current,
      plans: current.plans.map((plan) => (plan.id === selectedPlan.id ? mutator(plan) : plan)),
    }));
  }

  function generateDraft() {
    updateSelectedPlan((plan) => ({
      ...plan,
      state: 'draft_generated',
      updatedAt: 'Just now',
      version: plan.version + 1,
      versions: [
        {
          label: `AI generated v${plan.version + 1}`,
          by: 'Nuetra AI',
          time: 'Just now',
          note: 'Generated using reports, adherence timeline, meal timing history, and intervention memory.',
        },
        ...plan.versions,
      ],
    }));
  }

  function regenerateBlock(blockId) {
    updateSelectedPlan((plan) => ({
      ...plan,
      updatedAt: 'Just now',
      blocks: plan.blocks.map((block) =>
        block.id === blockId
          ? { ...block, content: `${block.content} Updated using similar profile intervention memory and ${selectedClient.region} meal pattern alignment.` }
          : block
      ),
    }));
  }

  function startEditPlanBlock(block) {
    setEditingBlockId(block.id);
    setEditingBlockText(block.content);
  }

  function saveEditPlanBlock() {
    if (!editingBlockId) return;
    updateSelectedPlan((plan) => ({
      ...plan,
      updatedAt: 'Just now',
      version: plan.version + 1,
      blocks: plan.blocks.map((block) => (block.id === editingBlockId ? { ...block, content: editingBlockText } : block)),
      versions: [
        {
          label: `Consultant edited v${plan.version + 1}`,
          by: user?.name || roleName,
          time: 'Just now',
          note: 'Updated plan block manually from client workspace.',
        },
        ...plan.versions,
      ],
    }));
    setEditingBlockId(null);
    setEditingBlockText('');
  }

  function setPlanState(nextState) {
    updateSelectedPlan((plan) => ({
      ...plan,
      state: nextState,
      updatedAt: 'Just now',
      version: plan.version + 1,
      versions: [
        {
          label: `${formatStatusLabel(nextState)} v${plan.version + 1}`,
          by: user?.name || roleName,
          time: 'Just now',
          note: `Plan moved to ${formatStatusLabel(nextState)}.`,
        },
        ...plan.versions,
      ],
    }));
  }

  function updateDietCell(rowId, field, value) {
    updateSelectedPlan((plan) => ({
      ...plan,
      updatedAt: 'Just now',
      dietRows: (plan.dietRows || []).map((row) => (row.id === rowId ? { ...row, [field]: value } : row)),
    }));
  }

  async function exportDietPlanDocx() {
    if (!selectedClient || !selectedPlan) return;

    const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } = await import('docx');
    const modules = buildDietProtocolModules(selectedClient, selectedPlan);
    const documentTitle = selectedClient.brand === 'Fiteatsy' ? 'Fiteatsy Recovery Protocol' : 'Nuetra Recovery Protocol';
    const careContext = selectedClient.brand === 'Fiteatsy'
      ? `${selectedClient.packageName} • ${selectedClient.packageDuration} • ${selectedClient.recoveryStage}`
      : `${selectedClient.organization} • ${selectedClient.department} • ${selectedClient.packageName}`;
    const exportedAt = new Date().toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });

    const bullet = (text, indent = 0) =>
      new Paragraph({
        text,
        bullet: { level: indent },
        spacing: { after: 80 },
      });

    const moduleParagraphs = modules.flatMap((module) => {
      const optionParagraphs = module.options.flatMap((option) => [
        new Paragraph({
          children: [new TextRun({ text: option.name, bold: true })],
          spacing: { before: 140, after: 80 },
        }),
        bullet(`Calories: ${option.calories} • Protein: ${option.protein}g • Fiber: ${option.fiber}g • Glycemic load: ${option.glycemicLoad}`),
        bullet(`Prep time: ${option.prepTime}`),
        bullet(`Alternative: ${option.alternatives}`),
        bullet(`Biomarker linkage: ${option.biomarkerLinkage}`),
      ]);

      return [
        new Paragraph({
          text: module.title,
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 220, after: 100 },
        }),
        new Paragraph({
          children: [new TextRun({ text: 'Protocol Summary: ', bold: true }), new TextRun(module.summary)],
          spacing: { after: 80 },
        }),
        new Paragraph({
          children: [new TextRun({ text: 'Clinical Reasoning: ', bold: true }), new TextRun(module.rationale)],
          spacing: { after: 80 },
        }),
        ...optionParagraphs,
      ];
    });

    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({
              text: documentTitle,
              heading: HeadingLevel.TITLE,
              alignment: AlignmentType.CENTER,
              spacing: { after: 180 },
            }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: `${selectedClient.name} • ${careContext}`, bold: true })],
              spacing: { after: 80 },
            }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              text: exportedAt,
              spacing: { after: 220 },
            }),
            new Paragraph({
              text: 'Client Summary',
              heading: HeadingLevel.HEADING_1,
              spacing: { after: 120 },
            }),
            bullet(`Goals: ${selectedClient.goals.join(', ')}`),
            bullet(`Conditions: ${selectedClient.conditions.join(', ')}`),
            bullet(`Brand and care program: ${selectedClient.brand} • ${selectedClient.packageName} • ${selectedClient.packageDuration}`),
            bullet(`Region and dietary style: ${selectedClient.region} • ${selectedClient.dietaryStyle}`),
            bullet(`Current focus: ${selectedClient.conditionFocus.condition}`),
            bullet(`Latest clinical interpretation: ${selectedClient.trendSummary.title}`),
            bullet(`Suggested action: ${selectedClient.trendSummary.action}`),
            new Paragraph({
              text: 'Daily Target Summary',
              heading: HeadingLevel.HEADING_1,
              spacing: { before: 220, after: 120 },
            }),
            bullet(`Recovery momentum: ${selectedClient.recoveryMomentum.label}`),
            bullet(`Recovery stage: ${selectedClient.recoveryStage}`),
            bullet(`Adherence score: ${selectedClient.adherenceScore}%`),
            bullet(`Hydration: ${selectedClient.hydration}%`),
            bullet(`Sleep quality: ${selectedClient.sleepQuality}%`),
            bullet(`Stress: ${selectedClient.stress}%`),
            new Paragraph({
              text: 'Protocol Modules',
              heading: HeadingLevel.HEADING_1,
              spacing: { before: 220, after: 120 },
            }),
            ...moduleParagraphs,
            new Paragraph({
              text: 'Supplements and Behavioral Goals',
              heading: HeadingLevel.HEADING_1,
              spacing: { before: 220, after: 120 },
            }),
            bullet(`Plan state: ${formatStatusLabel(selectedPlan.state)}`),
            bullet(`Reviewers: ${(selectedPlan.reviewers || []).join(', ') || 'Assigned consultant'}`),
            bullet(`Client-facing recommendation: ${selectedClient.brand === 'Fiteatsy' ? 'keep the routine calming, cycle-supportive, and easy to repeat through recovery fluctuations.' : 'keep the routine practical, culturally familiar, and easy to repeat on work-heavy days.'}`),
          ],
        },
      ],
    });

    const blob = await Packer.toBlob(doc);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedClient.name.toLowerCase().replace(/\s+/g, '-')}-${selectedClient.brand.toLowerCase()}-protocol.docx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  function shareDietPlanViaEmail() {
    if (!selectedClient) return;
    const subject = encodeURIComponent(`${selectedClient.name} - updated diet plan`);
    const body = encodeURIComponent(
      `Hello ${selectedClient.name},\n\nYour updated diet plan has been generated and is ready for review.\n\nKey focus: ${selectedClient.conditionFocus.action}\n\nPlease review the latest protocol and let us know if you need support with adherence.\n\nRegards,\n${user?.name || roleName}`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  }

  function shareDietPlanViaWhatsapp() {
    if (!selectedClient) return;
    const message = encodeURIComponent(
      `Hello ${selectedClient.name}, your updated Nuetra diet plan is ready. Current focus: ${selectedClient.conditionFocus.action} Please review the latest plan and message us if you need support.`
    );
    window.open(`https://wa.me/?text=${message}`, '_blank', 'noopener,noreferrer');
  }

  function addNote() {
    if (!noteDraft.trim()) return;
    setState((current) => ({
      ...current,
      employees: current.employees.map((employee) =>
        employee.id === selectedClient.id
          ? {
              ...employee,
              notes: [
                {
                  author: user?.name || roleName,
                  role: resolvedRole,
                  type: noteType,
                  severity: noteSeverity,
                  tags: [selectedClient.region, selectedClient.dietaryStyle, selectedClient.conditionFocus.condition],
                  linkedBiomarker: selectedClient.biomarkers.find((item) => item.status !== 'stable')?.name || selectedClient.biomarkers[0]?.name,
                  linkedIntervention: selectedClient.interventions[0]?.name || 'Routine support',
                  linkedReport: selectedClient.reports[0]?.name || 'Latest report',
                  text: noteDraft.trim(),
                  time: 'Just now',
                },
                ...employee.notes,
              ],
            }
          : employee
      ),
    }));
    setNoteDraft('');
    setNoteType(noteTypeOptions[0]);
    setNoteSeverity('medium');
  }

  return (
    <div className="min-h-screen bg-[var(--fluent-color-neutral-background-canvas)] text-[var(--fluent-color-neutral-foreground-1)]">
      <TopAppBar
        roleName={roleName}
        timeframe={timeframe}
        setTimeframe={setTimeframe}
        search={globalSearch}
        setSearch={setGlobalSearch}
        onSearchOpen={() => setSearchOpen(true)}
        user={user}
        logout={logout}
        onQuickAction={() => setSearchOpen(true)}
        onResumeWorkspace={usesRealFiteatsyClients ? undefined : () => openClient(selectedClientId, clientWorkspaceTab)}
        resumeLabel={selectedClient?.name}
      />

      <SearchOverlay
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        search={globalSearch}
        setSearch={setGlobalSearch}
        results={searchResults}
        onResultSelect={handleSearchResultSelect}
      />

      <OperationalTopNav
        items={topNavItems}
        active={nav}
        onChange={setNav}
        brandView={brandView}
        setBrandView={setBrandView}
        roleKind={roleKind}
      />

      <div className="mx-auto max-w-[1480px] px-4 py-5 md:px-6 lg:px-8">
        <main className="min-w-0 space-y-4">
          {roleKind === 'consultant' && nav === 'command-center' ? (
            <>
              <CommandCenterPage
                briefingMeta={briefingMeta}
                pulseItems={pulseItems}
                priorityQueue={priorityQueue}
                workloadItems={workloadItems}
                memoryItems={memoryItems}
                railItems={railItems}
                medicationExceptionFeed={medicationExceptionFeed}
                medicationExceptionsLoading={medicationExceptionsLoading}
                medicationExceptionsError={medicationExceptionsError}
                onMedicationExceptionsRefresh={refreshMedicationExceptionFeed}
                onMedicationExceptionAcknowledge={acknowledgeMedicationException}
                medicationExceptionAcknowledgingId={medicationExceptionAcknowledgingId}
                onClientOpen={openClient}
                onCreateFollowUp={createConsultantFollowUp}
                onPulseSelect={openPulseQueue}
              />
              <ConsultantOperationalOverview
                metrics={consultantQuickActions}
                appointmentsToday={consultantAppointmentsToday}
                pendingReviews={consultantPendingReviews}
                overdueFollowUps={consultantOverdueFollowUps}
                attentionClients={consultantAttentionClients}
                recentActivity={consultantRecentActivity}
                onOpenClient={openClient}
                onNavigate={setNav}
              />
            </>
          ) : null}

          {isSeniorConsultant && nav === 'diet-plan-reviews' ? (
            <DietPlanReviewQueuePage />
          ) : null}

          {isSeniorConsultant && nav === 'clients' ? (
            <SeniorConsultantClientAllocationPage currentUserId={user?.id || user?.accountId || ''} />
          ) : roleKind === 'consultant' && nav === 'clients' ? (
            <ClientDirectoryPage
              queueViews={queueViews}
              activeQueue={activeQueue}
              setActiveQueue={setActiveQueue}
              filteredClients={filteredClients}
              totalCount={clients.length}
              onClientOpen={openClient}
              loading={fiteatsyClientsLoading}
              error={fiteatsyClientsError}
              isRealFiteatsy={usesRealFiteatsyClients}
              isAdminDirectory={false}
              canManageAssignments={canManageProfessionalAssignments}
              onAssignClient={canManageProfessionalAssignments ? () => setNav('assignments') : undefined}
            />
          ) : null}

          {roleKind === 'consultant' && nav === 'consultations' ? (
            <ConsultationManagementPage
              appointments={consultantWorkspace.appointments}
              consultationNotes={consultantWorkspace.consultationNotes}
              clients={clients}
              onCreateAppointment={createConsultantAppointment}
              onSaveNotes={saveConsultationNotes}
              onCompleteAppointment={completeConsultationAppointment}
              onCreateFollowUp={createConsultantFollowUp}
              onOpenClient={openClient}
            />
          ) : null}

          {roleKind === 'consultant' && nav === 'operations' ? (
            <TasksTimelinePage
              tasks={consultantWorkspace.tasks}
              followUps={consultantWorkspace.followUps}
              recentActivity={consultantRecentActivity}
              onToggleTask={toggleConsultantTask}
              onResolveFollowUp={resolveConsultantFollowUp}
              onCreateTask={createConsultantTask}
              clients={clients}
              onOpenClient={openClient}
            />
          ) : null}

          {roleKind === 'consultant' && nav === 'progress' ? (
            <GoalsProgressPage
              clients={consultantProgressClients}
              attentionClients={consultantAttentionClients}
              onOpenClient={openClient}
            />
          ) : null}

          {roleKind === 'consultant' && nav === 'practice' ? (
            <ConsultantPracticePage
              clients={clients}
              consultantProfile={consultantProfile}
              consultantAvailability={consultantAvailability}
              onProfileSave={saveConsultantProfile}
              onAvailabilitySave={saveConsultantAvailability}
            />
          ) : null}

          {roleKind === 'consultant' && nav === 'protocols' ? (
            <ProtocolLibraryPage clients={clients} />
          ) : null}

          {roleKind === 'consultant' && nav === 'communication' ? (
            <CommunicationHubPage clients={clients} threads={state.communicationThreads} onClientOpen={openClient} />
          ) : null}

          {roleKind === 'consultant' && nav === 'intelligence' ? (
            <IntelligencePage clients={clients} organizationSignals={organizationSignals} />
          ) : null}

          {roleKind === 'consultant' && nav === 'organizations' ? (
            <OrganizationsPage organizationSignals={organizationSignals} />
          ) : null}

          {roleKind === 'mentor' ? (
            <>
              <CompactPageHeader title="Mentor command center" subtitle="Keep support lightweight, behavioral, and immediate." />
              <MentorHome clients={clients} sessions={state.sessions} tasks={state.tasks.filter((task) => task.owner.includes('Maya'))} />
            </>
          ) : null}

          {roleKind === 'admin' ? (
            <>
              {nav === 'assignments' ? (
                <ProfessionalAssignmentPage />
              ) : nav === 'organizations' ? (
                <OrganizationsPage organizationSignals={organizationSignals} />
              ) : nav === 'people' ? (
                isSuperAdmin ? <SuperAdminPeoplePage /> : <CompactPageHeader title="Restricted" subtitle="Only super admins can manage mentors, consultants, admins, and their authorities." />
              ) : nav === 'clients' && usesRealFiteatsyClients ? (
                <ClientDirectoryPage queueViews={queueViews} activeQueue={activeQueue} setActiveQueue={setActiveQueue} filteredClients={filteredClients} totalCount={clients.length} onClientOpen={openClient} loading={fiteatsyClientsLoading} error={fiteatsyClientsError} isRealFiteatsy={usesRealFiteatsyClients} canManageAssignments={canManageProfessionalAssignments} onAssignClient={() => setNav('assignments')} />
              ) : (
                <>
                  <CompactPageHeader title={adminHeader.title} subtitle={adminHeader.subtitle} />
                  <AdminHome billing={state.finance.billing} revenue={state.finance.revenue} quality={state.quality} brandView={brandView} />
                </>
              )}
            </>
          ) : null}
        </main>
      </div>

      {usesRealFiteatsyClients ? (
        <RealClientProfileDrawer
          isOpen={realClientDrawerOpen}
          onClose={() => setRealClientDrawerOpen(false)}
          summaryClient={selectedClient}
          profile={realClientProfile}
          loading={realClientProfileLoading}
          error={realClientProfileError}
          onProfileRefresh={refreshRealClientProfile}
          onCreateMedicationFollowUp={createConsultantFollowUp}
          onCreateFollowUp={createConsultantFollowUp}
          canManageNutrition={canManageConsultantNutrition}
          canReviewDietPlans={isSeniorConsultant}
          canPublishDietPlans={roleKind === 'consultant'}
        />
      ) : null}

      {roleKind === 'consultant' ? (
        <>
          {!usesRealFiteatsyClients ? (
            <>
              <ClientIntelligenceDrawer
                isOpen={clientDrawerOpen}
                onClose={() => setClientDrawerOpen(false)}
                employee={selectedClient}
                plan={selectedPlan}
                activeTab={clientWorkspaceTab}
                setActiveTab={setClientWorkspaceTab}
                noteDraft={noteDraft}
                setNoteDraft={setNoteDraft}
                noteType={noteType}
                setNoteType={setNoteType}
                noteSeverity={noteSeverity}
                setNoteSeverity={setNoteSeverity}
                onAddNote={addNote}
                onEditPlan={startEditPlanBlock}
                onGenerateDraft={openGenerateDraftModal}
                onRegenerateBlock={regenerateBlock}
                onPlanStateChange={setPlanState}
                onExportDocx={exportDietPlanDocx}
                onDietCellChange={updateDietCell}
              />
              <AIDraftProgressModal
                isOpen={aiDraftModalOpen}
                onClose={closeGenerateDraftModal}
                status={aiDraftStatus}
                progress={aiDraftProgress}
                stageLabel={aiDraftStageLabel}
                clientName={selectedClient?.name}
                onDownload={exportDietPlanDocx}
                onShareEmail={shareDietPlanViaEmail}
                onShareWhatsapp={shareDietPlanViaWhatsapp}
              />
              <QueueConsole
                mode={queueConsoleMode}
                setMode={setQueueConsoleMode}
                queueViews={queueViews}
                activeQueue={activeQueue}
                setActiveQueue={setActiveQueue}
                filteredClients={filteredClients}
                onClientOpen={openClient}
              />
            </>
          ) : null}
          <QueueBottomSheet
            isOpen={queueSheetOpen}
            onClose={() => setQueueSheetOpen(false)}
            queueViews={queueViews}
            activeQueue={activeQueue}
            setActiveQueue={setActiveQueue}
            filteredClients={filteredClients}
            onClientOpen={openClient}
            loading={fiteatsyClientsLoading}
            error={fiteatsyClientsError}
            isRealFiteatsy={usesRealFiteatsyClients}
          />
        </>
      ) : null}
    </div>
  );
}

export default PlatformWorkspace;

export const ConsultantWorkspace = withAuth(() => <PlatformWorkspace forcedRole="consultant" />, DELIVERY_ACCESS_POLICY);
export const SeniorConsultantWorkspace = withAuth(() => <PlatformWorkspace forcedRole="senior_consultant" />, DELIVERY_ACCESS_POLICY);
export const MentorWorkspace = withAuth(() => <PlatformWorkspace forcedRole="mentor" />, MENTOR_ACCESS_POLICY);
export const OrganizationWorkspace = withAuth(() => <PlatformWorkspace forcedRole="organization_admin" />, ORGANIZATION_ACCESS_POLICY);
export const AdminWorkspace = withAuth(() => <PlatformWorkspace forcedRole="admin" />, ADMIN_ACCESS_POLICY);
