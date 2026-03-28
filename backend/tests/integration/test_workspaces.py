"""
Integration tests for workspace endpoints.

Endpoints covered:
  GET    /api/workspaces
  POST   /api/workspaces
  GET    /api/workspaces/:id
  PUT    /api/workspaces/:id
  DELETE /api/workspaces/:id
"""
import pytest
from tests.integration.conftest import register_and_login


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers(client, email="ws_user@example.com", name="WS User"):
    return register_and_login(client, email=email, name=name)


def _create_workspace(client, headers, name="My Space", icon="🗂️"):
    resp = client.post(
        "/api/workspaces",
        json={"name": name, "icon": icon},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["workspace"]


# ---------------------------------------------------------------------------
# GET /api/workspaces
# ---------------------------------------------------------------------------

class TestListWorkspaces:
    def test_returns_list_with_default_workspace_after_register(self, client):
        headers = _headers(client)
        resp = client.get("/api/workspaces", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "workspaces" in body
        # registration creates one default workspace
        assert len(body["workspaces"]) >= 1

    def test_default_workspace_name_contains_user_name(self, client):
        headers = register_and_login(
            client, email="namedws@example.com", name="NamedUser"
        )
        resp = client.get("/api/workspaces", headers=headers)
        workspaces = resp.get_json()["workspaces"]
        names = [w["name"] for w in workspaces]
        assert any("NamedUser" in n for n in names)

    def test_returns_401_without_jwt(self, client):
        resp = client.get("/api/workspaces")
        assert resp.status_code == 401

    def test_does_not_return_other_users_workspaces(self, client):
        h1 = register_and_login(client, email="wsuser1@example.com", name="User1")
        h2 = register_and_login(client, email="wsuser2@example.com", name="User2")
        _create_workspace(client, h1, name="User1 Private Space")

        resp = client.get("/api/workspaces", headers=h2)
        names = [w["name"] for w in resp.get_json()["workspaces"]]
        assert "User1 Private Space" not in names


# ---------------------------------------------------------------------------
# POST /api/workspaces
# ---------------------------------------------------------------------------

class TestCreateWorkspace:
    def test_creates_workspace_with_name_and_icon(self, client):
        headers = _headers(client, email="createws@example.com")
        resp = client.post(
            "/api/workspaces",
            json={"name": "Science Notes", "icon": "🔬"},
            headers=headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert "workspace" in body
        ws = body["workspace"]
        assert ws["name"] == "Science Notes"
        assert ws["icon"] == "🔬"
        assert "id" in ws
        assert "owner_id" in ws
        assert "created_at" in ws

    def test_create_workspace_uses_default_icon_when_omitted(self, client):
        headers = _headers(client, email="defaulticon@example.com")
        resp = client.post(
            "/api/workspaces",
            json={"name": "No Icon Workspace"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["workspace"]["icon"] == "📓"

    def test_create_workspace_missing_name_returns_422(self, client):
        headers = _headers(client, email="missingname@example.com")
        resp = client.post(
            "/api/workspaces",
            json={"icon": "📚"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_create_workspace_empty_name_returns_422(self, client):
        headers = _headers(client, email="emptyname@example.com")
        resp = client.post(
            "/api/workspaces",
            json={"name": "   "},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_create_workspace_without_jwt_returns_401(self, client):
        resp = client.post(
            "/api/workspaces",
            json={"name": "Anon Workspace"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/workspaces/:id
# ---------------------------------------------------------------------------

class TestGetWorkspace:
    def test_returns_workspace_details(self, client):
        headers = _headers(client, email="getws@example.com")
        ws = _create_workspace(client, headers, name="Detail Space")
        resp = client.get(f"/api/workspaces/{ws['id']}", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["workspace"]["id"] == ws["id"]
        assert body["workspace"]["name"] == "Detail Space"

    def test_returns_404_for_nonexistent_id(self, client):
        headers = _headers(client, email="getws404@example.com")
        resp = client.get("/api/workspaces/00000000-0000-0000-0000-000000000000",
                          headers=headers)
        assert resp.status_code == 404

    def test_returns_404_for_another_users_workspace(self, client):
        """
        The workspace route uses filter_by(id=wid, owner_id=user.id).
        Querying another user's workspace returns 404 (not a 403) because
        the workspace simply isn't found for that owner.
        """
        h1 = register_and_login(client, email="wsowner@example.com", name="Owner")
        h2 = register_and_login(client, email="wsstranger@example.com", name="Stranger")

        ws = _create_workspace(client, h1, name="Owner's Private Space")
        resp = client.get(f"/api/workspaces/{ws['id']}", headers=h2)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/workspaces/:id
# ---------------------------------------------------------------------------

class TestUpdateWorkspace:
    def test_updates_name_and_icon(self, client):
        headers = _headers(client, email="updatews@example.com")
        ws = _create_workspace(client, headers, name="Old Name", icon="📓")

        resp = client.put(
            f"/api/workspaces/{ws['id']}",
            json={"name": "New Name", "icon": "🚀"},
            headers=headers,
        )
        assert resp.status_code == 200
        updated = resp.get_json()["workspace"]
        assert updated["name"] == "New Name"
        assert updated["icon"] == "🚀"

    def test_update_name_only(self, client):
        headers = _headers(client, email="updatenameonly@example.com")
        ws = _create_workspace(client, headers, name="Before")

        resp = client.put(
            f"/api/workspaces/{ws['id']}",
            json={"name": "After"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["workspace"]["name"] == "After"

    def test_update_returns_404_for_nonexistent_workspace(self, client):
        headers = _headers(client, email="updatenoexist@example.com")
        resp = client.put(
            "/api/workspaces/00000000-0000-0000-0000-000000000000",
            json={"name": "Nope"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_update_returns_404_for_another_users_workspace(self, client):
        h1 = register_and_login(client, email="wsupdate_owner@example.com", name="Owner")
        h2 = register_and_login(client, email="wsupdate_thief@example.com", name="Thief")

        ws = _create_workspace(client, h1, name="Owner Space")
        resp = client.put(
            f"/api/workspaces/{ws['id']}",
            json={"name": "Hijacked"},
            headers=h2,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/workspaces/:id
# ---------------------------------------------------------------------------

class TestDeleteWorkspace:
    def test_deletes_own_workspace(self, client):
        headers = _headers(client, email="deletews@example.com")
        ws = _create_workspace(client, headers, name="To Delete")

        resp = client.delete(f"/api/workspaces/{ws['id']}", headers=headers)
        assert resp.status_code == 200
        assert "deleted" in resp.get_json()["message"].lower()

        # Confirm it's gone
        get_resp = client.get(f"/api/workspaces/{ws['id']}", headers=headers)
        assert get_resp.status_code == 404

    def test_delete_returns_404_for_another_users_workspace(self, client):
        h1 = register_and_login(client, email="wsdel_owner@example.com", name="Owner")
        h2 = register_and_login(client, email="wsdel_thief@example.com", name="Thief")

        ws = _create_workspace(client, h1, name="Protected Space")
        resp = client.delete(f"/api/workspaces/{ws['id']}", headers=h2)
        assert resp.status_code == 404

    def test_delete_returns_404_for_nonexistent_id(self, client):
        headers = _headers(client, email="delnoexist@example.com")
        resp = client.delete(
            "/api/workspaces/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_delete_without_jwt_returns_401(self, client):
        resp = client.delete("/api/workspaces/some-id")
        assert resp.status_code == 401
