from pydantic import BaseModel, ConfigDict


class Procedure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    procedure_id: str
    title: str
    category: str
    preconditions: str
    diagnostic_steps: list[str]
    escalation_criteria: str
    source_reference: str
