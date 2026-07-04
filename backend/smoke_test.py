import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from app.db import AsyncSessionLocal
from app.models import User, Project, AgentRun
from app.core.security import get_password_hash
from orchestrator.graph import run_pipeline
from sqlalchemy import select

async def main():
    print("[START] Starting CodeForge AI local end-to-end smoke test...")
    
    async with AsyncSessionLocal() as session:
        # 1. Create a test user if not exists
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("Creating test user...")
            hashed_pwd = get_password_hash("password123")
            user = User(email="test@example.com", hashed_password=hashed_pwd)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"Created test user with ID: {user.id}")
        else:
            print(f"Found existing test user with ID: {user.id}")
            
        # 2. Create a test project
        project_idea = (
            "A simple task list API where users can sign up, create tasks, "
            "mark tasks as done, and list their tasks, only seeing their own data."
        )
        
        print("Creating test project...")
        project = Project(
            title="Task List API",
            description=project_idea,
            owner_id=user.id
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        print(f"Created test project with ID: {project.id}")
        
        project_id = project.id

    # 3. Run the LangGraph orchestration pipeline
    print(f"Executing Agent Pipeline for project {project_id}...")
    try:
        await run_pipeline(project_id, project_idea)
        print("Pipeline execution command finished. Checking run statuses...")
    except Exception as e:
        print(f"[FAIL] Pipeline execution threw an exception: {e}")
        return

    # 4. Verify the outputs in the database
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at)
        )
        runs = result.scalars().all()
        
        print(f"\n--- Agent Run Verification (Total Steps: {len(runs)}) ---")
        all_passed = True
        for r in runs:
            print(f"Agent: {r.agent_name:<20} | Status: {r.status:<10}")
            if r.status != "completed":
                all_passed = False
                if r.error_message:
                    print(f"   ↳ Error: {r.error_message}")
        
        if all_passed and len(runs) == 5:
            print("\n[SUCCESS] All 5 agents completed successfully!")
            
            # Check generated files in DB
            result = await session.execute(select(Project).where(Project.id == project_id))
            proj = result.scalar_one_or_none()
            if proj and proj.generated_files:
                print(f"[FILES] Generated files in database for project {project_id}:")
                for file_info in proj.generated_files:
                    print(f"  - {file_info['path']} ({len(file_info['content'])} bytes)")
            else:
                print("[ERROR] Generated files not found in database!")
        else:
            print("\n[FAIL] Some agents failed or did not run.")

if __name__ == "__main__":
    asyncio.run(main())
