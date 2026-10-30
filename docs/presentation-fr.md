# Présentation portfolio

SupportOps MCP V2 est une démonstration d'AI Automation Engineering où n8n orchestre un agent OpenAI et deux serveurs MCP Python spécialisés. Le serveur Ticketing expose des données fictives SQLite et prépare des propositions idempotentes. Le serveur Knowledge interroge six procédures Markdown autorisées. Les appels simples restent déterministes ; le modèle intervient uniquement pour comprendre et synthétiser.

La modification d'un ticket reste sous contrôle métier Python : validation humaine, session, expiration, version, autorisation, transaction atomique et audit. L'agent ne possède aucun outil d'approbation. Le projet démontre MCP Server Development, n8n Automation, tool calling, Human-in-the-Loop, sécurité transactionnelle, tests protocole stdio/HTTP et conteneurisation.

Toutes les données sont fictives. Le projet n'est pas présenté comme déployé chez un client réel.
