import assert from 'node:assert/strict';
import test from 'node:test';

import { collectAllClientAllocationPages } from '../lib/clientAllocationPagination.mjs';

test('collects every client beyond the first allocation-pool page', async () => {
  const source = Array.from({ length: 205 }, (_, index) => ({ userId: `client-${index + 1}` }));
  const requests = [];

  const clients = await collectAllClientAllocationPages(({ limit, offset }) => {
    requests.push({ limit, offset });
    return Promise.resolve(source.slice(offset, offset + limit));
  });

  assert.equal(clients.length, 205);
  assert.deepEqual(requests, [
    { limit: 100, offset: 0 },
    { limit: 100, offset: 100 },
    { limit: 100, offset: 200 },
  ]);
  assert.equal(clients.at(-1).userId, 'client-205');
});

test('deduplicates a client if pages shift during refresh', async () => {
  const pages = [
    [{ userId: 'client-1' }, { userId: 'client-2' }],
    [{ userId: 'client-2' }],
  ];

  const clients = await collectAllClientAllocationPages(
    () => Promise.resolve(pages.shift() || []),
    { pageSize: 2 },
  );

  assert.deepEqual(clients.map((client) => client.userId), ['client-1', 'client-2']);
});
