# Migration, flags, rollback, and support

Migration `0056_external_fiteatsy_connections` is additive and targets Practice Operations PostgreSQL only. It creates seven isolated tables and supporting indexes/constraints; it does not alter Fiteatsy or Internal tables.

Flags (all default `false`):

- `EXTERNAL_FITEATSY_CONNECTION_ENABLED`
- `EXTERNAL_FITEATSY_HEALTH_ACCESS_ENABLED`
- `EXTERNAL_FITEATSY_DIET_PUBLISH_ENABLED`
- `EXTERNAL_FITEATSY_SCHEDULING_ENABLED`

Enable only after the pepper and inbound public verification key are configured. Rollback order: disable flags, confirm no in-flight redemption, revert application, then downgrade only under an approved data-retention decision. Never log or export raw connection material. Support may inspect correlation IDs, invitation status/hint, expiry, connection state, consent version, and event history.
