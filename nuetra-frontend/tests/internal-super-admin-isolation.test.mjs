import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const roleRoutes=fs.readFileSync(new URL('../lib/roleRoutes.js',import.meta.url),'utf8');
const ownerRoutes=fs.readFileSync(new URL('../lib/ownerConsoleRoutes.js',import.meta.url),'utf8');
const layout=fs.readFileSync(new URL('../components/platform/OwnerConsoleLayout.jsx',import.meta.url),'utf8');

test('internal super admin reaches only the Internal owner workspace',()=>{
  assert.match(roleRoutes,/internal_super_admin:\s*'\/dashboard\/owner'/);
  assert.match(roleRoutes,/internal-platform-operations/);
  assert.match(layout,/INTERNAL_OWNER_ROUTE_SLUGS\.has\(item\.slug\)/);
});

test('External Marketplace and food authority are not assigned to internal super admin',()=>{
  const internalSet=ownerRoutes.split('INTERNAL_OWNER_ROUTE_SLUGS = new Set(',2)[1].split(');',1)[0];
  assert.doesNotMatch(internalSet,/marketplace/);
  const foodSet=roleRoutes.match(/FOOD_AUTHORISATION_ROLE_KEYS = new Set\(([^;]+)\)/s)?.[1]||'';
  assert.doesNotMatch(foodSet,/internal_super_admin/);
});
