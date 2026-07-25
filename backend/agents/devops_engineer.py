import os
import json
import logging
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import SolutionArchitectResponse, DevOpsEngineerResponse

logger = logging.getLogger(__name__)


class DevOpsEngineerAgent:
    """Agent that creates containerization configs, reverse proxies, CI/CD, and deployment guides."""

    def __init__(self):
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "devops_engineer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(self, solution_arch: SolutionArchitectResponse, doc_text: str) -> DevOpsEngineerResponse:
        """
        Run the DevOps Engineer agent.
        
        Args:
            solution_arch: The Solution Architect's response.
            doc_text: Documentation/README text from Doc Writer.
            
        Returns:
            Structured DevOpsEngineerResponse.
            
        Raises:
            AgentExecutionError: If execution fails.
        """
        # Pack inputs into unified context
        input_data = {
            "solution_architect": solution_arch.model_dump(),
            "documentation": doc_text
        }

        input_str = json.dumps(input_data, indent=2)

        # First attempt
        response_str = None
        try:
            logger.info("Running DevOps Engineer Agent - Attempt 1")
            response_str = self.base_agent.run(input_str)
            return self._parse_response(response_str)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"First attempt failed: {str(e)}. Retrying with correction...")

        # Second attempt with correction
        if response_str is None:
            raise AgentExecutionError("Failed to get response on first attempt.")

        try:
            logger.info("Running DevOps Engineer Agent - Attempt 2 (Correction)")
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

    def _parse_response(self, response_str: str) -> DevOpsEngineerResponse:
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

        # Clean double-escaped newlines in code and config fields if any
        config_fields = ["dockerfile", "docker_compose", "github_actions_workflow", "nginx_config"]
        for field in config_fields:
            if isinstance(data, dict) and field in data:
                val = data[field]
                if isinstance(val, str):
                    if "\\n" in val and "\n" not in val:
                        val = val.replace("\\n", "\n")
                    data[field] = val

        # Validate Pydantic model
        try:
            return DevOpsEngineerResponse(**data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {str(e)}")
            logger.error(f"Parsed dictionary content:\n{json.dumps(data, indent=2) if isinstance(data, dict) else data}")
            raise
