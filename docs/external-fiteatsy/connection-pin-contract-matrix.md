# Fiteatsy Consultant Connection PIN contract

This document records the service boundary used by the Fiteatsy mobile app to connect an authenticated user to an external consultant. A Connection PIN is never a Fiteatsy Login PIN and never creates or refreshes a Fiteatsy login session.

## Endpoint matrix

| Stage | Caller | Public path | Owner | Authentication | Request contract | Success contract | Persistence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Generate | Zestiva consultant UI | `POST /api/gateway/api/v1/practice-operations/fiteatsy-connections/invitations` | Practice Operations | Valid Zestiva consultant session, active tenant, external-consultant permission | Optional intended client; explicit requested scopes | Six-character numeric `pin`, `pin_hint`, expiry, invitation ID; PIN displayed once | Only the HMAC verifier and two-digit hint are stored |
| Preview | Fiteatsy backend | `POST /api/v1/fiteatsy-connections/preview` | Practice Operations | Short-lived RS256 Fiteatsy assertion with `actor_type=FITEATSY_USER` and `purpose=consultant_connection` | `{ "pin": "012345", "purpose": "CONSULTANT_CONNECTION_PIN" }` | Consultant projection, requested scopes, expiry, `consent_required=true` | No connection mutation |
| Redeem | Fiteatsy backend | `POST /api/v1/fiteatsy-connections/redeem` | Practice Operations | Same assertion as preview; UUID `Idempotency-Key` header required | PIN purpose, consent version, explicit accepted scopes | `connection_id`, `state=ACTIVE`, consented scopes | Invitation consumed, connection upserted, consent event appended atomically |
| List/revoke | Zestiva consultant UI | `/api/gateway/api/v1/practice-operations/fiteatsy-connections` | Practice Operations | Valid Zestiva consultant session and tenant | Tenant-scoped connection query or action | Active/revoked connection projection | Tenant-scoped connection/audit updates |

## Gateway behavior

`/api/v1/fiteatsy-connections/*` is routed to Practice Operations. The gateway delegates authentication for only that exact path boundary so the original Fiteatsy assertion reaches the owning service unchanged. It remains non-public: Practice Operations validates the signature, issuer, audience, expiry, actor type, and purpose.

## PIN format and compatibility

- All newly generated Connection PINs are exactly six numeric characters.
- PINs remain strings throughout the client and service path, preserving leading zeroes.
- Verification normalizes surrounding whitespace and ASCII letter case for existing unexpired legacy invitations. This is verification-only compatibility; new alphanumeric PINs cannot be generated.
- Login PIN values are rejected by the required request purpose and by the independent Connection PIN verifier namespace.

## Failure contracts

| Condition | Result |
| --- | --- |
| Missing, expired, revoked, consumed, or invalid PIN | Safe connection-specific error; no session mutation |
| Missing/wrong body purpose | Validation rejection |
| Wrong assertion actor or purpose | Authentication rejection |
| Missing/invalid idempotency key | Request rejection before mutation |
| Missing approved consultant profile | `CONSULTANT_PROFILE_UNAVAILABLE`; redemption is not offered |
| Scope outside invitation | Scope rejection |
| Same user retries same redemption key | Existing connection returned with the same response shape |
| Different replay or different user | Rejected |

## Before/after correction

Before this correction, the API Gateway had neither a route nor a delegated-auth boundary for `/api/v1/fiteatsy-connections`. It attempted to interpret the RS256 Fiteatsy assertion as a Zestiva login token, so valid preview and redemption requests could not reach Practice Operations.

After this correction, the path is routed to Practice Operations and the assertion is passed through for purpose-specific validation. The downstream request purpose is mandatory, profile readiness fails closed, idempotency is mandatory, and an idempotent replay returns the canonical `connection_id` response.
