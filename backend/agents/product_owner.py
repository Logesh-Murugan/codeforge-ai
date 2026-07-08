import os
import json
import logging
from typing import Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import ProductOwnerResponse, ProjectManagerResponse, BusinessAnalystResponse

logger = logging.getLogger(__name__)


class ProductOwnerAgent:
    """Agent that creates a prioritized product backlog from project manager plan and business requirements."""

    def __init__(self):
        # Load the system prompt from file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "product_owner.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(self, project_plan: ProjectManagerResponse, business_requirements: BusinessAnalystResponse) -> ProductOwnerResponse:
        """
        Run the product owner agent.
        
        Args:
            project_plan: The project manager's plan.
            business_requirements: The business analyst's requirements.
            
        Returns:
            Structured ProductOwnerResponse.
            
        Raises:
            AgentExecutionError: If execution fails.
        """
        # Package inputs into a unified JSON context
        input_data = {
            "project_plan": project_plan.model_dump(),
            "business_requirements": business_requirements.model_dump()
        }
        input_str = json.dumps(input_data, indent=2)

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

    def _parse_response(self, response_str: str) -> ProductOwnerResponse:
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

        # Validate with Pydantic
        return ProductOwnerResponse(**data)
