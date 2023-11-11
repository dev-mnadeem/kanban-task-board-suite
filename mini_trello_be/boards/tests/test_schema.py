"""GraphQL contract tests.

These execute the real schema, so they cover the exact queries the React
client sends.
"""

from __future__ import annotations

import pytest

from boards import lanes
from mini_trello_be.schema import schema


def run(query: str, **variables):
    result = schema.execute(query, variables=variables or None)
    return result


def run_ok(query: str, **variables):
    result = run(query, **variables)
    assert not result.errors, result.errors
    return result.data


ALL_CARDS = """
query GetCards { allCards { id title description status } }
"""

CREATE_CARD = """
mutation AddCard($title: String!, $description: String, $status: String) {
  createCard(title: $title, description: $description, status: $status) {
    card { id title description status }
  }
}
"""

UPDATE_CARD = """
mutation UpdateCard($id: String!, $title: String, $description: String, $status: String) {
  updateCard(cardId: $id, title: $title, description: $description, status: $status) {
    card { id title description status }
  }
}
"""

DELETE_CARD = """
mutation DeleteCard($id: String!) { deleteCard(cardId: $id) { success } }
"""


class TestQueries:
    def test_all_cards_returns_every_seeded_card(self, seeded, card_table):
        data = run_ok(ALL_CARDS)

        assert len(data["allCards"]) == len(seeded)
        assert {card["status"] for card in data["allCards"]} == set(lanes.lane_ids())

    def test_all_cards_on_an_empty_board_is_an_empty_list(self, card_table):
        assert run_ok(ALL_CARDS)["allCards"] == []

    def test_card_returns_null_for_an_unknown_id(self, card_table):
        """The original subscripted None here and raised TypeError."""
        result = run('query { card(id: "does-not-exist") { id } }')

        assert not result.errors
        assert result.data["card"] is None

    def test_card_page_exposes_a_cursor(self, seeded, card_table):
        data = run_ok("query { cardPage(limit: 2) { cards { id } nextCursor hasNextPage } }")

        assert len(data["cardPage"]["cards"]) == 2
        assert data["cardPage"]["hasNextPage"] is True
        assert data["cardPage"]["nextCursor"]

    def test_card_page_reports_the_last_page(self, seeded, card_table):
        data = run_ok("query { cardPage(limit: 50) { cards { id } nextCursor hasNextPage } }")

        assert data["cardPage"]["hasNextPage"] is False
        assert data["cardPage"]["nextCursor"] is None

    def test_lanes_come_from_the_registry(self, card_table):
        data = run_ok("query { lanes { id title position } }")

        assert [lane["id"] for lane in data["lanes"]] == list(lanes.lane_ids())


class TestMutations:
    def test_create_card_round_trips(self, card_table):
        data = run_ok(CREATE_CARD, title="From GraphQL", description="d", status="done")
        card = data["createCard"]["card"]

        assert card["title"] == "From GraphQL"
        assert card["status"] == "done"
        assert run_ok(ALL_CARDS)["allCards"] == [card]

    def test_create_card_without_a_status_lands_in_the_default_lane(self, card_table):
        data = run_ok(CREATE_CARD, title="No status")

        assert data["createCard"]["card"]["status"] == lanes.DEFAULT_LANE_ID

    def test_create_card_with_an_empty_title_returns_an_error(self, card_table):
        result = run(CREATE_CARD, title="")

        assert result.errors
        assert "Title is required" in str(result.errors[0])
        assert run_ok(ALL_CARDS)["allCards"] == []

    def test_create_card_with_a_bad_status_returns_an_error(self, card_table):
        result = run(CREATE_CARD, title="Valid", status="nowhere")

        assert result.errors
        assert "Unknown status" in str(result.errors[0])

    def test_update_card_changes_the_title(self, seeded, card_table):
        data = run_ok(UPDATE_CARD, id=seeded[0]["id"], title="Renamed")

        assert data["updateCard"]["card"]["title"] == "Renamed"
        assert data["updateCard"]["card"]["status"] == seeded[0]["status"]

    def test_moving_a_card_only_changes_its_status(self, seeded, card_table):
        data = run_ok(UPDATE_CARD, id=seeded[0]["id"], status="done")
        card = data["updateCard"]["card"]

        assert card["status"] == "done"
        assert card["title"] == seeded[0]["title"]

    def test_update_of_a_missing_card_returns_an_error(self, card_table):
        result = run(UPDATE_CARD, id="does-not-exist", title="Renamed")

        assert result.errors
        assert "does not exist" in str(result.errors[0])

    def test_delete_card_removes_it(self, seeded, card_table):
        data = run_ok(DELETE_CARD, id=seeded[0]["id"])

        assert data["deleteCard"]["success"] is True
        assert len(run_ok(ALL_CARDS)["allCards"]) == len(seeded) - 1

    def test_delete_of_a_missing_card_reports_failure(self, card_table):
        """The original hardcoded success: true for any id at all."""
        data = run_ok(DELETE_CARD, id="does-not-exist")

        assert data["deleteCard"]["success"] is False


class TestApiSurface:
    """Guards against an accidental change to the contract the client depends on."""

    @pytest.mark.parametrize("field", ["allCards", "cardPage", "card", "lanes"])
    def test_query_fields_exist(self, field):
        assert field in schema.get_query_type().fields

    @pytest.mark.parametrize("field", ["createCard", "updateCard", "deleteCard"])
    def test_mutation_fields_exist(self, field):
        assert field in schema.get_mutation_type().fields
