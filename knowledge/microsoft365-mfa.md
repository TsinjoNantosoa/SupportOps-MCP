# Microsoft 365 MFA Troubleshooting

## Purpose
Guide safe evidence collection for fictional MFA enrollment and sign-in issues.

## Category
Identity

## Symptoms
Prompts repeat, a replaced demo phone is unavailable, or a verification method fails.

## Preconditions
Verify the fictional user's identity using the lab procedure. Never request a password, recovery code, or one-time code.

## Diagnostic Steps
1. Record the sign-in error and timestamp without collecting authentication secrets.
2. Confirm device time and network connectivity.
3. Identify whether an already registered method remains available.
4. Check the fictional service-health notice supplied by the lab coordinator.
5. Document the identity-verification result for the authorized Identity team.

## Recommended Actions
Guide use of an already registered method. Authentication-method resets require the authorized Identity team.

## Escalation Criteria
Escalate lost-device cases, suspected compromise, lockout, or any method reset.

## References
Fictional SupportOps lab guide; source `microsoft365-mfa.md`.

