import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const workspace=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const vault=fs.readFileSync(new URL('../components/external/ExternalDocumentVault.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const portal=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');

test('P23 provides a permission-gated Document Vault workspace',()=>{
  assert.match(workspace,/DOCUMENT_VIEW/);
  assert.match(workspace,/ExternalDocumentVault clients=\{clients\}/);
  assert.match(vault,/Document Vault unavailable/);
  assert.match(vault,/confirmed empty result/);
});

test('P23 uploads directly through short-lived storage and finalises server-side',()=>{
  assert.match(api,/pending\.upload\.url/);
  assert.match(api,/method:'PUT'/);
  assert.match(api,/\/finalise/);
  assert.doesNotMatch(vault,/object_key|access.key|secret/i);
  assert.match(api,/uploadVaultDocumentVersion/);
  assert.match(vault,/New version/);
});

test('P23 enforces accepted file policy and 50 MB user guidance',()=>{
  assert.match(vault,/Maximum 50 MB/);
  assert.match(vault,/accept="\.pdf,\.jpg,\.jpeg,\.png,\.txt,\.csv,\.doc,\.docx,\.xls,\.xlsx"/);
});

test('P23 exposes only shared vault documents in the existing portal',()=>{
  assert.match(portal,/downloadPortalVaultDocument/);
  assert.match(portal,/item\.source==='VAULT'/);
  assert.match(portal,/No documents have been submitted or shared/);
});
