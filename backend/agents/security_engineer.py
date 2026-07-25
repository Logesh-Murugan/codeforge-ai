import os
import json
import logging
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import BackendDeveloperResponse, SecurityEngineerResponse

logger = logging.getLogger(__name__)


class SecurityEngineerAgent:
    """Agent that performs a security audit of generated backend code."""

    def __init__(self):
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "security_engineer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(self, backend_code: BackendDeveloperResponse) -> SecurityEngineerResponse:
        """
        Run the Security Engineer agent.

        Args:
            backend_code: The Backend Developer's generated file output.

        Returns:
            Structured SecurityEngineerResponse.

        Raises:
            AgentExecutionError: If execution fails after retries.
        """
        input_str = backend_code.model_dump_json(indent=2)

        # First attempt
        response_str = None
        try:
            logger.info("Running Security Engineer Agent - Attempt 1")
            response_str = self.base_agent.run(input_str)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"First attempt failed: {str(e)}. Retrying with correction...")

        if response_str is None:
            raise AgentExecutionError("Failed to get response on first attempt.")

        # Second attempt with correction
        try:
            logger.info("Running Security Engineer Agent - Attempt 2 (Correction)")
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

    def _parse_response(self, response_str: str) -> SecurityEngineerResponse:
        """Parse and validate the agent's response."""
        cleaned = response_str.strip()

        # 1. Strip markdown code fences
        if "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
                part_clean = part.strip()
                if part_clean.startswith("json"):
                    part_clean = part_clean[4:].strip()
                if part_clean.startswith("{") and part_clean.endswith("}"):
                    cleaned = part_clean
                    break

        # 2. Extract bounding braces if wrapped in prose
        if not (cleaned.startswith("{") and cleaned.endswith("}")):
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx:end_idx + 1]

        cleaned = cleaned.strip()

        # 3. Parse JSON (tolerating control characters)
        try:
            data = json.loads(cleaned, strict=False)
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {str(e)}")
            logger.error(f"Attempted to parse:\n{cleaned}")
            raise

        # 4. Ensure severity counts are consistent if missing
        if isinstance(data, dict):
            findings = data.get("findings", [])
            if not data.get("critical_count"):
                data["critical_count"] = sum(1 for f in findings if f.get("severity") == "critical")
            if not data.get("high_count"):
                data["high_count"] = sum(1 for f in findings if f.get("severity") == "high")
            if not data.get("medium_count"):
                data["medium_count"] = sum(1 for f in findings if f.get("severity") == "medium")
            if not data.get("low_count"):
                data["low_count"] = sum(1 for f in findings if f.get("severity") == "low")

        # 5. Validate with Pydantic
        try:
            return SecurityEngineerResponse(**data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {str(e)}")
            logger.error(f"Parsed data:\n{json.dumps(data, indent=2) if isinstance(data, dict) else data}")
            raise
