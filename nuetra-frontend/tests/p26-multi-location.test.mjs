import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalLocations.jsx',import.meta.url),'utf8');
test('P26 keeps one tenant and reports every branch integration',()=>{assert.match(ui,/One practice tenant/);for(const label of ['Team','Clients','Appointments','Services','Invoices','Leads'])assert.match(ui,new RegExp(label));});
test('P26 distinguishes loading failure and confirmed empty',()=>{assert.match(ui,/Loading locations/);assert.match(ui,/role="alert"/);assert.match(ui,/confirmed empty result/)});
