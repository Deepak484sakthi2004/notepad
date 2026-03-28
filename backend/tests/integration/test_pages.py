"""
Integration tests for page endpoints.

Endpoints covered:
  GET    /api/workspaces/:wid/pages
  POST   /api/workspaces/:wid/pages
  GET    /api/pages/:id
  PUT    /api/pages/:id
  PUT    /api/pages/:id/content
  DELETE /api/pages/:id              (soft delete)
  POST   /api/pages/:id/restore
  DELETE /api/pages/:id/permanent
  POST   /api/pages/:id/duplicate
  PUT    /api/pages/:id/favourite
  DELETE /api/pages/:id/favourite
  GET    /api/trash
"""
import pytest
from tests.integration.conftest import register_and_login


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(client, email="pages_user@example.com", name="Pages User"):
    """Register a user, return (headers, workspace_id)."""
    headers = register_and_login(client, email=email, name=name)
    ws_resp = client.get("/api/workspaces", headers=headers)
    workspace_id = ws_resp.get_json()["workspaces"][0]["id"]
    return headers, workspace_id


def _create_page(client, headers, workspace_id, title="Test Page",
                 parent_page_id=None):
    body = {"title": title, "icon": "📄"}
    if parent_page_id:
        body["parent_page_id"] = parent_page_id
    resp = client.post(
        f"/api/workspaces/{workspace_id}/pages",
        json=body,
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["page"]


# ---------------------------------------------------------------------------
# GET /api/workspaces/:wid/pages  — page tree
# ---------------------------------------------------------------------------

class TestListPages:
    def test_returns_page_tree_as_list(self, client):
        headers, wid = _setup(client, email="listp@example.com")
        _create_page(client, headers, wid, title="Alpha")
        _create_page(client, headers, wid, title="Beta")

        resp = client.get(f"/api/workspaces/{wid}/pages", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "pages" in body
        titles = [p["title"] for p in body["pages"]]
        assert "Alpha" in titles
        assert "Beta" in titles

    def test_returns_empty_list_for_new_workspace(self, client):
        headers = register_and_login(client, email="emptyws@example.com")
        ws = client.post(
            "/api/workspaces",
            json={"name": "Empty WS"},
            headers=headers,
        ).get_json()["workspace"]
        resp = client.get(f"/api/workspaces/{ws['id']}/pages", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["pages"] == []

    def test_returns_404_for_nonexistent_workspace(self, client):
        headers = register_and_login(client, email="noworkspace@example.com")
        resp = client.get(
            "/api/workspaces/00000000-0000-0000-0000-000000000000/pages",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_deleted_pages_not_included_in_tree(self, client):
        headers, wid = _setup(client, email="delnotintree@example.com")
        page = _create_page(client, headers, wid, title="Soon Deleted")

        client.delete(f"/api/pages/{page['id']}", headers=headers)

        resp = client.get(f"/api/workspaces/{wid}/pages", headers=headers)
        titles = [p["title"] for p in resp.get_json()["pages"]]
        assert "Soon Deleted" not in titles


# ---------------------------------------------------------------------------
# POST /api/workspaces/:wid/pages
# ---------------------------------------------------------------------------

class TestCreatePage:
    def test_creates_page_returns_201(self, client):
        headers, wid = _setup(client, email="createpage@example.com")
        resp = client.post(
            f"/api/workspaces/{wid}/pages",
            json={"title": "New Page", "icon": "📝"},
            headers=headers,
        )
        assert resp.status_code == 201
        page = resp.get_json()["page"]
        assert page["title"] == "New Page"
        assert page["icon"] == "📝"
        assert page["workspace_id"] == wid
        assert page["is_deleted"] is False
        assert "blocks" in page

    def test_creates_nested_page_with_parent_page_id(self, client):
        headers, wid = _setup(client, email="nestedpage@example.com")
        parent = _create_page(client, headers, wid, title="Parent Page")

        child_resp = client.post(
            f"/api/workspaces/{wid}/pages",
            json={"title": "Child Page", "parent_page_id": parent["id"]},
            headers=headers,
        )
        assert child_resp.status_code == 201
        child = child_resp.get_json()["page"]
        assert child["parent_page_id"] == parent["id"]

    def test_creates_page_with_default_title_when_omitted(self, client):
        headers, wid = _setup(client, email="defaulttitle@example.com")
        resp = client.post(
            f"/api/workspaces/{wid}/pages",
            json={},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["page"]["title"] == "Untitled"

    def test_create_page_in_nonexistent_workspace_returns_404(self, client):
        headers = register_and_login(client, email="badws_page@example.com")
        resp = client.post(
            "/api/workspaces/00000000-0000-0000-0000-000000000000/pages",
            json={"title": "Orphan"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_create_page_without_jwt_returns_401(self, client):
        _, wid = _setup(client, email="anonpage@example.com")
        resp = client.post(f"/api/workspaces/{wid}/pages", json={"title": "X"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/pages/:id
# ---------------------------------------------------------------------------

class TestGetPage:
    def test_returns_page_details_including_blocks(self, client):
        headers, wid = _setup(client, email="getpage@example.com")
        page = _create_page(client, headers, wid, title="Detail Page")

        resp = client.get(f"/api/pages/{page['id']}", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()["page"]
        assert body["id"] == page["id"]
        assert body["title"] == "Detail Page"
        assert "blocks" in body
        assert "plain_text" in body

    def test_returns_404_for_nonexistent_page(self, client):
        headers = register_and_login(client, email="nopageid@example.com")
        resp = client.get(
            "/api/pages/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_returns_403_or_404_for_another_users_page(self, client):
        """
        _assert_page_access checks workspace ownership; returns None/None
        which maps to a 404 response when ownership fails.
        """
        h1 = register_and_login(client, email="pageowner@example.com", name="Owner")
        h2 = register_and_login(client, email="pagestranger@example.com", name="Stranger")

        ws_resp = client.get("/api/workspaces", headers=h1)
        wid = ws_resp.get_json()["workspaces"][0]["id"]
        page = _create_page(client, h1, wid, title="Private Page")

        resp = client.get(f"/api/pages/{page['id']}", headers=h2)
        assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# PUT /api/pages/:id
# ---------------------------------------------------------------------------

class TestUpdatePage:
    def test_updates_title_and_icon(self, client):
        headers, wid = _setup(client, email="updatepage@example.com")
        page = _create_page(client, headers, wid, title="Old Title")

        resp = client.put(
            f"/api/pages/{page['id']}",
            json={"title": "New Title", "icon": "🌟"},
            headers=headers,
        )
        assert resp.status_code == 200
        updated = resp.get_json()["page"]
        assert updated["title"] == "New Title"
        assert updated["icon"] == "🌟"

    def test_partial_update_title_only(self, client):
        headers, wid = _setup(client, email="partialpageupdate@example.com")
        page = _create_page(client, headers, wid, title="Original")

        resp = client.put(
            f"/api/pages/{page['id']}",
            json={"title": "Changed"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["page"]["title"] == "Changed"

    def test_update_nonexistent_page_returns_404(self, client):
        headers = register_and_login(client, email="updatenopageid@example.com")
        resp = client.put(
            "/api/pages/00000000-0000-0000-0000-000000000000",
            json={"title": "Nope"},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/pages/:id/content
# ---------------------------------------------------------------------------

class TestUpdatePageContent:
    def test_saves_blocks_json_and_plain_text(self, client):
        headers, wid = _setup(client, email="pagecontent@example.com")
        page = _create_page(client, headers, wid, title="Content Page")

        blocks = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]}
            ],
        }
        resp = client.put(
            f"/api/pages/{page['id']}/content",
            json={"blocks": blocks, "plain_text": "Hello"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.get_json()["page"]
        assert body["blocks"] == blocks
        assert body["plain_text"] == "Hello"

    def test_saves_empty_blocks(self, client):
        headers, wid = _setup(client, email="emptycontent@example.com")
        page = _create_page(client, headers, wid)

        resp = client.put(
            f"/api/pages/{page['id']}/content",
            json={"blocks": {}, "plain_text": ""},
            headers=headers,
        )
        assert resp.status_code == 200

    def test_update_content_without_jwt_returns_401(self, client):
        resp = client.put(
            "/api/pages/some-id/content",
            json={"blocks": {}, "plain_text": ""},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/pages/:id  (soft delete)
# ---------------------------------------------------------------------------

class TestSoftDeletePage:
    def test_soft_delete_sets_is_deleted_true(self, client):
        headers, wid = _setup(client, email="softdel@example.com")
        page = _create_page(client, headers, wid, title="To Trash")

        resp = client.delete(f"/api/pages/{page['id']}", headers=headers)
        assert resp.status_code == 200
        assert "trash" in resp.get_json()["message"].lower()

        # The page is still retrievable (soft deleted)
        get_resp = client.get(f"/api/pages/{page['id']}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.get_json()["page"]["is_deleted"] is True

    def test_soft_deleted_page_appears_in_trash(self, client):
        headers, wid = _setup(client, email="trashedpage@example.com")
        page = _create_page(client, headers, wid, title="Trashed Page")

        client.delete(f"/api/pages/{page['id']}", headers=headers)

        trash_resp = client.get("/api/trash", headers=headers)
        assert trash_resp.status_code == 200
        titles = [p["title"] for p in trash_resp.get_json()["pages"]]
        assert "Trashed Page" in titles

    def test_soft_delete_nonexistent_page_returns_404(self, client):
        headers = register_and_login(client, email="softdelnoexist@example.com")
        resp = client.delete(
            "/api/pages/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/pages/:id/restore
# ---------------------------------------------------------------------------

class TestRestorePage:
    def test_restore_sets_is_deleted_false(self, client):
        headers, wid = _setup(client, email="restorepage@example.com")
        page = _create_page(client, headers, wid, title="Restored Page")

        client.delete(f"/api/pages/{page['id']}", headers=headers)

        resp = client.post(f"/api/pages/{page['id']}/restore", headers=headers)
        assert resp.status_code == 200
        restored = resp.get_json()["page"]
        assert restored["is_deleted"] is False
        assert restored["deleted_at"] is None

    def test_restore_removes_page_from_trash(self, client):
        headers, wid = _setup(client, email="restorefromtrash@example.com")
        page = _create_page(client, headers, wid, title="Back From Trash")

        client.delete(f"/api/pages/{page['id']}", headers=headers)
        client.post(f"/api/pages/{page['id']}/restore", headers=headers)

        trash_resp = client.get("/api/trash", headers=headers)
        titles = [p["title"] for p in trash_resp.get_json()["pages"]]
        assert "Back From Trash" not in titles


# ---------------------------------------------------------------------------
# DELETE /api/pages/:id/permanent
# ---------------------------------------------------------------------------

class TestPermanentDeletePage:
    def test_permanent_delete_removes_page(self, client):
        headers, wid = _setup(client, email="permdel@example.com")
        page = _create_page(client, headers, wid, title="Permanent Gone")

        resp = client.delete(f"/api/pages/{page['id']}/permanent", headers=headers)
        assert resp.status_code == 200
        assert "permanently" in resp.get_json()["message"].lower()

        # Verify it is truly gone
        get_resp = client.get(f"/api/pages/{page['id']}", headers=headers)
        assert get_resp.status_code == 404

    def test_permanent_delete_nonexistent_page_returns_404(self, client):
        headers = register_and_login(client, email="permdel404@example.com")
        resp = client.delete(
            "/api/pages/00000000-0000-0000-0000-000000000000/permanent",
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/pages/:id/duplicate
# ---------------------------------------------------------------------------

class TestDuplicatePage:
    def test_duplicate_creates_copy(self, client):
        headers, wid = _setup(client, email="dupeage@example.com")
        page = _create_page(client, headers, wid, title="Original Page")

        # Give the page some content first
        client.put(
            f"/api/pages/{page['id']}/content",
            json={"blocks": {"type": "doc"}, "plain_text": "Original content"},
            headers=headers,
        )

        resp = client.post(f"/api/pages/{page['id']}/duplicate", headers=headers)
        assert resp.status_code == 201
        copy = resp.get_json()["page"]
        assert copy["id"] != page["id"]
        assert copy["workspace_id"] == wid
        # The copy should have a title that indicates duplication
        assert copy["title"] is not None

    def test_duplicate_nonexistent_page_returns_404(self, client):
        headers = register_and_login(client, email="dupnoexist@example.com")
        resp = client.post(
            "/api/pages/00000000-0000-0000-0000-000000000000/duplicate",
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/pages/:id/favourite  +  DELETE /api/pages/:id/favourite
# ---------------------------------------------------------------------------

class TestFavourites:
    def test_add_favourite_returns_200(self, client):
        headers, wid = _setup(client, email="favpage@example.com")
        page = _create_page(client, headers, wid, title="Favourite Me")

        resp = client.put(f"/api/pages/{page['id']}/favourite", headers=headers)
        assert resp.status_code == 200
        assert "favourites" in resp.get_json()["message"].lower()

    def test_remove_favourite_returns_200(self, client):
        headers, wid = _setup(client, email="unfavpage@example.com")
        page = _create_page(client, headers, wid, title="Unfavourite Me")

        client.put(f"/api/pages/{page['id']}/favourite", headers=headers)
        resp = client.delete(f"/api/pages/{page['id']}/favourite", headers=headers)
        assert resp.status_code == 200

    def test_add_favourite_idempotent(self, client):
        """Adding the same page to favourites twice should not raise an error."""
        headers, wid = _setup(client, email="favtwice@example.com")
        page = _create_page(client, headers, wid, title="Double Fav")

        resp1 = client.put(f"/api/pages/{page['id']}/favourite", headers=headers)
        resp2 = client.put(f"/api/pages/{page['id']}/favourite", headers=headers)
        assert resp1.status_code == 200
        assert resp2.status_code == 200

    def test_favourite_nonexistent_page_returns_404(self, client):
        headers = register_and_login(client, email="favnoexist@example.com")
        resp = client.put(
            "/api/pages/00000000-0000-0000-0000-000000000000/favourite",
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/trash
# ---------------------------------------------------------------------------

class TestTrash:
    def test_returns_only_deleted_pages(self, client):
        headers, wid = _setup(client, email="trashlist@example.com")
        live_page = _create_page(client, headers, wid, title="Live Page")
        dead_page = _create_page(client, headers, wid, title="Dead Page")

        client.delete(f"/api/pages/{dead_page['id']}", headers=headers)

        resp = client.get("/api/trash", headers=headers)
        assert resp.status_code == 200
        pages = resp.get_json()["pages"]
        ids = [p["id"] for p in pages]
        assert dead_page["id"] in ids
        assert live_page["id"] not in ids

    def test_trash_without_jwt_returns_401(self, client):
        resp = client.get("/api/trash")
        assert resp.status_code == 401

    def test_trash_does_not_show_other_users_deleted_pages(self, client):
        h1 = register_and_login(client, email="trash_owner@example.com", name="Owner")
        h2 = register_and_login(client, email="trash_stranger@example.com",
                                 name="Stranger")

        ws_resp = client.get("/api/workspaces", headers=h1)
        wid = ws_resp.get_json()["workspaces"][0]["id"]
        page = _create_page(client, h1, wid, title="Owner's Deleted")
        client.delete(f"/api/pages/{page['id']}", headers=h1)

        resp = client.get("/api/trash", headers=h2)
        ids = [p["id"] for p in resp.get_json()["pages"]]
        assert page["id"] not in ids

    def test_trash_can_filter_by_workspace_id(self, client):
        headers = register_and_login(
            client, email="trashfilter@example.com", name="Filter User"
        )
        ws1 = client.post(
            "/api/workspaces", json={"name": "WS1"}, headers=headers
        ).get_json()["workspace"]
        ws2 = client.post(
            "/api/workspaces", json={"name": "WS2"}, headers=headers
        ).get_json()["workspace"]

        page1 = _create_page(client, headers, ws1["id"], title="WS1 Page")
        page2 = _create_page(client, headers, ws2["id"], title="WS2 Page")
        client.delete(f"/api/pages/{page1['id']}", headers=headers)
        client.delete(f"/api/pages/{page2['id']}", headers=headers)

        resp = client.get(f"/api/trash?workspace_id={ws1['id']}", headers=headers)
        ids = [p["id"] for p in resp.get_json()["pages"]]
        assert page1["id"] in ids
        assert page2["id"] not in ids
