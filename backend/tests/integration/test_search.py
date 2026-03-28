"""
Integration tests for the search endpoint.

Endpoints covered:
  GET /api/search?q=...
  GET /api/search?q=...&workspace_id=...
"""
import pytest
from tests.integration.conftest import register_and_login


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(client, email="search_user@example.com", name="Search User"):
    """Register user, return (headers, workspace_id)."""
    headers = register_and_login(client, email=email, name=name)
    ws_resp = client.get("/api/workspaces", headers=headers)
    wid = ws_resp.get_json()["workspaces"][0]["id"]
    return headers, wid


def _create_page_with_content(client, headers, wid, title, plain_text):
    """Create a page and immediately save content."""
    create_resp = client.post(
        f"/api/workspaces/{wid}/pages",
        json={"title": title},
        headers=headers,
    )
    assert create_resp.status_code == 201
    page = create_resp.get_json()["page"]

    client.put(
        f"/api/pages/{page['id']}/content",
        json={
            "blocks": {"type": "doc", "content": []},
            "plain_text": plain_text,
        },
        headers=headers,
    )
    return page


# ---------------------------------------------------------------------------
# Basic search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_returns_pages_matching_title(self, client):
        headers, wid = _setup(client, email="searchtitle@example.com")
        _create_page_with_content(
            client, headers, wid,
            title="Python Programming",
            plain_text="Intro content",
        )
        _create_page_with_content(
            client, headers, wid,
            title="JavaScript Fundamentals",
            plain_text="Some other content",
        )

        resp = client.get("/api/search?q=Python", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "results" in body
        assert "query" in body
        titles = [r["title"] for r in body["results"]]
        assert "Python Programming" in titles
        assert "JavaScript Fundamentals" not in titles

    def test_returns_pages_matching_plain_text_content(self, client):
        headers, wid = _setup(client, email="searchcontent@example.com")
        _create_page_with_content(
            client, headers, wid,
            title="Study Notes",
            plain_text="Photosynthesis converts sunlight into energy",
        )
        _create_page_with_content(
            client, headers, wid,
            title="Unrelated Page",
            plain_text="Nothing relevant here",
        )

        resp = client.get("/api/search?q=Photosynthesis", headers=headers)
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.get_json()["results"]]
        assert "Study Notes" in titles
        assert "Unrelated Page" not in titles

    def test_search_is_case_insensitive(self, client):
        """ILIKE query means uppercase/lowercase should match."""
        headers, wid = _setup(client, email="searchcase@example.com")
        _create_page_with_content(
            client, headers, wid,
            title="Biology Overview",
            plain_text="Mitochondria are the powerhouse of the cell",
        )

        resp = client.get("/api/search?q=mitochondria", headers=headers)
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.get_json()["results"]]
        assert "Biology Overview" in titles

    def test_returns_empty_list_for_no_matches(self, client):
        headers, wid = _setup(client, email="searchnomatch@example.com")
        _create_page_with_content(
            client, headers, wid,
            title="Algebra Basics",
            plain_text="Equations and variables",
        )

        resp = client.get("/api/search?q=XYZ_DEFINITELY_NOT_FOUND_999", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["results"] == []

    def test_returns_empty_list_when_query_is_blank(self, client):
        headers, wid = _setup(client, email="searchblank@example.com")
        resp = client.get("/api/search?q=", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["results"] == []

    def test_returns_empty_list_when_q_param_missing(self, client):
        headers, _ = _setup(client, email="searchnoparam@example.com")
        resp = client.get("/api/search", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["results"] == []

    def test_does_not_return_deleted_pages(self, client):
        headers, wid = _setup(client, email="searchdel@example.com")
        page = _create_page_with_content(
            client, headers, wid,
            title="Deleted Subject",
            plain_text="This page content should not appear",
        )
        # Soft-delete the page
        client.delete(f"/api/pages/{page['id']}", headers=headers)

        resp = client.get("/api/search?q=Deleted Subject", headers=headers)
        ids = [r["id"] for r in resp.get_json()["results"]]
        assert page["id"] not in ids

    def test_does_not_return_another_users_pages(self, client):
        h1 = register_and_login(
            client, email="searchown@example.com", name="Owner"
        )
        h2 = register_and_login(
            client, email="searchother@example.com", name="Other"
        )

        ws_resp = client.get("/api/workspaces", headers=h1)
        wid1 = ws_resp.get_json()["workspaces"][0]["id"]
        _create_page_with_content(
            client, h1, wid1,
            title="Owner Secret Notes",
            plain_text="top secret content",
        )

        resp = client.get("/api/search?q=Owner Secret Notes", headers=h2)
        assert resp.status_code == 200
        assert resp.get_json()["results"] == []

    def test_returns_401_without_jwt(self, client):
        resp = client.get("/api/search?q=anything")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Workspace-scoped search
# ---------------------------------------------------------------------------

class TestSearchByWorkspace:
    def test_filters_results_by_workspace_id(self, client):
        headers = register_and_login(
            client, email="searchwsfilter@example.com", name="WS Filter User"
        )
        ws1 = client.post(
            "/api/workspaces", json={"name": "WS1"}, headers=headers
        ).get_json()["workspace"]
        ws2 = client.post(
            "/api/workspaces", json={"name": "WS2"}, headers=headers
        ).get_json()["workspace"]

        _create_page_with_content(
            client, headers, ws1["id"],
            title="Quantum Mechanics",
            plain_text="wave-particle duality",
        )
        _create_page_with_content(
            client, headers, ws2["id"],
            title="Quantum Computing",
            plain_text="qubits and superposition",
        )

        resp = client.get(
            f"/api/search?q=Quantum&workspace_id={ws1['id']}",
            headers=headers,
        )
        assert resp.status_code == 200
        results = resp.get_json()["results"]
        titles = [r["title"] for r in results]
        assert "Quantum Mechanics" in titles
        assert "Quantum Computing" not in titles

    def test_search_result_includes_expected_fields(self, client):
        headers, wid = _setup(client, email="searchfields@example.com")
        _create_page_with_content(
            client, headers, wid,
            title="Field Test Page",
            plain_text="some searchable text here",
        )

        resp = client.get("/api/search?q=Field Test", headers=headers)
        assert resp.status_code == 200
        results = resp.get_json()["results"]
        assert len(results) >= 1
        result = results[0]
        # Verify the shape returned by search_service.py
        assert "id" in result
        assert "title" in result
        assert "icon" in result
        assert "workspace_id" in result
        assert "updated_at" in result
        assert "snippet" in result

    def test_snippet_contains_matching_text(self, client):
        headers, wid = _setup(client, email="searchsnippet@example.com")
        _create_page_with_content(
            client, headers, wid,
            title="Snippet Test",
            plain_text="The quick brown fox jumps over the lazy dog",
        )

        resp = client.get("/api/search?q=brown fox", headers=headers)
        assert resp.status_code == 200
        results = resp.get_json()["results"]
        assert len(results) >= 1
        # The snippet should contain the matched text
        snippet = results[0]["snippet"].lower()
        assert "brown" in snippet or "fox" in snippet
