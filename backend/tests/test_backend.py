import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, find_step_free_path, GRAPH, qa_cache, ask_limiter, route_limiter, help_limiter

client = TestClient(app)

def test_find_step_free_path():
    # Test valid step-free path from section_114 to restroom_114
    path = find_step_free_path("section_114", "restroom_114", GRAPH)
    assert path == ["section_114", "restroom_114"]

    # Test invalid step-free path to section_210 (which is not step_free)
    path = find_step_free_path("section_114", "section_210", GRAPH)
    assert path == []

def test_pydantic_validation():
    # Question too short
    response = client.post("/api/ask", json={"question": "", "language": "en"})
    assert response.status_code == 422

    # Question too long
    response = client.post("/api/ask", json={"question": "a" * 300, "language": "en"})
    assert response.status_code == 422

    # Route request validation
    response = client.post("/api/route", json={"start": "", "destination": "gate_b"})
    assert response.status_code == 422

def test_rate_limiter():
    # Reset limiters for clean test
    ask_limiter.requests.clear()
    
    # Hit ask_limiter threshold (10 calls per minute)
    for _ in range(10):
        client.post("/api/ask", json={"question": "Where is the exit?", "language": "en"})
    
    # 11th call should return 429
    response = client.post("/api/ask", json={"question": "Where is the exit?", "language": "en"})
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many questions. Please wait a moment."

@patch("main.embedding_model")
@patch("main.kb_index")
@patch("main.Anthropic")
def test_qa_caching(mock_anthropic, mock_kb_index, mock_embedding_model):
    # Reset cache and limiter
    qa_cache.clear()
    ask_limiter.requests.clear()

    # Mock embedding and index
    mock_embedding_model.encode.return_value = [[0.1] * 384]
    mock_kb_index.search.return_value = (None, [[0]])
    
    # Populate kb_chunks in main module to avoid index out of bounds
    import main
    main.kb_chunks = ["chunk 1"]

    # Mock Claude response
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"answer": "Restroom is behind section 114.", "citations": ["chunk 1"]}')]
    mock_client.messages.create.return_value = mock_response

    payload = {"question": "Where is the restroom?", "language": "en", "location": "Section 114"}
    
    # First request
    response1 = client.post("/api/ask", json=payload)
    assert response1.status_code == 200
    assert response1.json()["answer"] == "Restroom is behind section 114."
    assert mock_client.messages.create.call_count == 1

    # Second request (identical) should hit cache and not call LLM again
    response2 = client.post("/api/ask", json=payload)
    assert response2.status_code == 200
    assert response2.json()["answer"] == "Restroom is behind section 114."
    assert mock_client.messages.create.call_count == 1

def test_get_route():
    # Reset limiter
    route_limiter.requests.clear()
    
    response = client.post("/api/route", json={"start": "section_114", "destination": "restroom_114", "step_free": True})
    assert response.status_code == 200
    data = response.json()
    assert "route" in data
    assert "description" in data
    assert data["step_free"] is True

def test_rate_limiter():
    from main import InMemoryRateLimiter
    limiter = InMemoryRateLimiter(1, 10)
    assert limiter.is_allowed('127.0.0.1') == True
    assert limiter.is_allowed('127.0.0.1') == False
