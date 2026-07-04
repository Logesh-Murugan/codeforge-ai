import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from agents.base_agent import BaseAgent, AgentExecutionError


def test_base_agent_success():
    """Test successful agent execution."""
    with patch("agents.base_agent.OpenAI") as mock_openai:
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Test the agent
        agent = BaseAgent(system_prompt="Test system prompt")
        response = agent.run("Test input")

        assert response == "Test response"
        mock_client.chat.completions.create.assert_called_once()


def test_base_agent_rate_limit_retry():
    """Test that the agent retries on rate limit errors."""
    with patch("agents.base_agent.OpenAI") as mock_openai, patch("agents.base_agent.time.sleep") as mock_sleep:
        # Mock the OpenAI client to raise RateLimitError twice, then succeed
        mock_client = MagicMock()
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit", response=MagicMock(), body=None),
            RateLimitError("Rate limit", response=MagicMock(), body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Test response"))], usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30))
        ]
        mock_openai.return_value = mock_client

        # Test the agent
        agent = BaseAgent(max_retries=2)
        response = agent.run("Test input")

        assert response == "Test response"
        assert mock_client.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2


def test_base_agent_max_retries_exceeded():
    """Test that the agent raises AgentExecutionError after max retries."""
    with patch("agents.base_agent.OpenAI") as mock_openai, patch("agents.base_agent.time.sleep") as mock_sleep:
        # Mock the OpenAI client to always raise RateLimitError
        mock_client = MagicMock()
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = RateLimitError("Rate limit", response=MagicMock(), body=None)
        mock_openai.return_value = mock_client

        # Test the agent
        agent = BaseAgent(max_retries=2)

        with pytest.raises(AgentExecutionError) as excinfo:
            agent.run("Test input")

        assert "Rate limit exceeded" in str(excinfo.value)
        assert mock_client.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2
