# Unified Consultant Domain Router

Infrastructure-only entry layer for `consultant.nuetra.in`. It keeps the sealed in-house and external Consultant frontends independently deployable while selecting the authenticated workspace from canonical backend tenant context.

Required production environment:

- `IN_HOUSE_ORIGIN=https://consultants-dashboards.vercel.app`
- `EXTERNAL_ORIGIN=https://external-consultant.vercel.app`
- `CANONICAL_AUTH_ME_URL=<accepted gateway /api/v1/auth/me URL>`
- `ROUTING_STATE_SECRET=<random secret of at least 32 characters>`

The public domain must not be moved until preview acceptance and both product regression suites pass.
