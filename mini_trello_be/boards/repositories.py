"""Data access for cards.

This layer knows about DynamoDB and nothing else: no GraphQL types, no HTTP,
no validation. Everything above it talks in plain dicts.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from . import dynamodb

logger = logging.getLogger(__name__)

#: Attributes a card is made of. Used as a ProjectionExpression so a board read
#: never pulls back attributes the API does not expose.
CARD_ATTRIBUTES = ("id", "title", "description", "status", "created_at", "updated_at")

#: Hard ceiling on a single page. Protects the API from an unbounded read.
MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 100


class CardNotFound(LookupError):
    """Raised when a card id does not exist."""

    def __init__(self, card_id: str) -> None:
        super().__init__(f"Card {card_id!r} does not exist")
        self.card_id = card_id


def _now() -> str:
    return datetime.now(UTC).isoformat()


def encode_cursor(key: dict[str, Any] | None) -> str | None:
    """Encode a DynamoDB LastEvaluatedKey as an opaque pagination cursor."""
    if not key:
        return None
    return base64.urlsafe_b64encode(json.dumps(key, sort_keys=True).encode()).decode()


def decode_cursor(cursor: str | None) -> dict[str, Any] | None:
    """Decode a cursor produced by :func:`encode_cursor`.

    Returns None for a missing or malformed cursor rather than raising, so a
    stale cursor restarts the listing instead of failing the request.
    """
    if not cursor:
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except (ValueError, TypeError):
        logger.warning("Discarding malformed pagination cursor")
        return None


class Page(list):
    """A list of cards plus the cursor needed to fetch the next page."""

    def __init__(self, items: list[dict[str, Any]], next_cursor: str | None = None) -> None:
        super().__init__(items)
        self.next_cursor = next_cursor


class CardRepository:
    """CRUD over the Card table.

    The table handle is resolved per call rather than held on the instance so
    that a connection reset (see :mod:`boards.dynamodb`) is picked up
    immediately — which is what makes the suite able to swap in a mock.
    """

    @property
    def _table(self) -> Any:
        return dynamodb.get_card_table()

    # ---------------------------------------------------------------- reads

    def get(self, card_id: str) -> dict[str, Any] | None:
        """Return one card, or None when it does not exist."""
        response = self._table.get_item(
            Key={"id": card_id},
            ProjectionExpression=self._projection(),
            ExpressionAttributeNames=self._projection_names(),
        )
        return response.get("Item")

    def list(
        self,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        cursor: str | None = None,
    ) -> Page:
        """Return one page of cards.

        The original implementation called ``scan()`` once and returned
        ``response["Items"]``. DynamoDB caps a scan response at 1 MB, so any
        board larger than that silently lost cards — the dropped items were
        never reported, they simply stopped appearing on the board. This walks
        ``LastEvaluatedKey`` until the requested page is full and hands back a
        cursor so the caller can continue.
        """
        limit = max(1, min(int(limit), MAX_PAGE_SIZE))
        items: list[dict[str, Any]] = []
        start_key = decode_cursor(cursor)

        while True:
            kwargs: dict[str, Any] = {
                "Limit": limit - len(items),
                "ProjectionExpression": self._projection(),
                "ExpressionAttributeNames": self._projection_names(),
            }
            if start_key:
                kwargs["ExclusiveStartKey"] = start_key

            response = self._table.scan(**kwargs)
            items.extend(response.get("Items", []))
            start_key = response.get("LastEvaluatedKey")

            if len(items) >= limit or not start_key:
                break

        return Page(items[:limit], encode_cursor(start_key))

    def iter_all(self, *, page_size: int = DEFAULT_PAGE_SIZE) -> Iterator[dict[str, Any]]:
        """Yield every card, following pagination. For batch jobs, not requests."""
        cursor: str | None = None
        while True:
            page = self.list(limit=page_size, cursor=cursor)
            yield from page
            cursor = page.next_cursor
            if not cursor:
                return

    # --------------------------------------------------------------- writes

    def create(self, *, title: str, description: str = "", status: str) -> dict[str, Any]:
        """Insert a card and return it as stored."""
        now = _now()
        item = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description or "",
            "status": status,
            "created_at": now,
            "updated_at": now,
        }
        self._table.put_item(Item=item)
        return item

    def update(self, card_id: str, **changes: Any) -> dict[str, Any]:
        """Apply the given attribute changes and return the updated card.

        Only ``title``, ``description`` and ``status`` may be changed; anything
        else is ignored. Raises :class:`CardNotFound` if the card is gone.
        """
        editable = {
            field: value
            for field, value in changes.items()
            if field in ("title", "description", "status") and value is not None
        }
        if not editable:
            # The original built "SET " with no assignments, which DynamoDB
            # rejects with a ValidationException. A no-op update is not an
            # error: return the card unchanged.
            current = self.get(card_id)
            if current is None:
                raise CardNotFound(card_id)
            return current

        editable["updated_at"] = _now()

        names = {f"#{field}": field for field in editable}
        values = {f":{field}": value for field, value in editable.items()}
        assignments = ", ".join(f"#{field} = :{field}" for field in editable)

        try:
            response = self._table.update_item(
                Key={"id": card_id},
                UpdateExpression=f"SET {assignments}",
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression="attribute_exists(id)",
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise CardNotFound(card_id) from exc
            raise
        # ALL_NEW returns the whole item, so the original's second get_item
        # round trip is gone.
        return response["Attributes"]

    def delete(self, card_id: str) -> bool:
        """Delete a card. Returns False if it was not there to begin with."""
        try:
            self._table.delete_item(
                Key={"id": card_id},
                ConditionExpression="attribute_exists(id)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise
        return True

    # --------------------------------------------------------------- helpers

    @staticmethod
    def _projection() -> str:
        return ", ".join(f"#{name}" for name in CARD_ATTRIBUTES)

    @staticmethod
    def _projection_names() -> dict[str, str]:
        # "status" is a DynamoDB reserved word, so every attribute goes through
        # a name placeholder rather than special-casing one of them.
        return {f"#{name}": name for name in CARD_ATTRIBUTES}
