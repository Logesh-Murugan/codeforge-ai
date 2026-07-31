from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.state import AgentState, get_initial_state
from orchestrator.nodes import (
    project_manager_node,
    business_analyst_node,
    product_owner_node,
    solution_architect_node,
    database_engineer_node,
    api_designer_node,
    backend_developer_node,
    security_engineer_node,
    qa_engineer_node,
    frontend_developer_node,
    code_reviewer_node,
    documentation_writer_node,
    devops_engineer_node
)
from orchestrator.edges import should_continue


# Build the modular state graph
graph = StateGraph(AgentState)

# Register all compiled modular nodes
graph.add_node("project_manager", project_manager_node)
graph.add_node("business_analyst", business_analyst_node)
graph.add_node("product_owner", product_owner_node)
graph.add_node("solution_architect", solution_architect_node)
graph.add_node("database_engineer", database_engineer_node)
graph.add_node("api_designer", api_designer_node)
graph.add_node("backend_developer", backend_developer_node)
graph.add_node("security_engineer", security_engineer_node)
graph.add_node("qa_engineer", qa_engineer_node)
graph.add_node("frontend_developer", frontend_developer_node)
graph.add_node("code_reviewer", code_reviewer_node)
graph.add_node("documentation_writer", documentation_writer_node)
graph.add_node("devops_engineer", devops_engineer_node)

# Define entry point and conditional routing pathways
graph.set_entry_point("project_manager")
graph.add_conditional_edges("project_manager", should_continue)
graph.add_conditional_edges("business_analyst", should_continue)
graph.add_conditional_edges("product_owner", should_continue)
graph.add_conditional_edges("solution_architect", should_continue)
graph.add_conditional_edges("database_engineer", should_continue)
graph.add_conditional_edges("api_designer", should_continue)
graph.add_conditional_edges("backend_developer", should_continue)
graph.add_conditional_edges("security_engineer", should_continue)
graph.add_conditional_edges("qa_engineer", should_continue)
graph.add_conditional_edges("frontend_developer", should_continue)
graph.add_conditional_edges("code_reviewer", should_continue)
graph.add_conditional_edges("documentation_writer", should_continue)
graph.add_conditional_edges("devops_engineer", should_continue)

# Configure MemorySaver checkpointer for state persistence
memory = MemorySaver()
app = graph.compile(checkpointer=memory)


async def run_pipeline(project_id: int, project_idea: str, approval_mode: bool = False):
    """Run the modular agent pipeline under a thread checkpoint config."""
    initial_state = get_initial_state(project_id, project_idea, approval_mode=approval_mode)
    config = {"configurable": {"thread_id": f"project_{project_id}"}}
    
    async for state in app.astream(initial_state, config):
        pass


def get_pipeline_state(project_id: int) -> AgentState | None:
    """Retrieve current checkpoint state for a project."""
    config = {"configurable": {"thread_id": f"project_{project_id}"}}
    state_snapshot = app.get_state(config)
    if state_snapshot and state_snapshot.values:
        return state_snapshot.values
    return None


async def resume_pipeline(project_id: int):
    """Resume execution of a paused pipeline for a project."""
    config = {"configurable": {"thread_id": f"project_{project_id}"}}
    current_values = get_pipeline_state(project_id)
    if not current_values:
        raise ValueError(f"No checkpointed state found for project {project_id}")
    
    # Resume streaming from current snapshot
    async for state in app.astream(None, config):
        pass


def update_graph_state(project_id: int, state_update: dict):
    """Update checkpoint state values for a given project thread."""
    config = {"configurable": {"thread_id": f"project_{project_id}"}}
    app.update_state(config, state_update)

