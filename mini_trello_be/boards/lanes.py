"""The board's lane definitions.

This is the single source of truth for what a "status" may be. It is the seam a
future developer is most likely to need: adding a lane (e.g. "blocked") is one
entry here, and validation, the GraphQL schema and the seed command all follow.
Nothing else in the codebase may hardcode a status string.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lane:
    """One column on the board."""

    id: str
    title: str
    position: int


LANES: tuple[Lane, ...] = (
    Lane(id="todo", title="To Do", position=0),
    Lane(id="in-progress", title="In Progress", position=1),
    Lane(id="done", title="Done", position=2),
)

DEFAULT_LANE_ID: str = LANES[0].id

_LANES_BY_ID = {lane.id: lane for lane in LANES}


def lane_ids() -> tuple[str, ...]:
    """Every valid status, in board order."""
    return tuple(lane.id for lane in LANES)


def get_lane(lane_id: str) -> Lane | None:
    """Return the lane with this id, or None if it is not a known lane."""
    return _LANES_BY_ID.get(lane_id)


def is_valid_lane(lane_id: str) -> bool:
    return lane_id in _LANES_BY_ID
