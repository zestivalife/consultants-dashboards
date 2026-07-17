# 06 Code Review Standard

Document ID: EDO-06  
Version: 1.0  
Status: ACTIVE  
Owner: Engineering Leadership  
Review Frequency: Monthly and after major incidents

---

## Purpose

Define engineering review standards for code changes.

## Scope

Applies to backend, frontend, infrastructure, tests, scripts and documentation-as-code.

## Review Criteria

Reviewers must evaluate:

- Maintainability.
- Readability.
- Performance.
- Security.
- Testability.
- Consistency with existing patterns.
- Documentation alignment.
- API compatibility.
- Backward compatibility.
- Error handling.
- Observability.
- Accessibility for UI changes.
- Migration safety for database changes.

## Required Evidence

Every code review should include:

- Scope summary.
- Affected services and pages.
- Tests run.
- Migration impact where relevant.
- Runtime verification where relevant.
- Known limitations.

## Inputs

- Pull request.
- Impact analysis.
- Test results.
- Relevant docs.

## Outputs

- Approved change.
- Requested changes.
- Risk notes.

## Dependencies

- Coding Standards.
- API Guidelines.
- Database Guidelines.
- Security Guidelines.

## Success Metrics

- Fewer regressions.
- Less duplicate logic.
- Improved readability.
- More consistent APIs and UI patterns.

## Risks

- Review fatigue.
- Superficial approval without runtime evidence.
- Overlooking backward compatibility.

## Related Documents

- `docs/CODING_STANDARDS.md`
- `docs/API_GUIDELINES.md`
- `docs/DATABASE_GUIDELINES.md`
- `docs/SECURITY.md`

## Related ADRs

- None at creation.

