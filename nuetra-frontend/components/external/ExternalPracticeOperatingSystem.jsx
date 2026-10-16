import { Activity, CalendarDays, ChevronRight, ClipboardList, FileText, Settings, Sparkles, UsersRound } from 'lucide-react';

/**
 * @typedef {Object} ExternalModuleVM
 * @property {string} id
 * @property {string} title
 * @property {string} description
 * @property {string[]} views
 * @property {string[]} actions
 * @property {'available'|'capability'} state
 */

const GROUPS = {
  care: { eyebrow: 'Client care', icon: UsersRound },
  workflow: { eyebrow: 'Practice workflow', icon: ClipboardList },
  growth: { eyebrow: 'Practice operations', icon: Activity },
  system: { eyebrow: 'Configuration', icon: Settings },
};

/** @type {Record<string, ExternalModuleVM & {group: keyof typeof GROUPS}>} */
export const EXTERNAL_MODULES = {
  consultations: { id:'consultations', title:'Consultations', group:'care', description:'Prepare, run and finish focused client consultations.', views:['Today','Upcoming','Completed','Follow-up Due','Cancelled'], actions:['Start Consultation','Save Notes','Complete & Schedule Follow-up'], state:'capability' },
  followups: { id:'followups', title:'Follow-ups', group:'care', description:'Keep due, overdue and upcoming client follow-ups visible.', views:['Due Today','Overdue','Upcoming','Completed'], actions:['Complete','Reschedule','Open Client','Add Note'], state:'capability' },
  goals: { id:'goals', title:'Goals & Progress', group:'care', description:'Track client goals and meaningful progress without unsupported conclusions.', views:['Weight','Measurements','Biomarkers','Hydration','Sleep','Activity','Adherence'], actions:['Add Goal','Update Progress','View Trend'], state:'capability' },
  checkins: { id:'checkins', title:'Check-ins', group:'care', description:'Review weekly check-ins, adherence and client-submitted photos.', views:['Weekly','Adherence','Meal Photos','Progress Photos','Attention'], actions:['Review Check-in','Request Update','Open Client'], state:'capability' },
  preconsult: { id:'preconsult', title:'Pre-consultation Summary', group:'care', description:'Review what changed since the last consultation without generating unsupported clinical conclusions.', views:['Measurements','Reports','Biomarkers','Adherence','Plan Changes'], actions:['Open Consultation','Review Changes','Add Note'], state:'capability' },
  reportCompare: { id:'reportCompare', title:'Report Comparison', group:'care', description:'Compare governed biomarker results across two source reports.', views:['Improved','Worsened','Unchanged','Outside Range','Returned to Range'], actions:['Select Reports','Review Biomarker','Open Source Report'], state:'capability' },
  attention: { id:'attention', title:'Attention Rules', group:'care', description:'Prioritise new reports, overdue follow-ups, incomplete intake and expiring plans.', views:['High Priority','Needs Review','Overdue','Upcoming'], actions:['Review','Open Client','Snooze'], state:'capability' },
  clientPortal: { id:'clientPortal', title:'Client Portal', group:'care', description:'Control the mobile browser experience for Consultant-published client information.', views:['Published Plans','Appointments','Goals','Reports','Tasks','Packages'], actions:['Preview Portal','Share Access','Review Visibility'], state:'capability' },
  communication: { id:'communication', title:'Communication', group:'care', description:'Coordinate reminders and client communication from governed templates.', views:['All','Invitations','Reminders','Plan Shares','Delivery History'], actions:['Send Reminder','Share Plan','Request Report'], state:'capability' },
  referrals: { id:'referrals', title:'Referrals', group:'care', description:'Record and follow referrals to allied health professionals.', views:['Open','Completed','All Professionals'], actions:['Add Referral','Update Status','Open Client'], state:'capability' },
  notes: { id:'notes', title:'Client Notes', group:'care', description:'Organise private, consultation, follow-up and nutrition notes.', views:['Recent','Pinned','Private','Archived'], actions:['Add Note','Pin','Archive'], state:'capability' },
  tasks: { id:'tasks', title:'Tasks', group:'workflow', description:'Prioritise report, plan, measurement and follow-up work.', views:['To Do','In Progress','Overdue','Completed'], actions:['Add Task','Complete','Reschedule'], state:'capability' },
  calendar: { id:'calendar', title:'Calendar', group:'workflow', description:'Agenda-first scheduling for consultations, follow-ups and tasks.', views:['Agenda','Today','Week','Month'], actions:['Book Consultation','Add Follow-up','Add Task'], state:'capability' },
  teleconsultation: { id:'teleconsultation', title:'Tele-consultation', group:'workflow', description:'Prepare meeting links, consultation status and governed notes.', views:['Upcoming','In Progress','Completed'], actions:['Add Meeting Link','Join Consultation','Open Notes'], state:'capability' },
  templates: { id:'templates', title:'Templates', group:'workflow', description:'Reusable Diet Plan, note, goal, message and assessment templates.', views:['Diet Plans','Consultation Notes','Follow-ups','Goals','Messages','Assessments'], actions:['Preview','Use Template','Duplicate'], state:'capability' },
  assessments: { id:'assessments', title:'Assessments', group:'workflow', description:'Build mobile-friendly governed forms and questionnaires.', views:['Nutrition','Lifestyle','Condition-specific','Follow-up','Custom'], actions:['Create Assessment','Mobile Preview','Archive'], state:'capability' },
  segments: { id:'segments', title:'Tags & Segments', group:'workflow', description:'Create safe tenant-scoped client groups and saved views.', views:['Tags','Smart Segments','Saved Views'], actions:['Add Tag','Create Segment','Save Current View'], state:'capability' },
  team: { id:'team', title:'Practice / Team', group:'growth', description:'Manage practice roles, workload, locations and client assignment.', views:['Team Members','Workload','Locations','Permissions'], actions:['Invite Member','Assign Client','Transfer Client'], state:'capability' },
  billing: { id:'billing', title:'Billing & Packages', group:'growth', description:'Manage packages, invoices, receipts and renewals.', views:['Packages','Invoices','Payments','Renewals'], actions:['Create Package','Record Payment','Send Renewal'], state:'capability' },
  renewals: { id:'renewals', title:'Package Renewals', group:'growth', description:'Track remaining days, consultations, follow-ups and renewal attention.', views:['Expiring Soon','Active','Expired','Renewed'], actions:['Open Package','Send Renewal','Record Renewal'], state:'capability' },
  analytics: { id:'analytics', title:'Analytics', group:'growth', description:'Understand practice activity, engagement and workload.', views:['Overview','Clients','Plans','Follow-ups','Revenue'], actions:['Change Period','Export'], state:'capability' },
  audit: { id:'audit', title:'Practice Audit', group:'growth', description:'Review practitioner-facing access and change history.', views:['All Activity','Client Access','Plan Changes','Downloads'], actions:['Filter','Export'], state:'capability' },
  exports: { id:'exports', title:'Data Export', group:'growth', description:'Prepare authorised client, measurement and practice exports.', views:['Client List','Measurements','Consultations','Diet Plans','Billing'], actions:['Export CSV','Export PDF','Export DOCX'], state:'capability' },
  progressReports: { id:'progressReports', title:'Progress Reports', group:'growth', description:'Prepare professional client progress summaries.', views:['Drafts','Generated','Shared'], actions:['Preview','Generate','Share'], state:'capability' },
  settings: { id:'settings', title:'Settings & Branding', group:'system', description:'Manage practice identity, branding, working hours and preferences.', views:['Profile','Branding','Contact','Working Hours','Notifications','Locations'], actions:['Edit Settings','Preview Diet Chart Branding'], state:'capability' },
};

export const PRACTICE_NAV = [
  ['consultations','Consultations',CalendarDays], ['followups','Follow-ups',ClipboardList],
  ['goals','Goals & Progress',Activity], ['tasks','Tasks',ClipboardList],
  ['calendar','Calendar',CalendarDays], ['templates','Templates',Sparkles],
  ['team','Practice / Team',UsersRound], ['analytics','Analytics',Activity],
  ['settings','Practice settings',Settings],
];

function StatePanel({ title, body, icon:Icon=Sparkles }) {
  return <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-6 sm:p-8">
    <span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-blue-700"><Icon size={22}/></span>
    <h3 className="mt-5 text-lg font-bold text-slate-950">{title}</h3>
    <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{body}</p>
  </div>;
}

export function ExternalPracticeModule({ view, clients=[] }) {
  const module = EXTERNAL_MODULES[view] || EXTERNAL_MODULES.tasks;
  const group = GROUPS[module.group];
  const GroupIcon = group.icon;
  const clientCount = clients.length;
  return <div className="space-y-6">
    <header className="rounded-[28px] bg-gradient-to-br from-[#0c1728] via-[#10294b] to-[#174f7e] p-6 text-white sm:p-8">
      <p className="text-xs font-bold uppercase tracking-[.18em] text-blue-200">{group.eyebrow}</p>
      <div className="mt-3 flex items-start gap-4"><span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-white/10"><GroupIcon size={23}/></span><div><h2 className="text-3xl font-bold tracking-tight">{module.title}</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-blue-100">{module.description}</p></div></div>
    </header>

    <nav aria-label={`${module.title} views`} className="flex gap-2 overflow-x-auto pb-1">
      {module.views.map((item,index)=><button key={item} aria-current={index===0?'page':undefined} className={`min-h-11 shrink-0 rounded-full px-4 text-sm font-semibold ${index===0?'bg-slate-950 text-white':'border border-slate-200 bg-white text-slate-700'}`}>{item}</button>)}
    </nav>

    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {module.actions.slice(0,3).map((action,index)=><article key={action} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><span className="text-xs font-bold uppercase tracking-wider text-blue-700">{index===0?'Primary action':'Workflow action'}</span><h3 className="mt-3 font-bold">{action}</h3><p className="mt-2 text-sm leading-6 text-slate-500">Available when the governed {module.title.toLowerCase()} service grants this tenant capability.</p><button disabled className="mt-5 flex min-h-11 w-full items-center justify-between rounded-xl bg-slate-100 px-4 text-sm font-semibold text-slate-500">Capability pending <ChevronRight size={17}/></button></article>)}
    </section>

    <StatePanel icon={group.icon} title={`${module.title} is prepared for activation`} body={`The complete mobile-first workspace is present without fabricated production data. ${clientCount ? `${clientCount} real tenant-scoped client record${clientCount===1?' is':'s are'} available to its adapter.` : 'No client data is fabricated for this state.'} Actions remain fail-closed until the matching backend contract and permission are available.`}/>

    <div className="fixed inset-x-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-20 lg:hidden"><div className="rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-xl backdrop-blur"><button disabled className="min-h-12 w-full rounded-xl bg-slate-200 px-4 font-bold text-slate-500">{module.actions[0]} · capability pending</button></div></div>
  </div>;
}
