import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const api=await readFile(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
const proposal=await readFile(new URL('../components/platform/FoodProposalUx.jsx',import.meta.url),'utf8');
const editor=await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx',import.meta.url),'utf8');
const workspace=await readFile(new URL('../components/platform/PlatformWorkspace.jsx',import.meta.url),'utf8');

test('Food Library drawer provides the simple two-tab add and proposal flow',()=>{
  for(const value of ['Food Library','Propose New Food','Add Food','Replace Food','Add to Meal'])assert.ok(editor.includes(value),value);
  assert.match(editor,/role="tablist"/);assert.match(editor,/aria-selected/);assert.match(editor,/max-w-\[760px\]/);
});

test('consultant proposal UI preserves unknown nutrients and checks similar foods before submission',()=>{
  for(const value of ['Unknown nutrients may stay blank','Review Similar Foods','Similar foods already exist','Use Existing Food','Continue Proposal','Submit for Senior Review','Pending Review','Changes Requested'])assert.ok(proposal.includes(value),value);
  assert.match(proposal,/numberOrNull/);assert.doesNotMatch(proposal,/Math\.random|Edit Master Food/);
});

test('proposal API covers draft, edit, similarity, status, submit and governed Senior decision routes',()=>{
  for(const value of ['/food-proposals/similar','/food-proposals/mine','/food-proposals/review','/submit','/review'])assert.ok(api.includes(value),value);
  for(const method of ["method: 'POST'","method: 'PATCH'"])assert.ok(api.includes(method),method);
});

test('Senior review keeps food approval separate and exposes every backend decision',()=>{
  for(const value of ['Food Proposal Review','Food approval is separate from Diet Plan approval.','Approve as New','Reject as Duplicate','Use Existing Food Instead','Link as Alias','Request Changes','expectedRevision'])assert.ok(proposal.includes(value),value);
  assert.match(workspace,/SeniorFoodProposalReviewPanel/);
});

test('personalised plan context is compact, collapsed and backend-authored',()=>{
  for(const value of ['Plan Context','Generated using current client profile, food preferences and available biomarkers','Biomarkers affecting ranking','No governed generation rule'])assert.ok(editor.includes(value),value);
  assert.match(editor,/response\?\.generationSnapshot/);assert.doesNotMatch(editor,/generationSnapshot[^\n]+reduce\(/);
});
