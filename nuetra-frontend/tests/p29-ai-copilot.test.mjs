import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalAiCopilot.jsx',import.meta.url),'utf8');
test('P29 shows provider truth and AI_DRAFT classification',()=>{assert.match(ui,/AI runtime provider not configured/);assert.match(ui,/No AI output is fabricated/);assert.match(ui,/AI_DRAFT/);assert.match(ui,/mandatory human review/)});
test('P29 explicitly forbids autonomous clinical and operational actions',()=>{for(const word of ['diagnose','prescribe','publish plans','send messages','take payments','mutate health records'])assert.match(ui,new RegExp(word));assert.match(ui,/Autonomous actions: NO/)});
