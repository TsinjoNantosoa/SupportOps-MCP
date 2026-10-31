from __future__ import annotations

import hmac
from datetime import datetime
from typing import Literal

import uvicorn
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.applications import Starlette
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from supportops.config import Settings
from supportops.services.approval_service import ApprovalError, ApprovalService
from supportops.services.audit_service import record_audit
from supportops.services.ticket_service import TicketService
from supportops.storage.seed import initialize_database


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str = Field(pattern=r"^(APPROVE|REJECT)$")
    session_id: str = Field(min_length=1, max_length=200)
    decision_key: str = Field(min_length=1, max_length=200)


class ErrorEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    execution_id: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$")
    workflow_id: str | None = Field(default=None, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$")
    correlation_id: str | None = Field(
        default=None, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$"
    )
    error_code: Literal[
        "MCP_CONNECTION_ERROR",
        "MCP_TIMEOUT",
        "OPENAI_ERROR",
        "VALIDATION_ERROR",
        "APPROVAL_DENIED",
        "EXPIRED_PROPOSAL",
        "STALE_PROPOSAL",
        "DATABASE_ERROR",
        "WORKFLOW_ERROR",
    ]
    occurred_at: datetime
    status: Literal["FAILED"] = "FAILED"


def create_app(settings: Settings | None = None) -> Starlette:
    settings = settings or Settings.load()
    db = initialize_database(settings.db_path)
    tickets = TicketService(db)
    approvals = ApprovalService(db)

    def service_authorized(request: Request) -> bool:
        if not settings.approval_api_token:
            return False
        supplied = request.headers.get("authorization", "")
        return hmac.compare_digest(supplied, f"Bearer {settings.approval_api_token}")

    def authenticated_approver(request: Request) -> str | None:
        supplied = request.headers.get("authorization", "")
        matched_actor: str | None = None
        for actor, token in settings.approver_tokens:
            if hmac.compare_digest(supplied, f"Bearer {token}"):
                matched_actor = actor
        return matched_actor

    async def health(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "remote_decisions_enabled": settings.remote_approval_enabled,
                "approver_identity_mode": (
                    "individual_bearer" if settings.approver_tokens else "local_cli_only"
                ),
            }
        )

    async def get_proposal(request: Request) -> JSONResponse:
        if not service_authorized(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            proposal = tickets.get_proposal(request.path_params["proposal_id"])
        except LookupError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        return JSONResponse(proposal.model_dump(mode="json"))

    async def decide(request: Request) -> JSONResponse:
        approver = authenticated_approver(request)
        if approver is None:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        if not settings.remote_approval_enabled:
            return JSONResponse(
                {
                    "error": "remote_decisions_disabled",
                    "message": "Use the trusted local CLI approval flow.",
                },
                status_code=403,
            )
        try:
            content_length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return JSONResponse({"error": "invalid_content_length"}, status_code=400)
        if content_length > settings.max_request_body_size:
            return JSONResponse({"error": "request_too_large"}, status_code=413)
        try:
            payload = DecisionRequest.model_validate(await request.json())
            result = approvals.decide(
                request.path_params["proposal_id"],
                approve=payload.decision == "APPROVE",
                session_id=payload.session_id,
                actor=approver,
                trusted_controller=True,
                decision_key=payload.decision_key,
            )
        except ValidationError as exc:
            return JSONResponse({"error": "validation_error", "details": exc.errors()}, 422)
        except LookupError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except PermissionError as exc:
            return JSONResponse({"error": str(exc)}, status_code=403)
        except ApprovalError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        return JSONResponse(result)

    async def record_error_event(request: Request) -> JSONResponse:
        if not service_authorized(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            content_length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return JSONResponse({"error": "invalid_content_length"}, status_code=400)
        if content_length > settings.max_request_body_size:
            return JSONResponse({"error": "request_too_large"}, status_code=413)
        try:
            payload = ErrorEventRequest.model_validate(await request.json())
        except ValidationError as exc:
            return JSONResponse({"error": "validation_error", "details": exc.errors()}, 422)
        with db.transaction(immediate=True) as connection:
            event_id = record_audit(
                connection,
                actor="n8n-service",
                action="WORKFLOW_ERROR_RECORDED",
                target_type="n8n_execution",
                target_id=payload.execution_id,
                outcome=payload.error_code,
                details={
                    "workflow_id": payload.workflow_id,
                    "correlation_id": payload.correlation_id,
                    "occurred_at": payload.occurred_at.isoformat(),
                    "status": payload.status,
                },
            )
        return JSONResponse({"recorded": True, "audit_event_id": event_id}, status_code=201)

    app = Starlette(
        debug=False,
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/proposals/{proposal_id:str}", get_proposal, methods=["GET"]),
            Route("/proposals/{proposal_id:str}/decision", decide, methods=["POST"]),
            Route("/events/errors", record_error_event, methods=["POST"]),
        ],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(settings.approval_allowed_hosts),
    )
    return app


def main() -> None:
    settings = Settings.load()
    uvicorn.run(
        create_app(settings),
        host=settings.approval_host,
        port=settings.approval_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
