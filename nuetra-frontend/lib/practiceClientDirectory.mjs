function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(`Practice client directory ${label} is invalid.`);
  }
  return value;
}

export function normalizePracticeClientDirectory(payload) {
  const directory = requireObject(payload?.success === true ? payload.data : payload, 'response');
  if (!Array.isArray(directory.clients)) {
    throw new TypeError('Practice client directory clients collection is invalid.');
  }
  const pagination = requireObject(directory.pagination, 'pagination');
  for (const field of ['total', 'limit', 'offset']) {
    if (!Number.isInteger(pagination[field]) || pagination[field] < 0) {
      throw new TypeError(`Practice client directory pagination.${field} is invalid.`);
    }
  }

  return {
    ...directory,
    clients: directory.clients.map((client) => {
      requireObject(client, 'client');
      const clientId = client.clientId ?? client.id;
      if (clientId === undefined || clientId === null || String(clientId).trim() === '') {
        throw new TypeError('Practice client directory client identifier is invalid.');
      }
      return {
        ...client,
        id: String(clientId),
        clientId: String(clientId),
        connectionId: client.connectionId ? String(client.connectionId) : null,
        displayName: client.displayName || client.name || 'Unnamed client',
      };
    }),
    pagination: { ...pagination },
  };
}
