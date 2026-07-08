import { buildInitialPlatformState } from '../data/mockPlatformData';

const PACKAGE_PRICING = {
  'Reset Program': 12000,
  'Rebalance Program': 24000,
  'Restore Program': 42000,
};

function parseTimestamp(value) {
  if (!value) return null;
  const normalized = String(value).replace(' ', 'T');
  const date = new Date(`${normalized}:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function startOfDay(date) {
  const next = new Date(date);
  next.setHours(0, 0, 0, 0);
  return next;
}

function endOfDay(date) {
  const next = new Date(date);
  next.setHours(23, 59, 59, 999);
  return next;
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function formatDisplayDate(date) {
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
}

function average(values) {
  if (!values.length) return 0;
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

function getAdherenceScore(employee) {
  const values = employee.interventions?.map((item) => item.adherence) || [];
  return average(values);
}

function getAnchorDate(state) {
  const dates = [];

  state.plans.forEach((plan) => {
    const parsed = parseTimestamp(plan.updatedAt);
    if (parsed) dates.push(parsed);
  });

  state.employees.forEach((employee) => {
    employee.reports?.forEach((report) => {
      const parsed = parseTimestamp(report.uploadedAt);
      if (parsed) dates.push(parsed);
    });
  });

  if (!dates.length) {
    return new Date('2026-06-03T00:00:00');
  }

  return new Date(Math.max(...dates.map((date) => date.getTime())));
}

function resolveDateWindow(range, startDate, endDate, anchorDate) {
  const anchor = endOfDay(anchorDate);
  const anchorStart = startOfDay(anchorDate);

  if (range === 'custom' && startDate && endDate) {
    const customStart = startOfDay(new Date(`${startDate}T00:00:00`));
    const customEnd = endOfDay(new Date(`${endDate}T00:00:00`));
    return {
      key: 'custom',
      start: customStart,
      end: customEnd,
      label: `${formatDisplayDate(customStart)} - ${formatDisplayDate(customEnd)}`,
    };
  }

  if (range === 'year') {
    const start = new Date(anchor.getFullYear(), 0, 1);
    const end = new Date(anchor.getFullYear(), 11, 31, 23, 59, 59, 999);
    return {
      key: 'year',
      start,
      end,
      label: String(anchor.getFullYear()),
    };
  }

  if (range === 'quarter') {
    const quarterIndex = Math.floor(anchor.getMonth() / 3);
    const start = new Date(anchor.getFullYear(), quarterIndex * 3, 1);
    const end = new Date(anchor.getFullYear(), quarterIndex * 3 + 3, 0, 23, 59, 59, 999);
    return {
      key: 'quarter',
      start,
      end,
      label: `Q${quarterIndex + 1} ${anchor.getFullYear()}`,
    };
  }

  if (range === 'month') {
    const start = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
    const end = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0, 23, 59, 59, 999);
    return {
      key: 'month',
      start,
      end,
      label: new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric' }).format(anchor),
    };
  }

  const start = new Date(anchorStart);
  start.setDate(start.getDate() - 6);
  return {
    key: 'week',
    start,
    end: anchor,
    label: `${formatDisplayDate(start)} - ${formatDisplayDate(anchor)}`,
  };
}

function buildClientAnalytics(state, dateWindow) {
  const plansByEmployee = Object.fromEntries(state.plans.map((plan) => [plan.employeeId, plan]));

  return state.employees
    .filter((employee) => employee.brand === 'Fiteatsy')
    .map((employee) => {
      const plan = plansByEmployee[employee.id];
      const planDate = parseTimestamp(plan?.updatedAt);
      const reportDates = (employee.reports || []).map((report) => parseTimestamp(report.uploadedAt)).filter(Boolean);
      const latestActivityDate = [planDate, ...reportDates].filter(Boolean).sort((a, b) => b.getTime() - a.getTime())[0] || dateWindow.end;
      const adherenceScore = getAdherenceScore(employee);
      const criticalBiomarkers = employee.biomarkers.filter((item) => item.status === 'critical').length;
      const decliningBiomarkers = employee.biomarkers.filter((item) => item.status === 'declining').length;

      return {
        id: employee.id,
        name: employee.name,
        age: employee.age,
        gender: employee.gender,
        city: employee.city,
        planName: employee.packageName,
        planDuration: employee.packageDuration,
        planStatus: plan?.state || 'draft_generated',
        recoveryStage: employee.recoveryStage,
        organization: employee.organization,
        readiness: employee.readiness,
        recovery: employee.recovery,
        hydration: employee.hydration,
        sleepQuality: employee.sleepQuality,
        adherenceScore,
        symptomProfile: employee.symptomProfile,
        goals: employee.goals,
        latestActivity: formatDisplayDate(latestActivityDate),
        activityDate: latestActivityDate,
        planUpdatedAt: plan?.updatedAt || null,
        criticalBiomarkers,
        decliningBiomarkers,
        projectedRevenue: PACKAGE_PRICING[employee.packageName] || 18000,
      };
    })
    .filter((client) => client.activityDate >= dateWindow.start && client.activityDate <= dateWindow.end)
    .sort((a, b) => b.activityDate.getTime() - a.activityDate.getTime());
}

export function getFiteatsyIntelligence({ range = 'month', startDate, endDate } = {}) {
  const state = buildInitialPlatformState();
  const anchorDate = getAnchorDate(state);
  const dateWindow = resolveDateWindow(range, startDate, endDate, anchorDate);
  const clients = buildClientAnalytics(state, dateWindow);

  const totalRevenue = clients.reduce((sum, client) => sum + client.projectedRevenue, 0);
  const approvedPlans = clients.filter((client) => ['approved', 'published'].includes(client.planStatus)).length;
  const draftPlans = clients.filter((client) => ['draft_generated', 'consultant_review', 'consultant_modified', 'senior_review', 'revision_requested'].includes(client.planStatus)).length;
  const flaggedClients = clients.filter((client) => client.criticalBiomarkers > 0 || client.readiness < 55).length;
  const avgAdherence = average(clients.map((client) => client.adherenceScore));
  const avgRecovery = average(clients.map((client) => client.recovery));
  const avgSleep = average(clients.map((client) => client.sleepQuality));
  const activePrograms = new Set(clients.map((client) => client.planName)).size;

  return {
    brand: 'Fiteatsy',
    title: 'User Intelligence',
    subtitle: 'Client-level recovery visibility, plan mix, and quality for the selected Fiteatsy date range.',
    window: {
      range: dateWindow.key,
      label: dateWindow.label,
      startDate: formatDate(dateWindow.start),
      endDate: formatDate(dateWindow.end),
      anchorDate: formatDate(anchorDate),
    },
    clients,
    metrics: {
      revenue: [
        { label: 'Clients in range', value: String(clients.length), delta: `${activePrograms} active programs` },
        { label: 'Projected revenue', value: formatCurrency(totalRevenue), delta: 'Range-adjusted recovery plan value' },
        { label: 'Approved plans', value: String(approvedPlans), delta: `${draftPlans} still in workflow` },
        { label: 'Average adherence', value: `${avgAdherence}%`, delta: `${avgRecovery}% average recovery momentum` },
      ],
      quality: [
        { id: 'fti-q-1', label: 'Critical follow-up', count: String(flaggedClients), detail: 'Clients with critical biomarkers or low readiness scores' },
        { id: 'fti-q-2', label: 'Average sleep quality', count: `${avgSleep}%`, detail: 'Sleep quality across active Fiteatsy clients' },
        { id: 'fti-q-3', label: 'Program completion risk', count: `${clients.filter((client) => client.adherenceScore < 60).length}`, detail: 'Clients likely to need tighter coaching support' },
        { id: 'fti-q-4', label: 'Hormonal priority cases', count: `${clients.filter((client) => client.symptomProfile?.length >= 2).length}`, detail: 'Users with broader hormonal symptom clusters in range' },
      ],
    },
  };
}
