# DNS Diagnostics

## Purpose
Differentiate DNS resolution problems from broader network failures.

## Category
Network

## Symptoms
Approved IP tests work while hostnames fail, or name lookup returns inconsistent results.

## Preconditions
Basic connectivity has been checked and only fictional or approved test names are used.

## Diagnostic Steps
1. Record the failing hostname and exact lookup response.
2. Inspect configured DNS server addresses without changing them.
3. Resolve one approved internal test name and one approved public test name.
4. Compare results with another lab device on the same network.
5. Record cache and resolver observations for Network Support.

## Recommended Actions
Correct only a documented local lab misconfiguration with human authorization; otherwise preserve evidence.

## Escalation Criteria
Escalate when multiple devices fail, authoritative records may be wrong, or DNS infrastructure changes are required.

## References
Fictional SupportOps lab guide; source `dns-diagnostics.md`.

