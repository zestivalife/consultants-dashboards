import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalPayments.jsx',import.meta.url),'utf8');
test('P28 truthfully reports provider configuration',()=>{assert.match(ui,/Live payment provider not configured/);assert.match(ui,/No pay action is shown/);assert.match(ui,/Browser success authoritative: NO/)});
test('P28 keeps loading error and configured states distinct',()=>{assert.match(ui,/Loading payment provider/);assert.match(ui,/role="alert"/);assert.match(ui,/Razorpay configured/)});
