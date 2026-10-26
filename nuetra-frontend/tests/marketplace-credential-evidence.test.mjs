import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const external = await readFile(new URL("../components/external/ExternalMarketplace.jsx", import.meta.url), "utf8");
const governance = await readFile(new URL("../components/platform/MarketplaceGovernanceModule.jsx", import.meta.url), "utf8");
const api = await readFile(new URL("../lib/practiceOperationsApi.js", import.meta.url), "utf8");

test("optional consultant qualification evidence supports common safe formats up to 10 MB", () => {
  assert.match(external, /accept="\.jpg,\.jpeg,\.png,\.webp,\.pdf,image\/jpeg,image\/png,image\/webp,application\/pdf"/);
  assert.match(external, /Certificate file \(optional\)/);
  assert.match(api, /image\/webp/);
  assert.match(api, /application\/pdf/);
  assert.match(api, /file\.size>10\*1024\*1024/);
  assert.match(api, /evidence-finalise/);
});

test("Super Admin receives the private certificate for a simple manual decision", () => {
  assert.match(governance, /Loading certificate photo/);
  assert.match(governance, /Private certificate photo for Zestiva manual review/);
  assert.match(governance, /evidenceAttached && evidenceState!=="ready"/);
  assert.match(governance, /getAdminMarketplaceQualificationEvidence/);
  assert.match(governance, /Verify qualification/);
  assert.match(governance, /Reject qualification/);
});

test("consultant form avoids vault identifiers and institutional workflow language", () => {
  assert.doesNotMatch(external, /Document Vault UUID/);
  assert.doesNotMatch(external, /Link existing evidence/);
  assert.match(external, /certificate\s+photo is optional/i);
  assert.match(external, /manual Super Admin review/);
});

test("qualification saving is not blocked by missing or failed optional evidence", () => {
  assert.doesNotMatch(external, /if \(!certificate\)/);
  assert.match(external, /The qualification was saved, but the optional certificate could not be attached/);
  assert.match(external, /No certificate attached — Super Admin can still review manually/);
});

test("consultants can confirm and delete a saved qualification", () => {
  assert.match(api, /deleteMarketplaceQualification/);
  assert.match(api, /method:'DELETE'/);
  assert.match(external, /Delete qualification/);
  assert.match(external, /window\.confirm\(`Delete/);
  assert.match(external, /Qualification deleted\. Profile completeness has been updated\./);
});
