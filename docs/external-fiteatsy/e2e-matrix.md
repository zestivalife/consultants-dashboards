# Phase 1 E2E matrix

Automated contract coverage accompanies the scenarios below. Authenticated Fiteatsy mobile rendering is explicitly `DEFERRED_TO_PHASE_2`; it is not claimed as tested because the mobile app is frozen.

1. Create unbound PIN. 2. Create client-bound PIN. 3. Display PIN once. 4. Copy PIN. 5. WhatsApp share. 6. Expiry. 7. Revoke. 8. Invalid PIN. 9. Expired PIN. 10. Replayed PIN. 11. Atomic concurrent redemption. 12. Invalid identity JWT. 13. Wrong actor. 14. Consent subset. 15. Consent escalation denied. 16. Multiple consultants per Fiteatsy user. 17. Consultant tenant isolation. 18. Mobile subject isolation. 19. Consultant revoke. 20. Mobile disconnect. 21. Programme lifecycle. 22. Plan idempotency/version attribution. 23. Appointment idempotency. 24. Feature-disabled fail closed. 25. No Internal/Fiteatsy source regression.

Production browser acceptance and mobile UX remain release gates after Phase 2 implementation and explicit deployment approval.
