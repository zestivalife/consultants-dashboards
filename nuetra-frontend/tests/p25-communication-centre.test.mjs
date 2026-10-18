import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalCommunicationWorkspace.jsx',import.meta.url),'utf8');
test('P25 exposes all truthful preparation channels',()=>{for(const value of ['EMAIL_PREPARATION','SMS_PREPARATION','CLIENT_PORTAL_NOTIFICATION'])assert.match(ui,new RegExp(value));assert.match(ui,/Prepared only · not sent, delivered or read/);assert.match(ui,/WhatsApp opened/)});
test('P25 keeps failed and confirmed-empty states distinct',()=>{assert.match(ui,/role="alert"/);assert.match(ui,/confirmed empty result/);assert.match(ui,/Loading activity/)});
