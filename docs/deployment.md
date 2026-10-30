# Local deployment

## Docker

Copy `.env.example` to `.env`, choose strong local tokens, then run `docker compose up --build -d`. Ports are published to host loopback only. Attach an existing n8n container to the Compose network or replace workflow endpoints appropriately.

- n8n on Windows/Linux host: `http://127.0.0.1:8001/mcp` and `:8002/mcp`.
- n8n on the same Docker network: `http://supportops-ticketing:8001/mcp` and `http://supportops-knowledge:8002/mcp`.
- n8n container with Python on host: `http://host.docker.internal:8001/mcp` and `:8002/mcp`.
- Remote services: private routing, TLS, authentication, authorization, and adjusted allowlists are mandatory.

Check `docker compose ps` and service logs. Do not assume `127.0.0.1` inside an n8n container refers to the host.

SQLite is stored in the `supportops-data` volume and must remain centralized. Do not mount one SQLite file concurrently across machines.
