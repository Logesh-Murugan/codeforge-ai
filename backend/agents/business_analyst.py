import os
import json
import logging
from typing import Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import BusinessAnalystResponse

logger = logging.getLogger(__name__)


class BusinessAnalystAgent:
    """Agent that analyzes project ideas and returns structured requirements."""

    def __init__(self):
        # Load the system prompt from file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "business_analyst.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.1-8b-instant"
        )

    def run(self, project_idea: str) -> BusinessAnalystResponse:
        """
        Run the business analyst agent on a project idea.
        
        Args:
            project_idea: The free-text project idea.
            
        Returns:
            Structured BusinessAnalystResponse.
            
        Raises:
            AgentExecutionError: If the agent fails.
        """
        # First attempt
        try:
            response_str = self.base_agent.run(project_idea)
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

    def _parse_response(self, response_str: str) -> BusinessAnalystResponse:
        """Parse and validate the agent's response."""
        # Clean up the response string (remove any markdown fences)
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

        # Fix "from_" to "from" in relationships if needed
        for rel in data.get("relationships", []):
            if "from" in rel and "from_" not in rel:
                rel["from_"] = rel.pop("from")

        # Validate with Pydantic
        return BusinessAnalystResponse(**data)
