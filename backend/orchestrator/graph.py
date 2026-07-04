import logging
from typing import TypedDict
from sqlalchemy import select
from langgraph.graph import StateGraph, END

from app.db import AsyncSessionLocal
from app.models import Project, AgentRun
from agents.base_agent import AgentExecutionError
from agents.business_analyst import BusinessAnalystAgent
from agents.solution_architect import SolutionArchitectAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.doc_writer import DocWriterAgent

logger = logging.getLogger(__name__)


# Define the state
class AgentState(TypedDict):
    project_id: int
    project_idea: str
    business_requirements: dict | None
    solution_arch: dict | None
    backend_code: dict | None
    code_review: dict | None
    current_agent: str | None
    error: str | None


async def create_agent_run(
    project_id: int,
    agent_name: str,
    status: str,
    output_json: dict | None = None,
    error_message: str | None = None
) -> AgentRun:
    """Create a new AgentRun in the database."""
    async with AsyncSessionLocal() as session:
        agent_run = AgentRun(
            project_id=project_id,
            agent_name=agent_name,
            status=status,
            output_json=output_json,
            error_message=error_message
        )
        session.add(agent_run)
        await session.commit()
        await session.refresh(agent_run)
        return agent_run


async def update_agent_run(
    agent_run_id: int,
    status: str,
    output_json: dict | None = None,
    error_message: str | None = None
) -> AgentRun:
    """Update an existing AgentRun in the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AgentRun).where(AgentRun.id == agent_run_id))
        agent_run = result.scalar_one_or_none()
        if not agent_run:
            raise ValueError(f"AgentRun {agent_run_id} not found")
        
        agent_run.status = status
        if output_json:
            agent_run.output_json = output_json
        if error_message:
            agent_run.error_message = error_message
        
        await session.commit()
        await session.refresh(agent_run)
        return agent_run


async def update_project_files(project_id: int, files: list):
    """Save generated files to the database for the given project."""
    async with AsyncSessionLocal() as session:
        query = select(Project).where(Project.id == project_id)
        res = await session.execute(query)
        project = res.scalar_one_or_none()
        if project:
            project.generated_files = files
            await session.commit()


async def get_project_files(project_id: int) -> list:
    """Retrieve generated files from the database for the given project."""
    async with AsyncSessionLocal() as session:
        query = select(Project).where(Project.id == project_id)
        res = await session.execute(query)
        project = res.scalar_one_or_none()
        return project.generated_files if (project and project.generated_files) else []


async def business_analyst_node(state: AgentState) -> AgentState:
    """Run the Business Analyst agent."""
    project_id = state["project_id"]
    project_idea = state["project_idea"]
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "business_analyst", "running")
    
    try:
        agent = BusinessAnalystAgent()
        result = agent.run(project_idea)
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        return {
            **state,
            "business_requirements": result.model_dump(),
            "current_agent": "solution_architect",
            "error": None
        }
    except Exception as e:
        logger.error(f"Business Analyst agent failed: {e}", exc_info=True)
        await update_agent_run(
            agent_run.id,
            "failed",
            error_message=str(e)
        )
        return {
            **state,
            "error": str(e)
        }


async def solution_architect_node(state: AgentState) -> AgentState:
    """Run the Solution Architect agent."""
    project_id = state["project_id"]
    business_requirements = state["business_requirements"]
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "solution_architect", "running")
    
    try:
        if not business_requirements:
            raise ValueError("business_requirements is required")
        agent = SolutionArchitectAgent()
        from app.schemas import BusinessAnalystResponse
        result = agent.run(BusinessAnalystResponse(**business_requirements))
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        return {
            **state,
            "solution_arch": result.model_dump(),
            "current_agent": "backend_developer",
            "error": None
        }
    except Exception as e:
        logger.error(f"Solution Architect agent failed: {e}", exc_info=True)
        await update_agent_run(
            agent_run.id,
            "failed",
            error_message=str(e)
        )
        return {
            **state,
            "error": str(e)
        }


async def backend_developer_node(state: AgentState) -> AgentState:
    """Run the Backend Developer agent."""
    project_id = state["project_id"]
    solution_arch = state["solution_arch"]
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "backend_developer", "running")
    
    try:
        if not solution_arch:
            raise ValueError("solution_arch is required")
        agent = BackendDeveloperAgent()
        from app.schemas import SolutionArchitectResponse, BackendDeveloperResponse
        result = agent.run(SolutionArchitectResponse(**solution_arch))
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        # Save files to database
        files_list = [{"path": file.path, "content": file.content} for file in result.files]
        await update_project_files(project_id, files_list)
        
        return {
            **state,
            "backend_code": result.model_dump(),
            "current_agent": "code_reviewer",
            "error": None
        }
    except Exception as e:
        logger.error(f"Backend Developer agent failed: {e}", exc_info=True)
        await update_agent_run(
            agent_run.id,
            "failed",
            error_message=str(e)
        )
        return {
            **state,
            "error": str(e)
        }


async def code_reviewer_node(state: AgentState) -> AgentState:
    """Run the Code Reviewer agent."""
    project_id = state["project_id"]
    backend_code = state["backend_code"]
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "code_reviewer", "running")
    
    try:
        if not backend_code:
            raise ValueError("backend_code is required")
        agent = CodeReviewerAgent()
        from app.schemas import BackendDeveloperResponse, CodeReviewerResponse
        result = agent.run(BackendDeveloperResponse(**backend_code))
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        # Update auto-fixed files in database
        if result.auto_fixed_files:
            existing_files = await get_project_files(project_id)
            files_dict = {f["path"]: f["content"] for f in existing_files}
            for fixed_file in result.auto_fixed_files:
                files_dict[fixed_file.path] = fixed_file.content
            updated_files = [{"path": path, "content": content} for path, content in files_dict.items()]
            await update_project_files(project_id, updated_files)
        
        return {
            **state,
            "code_review": result.model_dump(),
            "current_agent": "doc_writer",
            "error": None
        }
    except Exception as e:
        logger.error(f"Code Reviewer agent failed: {e}", exc_info=True)
        await update_agent_run(
            agent_run.id,
            "failed",
            error_message=str(e)
        )
        return {
            **state,
            "error": str(e)
        }


async def doc_writer_node(state: AgentState) -> AgentState:
    """Run the Documentation Writer agent."""
    project_id = state["project_id"]
    project_idea = state["project_idea"]
    solution_arch = state.get("solution_arch")
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "doc_writer", "running")
    
    try:
        agent = DocWriterAgent()
        result = agent.run(project_idea, solution_arch)
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json={"documentation": result}
        )
        
        # Add README.md to database files
        existing_files = await get_project_files(project_id)
        files_dict = {f["path"]: f["content"] for f in existing_files}
        files_dict["README.md"] = result
        updated_files = [{"path": path, "content": content} for path, content in files_dict.items()]
        await update_project_files(project_id, updated_files)
        
        return {
            **state,
            "current_agent": None,
            "error": None
        }
    except Exception as e:
        logger.error(f"Documentation Writer agent failed: {e}", exc_info=True)
        await update_agent_run(
            agent_run.id,
            "failed",
            error_message=str(e)
        )
        return {
            **state,
            "error": str(e)
        }


def should_continue(state: AgentState) -> str:
    """Determine the next node or end."""
    if state.get("error"):
        return END
    if state.get("current_agent") == "solution_architect":
        return "solution_architect"
    if state.get("current_agent") == "backend_developer":
        return "backend_developer"
    if state.get("current_agent") == "code_reviewer":
        return "code_reviewer"
    if state.get("current_agent") == "doc_writer":
        return "doc_writer"
    return END


# Build the graph
graph = StateGraph(AgentState)

graph.add_node("business_analyst", business_analyst_node)
graph.add_node("solution_architect", solution_architect_node)
graph.add_node("backend_developer", backend_developer_node)
graph.add_node("code_reviewer", code_reviewer_node)
graph.add_node("doc_writer", doc_writer_node)

graph.set_entry_point("business_analyst")
graph.add_conditional_edges("business_analyst", should_continue)
graph.add_conditional_edges("solution_architect", should_continue)
graph.add_conditional_edges("backend_developer", should_continue)
graph.add_conditional_edges("code_reviewer", should_continue)
graph.add_conditional_edges("doc_writer", should_continue)

# Compile the graph
app = graph.compile()


async def run_pipeline(project_id: int, project_idea: str):
    """Run the full agent pipeline for a project."""
    initial_state: AgentState = {
        "project_id": project_id,
        "project_idea": project_idea,
        "business_requirements": None,
        "solution_arch": None,
        "backend_code": None,
        "code_review": None,
        "current_agent": None,
        "error": None
    }
    
    async for state in app.astream(initial_state):
        pass
