import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const read=(file)=>fs.readFileSync(new URL(`../${file}`,import.meta.url),'utf8');

test('owner console exposes authenticated grievance management',()=>{
  const routes=read('lib/ownerConsoleRoutes.js');const page=read('components/platform/OwnerConsolePage.jsx');const module=read('components/platform/GrievanceManagementModule.jsx');const api=read('lib/fiteatsyConsultantsApi.js');
  assert.match(routes,/slug: 'grievances'/);assert.match(page,/GrievanceManagementModule/);
  assert.match(module,/Search grievances/);assert.match(module,/Audit timeline/);assert.match(module,/updateAdminGrievance/);
  assert.match(api,/requestFiteatsy\(`\/v1\/admin\/grievances/);
  assert.match(api,/Authorization: `Bearer \$\{token\}`/);
});
