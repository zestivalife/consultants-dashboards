import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const api=fs.readFileSync(new URL('../lib/publicMarketplaceApi.js',import.meta.url),'utf8');
test('public booking can request only a server-authoritative promotion quote',()=>{assert.match(api,/quotePublicPromotion/);assert.match(api,/promotions\/quote/);assert.doesNotMatch(api,/discountMinor\s*=/);});
