import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bell,
  Bot,
  CalendarDays,
  ChevronRight,
  Clock3,
  Command,
  FileBarChart2,
  Filter,
  LayoutGrid,
  ListChecks,
  MessageSquare,
  Search,
  Settings,
  Sparkles,
  TrendingUp,
  Users,
  Wallet,
  X,
} from 'lucide-react';
import withAuth from '../../hocs/withAuth';
import { useAuth } from '../../context/AuthContext';
import { buildInitialPlatformState, getRoleDisplayName } from '../../data/mockPlatformData';
import { corporateAPI } from '../../lib/api';

const roleKinds = {
  consultant: 'consultant',
  provider: 'consultant',
  dietician: 'consultant',
  team_member: 'consultant',
  member: 'consultant',
  senior_consultant: 'consultant',
  admin: 'consultant',
  superuser: 'consultant',
  mentor: 'mentor',
  team_lead: 'mentor',
  organization_admin: 'admin',
  corporate_admin: 'admin',
  corporate_client: 'admin',
};

const consultantNav = [
  { id: 'command-center', label: 'Command Center', icon: LayoutGrid },
  { id: 'clients', label: 'Clients', icon: Users },
  { id: 'protocols', label: 'Protocols', icon: Sparkles },
  { id: 'communication', label: 'Communication', icon: MessageSquare },
  { id: 'intelligence', label: 'Intelligence', icon: TrendingUp },
  { id: 'organizations', label: 'Organizations', icon: FileBarChart2 },
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
  { id: 'intelligence', label: 'Intelligence', icon: TrendingUp },
  { id: 'organizations', label: 'Organizations', icon: FileBarChart2 },
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

function getRoleKind(role) {
  return roleKinds[role] || 'consultant';
}

function formatStatusLabel(value = '') {
  return value.replace(/_/g, ' ');
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
          {resumeLabel ? (
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

function SmartClientQueues({ queueViews, activeQueue, setActiveQueue, filteredClients, onClientOpen, onQueueOpen }) {
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
          {filteredClients.map((client) => (
            <motion.button key={client.id} onClick={() => onClientOpen(client.id)} {...hoverLift} className="grid w-full gap-3 px-4 py-4 text-left transition hover:bg-[var(--fluent-color-neutral-background-2)] lg:grid-cols-[1.5fr_0.7fr_0.7fr_1fr_1fr] lg:items-center">
              <div>
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                <p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.brand} · {client.packageLabel} · {client.brand === 'Nuetra' ? client.organization : client.recoveryStage}</p>
              </div>
              <div><StatusChip status={client.riskLevel}>{client.riskLevel}</StatusChip></div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-1)]">{client.adherenceScore}%</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.mentorName}</div>
              <div><StatusChip status={client.planStatus}>{formatStatusLabel(client.planStatus)}</StatusChip></div>
            </motion.button>
          ))}
        </div>
      </Surface>
    </div>
  );
}

function QueueBottomSheet({ isOpen, onClose, queueViews, activeQueue, setActiveQueue, filteredClients, onClientOpen }) {
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
                  {filteredClients.length ? filteredClients.map((client) => (
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
                        <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.brand} • {client.packageLabel} • {client.mentorName} • {client.adherenceScore}% adherence</p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <StatusChip status={client.riskLevel}>{client.riskLevel}</StatusChip>
                        <StatusChip status={client.planStatus}>{formatStatusLabel(client.planStatus)}</StatusChip>
                      </div>
                    </button>
                  )) : (
                    <div className="rounded-[16px] bg-[var(--fluent-color-neutral-background-2)] px-4 py-4 text-sm text-[var(--fluent-color-neutral-foreground-2)]">No clients match this queue and filter combination.</div>
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

          {submitSuccess?.tempPassword ? (
            <div className="mt-4 rounded-[18px] border border-[var(--fluent-color-status-success-border)] bg-[var(--fluent-color-status-success-background)] p-4">
              <p className="text-sm font-medium text-[var(--fluent-color-status-success-foreground)]">
                {submitSuccess?.consultant?.firstName || 'Consultant'} account created.
              </p>
              <p className="mt-1 text-sm text-[var(--fluent-color-status-success-foreground)]">
                Temporary password: <span className="font-semibold">{submitSuccess.tempPassword}</span>
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

function CommandCenterPage({ briefingMeta, pulseItems, priorityQueue, workloadItems, memoryItems, railItems, onClientOpen, onPulseSelect }) {
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

function ClientDirectoryPage({ queueViews, activeQueue, setActiveQueue, filteredClients, onClientOpen }) {
  return (
    <div className="space-y-4">
      <Surface className="border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-4 text-[var(--fluent-color-neutral-foreground-1)]" animated>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--fluent-color-neutral-foreground-3)]">Client Directory</p>
            <h2 className="mt-2 text-[24px] font-semibold tracking-[-0.02em]">Healthcare operating roster</h2>
            <p className="mt-2 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Filter the client population by risk, momentum, inactivity, and intervention stage before opening the workspace.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {queueViews.slice(0, 5).map((view) => (
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
          {filteredClients.slice(0, 16).map((client) => (
            <button
              key={client.id}
              onClick={() => onClientOpen(client.id)}
              className="grid w-full grid-cols-[1.3fr_0.9fr_1fr_0.8fr_1fr_0.9fr_1.1fr] gap-3 px-4 py-4 text-left transition hover:bg-[var(--fluent-color-neutral-background-2)]"
            >
              <div>
                <p className="text-sm font-medium text-[var(--fluent-color-neutral-foreground-1)]">{client.name}</p>
                <p className="mt-1 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.brand} · {client.organization}</p>
              </div>
              <div className="min-w-0 text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.packageLabel}</div>
              <div className="min-w-0">
                <StatusChip status={client.recoveryMomentum.status}>{client.recoveryMomentum.label}</StatusChip>
                <p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{client.trendSummary.title}</p>
              </div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.adherenceScore}%</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{formatStatusLabel(client.planStatus)}</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.lastActivity}</div>
              <div className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{client.conditionFocus.action.split('.')[0]}</div>
            </button>
          ))}
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
  const [state, setState] = useState(() => {
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
  const [nav, setNav] = useState('command-center');
  const [timeframe, setTimeframe] = useState('Week');
  const [brandView, setBrandView] = useState('All Brands');
  const [globalSearch, setGlobalSearch] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeQueue, setActiveQueue] = useState('needs_review');
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

  const allClients = useMemo(() => buildClientRecords(state), [state]);
  const clients = useMemo(() => (
    brandView === 'All Brands' ? allClients : allClients.filter((client) => client.brand === brandView)
  ), [allClients, brandView]);
  const selectedClient = useMemo(() => allClients.find((client) => client.id === selectedClientId) || allClients[0], [allClients, selectedClientId]);
  const selectedPlan = useMemo(() => state.plans.find((plan) => plan.employeeId === selectedClient?.id), [selectedClient, state.plans]);
  const roleName = getRoleDisplayName(resolvedRole);
  const topNavItems = roleKind === 'consultant' ? consultantNav : roleKind === 'mentor' ? mentorNav : adminNav;
  const adminHeader = brandView === 'Fiteatsy'
    ? {
        title: 'User Intelligence',
        subtitle: 'Client-level recovery visibility, plan mix, and quality for Fiteatsy.'
      }
    : {
        title: 'Organization intelligence',
        subtitle: 'Population-level recovery visibility and consultant performance.'
      };

  const queueViews = useMemo(() => {
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
  }, [clients]);

  const filteredClients = useMemo(() => {
    const activeView = queueViews.find((view) => view.key === activeQueue);
    return clients.filter((client) => {
      const matchesQueue = activeView ? activeView.filter(client) : true;
      const haystack = `${client.name} ${client.organization} ${client.region} ${client.conditions.join(' ')} ${client.biomarkers.map((item) => item.name).join(' ')}`.toLowerCase();
      const matchesSearch = haystack.includes(globalSearch.toLowerCase());
      return matchesQueue && matchesSearch;
    });
  }, [activeQueue, clients, globalSearch, queueViews]);

  const priorityQueue = useMemo(() => {
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
  }, [clients]);

  const dailySummary = useMemo(() => {
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
  }, [clients, state.plans]);

  const healthMovement = useMemo(() => ({
    period: timeframe,
    items: [
      { label: 'Clients improving', value: '42', delta: '+6 WoW', comparison: 'More clients are moving into recovery gains', spark: [16, 19, 24, 28, 35, 39, 42], color: '#2E7D32', status: 'improving' },
      { label: 'Clients declining', value: '11', delta: '-2 WoW', comparison: 'Fewer clients are sliding backward this week', spark: [18, 16, 15, 14, 12, 12, 11], color: '#EF5350', status: 'declining' },
      { label: 'Adherence', value: '+4%', delta: '+4% WoW', comparison: 'Meal and hydration consistency is trending upward', spark: [48, 49, 51, 52, 53, 54, 56], color: '#1E88E5', status: 'improving' },
      { label: 'Burnout risk', value: '-7%', delta: '-7% WoW', comparison: 'High-risk burnout cases are easing modestly', spark: [22, 21, 20, 19, 18, 17, 15], color: '#FB8C00', status: 'stable' },
      { label: 'Sleep consistency', value: '+5%', delta: '+5% WoW', comparison: 'Routine stability is improving across coached cohorts', spark: [44, 45, 46, 47, 48, 49, 51], color: '#5C6BC0', status: 'improving' },
    ],
  }), [timeframe]);

  const organizationSignals = useMemo(() => {
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
  }, [clients]);

  const uploadPipeline = useMemo(() => state.reportPipeline.slice(0, 4), [state.reportPipeline]);
  const reviewPipeline = useMemo(() => state.plans.filter((plan) => ['consultant_review', 'consultant_modified', 'senior_review'].includes(plan.state)).slice(0, 4).map((plan) => ({
    employeeName: plan.employeeName,
    state: plan.state,
    stateLabel: formatStatusLabel(plan.state),
  })), [state.plans]);
  const briefingMeta = useMemo(() => `Last ${timeframe === 'Day' ? '24 hours' : timeframe === 'Week' ? '7 days' : timeframe === 'Month' ? '30 days' : timeframe === 'Quarter' ? '90 days' : 'custom range'} • ${clients.length} active clients monitored`, [clients.length, timeframe]);
  const clusters = useMemo(() => [
    { title: 'HbA1c Risk Cluster', subtitle: 'Worsening glucose movement and low adherence', count: clients.filter((client) => client.biomarkers.some((item) => item.name === 'HbA1c' && (item.status === 'declining' || item.status === 'critical'))).length, status: 'critical' },
    { title: 'Burnout Escalations', subtitle: 'Recovery overload and sleep inconsistency', count: clients.filter((client) => client.burnoutRisk === 'critical' || client.burnoutRisk === 'high').length, status: 'high' },
    { title: 'Adherence Decline >20%', subtitle: 'Behavioral consistency dropped materially', count: clients.filter((client) => client.adherenceScore < 60).length, status: 'medium' },
    { title: 'Sleep Recovery Issues', subtitle: 'Sleep debt affecting stress and recovery', count: clients.filter((client) => client.sleepQuality < 60).length, status: 'medium' },
  ], [clients]);

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

  const pulseItems = useMemo(() => [
    { label: 'Worsening', value: clusters[0]?.count || 0, delta: '+4 WoW', status: 'critical', spark: [8, 10, 11, 12, 13, 14, clusters[0]?.count || 14], color: '#D13438', targetQueue: 'critical_biomarker_drift' },
    { label: 'Pending Reviews', value: reviewPipeline.length, delta: '-3 WoW', status: 'pending', spark: [9, 8, 7, 7, 6, 5, reviewPipeline.length || 5], color: '#637CEF', targetQueue: 'needs_review' },
    { label: 'Inactive', value: queueViews.find((view) => view.key === 'inactive_clients')?.count || 0, delta: '+1 WoW', status: 'medium', spark: [2, 2, 3, 3, 4, 4, queueViews.find((view) => view.key === 'inactive_clients')?.count || 4], color: '#FFB900', targetQueue: 'inactive_clients' },
    { label: 'Improving', value: clients.filter((client) => client.recoveryMomentum.status === 'improving').length, delta: '+6 WoW', status: 'improving', spark: [16, 19, 24, 28, 35, 39, clients.filter((client) => client.recoveryMomentum.status === 'improving').length || 39], color: '#107C10', targetQueue: 'recovery_momentum_improving' },
    { label: 'Critical Escalations', value: clients.filter((client) => client.riskLevel === 'critical').length, delta: '+2 WoW', status: 'high', spark: [3, 4, 4, 5, 5, 6, clients.filter((client) => client.riskLevel === 'critical').length || 6], color: '#FF8C00', targetQueue: 'burnout_escalation' },
  ], [clients, clusters, queueViews, reviewPipeline.length]);

  const workloadItems = useMemo(() => ([
    { label: 'Pending reviews', value: reviewPipeline.length, detail: 'Drafts and report interpretations waiting for consultant judgment.', status: 'pending' },
    { label: 'Unresolved escalations', value: clients.filter((client) => client.riskLevel === 'critical').length, detail: 'Critical cases still requiring consultant or mentor follow-through.', status: 'critical' },
    { label: 'Overdue follow-ups', value: clients.filter((client) => client.adherenceScore < 60).length, detail: 'Low adherence cases at risk of slipping further without intervention.', status: 'high' },
    { label: 'Active critical cases', value: priorityQueue.filter((item) => item.risk === 'critical').length, detail: 'Biomarker drift or recovery decline needs same-cycle action.', status: 'critical' },
  ]), [clients, priorityQueue, reviewPipeline.length]);

  const memoryItems = useMemo(() => ([
    { title: 'Emerging pattern', detail: `Late dinner timing is emerging across ${clusters[0]?.count || 0} worsening HbA1c cases.` },
    { title: 'Behavioral learning', detail: 'Hydration-first recovery improved adherence by 18% in similar corporate stress profiles.' },
    { title: 'Fiteatsy learning', detail: 'Hormonal recovery clients respond better when breakfast complexity is reduced before supplement intensification.' },
  ]), [clusters]);

  const railItems = useMemo(() => {
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
  }, [memoryItems, priorityQueue, state.recoveryAlerts]);

  function openClient(clientId, targetTab = 'Overview') {
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
        onResumeWorkspace={() => openClient(selectedClientId, clientWorkspaceTab)}
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
            <CommandCenterPage
              briefingMeta={briefingMeta}
              pulseItems={pulseItems}
              priorityQueue={priorityQueue}
              workloadItems={workloadItems}
              memoryItems={memoryItems}
              railItems={railItems}
              onClientOpen={openClient}
              onPulseSelect={openPulseQueue}
            />
          ) : null}

          {roleKind === 'consultant' && nav === 'clients' ? (
            <ClientDirectoryPage
              queueViews={queueViews}
              activeQueue={activeQueue}
              setActiveQueue={setActiveQueue}
              filteredClients={filteredClients}
              onClientOpen={openClient}
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
              {nav === 'organizations' ? (
                <OrganizationsPage organizationSignals={organizationSignals} />
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

      {roleKind === 'consultant' ? (
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
          <QueueBottomSheet
            isOpen={queueSheetOpen}
            onClose={() => setQueueSheetOpen(false)}
            queueViews={queueViews}
            activeQueue={activeQueue}
            setActiveQueue={setActiveQueue}
            filteredClients={filteredClients}
            onClientOpen={openClient}
          />
        </>
      ) : null}
    </div>
  );
}

export default PlatformWorkspace;

export const ConsultantWorkspace = withAuth(() => <PlatformWorkspace forcedRole="consultant" />, ['consultant', 'provider', 'dietician', 'team_member', 'member', 'senior_consultant', 'admin', 'superuser']);
export const SeniorConsultantWorkspace = withAuth(() => <PlatformWorkspace forcedRole="senior_consultant" />, ['senior_consultant', 'admin', 'superuser']);
export const MentorWorkspace = withAuth(() => <PlatformWorkspace forcedRole="mentor" />, ['mentor', 'team_lead']);
export const OrganizationWorkspace = withAuth(() => <PlatformWorkspace forcedRole="organization_admin" />, ['organization_admin', 'corporate_admin', 'corporate_client']);
