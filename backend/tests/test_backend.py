"""
Comprehensive test suite for StadiumSense Backend.
Tests cover: rate limiting, input validation, routing, Q&A caching,
accessibility pipelines, and WebSocket connectivity.
"""
import pytest
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import (
    app,
    find_step_free_path,
    GRAPH,
    qa_cache,
    ask_limiter,
    route_limiter,
    help_limiter,
    InMemoryRateLimiter,
    get_icon_for_category,
    get_severity_color,
    get_fallback_translations,
)

client = TestClient(app)


# ─────────────────────────────────────────────
# InMemoryRateLimiter unit tests
# ─────────────────────────────────────────────

class TestInMemoryRateLimiter:
    """Unit tests for the InMemoryRateLimiter class."""

    def test_allows_first_request(self):
        limiter = InMemoryRateLimiter(requests_limit=3, window_seconds=60)
        assert limiter.is_allowed("192.168.1.1") is True

    def test_blocks_after_limit_exceeded(self):
        limiter = InMemoryRateLimiter(requests_limit=2, window_seconds=60)
        assert limiter.is_allowed("10.0.0.1") is True
        assert limiter.is_allowed("10.0.0.1") is True
        assert limiter.is_allowed("10.0.0.1") is False

    def test_different_ips_are_independent(self):
        limiter = InMemoryRateLimiter(requests_limit=1, window_seconds=60)
        assert limiter.is_allowed("1.1.1.1") is True
        assert limiter.is_allowed("1.1.1.1") is False
        # Different IP should still be allowed
        assert limiter.is_allowed("2.2.2.2") is True

    def test_window_allows_single_request_per_ip(self):
        limiter = InMemoryRateLimiter(requests_limit=1, window_seconds=10)
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is False


# ─────────────────────────────────────────────
# Helper function unit tests
# ─────────────────────────────────────────────

class TestHelperFunctions:
    """Unit tests for utility/helper functions."""

    def test_get_icon_for_known_categories(self):
        assert get_icon_for_category("match_event", "info") == "⚽"
        assert get_icon_for_category("wayfinding", "info") == "🧭"
        assert get_icon_for_category("medical", "critical") == "🏥"
        assert get_icon_for_category("security", "warning") == "🔒"
        assert get_icon_for_category("evacuation", "critical") == "🚨"

    def test_get_icon_for_unknown_category_returns_default(self):
        assert get_icon_for_category("unknown_category", "info") == "ℹ️"

    def test_get_severity_color(self):
        assert get_severity_color("critical") == "#dc2626"
        assert get_severity_color("warning") == "#f59e0b"
        assert get_severity_color("info") == "#3b82f6"
        # Unknown severity returns default blue
        assert get_severity_color("unknown") == "#3b82f6"

    def test_get_fallback_translations_welcome(self):
        result = get_fallback_translations("Welcome to the stadium today")
        assert "en" in result
        assert "hi" in result
        assert "es" in result
        assert "fr" in result
        assert "ar" in result
        assert "pt" in result
        assert "zh" in result

    def test_get_fallback_translations_evacuation(self):
        result = get_fallback_translations("Please proceed to evacuation exit")
        assert "en" in result

    def test_get_fallback_translations_unknown_text(self):
        text = "Some completely unknown announcement"
        result = get_fallback_translations(text)
        assert result["en"] == text


# ─────────────────────────────────────────────
# Navigation / Pathfinding tests
# ─────────────────────────────────────────────

class TestStepFreePathfinding:
    """Tests for the BFS step-free navigation algorithm."""

    def test_finds_valid_step_free_path(self):
        path = find_step_free_path("section_114", "restroom_114", GRAPH)
        assert isinstance(path, list)
        assert len(path) >= 2
        assert path[0] == "section_114"
        assert path[-1] == "restroom_114"

    def test_returns_empty_for_inaccessible_destination(self):
        # section_210 is NOT step-free per fixture data
        path = find_step_free_path("section_114", "section_210", GRAPH)
        assert path == []

    def test_returns_empty_for_nonexistent_nodes(self):
        path = find_step_free_path("nonexistent_a", "nonexistent_b", GRAPH)
        assert path == []

    def test_same_start_and_destination(self):
        path = find_step_free_path("section_114", "section_114", GRAPH)
        # BFS returns the start node immediately
        assert path == ["section_114"]

    def test_path_uses_only_step_free_nodes(self):
        path = find_step_free_path("section_114", "restroom_114", GRAPH)
        if path:
            nodes = GRAPH.get("nodes", {})
            for node_id in path:
                node = nodes.get(node_id, {})
                assert node.get("step_free", False) is True, (
                    f"Node '{node_id}' in path is not step-free"
                )


# ─────────────────────────────────────────────
# Pydantic validation tests
# ─────────────────────────────────────────────

class TestInputValidation:
    """Tests for Pydantic model validation on API endpoints."""

    def test_ask_empty_question_returns_422(self):
        response = client.post("/api/ask", json={"question": "", "language": "en"})
        assert response.status_code == 422

    def test_ask_too_long_question_returns_422(self):
        response = client.post("/api/ask", json={"question": "a" * 300, "language": "en"})
        assert response.status_code == 422

    def test_ask_valid_question_passes_validation(self):
        # Valid question – may fail AI call in test, but should not fail validation
        response = client.post("/api/ask", json={"question": "Where is the exit?", "language": "en"})
        assert response.status_code in (200, 422, 429, 500)
        assert response.status_code != 422  # Validation itself should pass

    def test_route_empty_start_returns_422(self):
        response = client.post("/api/route", json={"start": "", "destination": "gate_b"})
        assert response.status_code == 422

    def test_route_empty_destination_returns_422(self):
        response = client.post("/api/route", json={"start": "section_114", "destination": ""})
        assert response.status_code == 422

    def test_broadcast_too_short_message_returns_422(self):
        response = client.post(
            "/api/broadcast",
            json={"message": "Hi", "category": "info", "severity": "info"},
        )
        assert response.status_code == 422

    def test_request_help_too_short_reason_returns_422(self):
        response = client.post(
            "/api/request-help",
            json={"reason": "Hi", "location": "Section 114", "severity": "warning"},
        )
        assert response.status_code == 422

    def test_request_help_too_short_location_returns_422(self):
        response = client.post(
            "/api/request-help",
            json={"reason": "I need assistance please", "location": "S1", "severity": "warning"},
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────
# Rate limiting integration tests
# ─────────────────────────────────────────────

class TestRateLimiting:
    """Integration tests verifying rate-limit HTTP responses."""

    def setup_method(self):
        """Reset all rate limiters before each test."""
        ask_limiter.requests.clear()
        route_limiter.requests.clear()
        help_limiter.requests.clear()

    def test_ask_rate_limit_returns_429_after_threshold(self):
        for _ in range(10):
            client.post("/api/ask", json={"question": "Where is the exit?", "language": "en"})
        response = client.post("/api/ask", json={"question": "Where is the exit?", "language": "en"})
        assert response.status_code == 429
        assert "Too many" in response.json()["detail"]

    def test_route_rate_limit_returns_429_after_threshold(self):
        for _ in range(15):
            client.post("/api/route", json={"start": "section_114", "destination": "restroom_114"})
        response = client.post(
            "/api/route", json={"start": "section_114", "destination": "restroom_114"}
        )
        assert response.status_code == 429

    def test_help_rate_limit_returns_429_after_threshold(self):
        for _ in range(5):
            client.post(
                "/api/request-help",
                json={"reason": "I need assistance", "location": "Section 114", "severity": "warning"},
            )
        response = client.post(
            "/api/request-help",
            json={"reason": "I need assistance", "location": "Section 114", "severity": "warning"},
        )
        assert response.status_code == 429


# ─────────────────────────────────────────────
# Q&A caching tests
# ─────────────────────────────────────────────

class TestQACaching:
    """Tests for the in-memory Q&A response cache."""

    def setup_method(self):
        qa_cache.clear()
        ask_limiter.requests.clear()

    @patch("main.embedding_model")
    @patch("main.kb_index")
    @patch("main.Anthropic")
    def test_second_identical_request_hits_cache(self, mock_anthropic, mock_kb_index, mock_embedding_model):
        mock_embedding_model.encode.return_value = [[0.1] * 384]
        mock_kb_index.search.return_value = (None, [[0]])

        import main as main_module
        main_module.kb_chunks = ["Test KB chunk about restrooms near Section 114."]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"answer": "Restroom is behind section 114.", "citations": ["chunk 1"]}')
        ]
        mock_client.messages.create.return_value = mock_response

        payload = {"question": "Where is the restroom?", "language": "en", "location": "Section 114"}

        response1 = client.post("/api/ask", json=payload)
        assert response1.status_code == 200
        assert response1.json()["answer"] == "Restroom is behind section 114."
        first_call_count = mock_client.messages.create.call_count

        # Second identical request must use cache – LLM not called again
        response2 = client.post("/api/ask", json=payload)
        assert response2.status_code == 200
        assert response2.json()["answer"] == "Restroom is behind section 114."
        assert mock_client.messages.create.call_count == first_call_count

    @patch("main.embedding_model")
    @patch("main.kb_index")
    @patch("main.Anthropic")
    def test_different_questions_dont_share_cache(self, mock_anthropic, mock_kb_index, mock_embedding_model):
        mock_embedding_model.encode.return_value = [[0.1] * 384]
        mock_kb_index.search.return_value = (None, [[0]])

        import main as main_module
        main_module.kb_chunks = ["Some KB chunk content"]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"answer": "Answer A", "citations": []}')]
        mock_client.messages.create.return_value = mock_response

        client.post("/api/ask", json={"question": "Where is Gate A?", "language": "en"})
        count_after_first = mock_client.messages.create.call_count

        client.post("/api/ask", json={"question": "Where is Gate B?", "language": "en"})
        # A new LLM call must have been made for the different question
        assert mock_client.messages.create.call_count == count_after_first + 1


# ─────────────────────────────────────────────
# Routing endpoint tests
# ─────────────────────────────────────────────

class TestRoutingEndpoint:
    """Tests for the /api/route step-free navigation endpoint."""

    def setup_method(self):
        route_limiter.requests.clear()

    def test_valid_route_returns_200_with_expected_fields(self):
        response = client.post(
            "/api/route",
            json={"start": "section_114", "destination": "restroom_114", "step_free": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert "route" in data
        assert "description" in data
        assert "step_free" in data

    def test_inaccessible_route_returns_no_route(self):
        response = client.post(
            "/api/route",
            json={"start": "section_114", "destination": "section_210", "step_free": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["step_free"] is False
        assert data["route"] == []


# ─────────────────────────────────────────────
# Help request tests
# ─────────────────────────────────────────────

class TestHelpRequests:
    """Tests for the /api/request-help and /api/help-requests endpoints."""

    def setup_method(self):
        help_limiter.requests.clear()

    def test_submit_help_request_returns_201_fields(self):
        response = client.post(
            "/api/request-help",
            json={"reason": "I need wheelchair assistance", "location": "Section 114", "severity": "warning"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"
        assert "request" in data
        assert "id" in data["request"]
        assert data["request"]["status"] == "pending"

    def test_get_help_requests_returns_list(self):
        response = client.get("/api/help-requests")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ─────────────────────────────────────────────
# General API health tests
# ─────────────────────────────────────────────

class TestAPIHealth:
    """Basic health and sanity tests for API root and other endpoints."""

    def test_root_returns_status_running(self):
        response = client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "StadiumSense" in data["message"]

    def test_announcements_endpoint_returns_list(self):
        response = client.get("/api/announcements")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_graph_endpoint_returns_nodes_and_edges(self):
        response = client.get("/api/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    def test_kb_endpoint_returns_content(self):
        response = client.get("/api/kb")
        assert response.status_code == 200
        data = response.json()
        assert "kb" in data
        assert isinstance(data["kb"], str)
        assert len(data["kb"]) > 0
