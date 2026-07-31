from typing import TypedDict


class AgentState(TypedDict):
    project_id: int
    project_idea: str
    project_manager: dict | None
    business_analyst: dict | None
    product_owner: dict | None
    solution_architect: dict | None
    database_engineer: dict | None
    api_designer: dict | None
    backend_developer: dict | None
    security_engineer: dict | None
    qa_engineer: dict | None
    frontend_developer: dict | None
    code_reviewer: dict | None
    documentation_writer: dict | None
    devops_engineer: dict | None
    current_agent: str | None
    error: str | None
    approval_mode: bool | None
    approval_status: str | None
    pending_approval: dict | None
    approval_history: list | None


def get_initial_state(project_id: int, project_idea: str, approval_mode: bool = False) -> AgentState:
    """Helper to return a fresh default AgentState dictionary with canonical keys."""
    return {
        "project_id": project_id,
        "project_idea": project_idea,
        "project_manager": None,
        "business_analyst": None,
        "product_owner": None,
        "solution_architect": None,
        "database_engineer": None,
        "api_designer": None,
        "backend_developer": None,
        "security_engineer": None,
        "qa_engineer": None,
        "frontend_developer": None,
        "code_reviewer": None,
        "documentation_writer": None,
        "devops_engineer": None,
        "current_agent": None,
        "error": None,
        "approval_mode": approval_mode,
        "approval_status": None,
        "pending_approval": None,
        "approval_history": []
    }
