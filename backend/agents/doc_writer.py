import json
import os
import logging
from typing import Optional

from agents.base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)


class DocWriterAgent:
    """Agent that generates documentation for the project."""

    def __init__(self):
        # Load the system prompt from file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "doc_writer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.1-8b-instant"
        )

    def run(self, project_idea: str, solution_arch: Optional[dict] = None) -> str:
        """
        Run the doc writer agent.
        
        Args:
            project_idea: The original project idea text.
            solution_arch: Optional solution architecture details.
            
        Returns:
            Markdown documentation string.
            
        Raises:
            AgentExecutionError: If the agent fails.
        """
        user_input = f"Project Idea: {project_idea}"
        if solution_arch:
            user_input += f"\n\nSolution Architecture & Endpoints:\n{json.dumps(solution_arch, indent=2)}"

        try:
            response_str = self.base_agent.run(user_input)
            return response_str.strip()
        except Exception as e:
            logger.error(f"Doc writer failed: {str(e)}")
            raise AgentExecutionError(f"Doc writer failed: {str(e)}") from e

