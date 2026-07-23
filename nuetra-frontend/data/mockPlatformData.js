export const SAMPLE_PASSWORD = 'Nuetra@123';

export const sampleUsers = [
  {
    id: 'usr-consultant-1',
    name: 'Dr. Aditi Kulkarni',
    email: 'aditi.kulkarni@nuetra.in',
    password: SAMPLE_PASSWORD,
    role: 'consultant',
    title: 'Nutrition Consultant',
    focus: 'Metabolic recovery and adaptive meal planning',
    avatar: 'AK',
  },
  {
    id: 'usr-senior-1',
    name: 'Dr. Rohan Mehta',
    email: 'rohan.mehta@nuetra.in',
    password: SAMPLE_PASSWORD,
    role: 'senior_consultant',
    title: 'Senior Consultant',
    focus: 'Quality review and clinical escalation',
    avatar: 'RM',
  },
  {
    id: 'usr-mentor-1',
    name: 'Maya Iyer',
    email: 'maya.iyer@nuetra.in',
    password: SAMPLE_PASSWORD,
    role: 'mentor',
    title: 'Recovery Mentor',
    focus: 'Burnout prevention and adherence coaching',
    avatar: 'MI',
  },
  {
    id: 'usr-org-1',
    name: 'Nikhil Rao',
    email: 'nikhil.rao@zenithforge.com',
    password: SAMPLE_PASSWORD,
    role: 'organization_admin',
    title: 'Organization Wellness Admin',
    focus: 'Engagement, billing, and wellness operations',
    avatar: 'NR',
  },
];

export const practitioners = {
  consultant: sampleUsers[0],
  senior_consultant: sampleUsers[1],
  mentor: sampleUsers[2],
  organization_admin: sampleUsers[3],
};

const FIRST_NAMES = [
  'Aarav', 'Aditi', 'Akash', 'Ananya', 'Arjun', 'Bhavna', 'Charu', 'Dev', 'Esha', 'Farhan',
  'Gauri', 'Harsh', 'Ishita', 'Jay', 'Karan', 'Kavya', 'Meera', 'Neha', 'Nikhil', 'Pooja',
  'Rahul', 'Rhea', 'Ritu', 'Saanvi', 'Sameer', 'Shreya', 'Tanmay', 'Tanya', 'Varun', 'Zoya',
];

const LAST_NAMES = [
  'Joshi', 'Kulkarni', 'Patel', 'Nair', 'Mehta', 'Rao', 'Sen', 'Iyer', 'Qureshi', 'Sharma',
  'Verma', 'Desai', 'Bose', 'Chatterjee', 'Mukherjee', 'Naidu', 'Pillai', 'Mishra', 'Kapoor', 'Singh',
];

const REGIONS = [
  { name: 'Maharashtrian', cities: ['Pune', 'Mumbai', 'Nashik', 'Nagpur'] },
  { name: 'Gujarati', cities: ['Ahmedabad', 'Vadodara', 'Surat', 'Rajkot'] },
  { name: 'South Indian', cities: ['Bengaluru', 'Chennai', 'Hyderabad', 'Kochi'] },
  { name: 'Punjabi', cities: ['Gurugram', 'Chandigarh', 'Ludhiana', 'Amritsar'] },
  { name: 'Bengali', cities: ['Kolkata', 'Howrah', 'Siliguri', 'Durgapur'] },
];

const DIETARY_STYLES = ['vegetarian', 'non-vegetarian', 'Jain', 'vegan', 'sattvic'];
const GENDERS = ['Female', 'Male'];
const BRANDS = ['Nuetra', 'Fiteatsy'];
const FITEATSY_PACKAGES = [
  { name: 'Reset Program', duration: '3 Months', philosophy: 'Symptom stabilization, inflammation reduction, and adherence building.' },
  { name: 'Rebalance Program', duration: '6 Months', philosophy: 'Hormonal correction, cycle stabilization, and metabolic repair.' },
  { name: 'Restore Program', duration: '12 Months', philosophy: 'Deep recovery, relapse prevention, and long-term resilience.' },
];
const NUETRA_ANNUAL_PROGRAM = {
  name: 'Annual Corporate Program',
  duration: '12 Months',
  philosophy: 'Burnout prevention, adherence intelligence, and workforce recovery support.',
};
const ORGANIZATIONS = [
  { name: 'Zenith Forge', subscription: 'Enterprise Recovery', employees: 420 },
  { name: 'Northstar Labs', subscription: 'Adaptive Nutrition', employees: 160 },
  { name: 'Aster Pulse', subscription: 'Wellness Core', employees: 98 },
  { name: 'Atlas Commerce', subscription: 'Performance Plus', employees: 230 },
  { name: 'Meridian HealthOps', subscription: 'Clinical Intelligence', employees: 185 },
  { name: 'BlueOrbit Systems', subscription: 'Enterprise Recovery', employees: 310 },
  { name: 'Saffron Mobility', subscription: 'Adaptive Nutrition', employees: 142 },
  { name: 'Riverline Finance', subscription: 'Wellness Core', employees: 116 },
];

const JOB_ROLES = [
  'Product Lead', 'Engineering Manager', 'Data Analyst', 'UX Researcher', 'Sales Director', 'People Ops Manager',
  'Finance Associate', 'Marketing Manager', 'Operations Lead', 'Customer Success Manager', 'Consulting Analyst', 'Program Manager',
];
const DEPARTMENTS = ['Engineering', 'Product', 'People Ops', 'Finance', 'Growth', 'Customer Success', 'Operations', 'Design'];
const COHORTS = ['Remote high-load cohort', 'Hybrid manager cohort', 'Travel-heavy cohort', 'Night-shift recovery cohort', 'Women leaders cohort'];
const WORK_SCHEDULES = ['9 AM - 6 PM hybrid', '10 AM - 7 PM office', 'Split shift', 'Night support rotation', 'Travel-heavy field schedule'];
const RECOVERY_STAGES = ['Signal Stabilization', 'Adherence Build', 'Metabolic Correction', 'Hormonal Rebalance', 'Recovery Consolidation'];
const FITEATSY_SYMPTOMS = [
  'cycle irregularity',
  'cravings',
  'bloating',
  'hair fall',
  'skin breakouts',
  'low energy',
  'sleep disruption',
  'mood swings',
];
const FITEATSY_GOALS = ['Cycle stability', 'Hormonal balance', 'Craving control', 'Weight recovery', 'Postpartum resilience', 'Fertility support'];

const OCR_STATES = ['complete', 'processing', 'biomarkers_detected', 'insights_generated'];
const PLAN_STATES = ['draft_generated', 'consultant_review', 'consultant_modified', 'senior_review', 'approved', 'published', 'revision_requested'];
const TASK_STATUSES = ['overdue', 'pending', 'in_progress', 'completed'];
const THREAD_TOPICS = ['glucose plan', 'burnout escalation', 'hydration drift', 'sleep recovery', 'thyroid review', 'adherence coaching'];
const KNOWLEDGE_BASE = [
  { id: 'kb-1', title: 'PCOS recovery framework', category: 'Metabolic', updated: '2 days ago' },
  { id: 'kb-2', title: 'HbA1c stabilization playbook', category: 'Biomarkers', updated: 'Today' },
  { id: 'kb-3', title: 'Vitamin D recovery protocol', category: 'Deficiency', updated: 'Yesterday' },
  { id: 'kb-4', title: 'Burnout recovery guidance', category: 'Mentor', updated: 'Today' },
  { id: 'kb-5', title: 'Thyroid nutrition guidance', category: 'Clinical', updated: '3 days ago' },
  { id: 'kb-6', title: 'Travel-heavy consultant nutrition guide', category: 'Lifestyle', updated: 'Today' },
];

const PROFILE_TEMPLATES = [
  {
    key: 'prediabetes',
    conditions: ['Prediabetes', 'Vitamin D deficiency'],
    goals: ['HbA1c stabilization', 'Energy recovery', 'Weight normalization'],
    biomarkers: {
      HbA1c: { base: 6.1, drift: 0.8, better: 5.6, worse: 6.9 },
      'Vitamin D': { base: 19, drift: 7, better: 28, worse: 12 },
      TSH: { base: 3.0, drift: 0.5, better: 2.6, worse: 3.5 },
      Cholesterol: { base: 206, drift: 24, better: 182, worse: 228 },
      CRP: { base: 4.7, drift: 1.4, better: 3.2, worse: 6.1 },
    },
    interventions: ['Hydration reset', 'Glucose stabilization', 'Sleep optimization'],
    blocks: ['Adaptive Nutrition Summary', 'Calorie Targets', 'Macro Targets', 'Meal Timing Strategy', 'Breakfast Framework', 'Dinner Framework'],
  },
  {
    key: 'thyroid',
    conditions: ['Subclinical hypothyroid'],
    goals: ['Thyroid support', 'Reduce afternoon crashes', 'Support recovery consistency'],
    biomarkers: {
      HbA1c: { base: 5.7, drift: 0.3, better: 5.4, worse: 6.0 },
      'Vitamin D': { base: 22, drift: 5, better: 30, worse: 16 },
      TSH: { base: 4.8, drift: 1.1, better: 2.6, worse: 5.6 },
      Cholesterol: { base: 188, drift: 18, better: 170, worse: 206 },
      CRP: { base: 3.2, drift: 0.7, better: 2.5, worse: 4.0 },
    },
    interventions: ['Recovery support', 'Meal timing strategy', 'Protein anchoring'],
    blocks: ['Adaptive Nutrition Summary', 'Breakfast Framework', 'Lunch Framework', 'Hydration Strategy', 'Lifestyle Recommendations'],
  },
  {
    key: 'burnout',
    conditions: ['High stress load'],
    goals: ['Burnout recovery', 'Improve sleep consistency', 'Reduce decision fatigue'],
    biomarkers: {
      HbA1c: { base: 5.8, drift: 0.2, better: 5.5, worse: 6.1 },
      'Vitamin D': { base: 18, drift: 4, better: 24, worse: 13 },
      TSH: { base: 2.8, drift: 0.4, better: 2.4, worse: 3.3 },
      Cholesterol: { base: 191, drift: 16, better: 176, worse: 208 },
      CRP: { base: 5.4, drift: 1.5, better: 3.8, worse: 6.9 },
    },
    interventions: ['Stress management', 'Sleep optimization', 'Recovery support'],
    blocks: ['Adaptive Nutrition Summary', 'Meal Timing Strategy', 'Breakfast Framework', 'Recovery Interventions', 'Lifestyle Recommendations'],
  },
  {
    key: 'dyslipidemia',
    conditions: ['Dyslipidemia'],
    goals: ['Reduce cholesterol', 'Increase movement', 'Sustain travel-friendly adherence'],
    biomarkers: {
      HbA1c: { base: 5.6, drift: 0.2, better: 5.3, worse: 5.9 },
      'Vitamin D': { base: 24, drift: 5, better: 31, worse: 18 },
      TSH: { base: 2.5, drift: 0.3, better: 2.2, worse: 2.9 },
      Cholesterol: { base: 224, drift: 30, better: 186, worse: 238 },
      CRP: { base: 3.0, drift: 0.8, better: 2.1, worse: 3.9 },
    },
    interventions: ['Movement consistency', 'Nutrition adherence', 'Fiber escalation'],
    blocks: ['Adaptive Nutrition Summary', 'Lunch Framework', 'Dinner Framework', 'Snack Guidance', 'Lifestyle Recommendations'],
  },
  {
    key: 'deficiency',
    conditions: ['Vitamin D deficiency'],
    goals: ['Correct Vitamin D deficiency', 'Improve hydration', 'Increase recovery resilience'],
    biomarkers: {
      HbA1c: { base: 5.5, drift: 0.1, better: 5.3, worse: 5.8 },
      'Vitamin D': { base: 14, drift: 4, better: 24, worse: 10 },
      TSH: { base: 2.9, drift: 0.4, better: 2.5, worse: 3.3 },
      Cholesterol: { base: 178, drift: 14, better: 164, worse: 192 },
      CRP: { base: 3.8, drift: 0.7, better: 2.9, worse: 4.4 },
    },
    interventions: ['Hydration adherence', 'Sunlight protocol', 'Supplement cadence'],
    blocks: ['Adaptive Nutrition Summary', 'Hydration Strategy', 'Recovery Interventions', 'Supplement Guidance', 'Snack Guidance'],
  },
  {
    key: 'pcos',
    conditions: ['PCOS', 'Insulin resistance'],
    goals: ['Cycle stability', 'Reduce cravings', 'Improve metabolic resilience'],
    biomarkers: {
      HbA1c: { base: 6.0, drift: 0.4, better: 5.5, worse: 6.4 },
      'Vitamin D': { base: 18, drift: 6, better: 26, worse: 12 },
      TSH: { base: 3.4, drift: 0.5, better: 2.8, worse: 3.9 },
      Cholesterol: { base: 198, drift: 18, better: 178, worse: 214 },
      CRP: { base: 5.1, drift: 1.1, better: 3.6, worse: 6.2 },
    },
    interventions: ['Glucose stabilization', 'Sleep optimization', 'Cycle support'],
    blocks: ['Adaptive Nutrition Summary', 'Macro Targets', 'Breakfast Framework', 'Dinner Framework', 'Lifestyle Recommendations'],
  },
];

function pad(value) {
  return String(value).padStart(2, '0');
}

function formatTimestamp(dayOffset, hour, minute) {
  const day = 3 - dayOffset;
  return `2026-06-${pad(Math.max(1, day))} ${pad(hour)}:${pad(minute)}`;
}

function formatHumanTime(dayOffset, hour, minute) {
  if (dayOffset === 0) return `Today, ${hour % 12 || 12}:${pad(minute)} ${hour >= 12 ? 'PM' : 'AM'}`;
  if (dayOffset === 1) return `Yesterday, ${hour % 12 || 12}:${pad(minute)} ${hour >= 12 ? 'PM' : 'AM'}`;
  return `${dayOffset} days ago`;
}

function pick(array, index) {
  return array[index % array.length];
}

function calculateStatus(current, previous, higherIsWorse) {
  const delta = current - previous;
  if (higherIsWorse) {
    if (delta > 0.35) return 'critical';
    if (delta > 0.12) return 'declining';
    if (delta < -0.12) return 'improving';
    return 'stable';
  }

  if (delta < -2.2) return 'critical';
  if (delta < -0.8) return 'declining';
  if (delta > 0.8) return 'improving';
  return 'stable';
}

function biomarkerSeries(index, template, metric) {
  const def = template.biomarkers[metric];
  const oscillation = ((index % 5) - 2) * 0.12;

  if (metric === 'HbA1c') {
    const previous = Number((def.base + ((index % 7) - 3) * 0.08).toFixed(1));
    const current = Number((previous + oscillation).toFixed(1));
    const earliest = Number((previous - 0.2 + ((index % 3) * 0.1)).toFixed(1));
    const status = calculateStatus(current, previous, true);
    return {
      current: `${current.toFixed(1)}%`,
      previous: `${previous.toFixed(1)}%`,
      status,
      dates: ['Jan', 'Mar', 'May'],
      values: [earliest, previous, current],
    };
  }

  if (metric === 'TSH') {
    const previous = Number((def.base + ((index % 5) - 2) * 0.2).toFixed(1));
    const current = Number((previous + ((index % 4) - 1.5) * 0.1).toFixed(1));
    const earliest = Number((previous + ((index % 3) - 1) * 0.2).toFixed(1));
    const status = current > 4.5 ? 'declining' : current < 2.6 ? 'improving' : 'stable';
    return {
      current: `${current.toFixed(1)} mIU/L`,
      previous: `${previous.toFixed(1)} mIU/L`,
      status,
      dates: ['Jan', 'Mar', 'May'],
      values: [earliest, previous, current],
    };
  }

  if (metric === 'Vitamin D') {
    const previous = Math.round(def.base + ((index % 6) - 2));
    const current = previous + ((index % 5) - 2);
    const earliest = previous - ((index % 4) - 1);
    const status = current < 14 ? 'critical' : current < previous ? 'declining' : current > previous ? 'improving' : 'stable';
    return {
      current: `${current} ng/mL`,
      previous: `${previous} ng/mL`,
      status,
      dates: ['Jan', 'Mar', 'May'],
      values: [earliest, previous, current],
    };
  }

  if (metric === 'Cholesterol') {
    const previous = Math.round(def.base + ((index % 6) - 2) * 5);
    const current = previous + ((index % 5) - 2) * 4;
    const earliest = previous + ((index % 4) - 1) * 6;
    const status = current > previous + 4 ? 'declining' : current < previous - 4 ? 'improving' : 'stable';
    return {
      current: `${current} mg/dL`,
      previous: `${previous} mg/dL`,
      status,
      dates: ['Jan', 'Mar', 'May'],
      values: [earliest, previous, current],
    };
  }

  const previous = Number((def.base + ((index % 6) - 2) * 0.35).toFixed(1));
  const current = Number((previous + ((index % 5) - 2) * 0.25).toFixed(1));
  const earliest = Number((previous + ((index % 4) - 1) * 0.4).toFixed(1));
  const status = current > previous + 0.3 ? 'declining' : current < previous - 0.3 ? 'improving' : 'stable';
  return {
    current: `${current.toFixed(1)} mg/L`,
    previous: `${previous.toFixed(1)} mg/L`,
    status,
    dates: ['Jan', 'Mar', 'May'],
    values: [earliest, previous, current],
  };
}

function generateInterventions(template, riskIndex, index) {
  return template.interventions.map((name, interventionIndex) => {
    const adherence = Math.max(32, Math.min(90, 72 - riskIndex * 9 + interventionIndex * 7 + ((index + interventionIndex) % 9 - 4)));
    const status = adherence < 42 ? 'critical' : adherence < 58 ? 'declining' : adherence > 74 ? 'improving' : 'stable';
    return {
      name,
      status,
      owner: interventionIndex === 1 ? 'consultant' : 'mentor',
      adherence,
    };
  });
}

function generateReports(index, employeeName, templateKey) {
  const count = 2 + (index % 2);
  return Array.from({ length: count }, (_, reportIndex) => {
    const state = pick(OCR_STATES, index + reportIndex);
    const fileType = reportIndex === 0 ? 'pdf' : reportIndex === 1 ? 'jpg' : 'pdf';
    const titleSeed = templateKey.replace(/_/g, '-');
    return {
      id: `rep-${index + 1}-${reportIndex + 1}`,
      name: `${titleSeed}-panel-${reportIndex + 1}.${fileType}`,
      uploadedAt: formatTimestamp(reportIndex + (index % 3), 8 + ((index + reportIndex) % 9), (index * 7 + reportIndex * 11) % 60),
      ocrState: state,
      extractionConfidence: 76 + ((index + reportIndex * 3) % 23),
      lab: pick(['Metropolis', 'Thyrocare', 'Dr. Lal PathLabs', 'Apollo Diagnostics'], index + reportIndex),
    };
  });
}

function generateNotes(index, template, employeeName, region, dietaryStyle) {
  const patterns = [
    `Responds well to ${region}-friendly breakfast anchors and simpler workday snacks.`,
    `Hydration and sleep routines fluctuate during travel-heavy weeks.`,
    `Meal complexity should stay low to protect adherence consistency.`,
    `Regional familiarity improves lunch adherence and lowers decision fatigue.`,
  ];

  return [
    {
      author: 'Dr. Aditi Kulkarni',
      role: 'consultant',
      text: patterns[index % patterns.length],
      time: formatHumanTime(0, 9 + (index % 4), (index * 3) % 60),
    },
    {
      author: 'Maya Iyer',
      role: 'mentor',
      text: `Behaviorally, ${employeeName.split(' ')[0]} benefits from prompts around ${template.interventions[0].toLowerCase()} and lower evening friction.`,
      time: formatHumanTime(1, 18, (index * 5) % 60),
    },
    {
      author: 'Dr. Rohan Mehta',
      role: 'senior_consultant',
      text: `Keep ${dietaryStyle} meal identity practical while aligning with current biomarker risk.`,
      time: formatHumanTime(2, 20, (index * 7) % 60),
    },
  ];
}

function generateEmployee(index) {
  const brand = index % 5 < 3 ? 'Nuetra' : 'Fiteatsy';
  const firstName = pick(FIRST_NAMES, index);
  const lastName = pick(LAST_NAMES, Math.floor(index / FIRST_NAMES.length) + index);
  const region = pick(REGIONS, index);
  const city = pick(region.cities, index + 1);
  const dietaryStyle = pick(DIETARY_STYLES, index + 2);
  const organizationRecord = brand === 'Nuetra' ? pick(ORGANIZATIONS, index + 3) : null;
  const organization = organizationRecord?.name || 'Fiteatsy Direct Care';
  const role = pick(JOB_ROLES, index + 4);
  const templatePool = brand === 'Fiteatsy'
    ? PROFILE_TEMPLATES.filter((item) => ['pcos', 'thyroid', 'deficiency', 'burnout'].includes(item.key))
    : PROFILE_TEMPLATES;
  const template = pick(templatePool, index + 5);
  const riskIndex = index % 5;
  const readiness = Math.max(44, 76 - riskIndex * 7 + (index % 6));
  const recovery = Math.max(40, 72 - riskIndex * 6 + ((index + 2) % 7));
  const hydration = Math.max(38, 74 - riskIndex * 7 + ((index + 3) % 8));
  const stress = Math.min(88, 48 + riskIndex * 9 + ((index + 1) % 7));
  const sleepQuality = Math.max(41, 73 - riskIndex * 7 + ((index + 4) % 6));
  const burnoutRisk = riskIndex >= 4 ? 'critical' : riskIndex === 3 ? 'high' : riskIndex === 2 ? 'medium' : 'low';
  const biomarkers = ['HbA1c', 'Vitamin D', 'TSH', 'Cholesterol', 'CRP'].map((metric) => ({
    name: metric,
    ...biomarkerSeries(index, template, metric),
  }));

  const name = `${firstName} ${lastName}`;
  const packageRecord = brand === 'Nuetra' ? NUETRA_ANNUAL_PROGRAM : pick(FITEATSY_PACKAGES, index + 7);
  const department = brand === 'Nuetra' ? pick(DEPARTMENTS, index + 8) : 'Direct Care';
  const cohort = brand === 'Nuetra' ? pick(COHORTS, index + 9) : 'Hormonal recovery cohort';
  const workSchedule = brand === 'Nuetra' ? pick(WORK_SCHEDULES, index + 10) : 'Lifestyle-led recovery cadence';
  const recoveryStage = pick(RECOVERY_STAGES, index + 11);
  const workflowType = brand === 'Nuetra' ? 'enterprise_operational' : 'retail_recovery';
  const aiMode = brand === 'Nuetra' ? 'workforce_recovery_intelligence' : 'hormonal_recovery_protocol';
  const onboardingType = brand === 'Nuetra' ? 'organization_employee_intake' : 'personal_recovery_journey';
  const symptomProfile = brand === 'Fiteatsy'
    ? Array.from({ length: 3 }, (_, symptomIndex) => pick(FITEATSY_SYMPTOMS, index + symptomIndex))
    : [];
  const hormonalGoals = brand === 'Fiteatsy'
    ? Array.from({ length: 2 }, (_, goalIndex) => pick(FITEATSY_GOALS, index + goalIndex))
    : [];
  const notes = generateNotes(index, template, name, region.name, dietaryStyle).map((note, noteIndex) => ({
    ...note,
    type: noteIndex === 0 ? 'Clinical Observation' : noteIndex === 1 ? 'Behavioral Pattern' : 'Mentor Review',
    severity: burnoutRisk === 'critical' ? 'critical' : noteIndex === 0 ? 'high' : 'medium',
    tags: [
      brand,
      packageRecord.name,
      region.name,
      dietaryStyle,
      template.conditions[0],
      ...(brand === 'Nuetra' ? [department] : symptomProfile.slice(0, 1)),
    ].filter(Boolean),
    linkedBiomarker: biomarkers.find((item) => item.status !== 'stable')?.name || biomarkers[0].name,
    linkedIntervention: template.interventions[noteIndex % template.interventions.length],
    linkedReport: `rep-${index + 1}-1`,
    reminder: noteIndex === 0 ? 'Review before next nutrition update' : 'Check in during next follow-up',
  }));
  return {
    id: `emp-${pad(index + 1)}`,
    name,
    age: 24 + (index % 27),
    gender: brand === 'Fiteatsy' ? 'Female' : pick(GENDERS, index),
    brand,
    packageName: packageRecord.name,
    packageDuration: packageRecord.duration,
    packagePhilosophy: packageRecord.philosophy,
    workflowType,
    aiMode,
    onboardingType,
    recoveryStage,
    city,
    organization,
    role,
    department,
    cohort,
    workSchedule,
    dietaryStyle,
    region: region.name,
    goals: brand === 'Fiteatsy' ? [...template.goals, ...hormonalGoals].slice(0, 4) : template.goals,
    conditions: template.conditions,
    symptomProfile,
    readiness,
    recovery,
    hydration,
    stress,
    sleepQuality,
    burnoutRisk,
    interventions: generateInterventions(template, riskIndex, index),
    biomarkers,
    reports: generateReports(index, name, template.key),
    notes,
    latestPlanId: `plan-${pad(index + 1)}`,
  };
}

function blockContent(title, employee) {
  const mealMap = {
    Maharashtrian: 'poha, thalipeeth, varan-bhaat, bhakri, sprouts',
    Gujarati: 'thepla, khichdi-kadhi, roti sabzi, handvo, chaas',
    'South Indian': 'idli, sambar, upma, pesarattu, curd rice',
    Punjabi: 'phulka, dal, paneer bhurji, chole, lassi',
    Bengali: 'chire doi, fish curry, moong dal, bhaja, rice',
  };
  const regionalMeals = mealMap[employee.region] || 'regional meals';
  const focus = employee.conditions[0];
  const contentMap = {
    'Adaptive Nutrition Summary': `Protocol supports ${focus.toLowerCase()} using ${employee.region.toLowerCase()}-friendly meals and lower-friction workday structure.`,
    'Calorie Targets': `Weekday target tuned for ${employee.goals[0].toLowerCase()} with slight flexibility on higher-activity days.`,
    'Macro Targets': `Protein-forward structure with moderated evening carbohydrate load to protect recovery and metabolic stability.`,
    'Meal Timing Strategy': `Breakfast within 60 minutes of waking, lunch before 2 PM, and earlier lighter dinners when work cadence allows.`,
    'Breakfast Framework': `Breakfast options favor ${regionalMeals} with stronger protein anchors and better satiety.`,
    'Lunch Framework': `Lunch remains culturally familiar to improve adherence while smoothing afternoon energy.`,
    'Dinner Framework': `Dinner is lighter and simpler to improve sleep and reduce late-day metabolic volatility.`,
    'Snack Guidance': `Snack structure focuses on easy office carry, fewer skipped windows, and more predictable hunger management.`,
    'Hydration Strategy': `Hydration checkpoints are front-loaded before noon with practical options for commute and meeting-heavy days.`,
    'Recovery Interventions': `Recovery routines focus on sleep protection, screen cutoff, and short post-meal movement windows.`,
    'Lifestyle Recommendations': `Behavioral goals reduce decision fatigue and make the plan realistic during travel and heavy work cycles.`,
    'Supplement Guidance': `Supplement timing aligns with current deficiencies, meal consistency, and adherence reliability.`,
  };
  return contentMap[title] || `Structured guidance for ${focus.toLowerCase()} with a stronger emphasis on repeatable routines.`;
}

function generatePlan(employee, index) {
  const template = pick(PROFILE_TEMPLATES, index + 5);
  const state = pick(PLAN_STATES, index);
  const version = 1 + (index % 4);
  const blockTitles = template.blocks;
  return {
    id: `plan-${pad(index + 1)}`,
    employeeId: employee.id,
    employeeName: employee.name,
    state,
    version,
    updatedAt: formatTimestamp(index % 4, 8 + (index % 8), (index * 9) % 60),
    reviewers: ['Dr. Aditi Kulkarni', ...(state === 'consultant_review' || state === 'draft_generated' ? [] : ['Dr. Rohan Mehta'])],
    comments: [
      employee.brand === 'Fiteatsy'
        ? `Preserve ${employee.packageName.toLowerCase()} tone with lower-friction hormonal recovery choices.`
        : `Keep ${employee.region.toLowerCase()} meal identity intact.`,
      employee.burnoutRisk === 'critical'
        ? 'Reduce meal complexity to improve adherence.'
        : employee.brand === 'Fiteatsy'
          ? 'Protect symptom stability by reducing late-day dietary decision load.'
          : 'Preserve schedule fit during heavy workdays.',
    ],
    blocks: blockTitles.map((title, blockIndex) => ({
      id: `blk-${index + 1}-${blockIndex + 1}`,
      title,
      content: blockContent(title, employee),
    })),
    versions: Array.from({ length: version }, (_, versionIndex) => ({
      label: versionIndex === 0 ? 'AI generated v1' : versionIndex === version - 1 ? `${state.replace(/_/g, ' ')} v${versionIndex + 1}` : `Consultant modified v${versionIndex + 1}`,
      by: versionIndex === 0 ? 'Nuetra AI' : versionIndex === version - 1 && state !== 'consultant_modified' ? 'Dr. Rohan Mehta' : 'Dr. Aditi Kulkarni',
      time: formatTimestamp(versionIndex + 1, 9 + ((index + versionIndex) % 8), (index * 4 + versionIndex * 13) % 60),
      note: versionIndex === 0
        ? `Draft generated from biomarkers, adherence history, ${employee.brand === 'Fiteatsy' ? 'hormonal symptom profile' : 'workforce behavior patterns'}, cultural preferences, and intervention memory.`
        : versionIndex === version - 1
          ? `Plan moved to ${state.replace(/_/g, ' ')} after clinical review.`
          : 'Meal timing and adherence friction were adjusted by consultant review.',
    })),
  };
}

const employees = Array.from({ length: 200 }, (_, index) => generateEmployee(index));
const plans = employees.map((employee, index) => generatePlan(employee, index));

function topRiskEmployees(limit = 6) {
  return employees
    .map((employee) => {
      const criticalBiomarkers = employee.biomarkers.filter((item) => item.status === 'critical').length;
      const decliningBiomarkers = employee.biomarkers.filter((item) => item.status === 'declining').length;
      const avgAdherence = Math.round(employee.interventions.reduce((sum, item) => sum + item.adherence, 0) / employee.interventions.length);
      const score = criticalBiomarkers * 40 + decliningBiomarkers * 20 + (100 - employee.readiness) + (100 - employee.recovery) + (100 - avgAdherence);
      return { employee, avgAdherence, score };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

const highRisk = topRiskEmployees(8);

const priorityQueue = highRisk.slice(0, 6).map((item, index) => ({
  id: `pq-${index + 1}`,
  title: `${item.employee.biomarkers.find((entry) => entry.status === 'critical' || entry.status === 'declining')?.name || 'Recovery'} drift for ${item.employee.name}`,
  subtitle: `${item.employee.organization} · ${item.employee.conditions.join(', ')} · attention required`,
  severity: item.employee.burnoutRisk === 'critical' ? 'critical' : item.employee.burnoutRisk === 'high' ? 'high' : 'medium',
  owner: index % 3 === 0 ? 'Dr. Aditi Kulkarni' : index % 3 === 1 ? 'Dr. Rohan Mehta' : 'Maya Iyer',
  due: index < 2 ? 'Today, 2:00 PM' : 'Today, 5:00 PM',
  action: index % 2 === 0 ? 'Review employee' : 'Open report intelligence',
}));

const recoveryAlerts = highRisk.slice(0, 10).map((item, index) => {
  const biomarker = item.employee.biomarkers.find((entry) => entry.status === 'critical' || entry.status === 'declining') || item.employee.biomarkers[0];
  return {
    id: `ra-${index + 1}`,
    employeeId: item.employee.id,
    employeeName: item.employee.name,
    alert: `${biomarker.name} ${biomarker.status === 'critical' ? 'requires escalation' : 'is drifting'} from ${biomarker.previous} to ${biomarker.current}`,
    trend: biomarker.status,
    recommendation: `Review ${item.employee.interventions[0].name.toLowerCase()} and tighten ${item.employee.goals[0].toLowerCase()} workflow support.`,
  };
});

const inbox = highRisk.slice(0, 12).map((item, index) => ({
  id: `ib-${index + 1}`,
  subject: index % 3 === 0 ? 'AI draft requires correction' : index % 3 === 1 ? 'Mentor escalation note added' : 'Report interpretation pending',
  type: index % 3 === 0 ? 'pending_review' : index % 3 === 1 ? 'escalation' : 'report_discussion',
  state: pick(['consultant_review', 'followup_pending', 'senior_review', 'draft_generated'], index),
  employee: item.employee.name,
  org: item.employee.organization,
  priority: item.employee.burnoutRisk === 'critical' ? 'high' : index % 2 === 0 ? 'medium' : 'low',
  unread: index % 4 !== 0,
  time: index < 4 ? `0${8 + index}:1${index}` : 'Yesterday',
  summary: `${item.employee.goals[0]} is affected by ${item.employee.interventions[0].name.toLowerCase()} inconsistency and changing biomarker movement.`,
}));

const reportPipeline = employees
  .flatMap((employee) => employee.reports.filter((report) => report.ocrState !== 'complete').map((report, index) => ({
    id: `rp-${employee.id}-${index + 1}`,
    employee: employee.name,
    file: report.name,
    state: report.ocrState === 'processing' ? 'Processing...' : report.ocrState === 'biomarkers_detected' ? 'Biomarkers detected...' : 'Insights generated...',
    progress: report.ocrState === 'processing' ? 48 : report.ocrState === 'biomarkers_detected' ? 76 : 100,
  })))
  .slice(0, 16);

const sessions = highRisk.slice(0, 18).map((item, index) => ({
  id: `sess-${index + 1}`,
  employee: item.employee.name,
  practitioner: index % 2 === 0 ? 'Maya Iyer' : 'Dr. Aditi Kulkarni',
  when: index < 8 ? `Today, ${10 + (index % 8)}:${index % 2 === 0 ? '00' : '30'} ${10 + (index % 8) >= 12 ? 'PM' : 'AM'}` : `Tomorrow, ${9 + (index % 5)}:00 AM`,
  type: index % 3 === 0 ? 'Recovery coaching' : index % 3 === 1 ? 'Plan review' : 'Adherence follow-up',
  burnout: item.employee.burnoutRisk,
  adherence: item.avgAdherence,
  mood: item.employee.stress > 74 ? 'fragile' : item.employee.stress > 62 ? 'variable' : 'steady',
}));

const tasks = highRisk.slice(0, 20).map((item, index) => ({
  id: `task-${index + 1}`,
  title: `${item.employee.biomarkers[0].name} and ${item.employee.goals[0].toLowerCase()} review for ${item.employee.name}`,
  owner: index % 3 === 0 ? 'Dr. Aditi Kulkarni' : index % 3 === 1 ? 'Dr. Rohan Mehta' : 'Maya Iyer',
  status: pick(TASK_STATUSES, index),
  due: index < 8 ? 'Today' : index < 14 ? 'Tomorrow' : 'This week',
}));

const communicationThreads = highRisk.slice(0, 10).map((item, index) => ({
  id: `thr-${index + 1}`,
  title: `${item.employee.name.split(' ')[0]} ${pick(THREAD_TOPICS, index)} thread`,
  participants: ['Dr. Aditi Kulkarni', ...(index % 2 === 0 ? ['Dr. Rohan Mehta'] : []), 'Maya Iyer'],
  latest: `Need follow-through on ${item.employee.interventions[0].name.toLowerCase()} before next review.`,
  unread: 1 + (index % 4),
}));

const finance = {
  payouts: [
    { name: 'Dr. Aditi Kulkarni', consultations: 82, approvedPlans: 64, sessionPayouts: 'Rs 1,82,500', incentives: 'Rs 24,000' },
    { name: 'Dr. Rohan Mehta', consultations: 41, approvedPlans: 93, sessionPayouts: 'Rs 1,48,000', incentives: 'Rs 31,500' },
    { name: 'Maya Iyer', consultations: 96, approvedPlans: 0, sessionPayouts: 'Rs 1,31,200', incentives: 'Rs 18,400' },
  ],
  billing: ORGANIZATIONS.map((organization, index) => ({
    organization: organization.name,
    subscription: organization.subscription,
    employees: organization.employees,
    invoice: `Rs ${(65000 + index * 18500).toLocaleString('en-IN')}`,
    usage: `${72 + (index % 6) * 4}% engagement`,
  })),
  revenue: [
    { label: 'MRR', value: 'Rs 18.4L', delta: '+14% vs last month' },
    { label: 'Active organizations', value: String(ORGANIZATIONS.length), delta: '+3 this quarter' },
    { label: 'Retention', value: '95%', delta: 'Strong among enterprise cohorts' },
    { label: 'Engagement', value: '81%', delta: 'Improving with mentor workflow' },
  ],
};

const quality = [
  { id: 'qa-1', label: 'Flagged AI plans', count: plans.filter((plan) => plan.state === 'revision_requested').length, detail: 'Macro mismatch or unsafe intensity' },
  { id: 'qa-2', label: 'High-risk biomarker review', count: employees.filter((employee) => employee.biomarkers.some((item) => item.status === 'critical')).length, detail: 'HbA1c, CRP, Vitamin D' },
  { id: 'qa-3', label: 'Plan audit queue', count: plans.filter((plan) => ['consultant_review', 'consultant_modified', 'senior_review'].includes(plan.state)).length, detail: 'Awaiting scoring or reviewer notes' },
  { id: 'qa-4', label: 'Quality score', count: '93/100', detail: 'Strong senior review compliance' },
];

const organizationOverview = {
  metrics: [
    { label: 'Participation', value: '82%', detail: 'Across enrolled employees' },
    { label: 'Burnout indicator', value: '16%', detail: 'High-risk cohort, aggregated only' },
    { label: 'Intervention adoption', value: '69%', detail: 'Hydration and sleep programs' },
    { label: 'Recovery trend', value: '+11 pts', detail: 'Rolling 30-day readiness shift' },
  ],
  trends: ORGANIZATIONS.slice(0, 6).map((organization, index) => ({
    team: organization.name,
    readiness: 58 + index * 3,
    burnout: 9 + index * 2,
  })),
};

const notifications = [
  { id: 'nt-1', title: 'Plan review reminder', body: `${plans.filter((plan) => ['consultant_review', 'senior_review'].includes(plan.state)).length} plans are waiting for review before end of day.`, kind: 'review' },
  { id: 'nt-2', title: 'Report upload alert', body: `${reportPipeline[0]?.employee || 'A client'} uploaded a new biomarker file.`, kind: 'report' },
  { id: 'nt-3', title: 'Session reminder', body: `${sessions[0]?.type || 'Recovery session'} with ${sessions[0]?.employee || 'client'} begins soon.`, kind: 'session' },
  { id: 'nt-4', title: 'Intervention follow-up', body: `${employees.filter((employee) => employee.interventions.some((item) => item.adherence < 45)).length} employees need intervention follow-up.`, kind: 'intervention' },
  { id: 'nt-5', title: 'Burnout cluster detected', body: 'Multiple high-stress employees are clustering inside Zenith Forge and BlueOrbit Systems.', kind: 'alert' },
  { id: 'nt-6', title: 'Published plan feedback', body: 'Recent client meal feedback requires consultant response in 6 threads.', kind: 'communication' },
];

const todayOps = [
  { label: 'Sessions today', value: sessions.filter((session) => session.when.startsWith('Today')).length, detail: `${sessions.filter((session) => session.practitioner === 'Maya Iyer').length} mentor, ${sessions.filter((session) => session.practitioner !== 'Maya Iyer').length} consultant` },
  { label: 'Plans pending review', value: plans.filter((plan) => ['consultant_review', 'consultant_modified', 'senior_review'].includes(plan.state)).length, detail: `${employees.filter((employee) => employee.biomarkers.some((item) => item.status === 'critical')).length} critical biomarker links` },
  { label: 'Employees needing attention', value: highRisk.length * 3, detail: 'Across glucose, sleep, stress, and adherence' },
  { label: 'Overdue follow-ups', value: tasks.filter((task) => task.status === 'overdue').length, detail: 'Operational queue priority for this week' },
];

export const platformSeed = {
  priorityQueue,
  todayOps,
  recoveryAlerts,
  inbox,
  employees,
  plans,
  reportPipeline,
  sessions,
  tasks,
  communicationThreads,
  finance,
  quality,
  organizationOverview,
  notifications,
  knowledgeBase: KNOWLEDGE_BASE,
};

export function buildInitialPlatformState() {
  return JSON.parse(JSON.stringify(platformSeed));
}

export function findUserByCredentials(email, password) {
  return sampleUsers.find(
    (user) => user.email.toLowerCase() === String(email).trim().toLowerCase() && user.password === password
  );
}

export function findUserByEmail(email) {
  return sampleUsers.find((user) => user.email.toLowerCase() === String(email).trim().toLowerCase());
}

export function getRoleDisplayName(role) {
  const roleKey = String(role || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
  const labels = {
    practitioner: 'Practitioner',
    consultant: 'Consultant',
    senior_consultant: 'Senior Consultant',
    mentor: 'Mentor',
    organization_admin: 'Organization Admin',
    employee: 'Employee',
    provider: 'Consultant',
    team_lead: 'Mentor',
    corporate_admin: 'Organization Admin',
    admin: 'Senior Consultant',
    superuser: 'Platform Owner',
    super_admin: 'Platform Owner',
    platform_owner: 'Platform Owner',
  };

  return labels[roleKey] || 'Practitioner';
}
