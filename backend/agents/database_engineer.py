import os
import json
import logging
from typing import Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import DatabaseEngineerResponse, SolutionArchitectResponse

logger = logging.getLogger(__name__)


class DatabaseEngineerAgent:
    """Agent that creates database design deliverables from the solution architect's designs."""

    def __init__(self):
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "database_engineer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(self, solution_arch: SolutionArchitectResponse) -> DatabaseEngineerResponse:
        """
        Run the database engineer agent.
        
        Args:
            solution_arch: The Solution Architect's response.
            
        Returns:
            Structured DatabaseEngineerResponse.
            
        Raises:
            AgentExecutionError: If execution fails.
        """
        # Pack inputs into unified context
        input_str = solution_arch.model_dump_json(indent=2)

        # First attempt
        try:
            response_str = self.base_agent.run(input_str)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"First attempt failed: {str(e)}. Retrying with correction...")

        # Second attempt with correction
        try:
            correction_prompt = (
                f"The previous response was not valid JSON. Please fix it and return ONLY valid JSON:\n"
                f"{response_str}"
            )
            response_str = self.base_agent.run(correction_prompt)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Second attempt failed: {str(e)}")
            raise AgentExecutionError(f"Failed to get valid JSON after two attempts: {str(e)}") from e

    def _parse_response(self, response_str: str) -> DatabaseEngineerResponse:
        """Parse and validate the agent's response."""
        # Clean up response string
        cleaned = response_str.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Parse JSON
        data = json.loads(cleaned)

        # Clean double-escaped newlines in code
        if isinstance(data, dict) and "sqlalchemy_models_code" in data:
            code = data["sqlalchemy_models_code"]
            if isinstance(code, str) and "\\n" in code and "\n" not in code:
                data["sqlalchemy_models_code"] = code.replace("\\n", "\n")

        # Validate Pydantic model
        return DatabaseEngineerResponse(**data)
