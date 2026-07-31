import logging
import time
import json
import copy
import asyncio
from typing import Callable, Any, Optional
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import Project, AgentRun
from orchestrator.state import AgentState

# Import all agents
from agents.project_manager import ProjectManagerAgent
from agents.business_analyst import BusinessAnalystAgent
from agents.product_owner import ProductOwnerAgent
from agents.solution_architect import SolutionArchitectAgent
from agents.database_engineer import DatabaseEngineerAgent
from agents.api_designer import APIDesignerAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.security_engineer import SecurityEngineerAgent
from agents.qa_engineer import QAEngineerAgent
from agents.frontend_developer import FrontendDeveloperAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.doc_writer import DocWriterAgent
from agents.devops_engineer import DevOpsEngineerAgent

logger = logging.getLogger(__name__)


# ==========================================
# Database Helpers & Persistency Layer
# ==========================================

async def create_agent_run(
    project_id: int,
    agent_name: str,
    status: str,
    output_json: dict | None = None,
    error_message: str | None = None
) -> AgentRun:
    """Create a new AgentRun track in the database."""
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
    """Update status, output or errors of an active AgentRun."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AgentRun).where(AgentRun.id == agent_run_id))
        agent_run = result.scalar_one_or_none()
        if not agent_run:
            raise ValueError(f"AgentRun {agent_run_id} not found")
        
        agent_run.status = status
        if output_json is not None:
            agent_run.output_json = output_json
        if error_message is not None:
            agent_run.error_message = error_message
        
        await session.commit()
        await session.refresh(agent_run)
        return agent_run


async def update_project_files(project_id: int, files: list):
    """Save generated project files into the DB."""
    async with AsyncSessionLocal() as session:
        query = select(Project).where(Project.id == project_id)
        res = await session.execute(query)
        project = res.scalar_one_or_none()
        if project:
            project.generated_files = files
            await session.commit()


async def get_project_files(project_id: int) -> list:
    """Retrieve all project files compiled so far."""
    async with AsyncSessionLocal() as session:
        query = select(Project).where(Project.id == project_id)
        res = await session.execute(query)
        project = res.scalar_one_or_none()
        return project.generated_files if (project and project.generated_files) else []


# ==========================================
# Execution Engine with Retry & Failure Recovery
# ==========================================

async def execute_node_with_retry_and_recovery(
    state: AgentState,
    agent_name: str,
    task_func: Callable[[AgentState], Any],
    next_agent: Optional[str] = None,
    max_retries: int = 3
) -> AgentState:
    """
    Standard wrapper around agent execution offering:
    - Retries (up to 3 times on runtime errors).
    - Deepcopy state protection (attempt-level isolation).
    - Status tracking (DB logging under AgentRun).
    - Failure recovery (safely maps crashes to error states).
    - Centralized logging metrics.
    """
    project_id = state["project_id"]
    logger.info(f"[ORCHESTRATOR] Starting node: '{agent_name}' for project {project_id}")
    
    agent_run = await create_agent_run(project_id, agent_name, "running")
    start_time = time.time()
    
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                logger.warning(
                    f"[ORCHESTRATOR] Retrying '{agent_name}' (Attempt {attempt}/{max_retries}) "
                    f"due to previous error: {last_exception}"
                )
            
            # Deep copy state for attempt-level isolation
            attempt_state = copy.deepcopy(state)
            
            # Run the task function (which performs agent run, parsing, validation, file updates)
            updated_state = await task_func(attempt_state)
            
            # Retrieve output_json for DB persistence from the updated state
            output_json = updated_state.get(agent_name)
            
            # Check approval mode configuration
            if updated_state.get("approval_mode"):
                updated_state["approval_status"] = "pending"
                updated_state["pending_approval"] = {
                    "agent_name": agent_name,
                    "agent_run_id": agent_run.id,
                    "project_id": project_id,
                    "next_agent": next_agent,
                    "output": output_json
                }
                await update_agent_run(agent_run.id, "waiting_approval", output_json=output_json)
            else:
                await update_agent_run(agent_run.id, "completed", output_json=output_json)
                updated_state["approval_status"] = None
                updated_state["pending_approval"] = None
            
            # Set current_agent to transition to the next step
            updated_state["current_agent"] = next_agent
            updated_state["error"] = None
            
            elapsed = time.time() - start_time
            logger.info(f"[ORCHESTRATOR] Node '{agent_name}' completed successfully in {elapsed:.2f}s (Attempts: {attempt})")
            
            return updated_state
            
        except Exception as e:
            last_exception = e
            import traceback
            tb_str = traceback.format_exc()
            logger.error(
                f"[ORCHESTRATOR] Attempt {attempt}/{max_retries} for agent '{agent_name}' failed with exception:\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n"
                f"Stack trace:\n{tb_str}"
            )
            # Brief wait before retry
            await asyncio.sleep(1.0)
            
    # Exhausted all retries
    elapsed = time.time() - start_time
    logger.error(f"[ORCHESTRATOR] Node '{agent_name}' failed after {max_retries} retries in {elapsed:.2f}s.")
    
    error_msg = f"Agent '{agent_name}' failed after {max_retries} retries. Last exception: {type(last_exception).__name__}: {str(last_exception)}"
    await update_agent_run(agent_run.id, "failed", error_message=error_msg)
    
    # Gracefully transition to failed state
    failed_state = copy.deepcopy(state)
    failed_state["error"] = error_msg
    failed_state["current_agent"] = None
    return failed_state


# ==========================================
# Agent Node Definitions
# ==========================================

async def project_manager_node(state: AgentState) -> AgentState:
    """Run the Project Manager agent."""
    async def task(curr_state: AgentState):
        agent = ProjectManagerAgent()
        result = agent.run(curr_state["project_idea"])
        curr_state["project_manager"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "project_manager", task, next_agent="business_analyst")


async def business_analyst_node(state: AgentState) -> AgentState:
    """Run the Business Analyst agent."""
    async def task(curr_state: AgentState):
        agent = BusinessAnalystAgent()
        project_plan = curr_state.get("project_manager")
        if project_plan:
            enriched_input = (
                f"{curr_state['project_idea']}\n\n"
                f"--- Project Manager Plan ---\n"
                f"{json.dumps(project_plan, indent=2)}"
            )
        else:
            enriched_input = curr_state["project_idea"]
        result = agent.run(enriched_input)
        curr_state["business_analyst"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "business_analyst", task, next_agent="product_owner")


async def product_owner_node(state: AgentState) -> AgentState:
    """Run the Product Owner agent."""
    async def task(curr_state: AgentState):
        pm_plan = curr_state.get("project_manager")
        ba_req = curr_state.get("business_analyst")
        if not pm_plan or not ba_req:
            raise ValueError("project_manager and business_analyst outputs are required for Product Owner")
            
        agent = ProductOwnerAgent()
        from app.schemas import ProjectManagerResponse, BusinessAnalystResponse
        result = agent.run(
            ProjectManagerResponse(**pm_plan),
            BusinessAnalystResponse(**ba_req)
        )
        curr_state["product_owner"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "product_owner", task, next_agent="solution_architect")


async def solution_architect_node(state: AgentState) -> AgentState:
    """Run the Solution Architect agent."""
    async def task(curr_state: AgentState):
        ba_req = curr_state.get("business_analyst")
        po_plan = curr_state.get("product_owner")
        if not ba_req:
            raise ValueError("business_analyst output is required for Solution Architect")
            
        agent = SolutionArchitectAgent()
        from app.schemas import BusinessAnalystResponse, ProductOwnerResponse
        po_model = ProductOwnerResponse(**po_plan) if po_plan else None
        result = agent.run(
            BusinessAnalystResponse(**ba_req),
            product_owner_plan=po_model
        )
        curr_state["solution_architect"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "solution_architect", task, next_agent="database_engineer")


async def database_engineer_node(state: AgentState) -> AgentState:
    """Run the Database Engineer agent."""
    async def task(curr_state: AgentState):
        sa_plan = curr_state.get("solution_architect")
        if not sa_plan:
            raise ValueError("solution_architect output is required for Database Engineer")
            
        agent = DatabaseEngineerAgent()
        from app.schemas import SolutionArchitectResponse
        result = agent.run(SolutionArchitectResponse(**sa_plan))
        curr_state["database_engineer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "database_engineer", task, next_agent="api_designer")


async def api_designer_node(state: AgentState) -> AgentState:
    """Run the API Designer agent."""
    async def task(curr_state: AgentState):
        sa_plan = curr_state.get("solution_architect")
        if not sa_plan:
            raise ValueError("solution_architect output is required for API Designer")
            
        agent = APIDesignerAgent()
        from app.schemas import SolutionArchitectResponse
        result = agent.run(SolutionArchitectResponse(**sa_plan))
        curr_state["api_designer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "api_designer", task, next_agent="backend_developer")


async def backend_developer_node(state: AgentState) -> AgentState:
    """Run the Backend Developer agent."""
    async def task(curr_state: AgentState):
        sa_plan = curr_state.get("solution_architect")
        db_plan = curr_state.get("database_engineer")
        api_plan = curr_state.get("api_designer")
        if not sa_plan:
            raise ValueError("solution_architect output is required for Backend Developer")
            
        agent = BackendDeveloperAgent()
        from app.schemas import SolutionArchitectResponse, DatabaseEngineerResponse, APIDesignerResponse
        db_model = DatabaseEngineerResponse(**db_plan) if db_plan else None
        api_model = APIDesignerResponse(**api_plan) if api_plan else None
        result = agent.run(
            SolutionArchitectResponse(**sa_plan),
            db_engineer_plan=db_model,
            api_design=api_model
        )
        
        # Save files
        files_list = [{"path": file.path, "content": file.content} for file in result.files]
        await update_project_files(curr_state["project_id"], files_list)
        
        curr_state["backend_developer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "backend_developer", task, next_agent="security_engineer")


async def security_engineer_node(state: AgentState) -> AgentState:
    """Run the Security Engineer agent."""
    async def task(curr_state: AgentState):
        be_code = curr_state.get("backend_developer")
        if not be_code:
            raise ValueError("backend_developer output is required for Security Engineer")
            
        agent = SecurityEngineerAgent()
        from app.schemas import BackendDeveloperResponse
        result = agent.run(BackendDeveloperResponse(**be_code))
        curr_state["security_engineer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "security_engineer", task, next_agent="qa_engineer")


async def qa_engineer_node(state: AgentState) -> AgentState:
    """Run the QA Engineer agent."""
    async def task(curr_state: AgentState):
        be_code = curr_state.get("backend_developer")
        sec_audit = curr_state.get("security_engineer")
        if not be_code:
            raise ValueError("backend_developer output is required for QA Engineer")
            
        agent = QAEngineerAgent()
        from app.schemas import BackendDeveloperResponse, SecurityEngineerResponse
        sec_model = SecurityEngineerResponse(**sec_audit) if sec_audit else None
        result = agent.run(
            BackendDeveloperResponse(**be_code),
            security_audit=sec_model
        )
        curr_state["qa_engineer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "qa_engineer", task, next_agent="frontend_developer")


async def frontend_developer_node(state: AgentState) -> AgentState:
    """Run the Frontend Developer agent."""
    async def task(curr_state: AgentState):
        sa_plan = curr_state.get("solution_architect")
        be_code = curr_state.get("backend_developer")
        if not sa_plan or not be_code:
            raise ValueError("solution_architect and backend_developer outputs are required for Frontend Developer")
            
        agent = FrontendDeveloperAgent()
        from app.schemas import SolutionArchitectResponse, BackendDeveloperResponse
        result = agent.run(
            SolutionArchitectResponse(**sa_plan),
            BackendDeveloperResponse(**be_code)
        )
        
        # Save both backend and frontend files
        existing_files = await get_project_files(curr_state["project_id"])
        files_dict = {f["path"]: f["content"] for f in existing_files}
        for file in result.files:
            files_dict[file.path] = file.content
        updated_files = [{"path": path, "content": content} for path, content in files_dict.items()]
        await update_project_files(curr_state["project_id"], updated_files)
        
        curr_state["frontend_developer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "frontend_developer", task, next_agent="code_reviewer")


async def code_reviewer_node(state: AgentState) -> AgentState:
    """Run the Code Reviewer agent."""
    async def task(curr_state: AgentState):
        be_code = curr_state.get("backend_developer")
        if not be_code:
            raise ValueError("backend_developer output is required for Code Reviewer")
            
        agent = CodeReviewerAgent()
        from app.schemas import BackendDeveloperResponse
        result = agent.run(BackendDeveloperResponse(**be_code))
        
        # Save auto-fixed files
        if result.auto_fixed_files:
            existing_files = await get_project_files(curr_state["project_id"])
            files_dict = {f["path"]: f["content"] for f in existing_files}
            for fixed_file in result.auto_fixed_files:
                files_dict[fixed_file.path] = fixed_file.content
            updated_files = [{"path": path, "content": content} for path, content in files_dict.items()]
            await update_project_files(curr_state["project_id"], updated_files)
            
        curr_state["code_reviewer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "code_reviewer", task, next_agent="documentation_writer")


async def documentation_writer_node(state: AgentState) -> AgentState:
    """Run the Documentation Writer agent."""
    async def task(curr_state: AgentState):
        solution_arch = curr_state.get("solution_architect")
        agent = DocWriterAgent()
        # Returns simple string documentation
        doc = agent.run(curr_state["project_idea"], solution_arch)
        
        # Save README.md in generated files
        existing_files = await get_project_files(curr_state["project_id"])
        files_dict = {f["path"]: f["content"] for f in existing_files}
        files_dict["README.md"] = doc
        updated_files = [{"path": path, "content": content} for path, content in files_dict.items()]
        await update_project_files(curr_state["project_id"], updated_files)
        
        curr_state["documentation_writer"] = {"documentation": doc}
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "documentation_writer", task, next_agent="devops_engineer")


async def devops_engineer_node(state: AgentState) -> AgentState:
    """Run the DevOps Engineer agent."""
    async def task(curr_state: AgentState):
        sa_plan = curr_state.get("solution_architect")
        if not sa_plan:
            raise ValueError("solution_architect output is required for DevOps Engineer")
            
        # Get documentation text
        files = await get_project_files(curr_state["project_id"])
        readme_file = next((f for f in files if f["path"] == "README.md"), None)
        doc_text = readme_file["content"] if readme_file else ""
        
        agent = DevOpsEngineerAgent()
        from app.schemas import SolutionArchitectResponse
        result = agent.run(SolutionArchitectResponse(**sa_plan), doc_text)
        curr_state["devops_engineer"] = result.model_dump()
        return curr_state
        
    return await execute_node_with_retry_and_recovery(state, "devops_engineer", task, next_agent=None)
