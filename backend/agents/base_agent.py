import time
import logging
import traceback
import httpx
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
        temperature: float = 0.0,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.temperature = temperature

        logger.info("=" * 80)
        logger.info(f"Initializing Groq Client for model: {self.model}")
        logger.info(f"GROQ_BASE_URL: {settings.GROQ_BASE_URL}")
        logger.info(f"GROQ_API_KEY starts with: {settings.GROQ_API_KEY[:10]}...")
        logger.info(f"Temperature: {self.temperature}")
        logger.info("=" * 80)

        # Force IPv4 socket binding to prevent Render network proxy/dual-stack IPv6 DNS resolution timeouts
        self.http_client = httpx.Client(
            transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            verify=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            http_client=self.http_client,
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
                logger.info(f"Sending request to Groq API (Attempt {retries + 1}/{self.max_retries + 1})...")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
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

            except httpx.ConnectTimeout as e:
                retries += 1
                logger.error(f"[DNS/Network Connect Timeout] httpx.ConnectTimeout occurred: {str(e)}")
                logger.error(traceback.format_exc())
                if retries > self.max_retries:
                    raise AgentExecutionError(f"Groq API connection timeout after {self.max_retries} retries: {str(e)}") from e
                time.sleep(delay)
                delay *= 2

            except httpx.ReadTimeout as e:
                retries += 1
                logger.error(f"[Groq Response Read Timeout] httpx.ReadTimeout occurred: {str(e)}")
                logger.error(traceback.format_exc())
                if retries > self.max_retries:
                    raise AgentExecutionError(f"Groq API read timeout after {self.max_retries} retries: {str(e)}") from e
                time.sleep(delay)
                delay *= 2

            except httpx.ConnectError as e:
                retries += 1
                logger.error(f"[DNS Resolve / SSL Trust Error] httpx.ConnectError occurred (Check DNS or SSL certificates): {str(e)}")
                logger.error(traceback.format_exc())
                if retries > self.max_retries:
                    raise AgentExecutionError(f"Groq API connection resolve error after {self.max_retries} retries: {str(e)}") from e
                time.sleep(delay)
                delay *= 2

            except httpx.TransportError as e:
                retries += 1
                logger.error(f"[Transport Layer Error] httpx.TransportError occurred: {str(e)}")
                logger.error(traceback.format_exc())
                if retries > self.max_retries:
                    raise AgentExecutionError(f"Groq API transport layer error after {self.max_retries} retries: {str(e)}") from e
                time.sleep(delay)
                delay *= 2

            except httpx.HTTPStatusError as e:
                retries += 1
                logger.error(f"[HTTP Status Error] httpx.HTTPStatusError occurred: {str(e)}")
                logger.error(traceback.format_exc())
                if retries > self.max_retries:
                    raise AgentExecutionError(f"Groq API returned bad HTTP status after {self.max_retries} retries: {str(e)}") from e
                time.sleep(delay)
                delay *= 2

            except RateLimitError as e:
                retries += 1
                logger.warning(f"Rate limit. Retry {retries}/{self.max_retries}")
                if retries > self.max_retries:
                    logger.exception("Rate limit exceeded.")
                    raise AgentExecutionError("Rate limit exceeded.") from e
                time.sleep(delay)
                delay *= 2

            except APIConnectionError as e:
                retries += 1
                logger.error(f"[API Connection Error] OpenAI/Groq APIConnectionError occurred: {str(e)}")
                logger.error(traceback.format_exc())
                if retries > self.max_retries:
                    raise AgentExecutionError(f"API Connection Error: {str(e)}") from e
                time.sleep(delay)
                delay *= 2

            except APIError as e:
                retries += 1
                logger.exception("OpenAI/Groq API Error")
                if retries > self.max_retries:
                    raise AgentExecutionError(f"API Error: {str(e)}") from e
                time.sleep(delay)
                delay *= 2

            except Exception as e:
                logger.error("=" * 80)
                logger.error(f"Unexpected Exception Type: {type(e).__name__}")
                logger.error(f"Exception Message: {str(e)}")
                logger.error(traceback.format_exc())
                logger.error("=" * 80)
                raise AgentExecutionError(f"Unexpected error: {str(e)}") from e