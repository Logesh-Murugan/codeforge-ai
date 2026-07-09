import os
import json
import logging
from typing import Optional
from pydantic import ValidationError

from agents.base_agent import BaseAgent, AgentExecutionError
from app.schemas import SolutionArchitectResponse, BackendDeveloperResponse, DatabaseEngineerResponse

logger = logging.getLogger(__name__)


class BackendDeveloperAgent:
    """Agent that generates backend code from the solution architect's design."""

    def __init__(self):
        # Load the system prompt from file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "backend_developer.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.base_agent = BaseAgent(
            system_prompt=self.system_prompt,
            model="llama-3.3-70b-versatile"
        )

    def run(self, solution_arch: SolutionArchitectResponse, db_engineer_plan: Optional[DatabaseEngineerResponse] = None) -> BackendDeveloperResponse:
        """
        Run the backend developer agent.
        
        Args:
            solution_arch: The output from the Solution Architect agent.
            db_engineer_plan: Optional database engineer designs.
            
        Returns:
            Structured BackendDeveloperResponse.
            
        Raises:
            AgentExecutionError: If the agent fails.
        """
        # Convert inputs to JSON string (supporting backward compatibility)
        if db_engineer_plan:
            input_data = {
                "solution_architect": solution_arch.model_dump(),
                "database_engineer_plan": db_engineer_plan.model_dump()
            }
            input_str = json.dumps(input_data, indent=2)
        else:
            input_str = solution_arch.model_dump_json(indent=2)

        # First attempt
        try:
            logger.info("Running Backend Developer Agent - Attempt 1")
            response_str = self.base_agent.run(input_str)
            
            logger.info("=" * 80)
            logger.info("RAW BACKEND DEVELOPER RESPONSE (ATTEMPT 1)")
            logger.info(response_str)
            logger.info("=" * 80)
            
            return self._parse_response(response_str)
        except Exception as e:
            logger.warning(f"First attempt failed: {type(e).__name__}: {str(e)}. Retrying with correction...")
            if 'response_str' in locals():
                logger.debug(f"Failed response: {response_str}")

        # Second attempt with correction
        try:
            logger.info("Running Backend Developer Agent - Attempt 2 (Correction)")
            correction_prompt = (
                f"You generated an invalid JSON response earlier. Please fix it and return ONLY valid, parseable JSON. "
                f"Do not include any markdown wrap, text explanations, or unescaped control characters like tabs/raw newlines. "
                f"Previous output:\n{response_str}"
            )
            response_str = self.base_agent.run(correction_prompt)
            
            logger.info("=" * 80)
            logger.info("RAW BACKEND DEVELOPER RESPONSE (ATTEMPT 2)")
            logger.info(response_str)
            logger.info("=" * 80)
            
            return self._parse_response(response_str)
        except Exception as e:
            logger.error("=" * 80)
            logger.error("BACKEND DEVELOPER AGENT CRITICAL FAILURE")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            if 'response_str' in locals():
                logger.error("FAILED RESPONSE ON ATTEMPT 2:")
                logger.error(response_str)
            logger.error("=" * 80)
            raise AgentExecutionError(f"Failed to get valid JSON after two attempts: {str(e)}") from e

    def _parse_response(self, response_str: str) -> BackendDeveloperResponse:
        """Parse and validate the agent's response with robust fallback."""
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

        # 4. Validate with Pydantic
        try:
            return BackendDeveloperResponse(**data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {str(e)}")
            logger.error(f"Parsed dictionary content:\n{json.dumps(data, indent=2) if isinstance(data, dict) else data}")
            raise
