export async function loadConnectedClientDirectory({ listConnections, getHealthContext }, filters = {}) {
  const ledger = await listConnections();
  const connections = Array.isArray(ledger?.connections) ? ledger.connections : [];
  const active = connections.filter((connection) => connection?.state === 'ACTIVE');
  const clients = await Promise.all(active.map(async (connection) => {
    const scopes = new Set((connection.consented_scopes || []).map((scope) => String(scope).toUpperCase()));
    let profile = null;
    if (scopes.has('PROFILE')) {
      const context = await getHealthContext(connection.id);
      profile = context?.profile?.client || null;
      if (!profile) throw new Error('The connected client profile could not be retrieved with the authorised scope.');
    }
    return {
      id: String(connection.consultant_client_id || connection.id),
      connectionId: String(connection.id),
      connectionState: 'ACTIVE',
      displayName: profile?.name || 'Connected Fiteatsy client',
      email: profile?.email || '',
      mobile: profile?.mobile || profile?.mobileNumberMasked || '',
      status: 'ACTIVE',
      registrationDate: profile?.registrationDate || connection.connected_at || null,
      consentedScopes: [...scopes],
      profileAvailable: Boolean(profile),
      programmeStatus: connection.programme_status || null,
    };
  }));
  const query = String(filters.q || '').trim().toLowerCase();
  const status = String(filters.status || '').trim().toUpperCase();
  const filtered = clients.filter((client) => (!status || client.status === status) && (!query || `${client.displayName} ${client.email} ${client.mobile}`.toLowerCase().includes(query)));
  const limit = Math.max(1, Number(filters.limit) || 100);
  return { clients: filtered.slice(0, limit), pagination: { total: filtered.length, limit } };
}
