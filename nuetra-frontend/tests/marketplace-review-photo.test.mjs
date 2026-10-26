import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const governance = await readFile(
  new URL("../components/platform/MarketplaceGovernanceModule.jsx", import.meta.url),
  "utf8",
);

test("Super Admin review shows the submitted marketplace photo", () => {
  assert.match(governance, /p\.profile_photo_url && !photoFailed/);
  assert.match(governance, /profile submission/);
  assert.match(governance, /onError=\{\(\) => setPhotoFailed\(true\)\}/);
  assert.match(governance, /place-items-center text-xl font-bold/);
});

test("Super Admin review presents structured marketplace data without raw JSON", () => {
  assert.match(governance, /Proposed public profile/);
  assert.match(governance, /ReviewCollection title="Services"/);
  assert.match(governance, /ReviewCollection title="Programmes"/);
  assert.match(governance, /ReviewCollection title="Public locations"/);
  assert.doesNotMatch(governance, /JSON\.stringify\(v\)/);
  assert.match(governance, /sticky bottom-0/);
  assert.match(governance, /const requiresReason = actions\.some/);
  assert.match(governance, /Publishing makes this exact submitted version visible/);
});

test("Super Admin review explains independent review and website visibility", () => {
  assert.match(governance, /Review in Credentials queue/);
  assert.match(governance, /item\.public_visibility\?'Visible':'Hidden'/);
  assert.match(governance, /Super Admin publication makes the reviewed profile visible/);
  assert.match(governance, /PUBLISH_SUBMISSION/);
});

test("Super Admin inventory opens the governed review surface for draft profiles", () => {
  assert.match(governance, /item\.profile_id/);
  assert.match(governance, /openReview\(item\)/);
  assert.match(governance, /Review profile/);
  assert.match(governance, /consultant must submit this draft/i);
});
