from langgraph.graph import END
from orchestrator.state import AgentState


def should_continue(state: AgentState) -> str:
    """
    Determine the next node or termination based on state.
    Provides conditional routing and failure recovery exits.
    """
    if state.get("error"):
        return END

    current = state.get("current_agent")
    if not current:
        return END

    # Supported Routing Destinations
    valid_agents = {
        "business_analyst",
        "product_owner",
        "solution_architect",
        "database_engineer",
        "api_designer",
        "backend_developer",
        "security_engineer",
        "qa_engineer",
        "frontend_developer",
        "code_reviewer",
        "documentation_writer",
        "devops_engineer"
    }

    if current in valid_agents:
        return current

    return END
