import asyncio
from app.db import AsyncSessionLocal
from app.models import Project, AgentRun
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        res_p = await session.execute(select(Project).order_by(Project.id.desc()).limit(5))
        projects = res_p.scalars().all()
        for p in projects:
            res_r = await session.execute(select(AgentRun).where(AgentRun.project_id == p.id))
            runs = res_r.scalars().all()
            print(f"Project ID {p.id}: {p.title} | Runs: {len(runs)} | Files: {len(p.generated_files) if p.generated_files else 0}")
            for r in runs:
                print(f"  - {r.agent_name}: {r.status} (has_error: {r.error_message is not None})")

if __name__ == "__main__":
    asyncio.run(main())
