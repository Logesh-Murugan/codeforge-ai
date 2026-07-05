import time
import logging
import traceback
from typing import Optional, List, Dict, Any

from openai import (
    OpenAI,
    APIError,
    RateLimitError,
    APIConnectionError,
)

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentExecutionError(Exception):
    """Custom exception for agent execution errors."""
    pass


class BaseAgent:
    """Base agent class that wraps Groq API calls with retry logic and token logging."""

    def __init__(
        self,
        model: str = "llama-3.1-8b-instant",
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay

        logger.info("=" * 80)
        logger.info(f"GROQ_BASE_URL: {settings.GROQ_BASE_URL}")
        logger.info(f"Model: {self.model}")
        logger.info(f"GROQ_API_KEY starts with: {settings.GROQ_API_KEY[:10]}...")
        logger.info("=" * 80)

        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=30.0,
        )

    def run(self, user_input: str, **kwargs) -> str:
        messages: List[Dict[str, Any]] = []

        if self.system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": self.system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        retries = 0
        delay = self.initial_retry_delay

        while retries <= self.max_retries:

            try:
                logger.info("Sending request to Groq API...")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs,
                )

                logger.info("Groq API request successful.")

                if hasattr(response, "usage") and response.usage:
                    usage = response.usage
                    logger.info(
                        f"Token Usage | "
                        f"Prompt={usage.prompt_tokens}, "
                        f"Completion={usage.completion_tokens}, "
                        f"Total={usage.total_tokens}"
                    )

                return response.choices[0].message.content.strip()

            except RateLimitError as e:

                retries += 1

                logger.warning(
                    f"Rate limit. Retry {retries}/{self.max_retries}"
                )

                if retries > self.max_retries:
                    logger.exception("Rate limit exceeded.")
                    raise AgentExecutionError(
                        "Rate limit exceeded."
                    ) from e

                time.sleep(delay)
                delay *= 2

            except APIConnectionError as e:

                retries += 1

                logger.exception("API Connection Error")

                if retries > self.max_retries:
                    raise AgentExecutionError(
                        f"API Connection Error: {str(e)}"
                    ) from e

                time.sleep(delay)
                delay *= 2

            except APIError as e:

                retries += 1

                logger.exception("OpenAI/Groq API Error")

                if retries > self.max_retries:
                    raise AgentExecutionError(
                        f"API Error: {str(e)}"
                    ) from e

                time.sleep(delay)
                delay *= 2

            except Exception as e:

                logger.error("=" * 80)
                logger.error(f"Exception Type: {type(e).__name__}")
                logger.error(f"Exception Message: {str(e)}")
                logger.error(traceback.format_exc())
                logger.error("=" * 80)

                raise AgentExecutionError(
                    f"Unexpected error: {str(e)}"
                ) from e