import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const page=readFileSync(new URL("../pages/index.js",import.meta.url),"utf8");
const source=readFileSync(new URL("../components/public-consultant/ConsultantLanding.jsx",import.meta.url),"utf8");
const css=readFileSync(new URL("../styles/ConsultantLanding.module.css",import.meta.url),"utf8");
const app=readFileSync(new URL("../pages/_app.js",import.meta.url),"utf8");

test("public root is isolated in its own component",()=>{
  assert.match(page,/public-consultant\/ConsultantLanding/);
  assert.doesNotMatch(source,/fetch\(|axios|\/api\//);
  assert.match(app,/router\.pathname === '\/'/);
  assert.match(app,/marketing root is deliberately isolated/);
});
test("approved identity, metadata, video and CTA destinations are exact",()=>{
  assert.match(source,/Zestiva Consultant — Intelligent Practice OS/);
  assert.match(source,/hf_20260601_110537_3a579fa0-7bbc-4d94-9d25-0e816c7840f5\.mp4/);
  assert.match(source,/https:\/\/consultant\.nuetra\.in\/login/);
  assert.match(source,/https:\/\/consultant\.nuetra\.in\/signup/);
  assert.match(source,/canonical/);
});
test("video supports desktop delta scrubbing and mobile playback",()=>{
  assert.match(source,/min-width: 1024px/);
  assert.match(source,/deltaX/);
  assert.match(source,/currentTime/);
  assert.match(source,/Math\.max\(0,Math\.min/);
  assert.match(source,/muted loop playsInline autoPlay/);
});
test("required landing narrative is complete",()=>{
  for(const phrase of ["Everything connected","Practice intelligence","Health intelligence","Health Records","Profile reconciliation","Client360","Care workflow","Built for real practices","Privacy by design"]){assert.ok(source.includes(phrase),phrase)}
});
test("responsive, touch target and reduced-motion rules exist",()=>{
  assert.match(css,/min-height:44px/);
  assert.match(css,/@media\(max-width:620px\)/);
  assert.match(css,/@media\(max-width:359px\)/);
  assert.match(css,/prefers-reduced-motion:reduce/);
});
