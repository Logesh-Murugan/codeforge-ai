import logging
from typing import TypedDict
from sqlalchemy import select
from langgraph.graph import StateGraph, END

from app.db import AsyncSessionLocal
from app.models import Project, AgentRun
from agents.base_agent import AgentExecutionError
from agents.project_manager import ProjectManagerAgent
from agents.business_analyst import BusinessAnalystAgent
from agents.product_owner import ProductOwnerAgent
from agents.solution_architect import SolutionArchitectAgent
from agents.database_engineer import DatabaseEngineerAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.frontend_developer import FrontendDeveloperAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.doc_writer import DocWriterAgent

logger = logging.getLogger(__name__)


# Define the state
class AgentState(TypedDict):
    project_id: int
    project_idea: str
    project_plan: dict | None
    business_requirements: dict | None
    product_owner_plan: dict | None
    solution_arch: dict | None
    db_engineer_plan: dict | None
    backend_code: dict | None
    frontend_code: dict | None
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


async def project_manager_node(state: AgentState) -> AgentState:
    """Run the Project Manager agent — first node in the pipeline."""
    project_id = state["project_id"]
    project_idea = state["project_idea"]
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "project_manager", "running")
    
    try:
        agent = ProjectManagerAgent()
        result = agent.run(project_idea)
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        return {
            **state,
            "project_plan": result.model_dump(),
            "current_agent": "business_analyst",
            "error": None
        }
    except Exception as e:
        logger.error(f"Project Manager agent failed: {e}", exc_info=True)
        await update_agent_run(
            agent_run.id,
            "failed",
            error_message=str(e)
        )
        return {
            **state,
            "error": str(e)
        }


async def business_analyst_node(state: AgentState) -> AgentState:
    """Run the Business Analyst agent."""
    project_id = state["project_id"]
    project_idea = state["project_idea"]
    project_plan = state.get("project_plan")
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "business_analyst", "running")
    
    try:
        agent = BusinessAnalystAgent()
        
        # Enrich the BA input with the Project Manager's plan
        if project_plan:
            import json
            enriched_input = (
                f"{project_idea}\n\n"
                f"--- Project Manager Plan ---\n"
                f"{json.dumps(project_plan, indent=2)}"
            )
        else:
            enriched_input = project_idea
        
        result = agent.run(enriched_input)
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        return {
            **state,
            "business_requirements": result.model_dump(),
            "current_agent": "product_owner",
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


async def product_owner_node(state: AgentState) -> AgentState:
    """Run the Product Owner agent."""
    project_id = state["project_id"]
    project_plan = state.get("project_plan")
    business_requirements = state.get("business_requirements")
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "product_owner", "running")
    
    try:
        if not project_plan:
            raise ValueError("project_plan is required for Product Owner")
        if not business_requirements:
            raise ValueError("business_requirements is required for Product Owner")
            
        agent = ProductOwnerAgent()
        from app.schemas import ProjectManagerResponse, BusinessAnalystResponse
        result = agent.run(
            ProjectManagerResponse(**project_plan),
            BusinessAnalystResponse(**business_requirements)
        )
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        return {
            **state,
            "product_owner_plan": result.model_dump(),
            "current_agent": "solution_architect",
            "error": None
        }
    except Exception as e:
        logger.error(f"Product Owner agent failed: {e}", exc_info=True)
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
    product_owner_plan = state.get("product_owner_plan")
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "solution_architect", "running")
    
    try:
        if not business_requirements:
            raise ValueError("business_requirements is required")
        agent = SolutionArchitectAgent()
        from app.schemas import BusinessAnalystResponse, ProductOwnerResponse
        po_plan = ProductOwnerResponse(**product_owner_plan) if product_owner_plan else None
        result = agent.run(
            BusinessAnalystResponse(**business_requirements),
            product_owner_plan=po_plan
        )
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        return {
            **state,
            "solution_arch": result.model_dump(),
            "current_agent": "database_engineer",
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


async def database_engineer_node(state: AgentState) -> AgentState:
    """Run the Database Engineer agent."""
    project_id = state["project_id"]
    solution_arch = state["solution_arch"]
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "database_engineer", "running")
    
    try:
        if not solution_arch:
            raise ValueError("solution_arch is required for Database Engineer")
            
        agent = DatabaseEngineerAgent()
        from app.schemas import SolutionArchitectResponse
        result = agent.run(SolutionArchitectResponse(**solution_arch))
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        return {
            **state,
            "db_engineer_plan": result.model_dump(),
            "current_agent": "backend_developer",
            "error": None
        }
    except Exception as e:
        logger.error(f"Database Engineer agent failed: {e}", exc_info=True)
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
    db_engineer_plan = state.get("db_engineer_plan")
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "backend_developer", "running")
    
    try:
        if not solution_arch:
            raise ValueError("solution_arch is required")
        agent = BackendDeveloperAgent()
        from app.schemas import SolutionArchitectResponse, BackendDeveloperResponse, DatabaseEngineerResponse
        db_plan = DatabaseEngineerResponse(**db_engineer_plan) if db_engineer_plan else None
        result = agent.run(
            SolutionArchitectResponse(**solution_arch),
            db_engineer_plan=db_plan
        )
        
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
            "current_agent": "frontend_developer",
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


async def frontend_developer_node(state: AgentState) -> AgentState:
    """Run the Frontend Developer agent."""
    project_id = state["project_id"]
    solution_arch = state["solution_arch"]
    backend_code = state["backend_code"]
    
    # Create agent run
    agent_run = await create_agent_run(project_id, "frontend_developer", "running")
    
    try:
        if not solution_arch:
            raise ValueError("solution_arch is required")
        if not backend_code:
            raise ValueError("backend_code is required")
            
        agent = FrontendDeveloperAgent()
        from app.schemas import SolutionArchitectResponse, BackendDeveloperResponse
        result = agent.run(
            SolutionArchitectResponse(**solution_arch),
            BackendDeveloperResponse(**backend_code)
        )
        
        # Update agent run
        await update_agent_run(
            agent_run.id,
            "completed",
            output_json=result.model_dump()
        )
        
        # Save both backend and frontend files to database (append frontend files to backend ones)
        existing_files = await get_project_files(project_id)
        files_dict = {f["path"]: f["content"] for f in existing_files}
        for file in result.files:
            files_dict[file.path] = file.content
        updated_files = [{"path": path, "content": content} for path, content in files_dict.items()]
        await update_project_files(project_id, updated_files)
        
        return {
            **state,
            "frontend_code": result.model_dump(),
            "current_agent": "code_reviewer",
            "error": None
        }
    except Exception as e:
        logger.error(f"Frontend Developer agent failed: {e}", exc_info=True)
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
    if state.get("current_agent") == "business_analyst":
        return "business_analyst"
    if state.get("current_agent") == "product_owner":
        return "product_owner"
    if state.get("current_agent") == "solution_architect":
        return "solution_architect"
    if state.get("current_agent") == "database_engineer":
        return "database_engineer"
    if state.get("current_agent") == "backend_developer":
        return "backend_developer"
    if state.get("current_agent") == "frontend_developer":
        return "frontend_developer"
    if state.get("current_agent") == "code_reviewer":
        return "code_reviewer"
    if state.get("current_agent") == "doc_writer":
        return "doc_writer"
    return END


# Build the graph
graph = StateGraph(AgentState)

graph.add_node("project_manager", project_manager_node)
graph.add_node("business_analyst", business_analyst_node)
graph.add_node("product_owner", product_owner_node)
graph.add_node("solution_architect", solution_architect_node)
graph.add_node("database_engineer", database_engineer_node)
graph.add_node("backend_developer", backend_developer_node)
graph.add_node("frontend_developer", frontend_developer_node)
graph.add_node("code_reviewer", code_reviewer_node)
graph.add_node("doc_writer", doc_writer_node)

graph.set_entry_point("project_manager")
graph.add_conditional_edges("project_manager", should_continue)
graph.add_conditional_edges("business_analyst", should_continue)
graph.add_conditional_edges("product_owner", should_continue)
graph.add_conditional_edges("solution_architect", should_continue)
graph.add_conditional_edges("database_engineer", should_continue)
graph.add_conditional_edges("backend_developer", should_continue)
graph.add_conditional_edges("frontend_developer", should_continue)
graph.add_conditional_edges("code_reviewer", should_continue)
graph.add_conditional_edges("doc_writer", should_continue)

# Compile the graph
app = graph.compile()


async def run_pipeline(project_id: int, project_idea: str):
    """Run the full agent pipeline for a project."""
    initial_state: AgentState = {
        "project_id": project_id,
        "project_idea": project_idea,
        "project_plan": None,
        "business_requirements": None,
        "product_owner_plan": None,
        "solution_arch": None,
        "db_engineer_plan": None,
        "backend_code": None,
        "frontend_code": None,
        "code_review": None,
        "current_agent": None,
        "error": None
    }
    
    async for state in app.astream(initial_state):
        pass

