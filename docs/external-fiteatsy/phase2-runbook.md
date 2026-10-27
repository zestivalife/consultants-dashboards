# Phase 2 Fiteatsy Connection Runbook

## Added configuration

- `EXTERNAL_FITEATSY_BACKEND_URL`
- `EXTERNAL_FITEATSY_OUTBOUND_PRIVATE_KEY`
- `EXTERNAL_FITEATSY_OUTBOUND_KEY_ID`
- `EXTERNAL_FITEATSY_OUTBOUND_ISSUER=zestiva-platform`
- `EXTERNAL_FITEATSY_OUTBOUND_AUDIENCE=fiteatsy-backend`

The private key remains in practice-operations only. Fiteatsy stores its public half. The reciprocal Fiteatsy assertion private key remains in the Fiteatsy backend only; practice-operations stores its public half.

## Migration

Apply `0057_fit_redeem_idempotency` after `0056_fiteatsy_connections`, then `0058_fit_active_plan`. The migrations add replay-safe redemption evidence and an explicit single active external diet-plan selection per Fiteatsy user without rewriting Phase 1 history. Downgrade is intentionally prohibited because connection, plan-selection, and consent audit evidence is retained.

## Verification

1. Confirm all feature flags are false by default.
2. Run `pytest -q services/practice-operations-service/tests/test_fiteatsy_connections.py` on Python 3.12.
3. Verify a six-digit PIN preview returns only approved public consultant fields and requested scopes.
4. Redeem with an idempotency UUID; replay the same request and confirm the same relationship is returned.
5. Confirm a different user cannot replay the PIN.
6. Confirm expired, used, and revoked PINs produce distinct structured errors.
7. With health access enabled in staging, verify existing and newly uploaded reports appear from canonical Fiteatsy storage.
8. Confirm original file download fails after disconnect and never returns a permanent URL.
9. Connect a second consultant and prove tenant, plan, appointment, and revocation isolation.

## Rollback

Disable `EXTERNAL_FITEATSY_HEALTH_ACCESS_ENABLED`, `EXTERNAL_FITEATSY_DIET_PUBLISH_ENABLED`, `EXTERNAL_FITEATSY_SCHEDULING_ENABLED`, then `EXTERNAL_FITEATSY_CONNECTION_ENABLED`. Do not delete connection, consent, or event rows. Re-enable only after the cause is fixed and negative-access tests pass.
