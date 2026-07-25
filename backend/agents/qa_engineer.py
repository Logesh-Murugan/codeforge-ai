import os
import json
import logging
from typing import Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import BackendDeveloperResponse, SecurityEngineerResponse, QAEngineerResponse

logger = logging.getLogger(__name__)


class QAEngineerAgent:
    """Agent that creates test plans, edge cases, unit, integration, and API tests."""

    def __init__(self):
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "qa_engineer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(
        self,
        backend_code: BackendDeveloperResponse,
        security_audit: Optional[SecurityEngineerResponse] = None
    ) -> QAEngineerResponse:
        """
        Run the QA Engineer agent.
        
        Args:
            backend_code: The Backend Developer's response.
            security_audit: Optional Security Engineer's audit response.
            
        Returns:
            Structured QAEngineerResponse.
            
        Raises:
            AgentExecutionError: If execution fails.
        """
        # Pack inputs into unified context
        input_data = {
            "backend_code": backend_code.model_dump()
        }
        if security_audit:
            input_data["security_audit"] = security_audit.model_dump()

        input_str = json.dumps(input_data, indent=2)

        # First attempt
        response_str = None
        try:
            logger.info("Running QA Engineer Agent - Attempt 1")
            response_str = self.base_agent.run(input_str)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"First attempt failed: {str(e)}. Retrying with correction...")

        # Second attempt with correction
        if response_str is None:
            raise AgentExecutionError("Failed to get response on first attempt.")

        try:
            logger.info("Running QA Engineer Agent - Attempt 2 (Correction)")
            correction_prompt = (
                f"The previous response was not valid JSON. Please fix it and return ONLY valid JSON. "
                f"Do not include any markdown code blocks, prose explanations, or unescaped control characters:\n"
                f"{response_str}"
            )
            response_str = self.base_agent.run(correction_prompt)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Second attempt failed: {str(e)}")
            raise AgentExecutionError(f"Failed to get valid JSON after two attempts: {str(e)}") from e

    def _parse_response(self, response_str: str) -> QAEngineerResponse:
        """Parse and validate the agent's response."""
        # Clean up response string
        cleaned = response_str.strip()
        if "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
                part_clean = part.strip()
                if part_clean.startswith("json"):
                    part_clean = part_clean[4:].strip()
                if part_clean.startswith("{") and part_clean.endswith("}"):
                    cleaned = part_clean
                    break

        if not (cleaned.startswith("{") and cleaned.endswith("}")):
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx:end_idx + 1]

        cleaned = cleaned.strip()

        # Parse JSON
        data = json.loads(cleaned, strict=False)

        # Clean double-escaped newlines in test code fields if any
        for field in ["unit_tests_code", "integration_tests_code", "api_tests_code"]:
            if isinstance(data, dict) and field in data:
                code = data[field]
                if isinstance(code, str):
                    if "\\n" in code and "\n" not in code:
                        code = code.replace("\\n", "\n")
                    data[field] = code

        # Validate Pydantic model
        try:
            return QAEngineerResponse(**data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {str(e)}")
            logger.error(f"Parsed dictionary content:\n{json.dumps(data, indent=2) if isinstance(data, dict) else data}")
            raise
