import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const external = await readFile(new URL("../components/external/ExternalMarketplace.jsx", import.meta.url), "utf8");
const governance = await readFile(new URL("../components/platform/MarketplaceGovernanceModule.jsx", import.meta.url), "utf8");
const api = await readFile(new URL("../lib/practiceOperationsApi.js", import.meta.url), "utf8");

test("consultant qualification evidence accepts only JPEG up to one megabyte", () => {
  assert.match(external, /accept="\.jpg,\.jpeg,image\/jpeg"/);
  assert.match(external, /maximum 1 MB/);
  assert.match(api, /file\.type!=='image\/jpeg'/);
  assert.match(api, /file\.size>1024\*1024/);
  assert.match(api, /evidence-finalise/);
});

test("Super Admin receives the private certificate for a simple manual decision", () => {
  assert.match(governance, /Loading certificate photo/);
  assert.match(governance, /Private certificate photo for Zestiva manual review/);
  assert.match(governance, /evidenceState!=="ready"/);
  assert.match(governance, /getAdminMarketplaceQualificationEvidence/);
  assert.match(governance, /Approve certificate/);
  assert.match(governance, /Reject certificate/);
});

test("consultant form avoids vault identifiers and institutional workflow language", () => {
  assert.doesNotMatch(external, /Document Vault UUID/);
  assert.doesNotMatch(external, /Link existing evidence/);
  assert.match(external, /upload a clear photo of its certificate/i);
  assert.match(external, /manual Super Admin review/);
});
