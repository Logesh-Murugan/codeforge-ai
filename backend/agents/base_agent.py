import os
import time
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI, APIError, RateLimitError
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
        initial_retry_delay: float = 1.0
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL
        )

    def run(self, user_input: str, **kwargs) -> str:
        """
        Run the agent with the given user input.
        
        Args:
            user_input: The user's input string.
            **kwargs: Additional arguments to pass to the OpenAI API.
            
        Returns:
            The agent's response string.
            
        Raises:
            AgentExecutionError: If the agent fails after max retries.
        """
        messages: List[Dict[str, Any]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_input})

        retries = 0
        delay = self.initial_retry_delay

        while retries <= self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )

                # Log token usage
                if hasattr(response, 'usage'):
                    usage = response.usage
                    logger.info(
                        f"Token usage: Input={usage.prompt_tokens}, "
                        f"Output={usage.completion_tokens}, "
                        f"Total={usage.total_tokens}"
                    )

                # Return the response
                return response.choices[0].message.content.strip()

            except RateLimitError as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded for rate limit.")
                    raise AgentExecutionError(f"Rate limit exceeded after {self.max_retries} retries.") from e

                logger.warning(f"Rate limit hit, retrying in {delay:.2f} seconds... (Retry {retries}/{self.max_retries})")
                time.sleep(delay)
                delay *= 2  # Exponential backoff

            except APIError as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded for API error.")
                    raise AgentExecutionError(f"API error after {self.max_retries} retries: {str(e)}") from e

                logger.warning(f"API error, retrying in {delay:.2f} seconds... (Retry {retries}/{self.max_retries})")
                time.sleep(delay)
                delay *= 2  # Exponential backoff

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise AgentExecutionError(f"Unexpected error: {str(e)}") from e
