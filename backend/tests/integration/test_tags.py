"""
Integration tests for tag endpoints.

Endpoints covered:
  GET    /api/workspaces/:wid/tags
  POST   /api/workspaces/:wid/tags
  PUT    /api/tags/:id
  DELETE /api/tags/:id
  POST   /api/pages/:id/tags
  DELETE /api/pages/:id/tags/:tag_id
"""
import pytest
from tests.integration.conftest import register_and_login


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(client, email="tags_user@example.com", name="Tags User"):
    """Register a user; return (headers, workspace_id, workspace)."""
    headers = register_and_login(client, email=email, name=name)
    ws_resp = client.get("/api/workspaces", headers=headers)
    workspace = ws_resp.get_json()["workspaces"][0]
    return headers, workspace["id"], workspace


def _create_tag(client, headers, workspace_id, name="My Tag", colour="#ff0000"):
    resp = client.post(
        f"/api/workspaces/{workspace_id}/tags",
        json={"name": name, "colour": colour},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["tag"]


def _create_page(client, headers, workspace_id, title="Tagged Page"):
    resp = client.post(
        f"/api/workspaces/{workspace_id}/pages",
        json={"title": title},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.get_json()["page"]


# ---------------------------------------------------------------------------
# GET /api/workspaces/:wid/tags
# ---------------------------------------------------------------------------

class TestListTags:
    def test_returns_empty_list_for_new_workspace(self, client):
        headers, wid, _ = _setup(client, email="listtagsnone@example.com")
        resp = client.get(f"/api/workspaces/{wid}/tags", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["tags"] == []

    def test_returns_created_tags(self, client):
        headers, wid, _ = _setup(client, email="listtagssome@example.com")
        _create_tag(client, headers, wid, name="Alpha")
        _create_tag(client, headers, wid, name="Beta")

        resp = client.get(f"/api/workspaces/{wid}/tags", headers=headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.get_json()["tags"]]
        assert "Alpha" in names
        assert "Beta" in names

    def test_returns_404_for_nonexistent_workspace(self, client):
        headers = register_and_login(client, email="listtags404@example.com")
        resp = client.get(
            "/api/workspaces/00000000-0000-0000-0000-000000000000/tags",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_returns_401_without_jwt(self, client):
        resp = client.get("/api/workspaces/some-id/tags")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/workspaces/:wid/tags
# ---------------------------------------------------------------------------

class TestCreateTag:
    def test_creates_tag_with_name_and_colour(self, client):
        headers, wid, _ = _setup(client, email="createtag@example.com")
        resp = client.post(
            f"/api/workspaces/{wid}/tags",
            json={"name": "Important", "colour": "#e74c3c"},
            headers=headers,
        )
        assert resp.status_code == 201
        tag = resp.get_json()["tag"]
        assert tag["name"] == "Important"
        assert tag["colour"] == "#e74c3c"
        assert tag["workspace_id"] == wid
        assert "id" in tag

    def test_creates_tag_with_default_colour_when_omitted(self, client):
        headers, wid, _ = _setup(client, email="defaultcolour@example.com")
        resp = client.post(
            f"/api/workspaces/{wid}/tags",
            json={"name": "Plain Tag"},
            headers=headers,
        )
        assert resp.status_code == 201
        # Default colour is #6366f1 per routes/tags.py
        assert resp.get_json()["tag"]["colour"] == "#6366f1"

    def test_create_tag_missing_name_returns_422(self, client):
        headers, wid, _ = _setup(client, email="missingtagname@example.com")
        resp = client.post(
            f"/api/workspaces/{wid}/tags",
            json={"colour": "#000000"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_create_tag_empty_name_returns_422(self, client):
        headers, wid, _ = _setup(client, email="emptytagname@example.com")
        resp = client.post(
            f"/api/workspaces/{wid}/tags",
            json={"name": "   "},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_create_tag_invalid_colour_falls_back_to_default(self, client):
        """Invalid hex colour is silently replaced with the default."""
        headers, wid, _ = _setup(client, email="invalidcolour@example.com")
        resp = client.post(
            f"/api/workspaces/{wid}/tags",
            json={"name": "Weird Colour", "colour": "not-a-color"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["tag"]["colour"] == "#6366f1"

    def test_create_tag_in_nonexistent_workspace_returns_404(self, client):
        headers = register_and_login(client, email="tagnoworkspace@example.com")
        resp = client.post(
            "/api/workspaces/00000000-0000-0000-0000-000000000000/tags",
            json={"name": "Lost Tag"},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/tags/:id
# ---------------------------------------------------------------------------

class TestUpdateTag:
    def test_updates_tag_name(self, client):
        headers, wid, _ = _setup(client, email="updatetagname@example.com")
        tag = _create_tag(client, headers, wid, name="Old Name")

        resp = client.put(
            f"/api/tags/{tag['id']}",
            json={"name": "New Name"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["tag"]["name"] == "New Name"

    def test_updates_tag_colour(self, client):
        headers, wid, _ = _setup(client, email="updatetagcolour@example.com")
        tag = _create_tag(client, headers, wid, name="Colour Tag", colour="#aaaaaa")

        resp = client.put(
            f"/api/tags/{tag['id']}",
            json={"colour": "#123456"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["tag"]["colour"] == "#123456"

    def test_update_returns_403_for_another_users_tag(self, client):
        h1 = register_and_login(client, email="tagsowner@example.com", name="Owner")
        h2 = register_and_login(client, email="tagstranger@example.com",
                                 name="Stranger")

        ws_resp = client.get("/api/workspaces", headers=h1)
        wid = ws_resp.get_json()["workspaces"][0]["id"]
        tag = _create_tag(client, h1, wid, name="Owner Tag")

        resp = client.put(
            f"/api/tags/{tag['id']}",
            json={"name": "Stolen"},
            headers=h2,
        )
        assert resp.status_code in (403, 404)

    def test_update_nonexistent_tag_returns_404(self, client):
        headers = register_and_login(client, email="notagid@example.com")
        resp = client.put(
            "/api/tags/00000000-0000-0000-0000-000000000000",
            json={"name": "Ghost"},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/tags/:id
# ---------------------------------------------------------------------------

class TestDeleteTag:
    def test_deletes_own_tag(self, client):
        headers, wid, _ = _setup(client, email="deletetag@example.com")
        tag = _create_tag(client, headers, wid, name="Delete Me")

        resp = client.delete(f"/api/tags/{tag['id']}", headers=headers)
        assert resp.status_code == 200
        assert "deleted" in resp.get_json()["message"].lower()

        # Confirm it's gone from the workspace tag list
        list_resp = client.get(f"/api/workspaces/{wid}/tags", headers=headers)
        ids = [t["id"] for t in list_resp.get_json()["tags"]]
        assert tag["id"] not in ids

    def test_delete_returns_403_for_another_users_tag(self, client):
        h1 = register_and_login(client, email="tagdelowner@example.com", name="Owner")
        h2 = register_and_login(client, email="tagdelthief@example.com",
                                 name="Thief")

        ws_resp = client.get("/api/workspaces", headers=h1)
        wid = ws_resp.get_json()["workspaces"][0]["id"]
        tag = _create_tag(client, h1, wid, name="Protected Tag")

        resp = client.delete(f"/api/tags/{tag['id']}", headers=h2)
        assert resp.status_code in (403, 404)

    def test_delete_nonexistent_tag_returns_404(self, client):
        headers = register_and_login(client, email="delnotagid@example.com")
        resp = client.delete(
            "/api/tags/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/pages/:id/tags  (attach tag to page)
# ---------------------------------------------------------------------------

class TestAddPageTag:
    def test_attaches_tag_to_page(self, client):
        headers, wid, _ = _setup(client, email="addpagetag@example.com")
        page = _create_page(client, headers, wid)
        tag = _create_tag(client, headers, wid, name="Page Tag")

        resp = client.post(
            f"/api/pages/{page['id']}/tags",
            json={"tag_id": tag["id"]},
            headers=headers,
        )
        assert resp.status_code == 200
        tag_ids = [t["id"] for t in resp.get_json()["tags"]]
        assert tag["id"] in tag_ids

    def test_adding_same_tag_twice_does_not_create_duplicate(self, client):
        """Idempotent – adding a tag a second time leaves exactly one entry."""
        headers, wid, _ = _setup(client, email="dupetag@example.com")
        page = _create_page(client, headers, wid)
        tag = _create_tag(client, headers, wid, name="No Dupe Tag")

        client.post(
            f"/api/pages/{page['id']}/tags",
            json={"tag_id": tag["id"]},
            headers=headers,
        )
        resp2 = client.post(
            f"/api/pages/{page['id']}/tags",
            json={"tag_id": tag["id"]},
            headers=headers,
        )
        assert resp2.status_code == 200
        tag_ids = [t["id"] for t in resp2.get_json()["tags"]]
        assert tag_ids.count(tag["id"]) == 1

    def test_add_tag_missing_tag_id_returns_422(self, client):
        headers, wid, _ = _setup(client, email="notagid_page@example.com")
        page = _create_page(client, headers, wid)

        resp = client.post(
            f"/api/pages/{page['id']}/tags",
            json={},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_add_nonexistent_tag_to_page_returns_404(self, client):
        headers, wid, _ = _setup(client, email="addglosttag@example.com")
        page = _create_page(client, headers, wid)

        resp = client.post(
            f"/api/pages/{page['id']}/tags",
            json={"tag_id": "00000000-0000-0000-0000-000000000000"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_add_tag_to_nonexistent_page_returns_404(self, client):
        headers, wid, _ = _setup(client, email="addtagnopage@example.com")
        tag = _create_tag(client, headers, wid)

        resp = client.post(
            "/api/pages/00000000-0000-0000-0000-000000000000/tags",
            json={"tag_id": tag["id"]},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_add_tag_to_another_users_page_returns_403(self, client):
        h1 = register_and_login(
            client, email="tagaccessowner@example.com", name="Owner"
        )
        h2 = register_and_login(
            client, email="tagaccessstranger@example.com", name="Stranger"
        )

        ws1_resp = client.get("/api/workspaces", headers=h1)
        wid1 = ws1_resp.get_json()["workspaces"][0]["id"]
        ws2_resp = client.get("/api/workspaces", headers=h2)
        wid2 = ws2_resp.get_json()["workspaces"][0]["id"]

        page = _create_page(client, h1, wid1, title="Owner Page")
        tag = _create_tag(client, h2, wid2, name="Stranger Tag")

        resp = client.post(
            f"/api/pages/{page['id']}/tags",
            json={"tag_id": tag["id"]},
            headers=h2,
        )
        assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# DELETE /api/pages/:id/tags/:tag_id  (detach tag from page)
# ---------------------------------------------------------------------------

class TestRemovePageTag:
    def test_detaches_tag_from_page(self, client):
        headers, wid, _ = _setup(client, email="removepagetag@example.com")
        page = _create_page(client, headers, wid)
        tag = _create_tag(client, headers, wid, name="Removable Tag")

        # Attach first
        client.post(
            f"/api/pages/{page['id']}/tags",
            json={"tag_id": tag["id"]},
            headers=headers,
        )

        # Then detach
        resp = client.delete(
            f"/api/pages/{page['id']}/tags/{tag['id']}",
            headers=headers,
        )
        assert resp.status_code == 200
        tag_ids = [t["id"] for t in resp.get_json()["tags"]]
        assert tag["id"] not in tag_ids

    def test_remove_tag_that_was_never_attached_returns_200(self, client):
        """
        The route silently ignores attempts to remove a tag that wasn't there.
        """
        headers, wid, _ = _setup(client, email="removenotthere@example.com")
        page = _create_page(client, headers, wid)
        tag = _create_tag(client, headers, wid, name="Never Attached")

        resp = client.delete(
            f"/api/pages/{page['id']}/tags/{tag['id']}",
            headers=headers,
        )
        assert resp.status_code == 200
