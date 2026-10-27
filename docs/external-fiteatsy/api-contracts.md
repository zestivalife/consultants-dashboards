# API contracts

Consultant routes require the established External tenant/user context. Mobile routes require a short-lived RS256 Fiteatsy assertion with issuer, audience, expiry, subject, and `actor_type=FITEATSY_USER`.

- `POST /api/v1/practice-operations/fiteatsy-connections/invitations`
- `GET /api/v1/practice-operations/fiteatsy-connections`
- `GET /api/v1/practice-operations/fiteatsy-connections/{id}`
- `POST .../invitations/{id}/revoke`
- `POST .../{id}/revoke`
- `POST .../{id}/programmes` and `POST .../programmes/{programmeId}/action`
- `POST .../{id}/diet-plans` and `POST .../{id}/appointments`
- `POST /api/v1/fiteatsy-connections/preview`
- `POST /api/v1/fiteatsy-connections/redeem`
- `GET /api/v1/fiteatsy-connections`
- `GET /api/v1/fiteatsy-connections/{id}`
- `DELETE /api/v1/fiteatsy-connections/{id}`
- `GET /api/v1/fiteatsy-connections/{id}/diet-plans`
- `GET /api/v1/fiteatsy-connections/{id}/appointments`

PIN preview does not imply consent. Redemption is atomic and records the accepted consent version/scopes.
