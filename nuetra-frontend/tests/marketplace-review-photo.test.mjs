import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const governance = await readFile(
  new URL("../components/platform/MarketplaceGovernanceModule.jsx", import.meta.url),
  "utf8",
);

test("Super Admin review shows the submitted marketplace photo", () => {
  assert.match(governance, /p\.profile_photo_url&&<img/);
  assert.match(governance, /profile submission/);
});

test("Super Admin review explains independent review and website visibility", () => {
  assert.match(governance, /Review in Credentials queue/);
  assert.match(governance, /item\.public_visibility\?'Visible':'Hidden'/);
  assert.match(governance, /Approval and publication are independent/);
});
