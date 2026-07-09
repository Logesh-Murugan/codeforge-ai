import asyncio
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models import AgentRun

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentRun).where(AgentRun.project_id == 16).order_index(AgentRun.id) if hasattr(AgentRun, 'order_index') 
            else select(AgentRun).where(AgentRun.project_id == 16).order_by(AgentRun.id)
        )
        runs = result.scalars().all()
        for run in runs:
            print("=" * 80)
            print(f"Agent: {run.agent_name} | Status: {run.status}")
            if run.agent_name == "database_engineer":
                print("ER Mermaid starts with:", run.output_json.get("er_diagram_mermaid")[:100] if run.output_json else None)
                print("Models Code starts with:", run.output_json.get("sqlalchemy_models_code")[:200] if run.output_json else None)
            elif run.agent_name == "backend_developer":
                print("Files:")
                if run.output_json and "files" in run.output_json:
                    for f in run.output_json["files"]:
                        print(f"  - {f['path']} (length: {len(f['content'])})")
                        print("    Content start:", repr(f['content'][:150]))

if __name__ == "__main__":
    asyncio.run(main())
