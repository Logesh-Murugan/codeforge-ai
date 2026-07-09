import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models import AgentRun

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentRun).where(AgentRun.project_id == 18).where(AgentRun.agent_name == "backend_developer")
        )
        run = result.scalars().first()
        if run:
            print("Status:", run.status)
            print("Error message:")
            print(run.error_message)
            print("Output JSON:")
            print(run.output_json)
        else:
            print("Run not found")

if __name__ == "__main__":
    asyncio.run(main())
