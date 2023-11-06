"""Business rules for cards.

Validation and orchestration live here, so the GraphQL layer stays a thin
adapter and the repository stays pure data access. Dependencies point inward:
``schema`` -> ``services`` -> ``repositories`` -> ``dynamodb``.
"""

from __future__ import annotations

from typing import Any

from . import lanes
from .repositories import CardNotFound, CardRepository, Page

#: Keeps a card title to something that fits on a board column.
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000


class ValidationError(ValueError):
    """Raised when input fails a business rule."""


class CardService:
    """Everything the API is allowed to do to a card."""

    def __init__(self, repository: CardRepository | None = None) -> None:
        self.repository = repository or CardRepository()

    # ---------------------------------------------------------------- reads

    def list_cards(self, *, limit: int | None = None, cursor: str | None = None) -> Page:
        kwargs: dict[str, Any] = {"cursor": cursor}
        if limit is not None:
            kwargs["limit"] = limit
        return self.repository.list(**kwargs)

    def get_card(self, card_id: str) -> dict[str, Any] | None:
        return self.repository.get(card_id)

    # --------------------------------------------------------------- writes

    def create_card(
        self,
        *,
        title: str,
        description: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        title = self._clean_title(title)
        description = self._clean_description(description)
        status = self._clean_status(status) if status else lanes.DEFAULT_LANE_ID
        return self.repository.create(title=title, description=description, status=status)

    def update_card(
        self,
        card_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        changes: dict[str, Any] = {}
        if title is not None:
            changes["title"] = self._clean_title(title)
        if description is not None:
            changes["description"] = self._clean_description(description)
        if status is not None:
            changes["status"] = self._clean_status(status)
        return self.repository.update(card_id, **changes)

    def move_card(self, card_id: str, status: str) -> dict[str, Any]:
        """Move a card to another lane. A move is just a validated status change."""
        return self.update_card(card_id, status=status)

    def delete_card(self, card_id: str) -> bool:
        return self.repository.delete(card_id)

    # ----------------------------------------------------------- validation

    @staticmethod
    def _clean_title(title: str) -> str:
        title = (title or "").strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError(f"Title must be {MAX_TITLE_LENGTH} characters or fewer.")
        return title

    @staticmethod
    def _clean_description(description: str | None) -> str:
        description = (description or "").strip()
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
            )
        return description

    @staticmethod
    def _clean_status(status: str) -> str:
        status = (status or "").strip()
        if not lanes.is_valid_lane(status):
            valid = ", ".join(lanes.lane_ids())
            raise ValidationError(f"Unknown status {status!r}. Expected one of: {valid}.")
        return status


__all__ = ["CardService", "ValidationError", "CardNotFound"]
