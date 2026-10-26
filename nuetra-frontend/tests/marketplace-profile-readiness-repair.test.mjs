import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const marketplace = readFileSync(
  new URL("../components/external/ExternalMarketplace.jsx", import.meta.url),
  "utf8",
);
const preview = readFileSync(
  new URL("../pages/consultants/[slug].js", import.meta.url),
  "utf8",
);

test("professional profile uses accessible governed choices instead of comma-separated text", () => {
  for (const label of [
    "Specialisations",
    "Languages",
    "Consultation modes",
    "Session duration",
    "Areas of focus",
    "Previous workplaces",
  ])
    assert.match(marketplace, new RegExp(`label=\"${label}\"`));
  assert.match(marketplace, /function ChoiceField/);
  assert.match(marketplace, /aria-pressed/);
  for (const option of [
    "Clinical nutrition",
    "Hindi",
    "Online video",
    "Diet planning",
    "Hospital",
  ])
    assert.match(marketplace, new RegExp(option));
  assert.match(marketplace, /session_duration:\s*\[30,\s*45,\s*60/);
});

test("existing account telephone is reused and photo state survives the reload contract", () => {
  assert.match(marketplace, /canonicalPhone/);
  assert.match(marketplace, /Account telephone/);
  assert.match(
    marketplace,
    /setForm\(\(current\) => \(\{[\s\S]*profile_photo_url: saved\.profile_photo_url/,
  );
  assert.match(marketplace, /setPreview\(form\.profile_photo_url \|\| ""\)/);
});

test("draft preview is private, themed and separate from public publication", () => {
  assert.match(marketplace, /preview=draft/);
  for (const value of [
    "Private draft preview",
    "noindex,nofollow",
    "Only your authenticated consultant session",
    "fff7cf",
    "Profile and credentials reviewed",
  ])
    assert.match(preview, new RegExp(value));
  assert.match(preview, /getMarketplaceProfile\(false\)/);
  assert.match(preview, /getPublicConsultant\(slug\)/);
});

test("profile explains actionable submission blockers and review lifecycle", () => {
  for (const value of [
    "Ready for review",
    "Complete the items above",
    "Qualification evidence is verified during Super Admin review",
    "explicitly published",
  ])
    assert.match(marketplace, new RegExp(value));
});
