# Consent and threat model

- Raw PINs are returned once and never persisted; HMAC-SHA256 verifiers use a production secret pepper.
- PINs exclude ambiguous characters, expire within 1–168 hours, are single-use, revocable, and locked transactionally during redemption.
- High entropy plus Gateway/IP throttling protects unknown-PIN attempts; known records enforce attempt ceilings.
- Mobile identity is never accepted from request parameters. Only verified asymmetric assertions establish the Fiteatsy subject.
- Consent is scope-limited, versioned, auditable, and independently revocable by either side.
- Every consultant query includes tenant and consultant ownership. Every mobile query includes the asserted Fiteatsy subject.
- Plan and appointment writes are idempotent. Publication never changes another plan's active state.
- Logs and events contain identifiers/status metadata, never PINs, tokens, credentials, or clinical payloads.
- Key rotation uses overlapping public verification keys at the control plane; the application receives only public keys.
