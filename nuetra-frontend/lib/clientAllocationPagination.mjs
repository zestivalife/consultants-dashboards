export async function collectAllClientAllocationPages(loadPage, { pageSize = 100 } = {}) {
  const clients = [];
  const seenUserIds = new Set();
  let offset = 0;

  while (true) {
    const page = await loadPage({ limit: pageSize, offset });

    page.forEach((client) => {
      if (!client?.userId || seenUserIds.has(client.userId)) return;
      seenUserIds.add(client.userId);
      clients.push(client);
    });

    if (page.length < pageSize) break;
    offset += page.length;
  }

  return clients;
}
