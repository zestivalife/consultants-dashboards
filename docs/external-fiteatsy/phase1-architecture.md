# External Consultant ↔ Fiteatsy — Phase 1 architecture

## Boundary

Practice Operations owns invitations, consultant relationships, consent receipts, programmes, plan publications, appointment projections, and audit events. Fiteatsy remains the canonical source for the consumer identity and consumer health record. No Fiteatsy health data is copied into a second clinical store.

`External Consultant UI → Gateway → Practice Operations → connection ledger`

`Fiteatsy authenticated user → Gateway → asymmetric identity verification → atomic PIN redemption`

## Parity matrix

| Capability | Internal | External Phase 1 |
|---|---:|---:|
| Authenticated consumer identity | Existing | Contract complete |
| Explicit scoped consent | Existing policy | Implemented |
| Health context | Canonical Fiteatsy | Live-reference contract; Phase 2 adapter pending |
| Diet-plan publication | Existing | Versioned/idempotent contract |
| Scheduling | Existing | Idempotent projection contract |
| Mobile screens | Existing | Phase 2; Fiteatsy app untouched |

Feature flags default off. Internal Consultant and Fiteatsy application source are unchanged.
