# Outlook Email Sending Issue

## Purpose
Guide first-line diagnosis when Outlook Desktop cannot send messages in the fictional SupportOps lab.

## Category
Microsoft 365

## Symptoms
Messages remain in Outbox, sending reports an error, or Outlook shows disconnected.

## Preconditions
The technician has the exact error and can ask the user to test an approved web-mail simulation. No administrative access is required.

## Diagnostic Steps
1. Record the exact error, time, and whether all messages or only large attachments fail.
2. Verify general network connectivity using the approved network procedure.
3. Compare with the fictional web-mail test to separate client and service symptoms.
4. Confirm Outlook is not in Work Offline mode and inspect the Outbox for an oversized message.
5. Restart Outlook once and record whether the symptom changes.

## Recommended Actions
Remove an oversized test attachment, leave Work Offline mode, or collect reproducible evidence for Messaging Support. Do not change tenant settings.

## Escalation Criteria
Escalate when web mail also fails, several users are affected, the exact error persists after safe client checks, or account policy changes appear necessary.

## References
Fictional SupportOps lab guide; source `outlook-send-failure.md`.

