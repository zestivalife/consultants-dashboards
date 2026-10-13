export const EXTERNAL_P1_MODULES = Object.freeze({
  clientPortal: { title: 'Client portal', audience: ['CLIENT'], capability: 'client_portal', empty: 'Nothing has been shared with this client yet.', sections: ['Current diet plan', 'Published plan history', 'Appointments', 'Goals and progress', 'Tasks', 'Check-ins', 'Shared reports', 'Package status', 'Consultant contact'] },
  team: { title: 'Practice team', audience: ['OWNER'], capability: 'practice_team', empty: 'No team members are available.', sections: ['Team', 'Practitioner profile', 'Roles and status', 'Locations', 'Client assignments', 'Transfers', 'Workload', 'Practice branding'] },
  billing: { title: 'Billing & packages', audience: ['OWNER', 'CONSULTANT'], capability: 'billing_packages', empty: 'No package or billing records are available.', sections: ['Packages', 'Invoices', 'Receipts', 'Payment history'] },
  renewals: { title: 'Renewals', audience: ['OWNER', 'CONSULTANT'], capability: 'package_renewals', empty: 'No renewal information is available.', sections: ['Days remaining', 'Consultations remaining', 'Follow-ups remaining', 'Renewal due'] },
  analytics: { title: 'Analytics', audience: ['OWNER', 'CONSULTANT'], capability: 'practice_analytics', empty: 'Connect a verified data source to view analytics.', sections: ['Client activity', 'Intake completion', 'Care activity', 'Retention', 'Workload', 'Engagement', 'Connected revenue'] },
  templates: { title: 'Templates', audience: ['OWNER', 'CONSULTANT'], capability: 'practice_templates', empty: 'No templates have been created.', sections: ['Diet plans', 'Consultation notes', 'Follow-ups', 'Goals', 'Messages', 'Assessments'] },
  assessments: { title: 'Assessment builder', audience: ['OWNER', 'CONSULTANT'], capability: 'assessment_builder', empty: 'Create an assessment when this capability is enabled.', sections: ['Nutrition', 'Lifestyle', 'PCOS', 'Diabetes', 'Stress', 'Fitness readiness', 'Follow-up questionnaire', 'Custom'] },
  communication: { title: 'Communication centre', audience: ['OWNER', 'CONSULTANT', 'COORDINATOR'], capability: 'communication_centre', empty: 'No communication history is available.', sections: ['Invitations', 'Reminders', 'Plan sharing', 'Renewals', 'Report requests'] },
  referrals: { title: 'Referrals', audience: ['OWNER', 'CONSULTANT'], capability: 'referrals', empty: 'No referrals have been recorded.', sections: ['Doctor', 'Psychologist', 'Physiotherapist', 'Fitness trainer', 'Dietitian', 'Other professional'] },
  progressReport: { title: 'Progress report', audience: ['OWNER', 'CONSULTANT'], capability: 'progress_reports', empty: 'There is not enough authorised client data to build a report.', sections: ['Starting vs current', 'Measurements', 'Goals', 'Biomarker changes', 'Diet plan history', 'Adherence', 'Check-in summary', 'Consultant notes'] },
  export: { title: 'Data export', audience: ['OWNER', 'CONSULTANT'], capability: 'practice_exports', empty: 'No export is available for your current permissions.', sections: ['Client list', 'Measurements', 'Consultation history', 'Diet plan history', 'Billing', 'Analytics'] },
  audit: { title: 'Practice audit', audience: ['OWNER'], capability: 'practice_audit', empty: 'No audit activity matches these filters.', sections: ['Client access', 'Profile changes', 'Report uploads', 'Plan changes', 'Publishing', 'Downloads'] },
});

export const ASSESSMENT_CONTROLS = Object.freeze(['SINGLE_SELECT', 'MULTI_SELECT', 'YES_NO', 'NUMBER', 'SCALE', 'TEXT', 'DATE', 'TIME', 'UPLOAD', 'CONDITIONAL_SECTION']);
export const TEMPLATE_ACTIONS = Object.freeze(['PREVIEW', 'USE', 'DUPLICATE', 'EDIT', 'ARCHIVE']);
export const EXPORT_FORMATS = Object.freeze({ client_list: ['CSV'], measurements: ['CSV', 'PDF'], consultation_history: ['CSV', 'PDF', 'DOCX'], diet_plan_history: ['PDF', 'DOCX'], billing: ['CSV', 'PDF'], analytics: ['CSV', 'PDF'] });

export function getModuleDefinition(moduleKey) {
  const definition = EXTERNAL_P1_MODULES[moduleKey];
  if (!definition) throw new Error(`Unknown external P1 module: ${moduleKey}`);
  return definition;
}
