import os
import json
import logging
from typing import Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import APIDesignerResponse, SolutionArchitectResponse

logger = logging.getLogger(__name__)


class APIDesignerAgent:
    """Agent that designs a complete REST API specification from the solution architect's designs."""

    def __init__(self):
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "api_designer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(self, solution_arch: SolutionArchitectResponse) -> APIDesignerResponse:
        """
        Run the API Designer agent.
        
        Args:
            solution_arch: The Solution Architect's response.
            
        Returns:
            Structured APIDesignerResponse.
            
        Raises:
            AgentExecutionError: If execution fails.
        """
        # Pack inputs into unified context
        input_str = solution_arch.model_dump_json(indent=2)

        # First attempt
        response_str = None
        try:
            logger.info("Running API Designer Agent - Attempt 1")
            response_str = self.base_agent.run(input_str)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"First attempt failed: {str(e)}. Retrying with correction...")

        # Second attempt with correction
        if response_str is None:
            raise AgentExecutionError("Failed to get response on first attempt.")

        try:
            logger.info("Running API Designer Agent - Attempt 2 (Correction)")
            correction_prompt = (
                f"The previous response was not valid JSON. Please fix it and return ONLY valid JSON. "
                f"Do not include any markdown wrap, text explanations, or unescaped control characters:\n"
                f"{response_str}"
            )
            response_str = self.base_agent.run(correction_prompt)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Second attempt failed: {str(e)}")
            raise AgentExecutionError(f"Failed to get valid JSON after two attempts: {str(e)}") from e

    def _parse_response(self, response_str: str) -> APIDesignerResponse:
        """Parse and validate the agent's response."""
        cleaned = response_str.strip()

        # 1. Clean markdown code fences if present
        if "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
                part_clean = part.strip()
                if part_clean.startswith("json"):
                    part_clean = part_clean[4:].strip()
                if part_clean.startswith("{") and part_clean.endswith("}"):
                    cleaned = part_clean
                    break

        # 2. Extract bounding brackets if there is leading/trailing text outside the JSON
        if not (cleaned.startswith("{") and cleaned.endswith("}")):
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx:end_idx + 1]

        cleaned = cleaned.strip()

        # 3. Parse JSON tolerating control characters (strict=False)
        try:
            data = json.loads(cleaned, strict=False)
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError occurred during json.loads: {str(e)}")
            logger.error(f"Target string for parsing:\n{cleaned}")
            raise

        # 4. Clean double-escaped newlines in the openapi_spec field
        if isinstance(data, dict) and "openapi_spec" in data:
            spec = data["openapi_spec"]
            if isinstance(spec, str):
                if "\\n" in spec and "\n" not in spec:
                    spec = spec.replace("\\n", "\n")
                data["openapi_spec"] = spec

        # 5. Validate with Pydantic
        try:
            return APIDesignerResponse(**data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {str(e)}")
            logger.error(f"Parsed dictionary content:\n{json.dumps(data, indent=2) if isinstance(data, dict) else data}")
            raise
