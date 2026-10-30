from __future__ import annotations

import asyncio
import json
from typing import Annotated

import typer

from supportops.config import Settings
from supportops.services.approval_service import ApprovalError, ApprovalService
from supportops.services.audit_service import list_audit
from supportops.services.ticket_service import TicketService
from supportops.storage.seed import initialize_database

app = typer.Typer(help="SupportOps MCP AI IT Helpdesk Copilot")


def _services() -> tuple[Settings, TicketService, ApprovalService]:
    settings = Settings.load()
    db = initialize_database(settings.db_path)
    return settings, TicketService(db), ApprovalService(db)


@app.command()
def init(
    reset: Annotated[bool, typer.Option("--reset", help="Replace local demo data.")] = False,
) -> None:
    """Initialize deterministic fictional demo data."""
    settings = Settings.load()
    initialize_database(settings.db_path, reset=reset)
    typer.echo(f"Initialized SupportOps database: {settings.db_path}")


@app.command()
def demo() -> None:
    """Call both independent MCP servers over stdio without OpenAI."""
    from supportops.mcp_client import run_demo

    settings = Settings.load()
    initialize_database(settings.db_path)
    typer.echo(json.dumps(asyncio.run(run_demo()), indent=2, default=str))


@app.command()
def tickets(status: str | None = None, priority: str | None = None, limit: int = 20) -> None:
    """List local fictional tickets."""
    from supportops.models.ticket import Priority, TicketStatus

    _, service, _ = _services()
    rows = service.list_tickets(
        TicketStatus(status.upper()) if status else None,
        Priority(priority.upper()) if priority else None,
        limit,
    )
    typer.echo(json.dumps(rows, indent=2, default=str))


@app.command()
def proposals(status: str | None = None) -> None:
    """List persisted ticket update proposals."""
    _, service, _ = _services()
    typer.echo(json.dumps(service.list_proposals(status.upper() if status else None), indent=2))


def _decide(proposal_id: str, approve: bool, yes: bool) -> None:
    settings, service, approval = _services()
    proposal = service.get_proposal(proposal_id)
    typer.echo(json.dumps(proposal.model_dump(mode="json"), indent=2))
    verb = "APPROVE and apply exactly these changes" if approve else "REJECT this proposal"
    if not yes and not typer.confirm(verb, default=False):
        typer.echo("Cancelled; proposal remains PENDING.")
        raise typer.Exit()
    try:
        result = approval.decide(
            proposal_id,
            approve=approve,
            session_id=settings.session_id,
            actor=settings.user_id,
            trusted_controller=True,
        )
    except (ApprovalError, PermissionError, LookupError) as exc:
        typer.echo(f"Decision refused: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2))


@app.command()
def approve(proposal_id: str, yes: Annotated[bool, typer.Option("--yes")] = False) -> None:
    """Apply a proposal after explicit trusted-terminal confirmation."""
    _decide(proposal_id, True, yes)


@app.command()
def reject(proposal_id: str, yes: Annotated[bool, typer.Option("--yes")] = False) -> None:
    """Reject a proposal after explicit trusted-terminal confirmation."""
    _decide(proposal_id, False, yes)


@app.command()
def audit(limit: int = 100) -> None:
    """Display local audit events."""
    settings = Settings.load()
    db = initialize_database(settings.db_path)
    typer.echo(json.dumps(list_audit(db, limit), indent=2))


@app.command()
def chat() -> None:
    """Start an interactive OpenAI agent connected to both MCP servers."""
    from supportops.agent.copilot import run_copilot

    typer.echo("SupportOps AI Copilot (type 'exit' to quit)")
    while True:
        prompt = typer.prompt("You")
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        try:
            typer.echo(f"Assistant: {asyncio.run(run_copilot(prompt))}")
        except RuntimeError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
