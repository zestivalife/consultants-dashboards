import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  foodPreferenceSections,
  formatFoodPreferenceValue,
  mapConsultantFoodPreferences,
} from '../lib/foodPreferencePresentation.mjs';

const workspace = (overrides = {}) => ({
  foodPreferences: {
    status: 'COMPLETE',
    updatedAtISO: '2026-09-03T10:00:00.000Z',
    profile: {
      dietType: 'vegetarian',
      proteins: ['Paneer', 'Pulses'],
      cuisines: ['South Indian', 'Maharashtrian', 'North Indian'],
      foodsLiked: ['Poha', 'Idli'],
      foodsDisliked: ['Oats', 'Bitter gourd'],
      foodsAvoided: ['Mushroom', 'Shellfish'],
      likedFoodIds: ['food-poha', 'food-idli'],
      dislikedFoodIds: ['food-oats'],
      avoidedFoodIds: ['food-mushroom'],
      restrictions: ['No onion after sunset'],
      staplePreference: 'rice',
      dairyPreference: 'allowed',
      practicality: ['Quick preparation', 'Office-friendly'],
    },
  },
  healthProfile: {
    foodAllergies: ['Peanuts', 'Sesame'],
    foodIntolerances: ['Lactose'],
  },
  ...overrides,
});

test('adapter preserves every canonical field and all ordered multi-values', () => {
  const mapped = mapConsultantFoodPreferences(workspace());
  assert.deepEqual(mapped.hard, {
    dietPattern: 'Vegetarian',
    avoidedFoods: ['Mushroom', 'Shellfish'],
    avoidedFoodIds: ['food-mushroom'],
    allergies: ['Peanuts', 'Sesame'],
    intolerances: ['Lactose'],
    restrictions: ['No onion after sunset'],
  });
  assert.deepEqual(mapped.soft, {
    preferredCuisines: ['South Indian', 'Maharashtrian', 'North Indian'],
    staplePreference: 'Rice',
    dairyPreference: 'Allowed',
    preferredProteins: ['Paneer', 'Pulses'],
    likes: ['Poha', 'Idli'],
    likedFoodIds: ['food-poha', 'food-idli'],
    dislikes: ['Oats', 'Bitter gourd'],
    dislikedFoodIds: ['food-oats'],
    practicality: ['Quick preparation', 'Office-friendly'],
  });
});

test('hard and soft semantics stay visibly separate', () => {
  const sections = foodPreferenceSections(mapConsultantFoodPreferences(workspace()));
  assert.deepEqual(sections.map(({ key }) => key), ['hard', 'soft']);
  assert.deepEqual(sections[0].fields.map(([label]) => label), ['Diet Pattern', 'Avoided Foods', 'Allergies', 'Intolerances', 'Dietary / Clinical Restrictions']);
  assert.deepEqual(sections[1].fields.map(([label]) => label), ['Preferred Cuisines', 'Staple / Base Preference', 'Dairy', 'Preferred Proteins', 'Likes', 'Dislikes', 'Practicality / Lifestyle']);
});

test('partial and empty fields render truthfully without invented values', () => {
  const mapped = mapConsultantFoodPreferences(workspace({
    foodPreferences: { status: 'PARTIAL', profile: { cuisines: ['Maharashtrian'] } },
    healthProfile: { foodAllergies: [], foodIntolerances: [] },
  }));
  assert.deepEqual(mapped.soft.preferredCuisines, ['Maharashtrian']);
  assert.equal(formatFoodPreferenceValue(mapped.soft.preferredCuisines), 'Maharashtrian');
  assert.equal(formatFoodPreferenceValue(mapped.soft.preferredProteins), 'Not provided');
  assert.equal(formatFoodPreferenceValue(mapped.hard.allergies), 'Not provided');
  assert.equal(formatFoodPreferenceValue(mapped.hard.dietPattern), 'Not provided');
});

test('mapping clients independently prevents cross-client residue', () => {
  const clientA = mapConsultantFoodPreferences(workspace());
  const clientB = mapConsultantFoodPreferences(workspace({
    foodPreferences: { status: 'PARTIAL', profile: { dietType: 'vegan', cuisines: ['Gujarati'] } },
    healthProfile: { foodAllergies: ['Cashew'], foodIntolerances: [] },
  }));
  assert.deepEqual(clientA.soft.preferredCuisines, ['South Indian', 'Maharashtrian', 'North Indian']);
  assert.deepEqual(clientB.soft.preferredCuisines, ['Gujarati']);
  assert.deepEqual(clientB.hard.allergies, ['Cashew']);
  assert.equal(clientB.soft.likes.length, 0);
});

test('production adapter and Consultant profile render the canonical projection', async () => {
  const [adapter, component] = await Promise.all([
    readFile(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8'),
    readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8'),
  ]);
  assert.match(adapter, /foodPreferences: mapConsultantFoodPreferences\(body\)/);
  assert.match(component, /key: 'Food Preferences', label: 'Food Preferences'/);
  assert.match(component, /'Food Preferences': renderFoodPreferences/);
  assert.match(component, /setRealClientProfile\(null\)/);
  assert.doesNotMatch(component, /Recommended cuisine/i);
});
