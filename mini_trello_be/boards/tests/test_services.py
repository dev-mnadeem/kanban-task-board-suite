"""Business-rule tests. These are the rules the GraphQL layer relies on."""

from __future__ import annotations

import pytest

from boards import lanes
from boards.repositories import CardNotFound
from boards.services import MAX_TITLE_LENGTH, ValidationError


class TestCreateValidation:
    def test_a_title_is_required(self, service):
        with pytest.raises(ValidationError, match="Title is required"):
            service.create_card(title="")

    def test_a_whitespace_only_title_is_rejected(self, service):
        with pytest.raises(ValidationError, match="Title is required"):
            service.create_card(title="   \n\t ")

    def test_the_title_is_trimmed(self, service):
        card = service.create_card(title="  Padded  ")

        assert card["title"] == "Padded"

    def test_an_overlong_title_is_rejected(self, service):
        with pytest.raises(ValidationError, match="characters or fewer"):
            service.create_card(title="x" * (MAX_TITLE_LENGTH + 1))

    def test_a_title_at_the_limit_is_accepted(self, service):
        card = service.create_card(title="x" * MAX_TITLE_LENGTH)

        assert len(card["title"]) == MAX_TITLE_LENGTH

    def test_an_unknown_status_is_rejected(self, service):
        with pytest.raises(ValidationError, match="Unknown status"):
            service.create_card(title="Valid", status="nowhere")

    def test_the_status_defaults_to_the_first_lane(self, service):
        card = service.create_card(title="No status given")

        assert card["status"] == lanes.DEFAULT_LANE_ID

    def test_a_missing_description_becomes_an_empty_string(self, service):
        card = service.create_card(title="No description")

        assert card["description"] == ""

    @pytest.mark.parametrize("status", lanes.lane_ids())
    def test_every_declared_lane_is_accepted(self, service, status):
        assert service.create_card(title="Anywhere", status=status)["status"] == status


class TestUpdateValidation:
    def test_an_unknown_status_is_rejected(self, service, seeded):
        with pytest.raises(ValidationError, match="Unknown status"):
            service.update_card(seeded[0]["id"], status="nowhere")

    def test_an_empty_title_is_rejected(self, service, seeded):
        with pytest.raises(ValidationError, match="Title is required"):
            service.update_card(seeded[0]["id"], title="  ")

    def test_updating_a_missing_card_raises(self, service):
        with pytest.raises(CardNotFound):
            service.update_card("does-not-exist", title="New")

    def test_a_failed_validation_does_not_write(self, service, seeded):
        card = seeded[0]

        with pytest.raises(ValidationError):
            service.update_card(card["id"], title="Fine", status="nowhere")

        assert service.get_card(card["id"])["title"] == card["title"]


class TestMove:
    def test_moving_changes_the_lane(self, service, seeded):
        card = seeded[0]

        moved = service.move_card(card["id"], "done")

        assert moved["status"] == "done"
        assert moved["id"] == card["id"]

    def test_moving_to_an_unknown_lane_is_rejected(self, service, seeded):
        with pytest.raises(ValidationError):
            service.move_card(seeded[0]["id"], "archive")


class TestLaneRegistry:
    def test_lane_ids_are_unique_and_ordered(self):
        ids = lanes.lane_ids()

        assert len(set(ids)) == len(ids)
        assert [lane.position for lane in lanes.LANES] == sorted(
            lane.position for lane in lanes.LANES
        )

    def test_the_default_lane_is_a_real_lane(self):
        assert lanes.is_valid_lane(lanes.DEFAULT_LANE_ID)

    def test_an_unknown_lane_is_not_valid(self):
        assert not lanes.is_valid_lane("archive")
        assert lanes.get_lane("archive") is None
