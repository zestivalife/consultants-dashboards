import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const portal=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const dashboard=fs.readFileSync(new URL('../components/external/ExternalIntelligentHome.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const backend=fs.readFileSync(new URL('../../services/practice-operations-service/app/main.py',import.meta.url),'utf8');
test('P37 adds staged mobile-first portal onboarding without a second token system',()=>{for(const value of ['Get ready','Required progress','required steps complete','You’re ready for your consultation','min-h-11'])assert.match(portal,new RegExp(value.replace(/[’]/g,'’')));assert.match(backend,/issue_portal_token/);assert.doesNotMatch(portal,/diagnos/i)});
test('P37 exposes consultant readiness and explicit blockers',()=>{for(const value of ['Pre-consultation readiness','readinessPercent','blockers','Required steps only'])assert.match(dashboard,new RegExp(value));assert.match(backend,/CONSENT_PENDING|REQUIRED_INTAKE_PENDING/);assert.match(backend,/APPOINTMENT_APPROACHING_ONBOARDING_INCOMPLETE/)});
test('P37 frontend API supports governed invite, read model, and analytics',()=>{for(const value of ['getPreConsultation','invitePreConsultation','getPreConsultationAnalytics'])assert.match(api,new RegExp(value));assert.match(api,/pre-consultation\/invite/)});
