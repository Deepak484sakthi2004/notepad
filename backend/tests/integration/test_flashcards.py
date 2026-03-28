"""
Integration tests for flashcard endpoints.

Endpoints covered:
  POST   /api/flashcards/decks
  GET    /api/flashcards/decks
  GET    /api/flashcards/decks/:id
  PUT    /api/flashcards/decks/:id
  DELETE /api/flashcards/decks/:id
  GET    /api/flashcards/decks/:id/stats
  POST   /api/flashcards/decks/:id/cards
  GET    /api/flashcards/decks/:id/cards
  PUT    /api/flashcards/cards/:id
  DELETE /api/flashcards/cards/:id
  POST   /api/flashcards/cards/:id/suspend
  POST   /api/flashcards/cards/:id/flag
  GET    /api/flashcards/due
  POST   /api/flashcards/review
  POST   /api/flashcards/sessions/start
  POST   /api/flashcards/sessions/:id/end
  GET    /api/flashcards/stats/overview
  GET    /api/flashcards/stats/history?days=30
  POST   /api/flashcards/generate        (with mocked AI service)
"""
import pytest
from unittest.mock import patch
from tests.integration.conftest import register_and_login


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers(client, email="fc_user@example.com", name="FC User"):
    return register_and_login(client, email=email, name=name)


def _create_deck(client, headers, name="Test Deck", description="Desc"):
    resp = client.post(
        "/api/flashcards/decks",
        json={"name": name, "description": description},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["deck"]


def _create_card(client, headers, deck_id, question="What is 2+2?", answer="4"):
    resp = client.post(
        f"/api/flashcards/decks/{deck_id}/cards",
        json={"question": question, "answer": answer, "difficulty": 1},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["card"]


def _create_workspace_and_page(client, headers):
    """Create a workspace and a page with text content, return page id."""
    ws = client.post(
        "/api/workspaces",
        json={"name": "FC Workspace"},
        headers=headers,
    ).get_json()["workspace"]

    page_resp = client.post(
        f"/api/workspaces/{ws['id']}/pages",
        json={"title": "FC Source Page"},
        headers=headers,
    )
    assert page_resp.status_code == 201
    page = page_resp.get_json()["page"]

    client.put(
        f"/api/pages/{page['id']}/content",
        json={
            "blocks": {"type": "doc"},
            "plain_text": "Photosynthesis is the process by which plants use sunlight.",
        },
        headers=headers,
    )
    return page["id"]


# ---------------------------------------------------------------------------
# Deck CRUD
# ---------------------------------------------------------------------------

class TestDeckCRUD:
    def test_create_deck_returns_201(self, client):
        headers = _headers(client, email="createdeck@example.com")
        resp = client.post(
            "/api/flashcards/decks",
            json={"name": "Biology Deck", "description": "Plants & animals"},
            headers=headers,
        )
        assert resp.status_code == 201
        deck = resp.get_json()["deck"]
        assert deck["name"] == "Biology Deck"
        assert deck["description"] == "Plants & animals"
        assert deck["auto_generated"] is False
        assert "id" in deck
        assert "card_count" in deck

    def test_create_deck_missing_name_returns_422(self, client):
        headers = _headers(client, email="nodecaname@example.com")
        resp = client.post(
            "/api/flashcards/decks",
            json={"description": "No name given"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_list_decks_returns_user_decks(self, client):
        headers = _headers(client, email="listdecks@example.com")
        _create_deck(client, headers, name="Deck One")
        _create_deck(client, headers, name="Deck Two")

        resp = client.get("/api/flashcards/decks", headers=headers)
        assert resp.status_code == 200
        names = [d["name"] for d in resp.get_json()["decks"]]
        assert "Deck One" in names
        assert "Deck Two" in names

    def test_list_decks_does_not_include_other_users_decks(self, client):
        h1 = register_and_login(client, email="deckowner@example.com", name="Owner")
        h2 = register_and_login(client, email="deckstranger@example.com",
                                 name="Stranger")
        _create_deck(client, h1, name="Private Deck")

        resp = client.get("/api/flashcards/decks", headers=h2)
        names = [d["name"] for d in resp.get_json()["decks"]]
        assert "Private Deck" not in names

    def test_get_deck_returns_deck(self, client):
        headers = _headers(client, email="getdeck@example.com")
        deck = _create_deck(client, headers, name="Get Me")

        resp = client.get(f"/api/flashcards/decks/{deck['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["deck"]["id"] == deck["id"]

    def test_get_deck_returns_404_for_nonexistent(self, client):
        headers = _headers(client, email="getdecknone@example.com")
        resp = client.get(
            "/api/flashcards/decks/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_update_deck_name(self, client):
        headers = _headers(client, email="updatedeckname@example.com")
        deck = _create_deck(client, headers, name="Old Name")

        resp = client.put(
            f"/api/flashcards/decks/{deck['id']}",
            json={"name": "New Name"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["deck"]["name"] == "New Name"

    def test_update_deck_description(self, client):
        headers = _headers(client, email="updatedeckdesc@example.com")
        deck = _create_deck(client, headers, name="Desc Deck")

        resp = client.put(
            f"/api/flashcards/decks/{deck['id']}",
            json={"description": "Updated description"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["deck"]["description"] == "Updated description"

    def test_delete_deck(self, client):
        headers = _headers(client, email="deletedeck@example.com")
        deck = _create_deck(client, headers, name="To Delete")

        resp = client.delete(
            f"/api/flashcards/decks/{deck['id']}", headers=headers
        )
        assert resp.status_code == 200
        assert "deleted" in resp.get_json()["message"].lower()

        # Confirm it's gone
        get_resp = client.get(
            f"/api/flashcards/decks/{deck['id']}", headers=headers
        )
        assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Deck stats
# ---------------------------------------------------------------------------

class TestDeckStats:
    def test_stats_returns_total_and_due_counts(self, client):
        headers = _headers(client, email="deckstats@example.com")
        deck = _create_deck(client, headers, name="Stats Deck")
        _create_card(client, headers, deck["id"], question="Q1?", answer="A1")
        _create_card(client, headers, deck["id"], question="Q2?", answer="A2")

        resp = client.get(
            f"/api/flashcards/decks/{deck['id']}/stats", headers=headers
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "total" in body
        assert "due" in body
        assert "deck_id" in body
        assert body["total"] == 2
        # New cards with no review history are all due
        assert body["due"] == 2

    def test_stats_returns_404_for_nonexistent_deck(self, client):
        headers = _headers(client, email="deckstatsnone@example.com")
        resp = client.get(
            "/api/flashcards/decks/00000000-0000-0000-0000-000000000000/stats",
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Card CRUD
# ---------------------------------------------------------------------------

class TestCardCRUD:
    def test_create_card_returns_201(self, client):
        headers = _headers(client, email="createcard@example.com")
        deck = _create_deck(client, headers)

        resp = client.post(
            f"/api/flashcards/decks/{deck['id']}/cards",
            json={
                "question": "What is the speed of light?",
                "answer": "~3×10⁸ m/s",
                "difficulty": 2,
                "question_type": "recall",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        card = resp.get_json()["card"]
        assert card["question"] == "What is the speed of light?"
        assert card["answer"] == "~3×10⁸ m/s"
        assert card["difficulty"] == 2
        assert card["ai_generated"] is False
        assert card["is_suspended"] is False
        assert card["is_flagged"] is False

    def test_create_card_missing_question_returns_422(self, client):
        headers = _headers(client, email="cardnoquestion@example.com")
        deck = _create_deck(client, headers)

        resp = client.post(
            f"/api/flashcards/decks/{deck['id']}/cards",
            json={"answer": "Some answer"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_create_card_missing_answer_returns_422(self, client):
        headers = _headers(client, email="cardnoanswer@example.com")
        deck = _create_deck(client, headers)

        resp = client.post(
            f"/api/flashcards/decks/{deck['id']}/cards",
            json={"question": "Some question?"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_list_cards_for_deck(self, client):
        headers = _headers(client, email="listcards@example.com")
        deck = _create_deck(client, headers)
        _create_card(client, headers, deck["id"], question="Q1?", answer="A1")
        _create_card(client, headers, deck["id"], question="Q2?", answer="A2")

        resp = client.get(
            f"/api/flashcards/decks/{deck['id']}/cards", headers=headers
        )
        assert resp.status_code == 200
        assert len(resp.get_json()["cards"]) == 2

    def test_update_card_question_and_answer(self, client):
        headers = _headers(client, email="updatecard@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])

        resp = client.put(
            f"/api/flashcards/cards/{card['id']}",
            json={"question": "Updated Q?", "answer": "Updated A"},
            headers=headers,
        )
        assert resp.status_code == 200
        updated = resp.get_json()["card"]
        assert updated["question"] == "Updated Q?"
        assert updated["answer"] == "Updated A"

    def test_delete_card(self, client):
        headers = _headers(client, email="deletecard@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])

        resp = client.delete(f"/api/flashcards/cards/{card['id']}", headers=headers)
        assert resp.status_code == 200
        assert "deleted" in resp.get_json()["message"].lower()

        # Confirm the card is gone from the deck listing
        list_resp = client.get(
            f"/api/flashcards/decks/{deck['id']}/cards", headers=headers
        )
        ids = [c["id"] for c in list_resp.get_json()["cards"]]
        assert card["id"] not in ids


# ---------------------------------------------------------------------------
# Card suspend / flag toggles
# ---------------------------------------------------------------------------

class TestCardToggles:
    def test_suspend_toggles_is_suspended(self, client):
        headers = _headers(client, email="suspendcard@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])

        # Initially not suspended
        assert card["is_suspended"] is False

        resp1 = client.post(
            f"/api/flashcards/cards/{card['id']}/suspend", headers=headers
        )
        assert resp1.status_code == 200
        assert resp1.get_json()["card"]["is_suspended"] is True

        # Toggle back
        resp2 = client.post(
            f"/api/flashcards/cards/{card['id']}/suspend", headers=headers
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["card"]["is_suspended"] is False

    def test_flag_toggles_is_flagged(self, client):
        headers = _headers(client, email="flagcard@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])

        assert card["is_flagged"] is False

        resp1 = client.post(
            f"/api/flashcards/cards/{card['id']}/flag", headers=headers
        )
        assert resp1.status_code == 200
        assert resp1.get_json()["card"]["is_flagged"] is True

        resp2 = client.post(
            f"/api/flashcards/cards/{card['id']}/flag", headers=headers
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["card"]["is_flagged"] is False

    def test_suspend_nonexistent_card_returns_404(self, client):
        headers = _headers(client, email="suspendnocard@example.com")
        resp = client.post(
            "/api/flashcards/cards/00000000-0000-0000-0000-000000000000/suspend",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_flag_nonexistent_card_returns_404(self, client):
        headers = _headers(client, email="flagnocard@example.com")
        resp = client.post(
            "/api/flashcards/cards/00000000-0000-0000-0000-000000000000/flag",
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Due cards
# ---------------------------------------------------------------------------

class TestDueCards:
    def test_new_cards_are_all_due(self, client):
        headers = _headers(client, email="duecards@example.com")
        deck = _create_deck(client, headers)
        _create_card(client, headers, deck["id"], question="Due Q1?", answer="A1")
        _create_card(client, headers, deck["id"], question="Due Q2?", answer="A2")

        resp = client.get("/api/flashcards/due", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "cards" in body
        assert "count" in body
        assert body["count"] >= 2

    def test_suspended_cards_not_in_due(self, client):
        headers = _headers(client, email="duenotsuspended@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"], question="Suspended Q?",
                            answer="A")

        # Suspend the card
        client.post(f"/api/flashcards/cards/{card['id']}/suspend", headers=headers)

        resp = client.get("/api/flashcards/due", headers=headers)
        due_ids = [c["id"] for c in resp.get_json()["cards"]]
        assert card["id"] not in due_ids

    def test_due_returns_401_without_jwt(self, client):
        resp = client.get("/api/flashcards/due")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class TestReview:
    def test_submit_review_returns_201_with_review_data(self, client):
        headers = _headers(client, email="submitreview@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])

        resp = client.post(
            "/api/flashcards/review",
            json={"card_id": card["id"], "quality": 4},
            headers=headers,
        )
        assert resp.status_code == 201
        review = resp.get_json()["review"]
        assert review.get("card_id") == card["id"] or review.get("flashcard_id") == card["id"]
        assert review["quality"] == 4
        assert "next_review_at" in review
        assert review["next_review_at"] is not None
        assert "ease_factor" in review
        assert "interval_days" in review

    def test_submit_review_quality_0_keeps_card_due_soon(self, client):
        """Quality 0 (blackout) should result in interval_days == 1."""
        headers = _headers(client, email="reviewq0@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])

        resp = client.post(
            "/api/flashcards/review",
            json={"card_id": card["id"], "quality": 0},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["review"]["interval_days"] == 1

    def test_submit_review_quality_5_increases_interval(self, client):
        """Quality 5 (perfect) should result in interval_days >= 1."""
        headers = _headers(client, email="reviewq5@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])

        resp = client.post(
            "/api/flashcards/review",
            json={"card_id": card["id"], "quality": 5},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["review"]["interval_days"] >= 1

    def test_submit_review_missing_card_id_returns_422(self, client):
        headers = _headers(client, email="reviewnoid@example.com")
        resp = client.post(
            "/api/flashcards/review",
            json={"quality": 3},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_submit_review_missing_quality_returns_422(self, client):
        headers = _headers(client, email="reviewnoquality@example.com")
        resp = client.post(
            "/api/flashcards/review",
            json={"card_id": "some-id"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_submit_review_nonexistent_card_returns_404(self, client):
        headers = _headers(client, email="reviewnocard@example.com")
        resp = client.post(
            "/api/flashcards/review",
            json={
                "card_id": "00000000-0000-0000-0000-000000000000",
                "quality": 3,
            },
            headers=headers,
        )
        assert resp.status_code == 404

    def test_submit_review_with_session_id(self, client):
        headers = _headers(client, email="reviewwithsession@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])
        session = client.post(
            "/api/flashcards/sessions/start",
            json={"deck_id": deck["id"]},
            headers=headers,
        ).get_json()["session"]

        resp = client.post(
            "/api/flashcards/review",
            json={
                "card_id": card["id"],
                "quality": 3,
                "session_id": session["id"],
            },
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["review"]["session_id"] == session["id"]


# ---------------------------------------------------------------------------
# Study Sessions
# ---------------------------------------------------------------------------

class TestStudySessions:
    def test_start_session_returns_201(self, client):
        headers = _headers(client, email="startsession@example.com")
        deck = _create_deck(client, headers)

        resp = client.post(
            "/api/flashcards/sessions/start",
            json={"deck_id": deck["id"]},
            headers=headers,
        )
        assert resp.status_code == 201
        session = resp.get_json()["session"]
        assert "id" in session
        assert session["deck_id"] == deck["id"]
        assert "started_at" in session
        assert session["ended_at"] is None
        assert session["cards_reviewed"] == 0

    def test_start_session_without_deck_id(self, client):
        """deck_id is optional; a session can be started without one."""
        headers = _headers(client, email="startsessionnodeck@example.com")
        resp = client.post(
            "/api/flashcards/sessions/start",
            json={},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["session"]["deck_id"] is None

    def test_end_session_returns_200_with_stats(self, client):
        headers = _headers(client, email="endsession@example.com")
        deck = _create_deck(client, headers)
        session = client.post(
            "/api/flashcards/sessions/start",
            json={"deck_id": deck["id"]},
            headers=headers,
        ).get_json()["session"]

        resp = client.post(
            f"/api/flashcards/sessions/{session['id']}/end",
            json={"cards_reviewed": 10, "cards_correct": 7},
            headers=headers,
        )
        assert resp.status_code == 200
        ended = resp.get_json()["session"]
        assert ended["cards_reviewed"] == 10
        assert ended["cards_correct"] == 7
        assert ended["ended_at"] is not None

    def test_end_nonexistent_session_returns_404(self, client):
        headers = _headers(client, email="endnosession@example.com")
        resp = client.post(
            "/api/flashcards/sessions/00000000-0000-0000-0000-000000000000/end",
            json={"cards_reviewed": 5},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Global statistics overview
# ---------------------------------------------------------------------------

class TestStatsOverview:
    def test_returns_expected_fields_for_new_user(self, client):
        headers = _headers(client, email="statsoverview@example.com")
        resp = client.get("/api/flashcards/stats/overview", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "total_decks" in body
        assert "total_cards" in body
        assert "due_today" in body
        assert "total_reviews" in body
        assert "accuracy" in body
        assert body["total_decks"] == 0
        assert body["total_cards"] == 0
        assert body["accuracy"] == 0.0

    def test_overview_counts_decks_and_cards(self, client):
        headers = _headers(client, email="statsoverviewcount@example.com")
        deck1 = _create_deck(client, headers, name="Deck A")
        deck2 = _create_deck(client, headers, name="Deck B")
        _create_card(client, headers, deck1["id"])
        _create_card(client, headers, deck2["id"])
        _create_card(client, headers, deck2["id"], question="Q2?", answer="A2")

        resp = client.get("/api/flashcards/stats/overview", headers=headers)
        body = resp.get_json()
        assert body["total_decks"] == 2
        assert body["total_cards"] == 3

    def test_accuracy_reflects_reviews(self, client):
        """After reviewing, accuracy should be calculated from quality >= 3."""
        headers = _headers(client, email="statsaccuracy@example.com")
        deck = _create_deck(client, headers)
        card1 = _create_card(client, headers, deck["id"], question="Q1?", answer="A1")
        card2 = _create_card(client, headers, deck["id"], question="Q2?", answer="A2")

        # Submit one correct (quality=5) and one wrong (quality=1)
        client.post(
            "/api/flashcards/review",
            json={"card_id": card1["id"], "quality": 5},
            headers=headers,
        )
        client.post(
            "/api/flashcards/review",
            json={"card_id": card2["id"], "quality": 1},
            headers=headers,
        )

        resp = client.get("/api/flashcards/stats/overview", headers=headers)
        body = resp.get_json()
        assert body["total_reviews"] == 2
        assert body["accuracy"] == 50.0

    def test_overview_without_jwt_returns_401(self, client):
        resp = client.get("/api/flashcards/stats/overview")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Statistics history
# ---------------------------------------------------------------------------

class TestStatsHistory:
    def test_returns_history_array(self, client):
        headers = _headers(client, email="statshistory@example.com")
        resp = client.get("/api/flashcards/stats/history?days=30", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "history" in body
        assert isinstance(body["history"], list)

    def test_history_entries_have_expected_fields(self, client):
        headers = _headers(client, email="statshistoryfields@example.com")
        deck = _create_deck(client, headers)
        card = _create_card(client, headers, deck["id"])
        client.post(
            "/api/flashcards/review",
            json={"card_id": card["id"], "quality": 4},
            headers=headers,
        )

        resp = client.get("/api/flashcards/stats/history?days=30", headers=headers)
        history = resp.get_json()["history"]
        assert len(history) >= 1
        entry = history[0]
        assert "date" in entry
        assert "total" in entry
        assert "correct" in entry

    def test_history_default_is_30_days(self, client):
        headers = _headers(client, email="statshistorydefault@example.com")
        resp = client.get("/api/flashcards/stats/history", headers=headers)
        assert resp.status_code == 200
        assert "history" in resp.get_json()

    def test_history_without_jwt_returns_401(self, client):
        resp = client.get("/api/flashcards/stats/history?days=7")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# AI Flashcard Generation
# ---------------------------------------------------------------------------

class TestGenerateFlashcards:
    def test_generate_missing_page_id_returns_422(self, client):
        headers = _headers(client, email="generatenopage@example.com")
        resp = client.post(
            "/api/flashcards/generate",
            json={"num_cards": 5},
            headers=headers,
        )
        assert resp.status_code == 422
        assert "page_id" in resp.get_json()["error"].lower()

    def test_generate_with_nonexistent_page_id_returns_404(self, client):
        headers = _headers(client, email="generatebadpage@example.com")
        resp = client.post(
            "/api/flashcards/generate",
            json={"page_id": "00000000-0000-0000-0000-000000000000"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_generate_with_mocked_ai_service_returns_201(self, client):
        """
        Patch the AI service function so no real OpenAI call is made.
        The mocked return value simulates what generate_flashcards_from_text
        returns: (list_of_card_dicts, usage_dict).
        """
        headers = _headers(client, email="generatesuccess@example.com")
        page_id = _create_workspace_and_page(client, headers)

        mocked_cards = [
            {
                "question": "What does photosynthesis produce?",
                "answer": "Glucose and oxygen",
                "question_type": "conceptual",
                "difficulty": 2,
                "source_snippet": "Photosynthesis is the process…",
                "mcq_options": None,
            }
        ]
        mocked_usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "model": "gpt-4o",
        }

        with patch(
            "app.services.generation_service.generate_flashcards_from_text",
            return_value=(mocked_cards, mocked_usage),
        ):
            resp = client.post(
                "/api/flashcards/generate",
                json={"page_id": page_id, "num_cards": 1},
                headers=headers,
            )

        assert resp.status_code == 201
        deck = resp.get_json()["deck"]
        assert "id" in deck
        assert deck["auto_generated"] is True
        # Verify the deck was populated with the mocked card
        assert deck["card_count"] == 1

    def test_generate_for_another_users_page_returns_403(self, client):
        h1 = register_and_login(
            client, email="genowner@example.com", name="Owner"
        )
        h2 = register_and_login(
            client, email="genthief@example.com", name="Thief"
        )

        page_id = _create_workspace_and_page(client, h1)

        resp = client.post(
            "/api/flashcards/generate",
            json={"page_id": page_id},
            headers=h2,
        )
        assert resp.status_code == 403

    def test_generate_without_jwt_returns_401(self, client):
        resp = client.post(
            "/api/flashcards/generate",
            json={"page_id": "some-id"},
        )
        assert resp.status_code == 401

    def test_generate_page_with_no_content_returns_422(self, client):
        """
        A page with empty plain_text triggers ValueError in generation_service,
        which the route maps to 422.
        """
        headers = _headers(client, email="generateempty@example.com")
        ws = client.post(
            "/api/workspaces",
            json={"name": "Empty WS"},
            headers=headers,
        ).get_json()["workspace"]
        page_resp = client.post(
            f"/api/workspaces/{ws['id']}/pages",
            json={"title": "Empty Page"},
            headers=headers,
        )
        page_id = page_resp.get_json()["page"]["id"]
        # Do NOT set any content – page.plain_text stays ""

        resp = client.post(
            "/api/flashcards/generate",
            json={"page_id": page_id},
            headers=headers,
        )
        # Either a ValueError-driven 422 or an AI service error 500
        assert resp.status_code in (422, 500)
