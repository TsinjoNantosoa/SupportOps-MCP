# SupportOps MCP V2.2 — présentation portfolio

SupportOps est un copilote local de support IT sur données fictives. n8n orchestre une conversation et deux serveurs MCP Python : Ticketing pour les incidents et Knowledge pour les procédures. Python conserve l'autorité sur la validation, SQLite, les transactions, l'approbation humaine et l'audit.

Le projet démontre la récupération d'`INC-1042`, la recherche de la procédure Outlook, un diagnostic sourcé, une proposition `PENDING`, puis une décision locale vérifiée avec idempotence, expiration, contrôle de version et audit. L'exécution OpenAI live, Wait/resume navigateur et l'approbation distante restent explicitement **NON VÉRIFIÉS** tant qu'un credential et une identité forte ne sont pas configurés.

Stack : Python, MCP, Streamable HTTP, n8n, appels d'outils OpenAI, SQLite, Docker Compose, pytest et Ruff. Aucune connexion à des clients, Microsoft 365, Windows, réseaux ou systèmes de production réels.
