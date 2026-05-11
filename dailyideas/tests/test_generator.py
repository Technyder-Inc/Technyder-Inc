import pytest
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))


@patch("generator._client")
def test_generate_daily_ideas_returns_list(mock_client):
    mock_response = MagicMock()
    mock_response.content[0].text = (
        '[{"title":"Idea 1","description":"Desc 1","category":"AI","priority":"high"}]'
    )
    mock_client.messages.create.return_value = mock_response

    from generator import generate_daily_ideas
    ideas = generate_daily_ideas(topic="AI", count=1)

    assert isinstance(ideas, list)
    assert len(ideas) == 1
    assert ideas[0]["title"] == "Idea 1"
    assert "date" in ideas[0]
    assert ideas[0]["topic"] == "AI"
