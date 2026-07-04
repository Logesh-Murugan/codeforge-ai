import asyncio
from orchestrator.graph import run_pipeline

async def test():
    project_id = 7  # New project ID
    project_idea = "A simple task management API where users can create tasks, mark them as done, and list their tasks."
    await run_pipeline(project_id, project_idea)

asyncio.run(test())
