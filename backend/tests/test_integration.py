import pytest
import asyncio
from unittest.mock import MagicMock, patch
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import User, Project, AgentRun
from orchestrator.graph import run_pipeline, app
from app.schemas import (
    ProjectManagerResponse,
    BusinessAnalystResponse,
    ProductOwnerResponse,
    SolutionArchitectResponse,
    DatabaseEngineerResponse,
    APIDesignerResponse,
    BackendDeveloperResponse,
    SecurityEngineerResponse,
    QAEngineerResponse,
    FrontendDeveloperResponse,
    CodeReviewerResponse,
    DevOpsEngineerResponse
)
from app.schemas.agents import Entity, Relationship, BacklogItem


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_modular_orchestrator_pipeline_success():
    """
    Integration test verifying E2E modular orchestration graph traversal
    under mocked LLM agent calls.
    """
    # 1. Setup mock returns for all 13 agents matching agents.py schemas
    mock_pm = ProjectManagerResponse(
        project_summary="Notes App summary",
        project_scope="Backend and frontend notes tracker",
        goals=["Create notes", "Delete notes"],
        milestones=[],
        priority_features=[],
        estimated_complexity="low",
        agent_execution_plan=[],
        parallel_execution_groups=[],
        risks=[],
        assumptions=[]
    )
    
    mock_ba = BusinessAnalystResponse(
        entities=[Entity(name="Note", fields=["id", "title", "content"])],
        relationships=[],
        requires_auth=True,
        core_actions=["CRUD Notes"]
    )
    
    mock_po = ProductOwnerResponse(
        sprint_goals=["Build notes CRUD API"],
        must_have_features=["Create notes", "Delete notes"],
        should_have_features=[],
        could_have_features=[],
        wont_have_features=[],
        backlog=[
            BacklogItem(
                feature_name="Create notes",
                category="Core",
                description="Allows users to write new notes",
                business_value="High",
                risk_level="Low",
                priority_score=9,
                acceptance_criteria=["Note title is required"],
                dependencies=[]
            )
        ]
    )
    
    mock_sa = SolutionArchitectResponse(
        db_schema=[],
        endpoints=[],
        file_structure=[]
    )
    
    mock_db = DatabaseEngineerResponse(
        er_diagram_mermaid="erDiagram USERS ||--|{ NOTES : has",
        db_schema_details="Table users, Table notes",
        indexes=[],
        relationships=[],
        migration_plan=["CREATE TABLE users ...", "CREATE TABLE notes ..."],
        normalization_review="3NF normalization confirmed",
        sqlalchemy_models_code="class User(Base): ..."
    )
    
    mock_api = APIDesignerResponse(
        openapi_spec="openapi: 3.1.0\ninfo:\n  title: Notes API",
        endpoints=[],
        request_models=[],
        response_models=[],
        error_models=[],
        authentication_flow={
            "method": "JWT Bearer",
            "token_endpoint": "/auth/login",
            "refresh_endpoint": "/auth/refresh",
            "description": "Lifecycle specs"
        },
        versioning_strategy="URL prefix /api/v1/"
    )
    
    mock_be = BackendDeveloperResponse(files=[])
    
    mock_sec = SecurityEngineerResponse(
        overall_risk="low",
        findings=[],
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
        jwt_assessment="Robust signing key assessment",
        dependency_risks=[],
        secrets_detected=[],
        owasp_coverage=[],
        recommended_patches=[]
    )
    
    mock_qa = QAEngineerResponse(
        test_plan="Simulated QA test strategy",
        unit_tests_code="def test_note(): pass",
        integration_tests_code="def test_integration(): pass",
        api_tests_code="def test_api(): pass",
        edge_cases=[],
        coverage_report_summary="100% simulated",
        estimated_coverage=100.0
    )
    
    mock_fe = FrontendDeveloperResponse(files=[])
    
    mock_rev = CodeReviewerResponse(
        issues=[],
        auto_fixed_files=[]
    )
    
    mock_devops = DevOpsEngineerResponse(
        dockerfile="FROM python:3.10",
        docker_compose="version: '3.8'",
        github_actions_workflow="name: Deploy",
        nginx_config="server { listen 80; }",
        production_env_vars=[],
        deployment_guide="Step-by-step deploy instructions"
    )

    # 2. Seed temporary test user and project
    async with AsyncSessionLocal() as session:
        # User
        res_u = await session.execute(select(User).where(User.email == "integration_tester@example.com"))
        user = res_u.scalar_one_or_none()
        if not user:
            user = User(email="integration_tester@example.com", hashed_password="password")
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        # Project
        project = Project(
            title="Mock Integration Notes App",
            description="A sample notes application testing orchestrator logic E2E.",
            owner_id=user.id
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        project_id = project.id

    # 3. Patch all agent runs
    with patch("agents.project_manager.ProjectManagerAgent.run", return_value=mock_pm), \
         patch("agents.business_analyst.BusinessAnalystAgent.run", return_value=mock_ba), \
         patch("agents.product_owner.ProductOwnerAgent.run", return_value=mock_po), \
         patch("agents.solution_architect.SolutionArchitectAgent.run", return_value=mock_sa), \
         patch("agents.database_engineer.DatabaseEngineerAgent.run", return_value=mock_db), \
         patch("agents.api_designer.APIDesignerAgent.run", return_value=mock_api), \
         patch("agents.backend_developer.BackendDeveloperAgent.run", return_value=mock_be), \
         patch("agents.security_engineer.SecurityEngineerAgent.run", return_value=mock_sec), \
         patch("agents.qa_engineer.QAEngineerAgent.run", return_value=mock_qa), \
         patch("agents.frontend_developer.FrontendDeveloperAgent.run", return_value=mock_fe), \
         patch("agents.code_reviewer.CodeReviewerAgent.run", return_value=mock_rev), \
         patch("agents.doc_writer.DocWriterAgent.run", return_value="Mock README documentation text"), \
         patch("agents.devops_engineer.DevOpsEngineerAgent.run", return_value=mock_devops):

        # Execute E2E pipeline
        await run_pipeline(project_id, "A simple notes application.")

    # 4. Verify all 13 runs exist and are completed successfully
    async with AsyncSessionLocal() as session:
        res_runs = await session.execute(
            select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at)
        )
        runs = res_runs.scalars().all()
        
        assert len(runs) == 13
        for run in runs:
            assert run.status == "completed"
            assert run.error_message is None
            assert run.output_json is not None
            
        # Verify specific renamed state key in run values
        doc_writer_run = next(r for r in runs if r.agent_name == "documentation_writer")
        assert doc_writer_run.output_json["documentation"] == "Mock README documentation text"
