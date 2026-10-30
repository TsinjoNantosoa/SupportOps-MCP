# Network Connectivity Troubleshooting

## Purpose
Provide a deterministic N1 sequence for connectivity symptoms in the fictional lab.

## Category
Network

## Symptoms
No internet indication, unreachable approved test endpoints, or intermittent connectivity.

## Preconditions
Use only approved diagnostic endpoints and read-only operating-system status commands.

## Diagnostic Steps
1. Record scope: one device, one location, or several users.
2. Check cable or Wi-Fi state and verify a plausible IP configuration.
3. Test the configured gateway, then an approved IP endpoint, then an approved hostname.
4. Compare IP connectivity with name resolution and follow the DNS procedure if they differ.
5. Record packet loss and timestamps without changing network equipment.

## Recommended Actions
Reconnect a loose cable or approved Wi-Fi profile and collect evidence. Do not reset shared switches, firewalls, or routers.

## Escalation Criteria
Escalate multi-user impact, gateway failure, persistent packet loss, or any required infrastructure change.

## References
Fictional SupportOps lab guide; source `network-troubleshooting.md`.

