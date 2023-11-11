"""Data-access tests, including the pagination bug the original shipped."""

from __future__ import annotations

import pytest

from boards.repositories import (
    MAX_PAGE_SIZE,
    CardNotFound,
    CardRepository,
    Page,
    decode_cursor,
    encode_cursor,
)


class TestCrud:
    def test_create_returns_the_stored_card(self, repository):
        card = repository.create(title="Ship it", description="today", status="todo")

        assert card["id"]
        assert card["title"] == "Ship it"
        assert card["status"] == "todo"
        assert card["created_at"] == card["updated_at"]
        assert repository.get(card["id"]) == card

    def test_get_returns_none_for_an_unknown_id(self, repository):
        assert repository.get("does-not-exist") is None

    def test_update_changes_only_the_given_fields(self, repository):
        card = repository.create(title="Old", description="keep me", status="todo")

        updated = repository.update(card["id"], title="New")

        assert updated["title"] == "New"
        assert updated["description"] == "keep me"
        assert updated["status"] == "todo"
        assert updated["updated_at"] >= card["updated_at"]

    def test_update_with_no_changes_returns_the_card_unchanged(self, repository):
        """The original built 'SET ' with no assignments and DynamoDB rejected it."""
        card = repository.create(title="Untouched", status="todo")

        assert repository.update(card["id"]) == card

    def test_update_ignores_fields_that_are_not_editable(self, repository):
        card = repository.create(title="Fixed id", status="todo")

        updated = repository.update(card["id"], id="hacked", created_at="1970-01-01")

        assert updated["id"] == card["id"]
        assert updated["created_at"] == card["created_at"]

    def test_update_of_a_missing_card_raises(self, repository):
        with pytest.raises(CardNotFound):
            repository.update("does-not-exist", title="New")

    def test_delete_reports_whether_anything_was_removed(self, repository):
        card = repository.create(title="Temporary", status="todo")

        assert repository.delete(card["id"]) is True
        assert repository.delete(card["id"]) is False
        assert repository.get(card["id"]) is None


class TestPagination:
    def test_list_returns_every_card_when_they_fit_on_one_page(self, repository, seeded):
        page = repository.list()

        assert len(page) == 3
        assert page.next_cursor is None

    def test_list_respects_the_requested_page_size(self, repository, seeded):
        page = repository.list(limit=2)

        assert len(page) == 2
        assert page.next_cursor is not None

    def test_a_cursor_walks_the_whole_table_exactly_once(self, repository, seeded):
        seen, cursor = [], None
        while True:
            page = repository.list(limit=1, cursor=cursor)
            seen.extend(card["id"] for card in page)
            cursor = page.next_cursor
            if not cursor:
                break

        assert sorted(seen) == sorted(card["id"] for card in seeded)

    def test_page_size_is_capped(self, monkeypatch):
        """An API caller cannot ask for an unbounded read."""
        table = _RecordingTable()
        monkeypatch.setattr(CardRepository, "_table", property(lambda self: table))

        CardRepository().list(limit=10_000)

        assert table.calls[0]["Limit"] == MAX_PAGE_SIZE

    def test_page_size_has_a_floor(self, monkeypatch):
        table = _RecordingTable()
        monkeypatch.setattr(CardRepository, "_table", property(lambda self: table))

        CardRepository().list(limit=0)

        assert table.calls[0]["Limit"] == 1

    def test_a_malformed_cursor_restarts_the_listing(self, repository, seeded):
        page = repository.list(cursor="not-base64-json")

        assert len(page) == 3

    def test_iter_all_follows_pagination(self, repository, seeded):
        assert len({card["id"] for card in repository.iter_all(page_size=1)}) == 3


class _RecordingTable:
    """Records the kwargs every scan was called with and returns nothing."""

    def __init__(self):
        self.calls = []

    def scan(self, **kwargs):
        self.calls.append(kwargs)
        return {"Items": []}


class _TruncatingTable:
    """A table double that returns one item per scan, like a 1 MB cap.

    Real DynamoDB caps a scan response at 1 MB and hands back LastEvaluatedKey.
    The original implementation called scan() once and returned
    response["Items"], so every card past the cap silently vanished from the
    board. This double reproduces that shape without needing a megabyte of data.
    """

    def __init__(self, items):
        self.items = items
        self.scan_calls = 0

    def scan(self, **kwargs):
        self.scan_calls += 1
        start = 0
        if "ExclusiveStartKey" in kwargs:
            start = int(kwargs["ExclusiveStartKey"]["id"]) + 1
        chunk = self.items[start : start + 1]
        response = {"Items": chunk}
        if start + 1 < len(self.items):
            response["LastEvaluatedKey"] = {"id": str(start)}
        return response


class TestTruncationRegression:
    def test_list_follows_last_evaluated_key_instead_of_truncating(self, monkeypatch):
        items = [{"id": str(i), "title": f"Card {i}", "status": "todo"} for i in range(25)]
        table = _TruncatingTable(items)
        monkeypatch.setattr(CardRepository, "_table", property(lambda self: table))

        page = CardRepository().list(limit=25)

        assert len(page) == 25, "cards past the first scan page were dropped"
        assert table.scan_calls == 25


class TestCursorEncoding:
    def test_round_trips(self):
        key = {"id": "abc-123"}

        assert decode_cursor(encode_cursor(key)) == key

    def test_empty_key_has_no_cursor(self):
        assert encode_cursor(None) is None
        assert encode_cursor({}) is None

    def test_decode_tolerates_garbage(self):
        assert decode_cursor("!!!not-valid!!!") is None
        assert decode_cursor(None) is None


def test_page_is_a_list_with_a_cursor():
    page = Page([{"id": "1"}], next_cursor="abc")

    assert page == [{"id": "1"}]
    assert page.next_cursor == "abc"
