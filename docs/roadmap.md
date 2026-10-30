# Roadmap after V2 stabilization

1. Validate all exports on a pinned n8n test instance and add automated import/export compatibility checks.
2. Replace shared demo approval credentials with individual OIDC identity and policy-backed authorization.
3. Move centralized persistence to PostgreSQL for multi-service deployments.
4. Add OpenTelemetry metrics, centralized redacted logs, workflow SLAs, and alerting.
5. Add a React operator dashboard only when workflow operations justify it.
6. Evaluate Qdrant for a materially larger corpus.
7. Add authorized Jira/GLPI adapters, Teams notifications, support reporting, and SLA automation.
8. Consider multi-tenant SaaS controls only after identity, isolation, and audit are production-ready.
