import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const shell = readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx', import.meta.url), 'utf8');
const account = readFileSync(new URL('../components/external/ExternalAccountMenu.jsx', import.meta.url), 'utf8');
const route = readFileSync(new URL('../pages/dashboard/consultant.js', import.meta.url), 'utf8');
const client360 = readFileSync(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');

test('external tenant resolves to the dedicated SaaS shell without touching the internal workspace', () => {
  assert.match(route, /workspace==='EXTERNAL'\)return <ExternalSaaSWorkspace\/>/);
  assert.match(route, /workspace==='IN_HOUSE'\)return <ConsultantWorkspace\/>/);
});

test('P0 shell exposes real navigation, command centre, client management, reports, and plans', () => {
  for (const label of ['Dashboard', 'Clients', 'Diet Plans', 'Reports', 'Needs your attention', 'Today', 'Recent activity']) {
    assert.match(shell, new RegExp(label));
  }
  assert.match(shell, /Search by name, mobile or email/);
  assert.match(shell, /Start with your first client/);
  assert.match(shell, /Version history/);
});

test('responsive and accessible controls remain available without hover-only actions', () => {
  assert.match(shell, /aria-label="Mobile navigation"/);
  assert.match(shell, /aria-current=/);
  assert.match(shell, /min-h-11/);
  assert.match(shell, /Skip to content/);
  assert.match(account, /event\.key==='Escape'/);
  assert.match(account, /data-testid="external-logout"/);
});

test('secondary modules and notifications use controlled, non-dead capability states',()=>{
  for(const label of ['Consultations','Follow-ups','Tasks','Templates','Analytics','Settings & Branding','Notifications'])assert.match(shell,new RegExp(label));
  assert.match(shell,/controlled empty state/);
  assert.match(shell,/aria-expanded=\{notificationsOpen\}/);
  assert.match(shell,/NotificationsDrawer/);
});

test('Client 360 accepts contextual deep links while retaining all P0 tabs', () => {
  assert.match(client360, /initialTab='Overview'/);
  for (const tab of ['Overview', 'Health Profile', 'Nutrition', 'Diet Plan', 'Measurements', 'Reports', 'Biomarkers', 'Timeline']) {
    assert.match(client360, new RegExp(tab));
  }
});
