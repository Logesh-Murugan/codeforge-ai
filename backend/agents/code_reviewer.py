import os
import json
import logging
from typing import Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import CodeReviewerResponse, BackendDeveloperResponse

logger = logging.getLogger(__name__)


class CodeReviewerAgent:
    """Agent that reviews generated code and reports issues."""

    def __init__(self):
        # Load the system prompt from file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "code_reviewer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(self, backend_output: BackendDeveloperResponse) -> CodeReviewerResponse:
        """
        Run the code reviewer agent.
        
        Args:
            backend_output: The output from the Backend Developer agent.
            
        Returns:
            Structured CodeReviewerResponse.
            
        Raises:
            AgentExecutionError: If the agent fails.
        """
        # Convert backend output to JSON string
        input_str = backend_output.model_dump_json(indent=2)

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

    def _parse_response(self, response_str: str) -> CodeReviewerResponse:
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

        # Clean double-escaped newlines in generated auto-fixed files
        if isinstance(data, dict) and "auto_fixed_files" in data:
            for file in data["auto_fixed_files"]:
                if "content" in file and isinstance(file["content"], str):
                    content = file["content"]
                    if "\\n" in content and "\n" not in content:
                        file["content"] = content.replace("\\n", "\n")

        # Validate with Pydantic
        return CodeReviewerResponse(**data)
