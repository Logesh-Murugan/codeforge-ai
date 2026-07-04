import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from agents.business_analyst import BusinessAnalystAgent
from agents.base_agent import AgentExecutionError


def test_business_analyst_success():
    """Test successful business analyst execution."""
    with patch("agents.business_analyst.BaseAgent") as mock_base_agent:
        # Mock the base agent
        mock_instance = MagicMock()
        mock_instance.run.return_value = '''
        {
          "entities": [{"name": "User", "fields": ["id", "email"]}],
          "relationships": [],
          "requires_auth": true,
          "core_actions": ["create_user"]
        }
        '''
        mock_base_agent.return_value = mock_instance

        # Test the agent
        agent = BusinessAnalystAgent()
        response = agent.run("Test project idea")

        assert response.requires_auth is True
        assert response.entities[0].name == "User"


def test_business_analyst_malformed_json_retry():
    """Test that the agent retries on malformed JSON."""
    with patch("agents.business_analyst.BaseAgent") as mock_base_agent:
        # Mock the base agent to return malformed JSON first, then valid JSON
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            '''This is not JSON''',
            '''
            {
              "entities": [{"name": "User", "fields": ["id", "email"]}],
              "relationships": [],
              "requires_auth": true,
              "core_actions": ["create_user"]
            }
            '''
        ]
        mock_base_agent.return_value = mock_instance

        # Test the agent
        agent = BusinessAnalystAgent()
        response = agent.run("Test project idea")

        assert response.requires_auth is True
        assert mock_instance.run.call_count == 2


def test_business_analyst_max_retries_exceeded():
    """Test that the agent raises AgentExecutionError after two failed attempts."""
    with patch("agents.business_analyst.BaseAgent") as mock_base_agent:
        # Mock the base agent to always return malformed JSON
        mock_instance = MagicMock()
        mock_instance.run.return_value = '''This is not JSON'''
        mock_base_agent.return_value = mock_instance

        # Test the agent
        agent = BusinessAnalystAgent()

        with pytest.raises(AgentExecutionError):
            agent.run("Test project idea")

        assert mock_instance.run.call_count == 2
