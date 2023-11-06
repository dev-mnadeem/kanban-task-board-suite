"""GraphQL schema for the board.

This module is a thin adapter: it maps GraphQL arguments onto
:class:`~boards.services.CardService` calls and maps service exceptions onto
GraphQL errors. No business rule and no DynamoDB detail belongs here.
"""

from __future__ import annotations

from typing import Any

import graphene
from graphql import GraphQLError

from . import lanes
from .repositories import CardNotFound
from .services import CardService, ValidationError

service = CardService()


def _handle(call, *args, **kwargs):
    """Run a service call, translating domain errors into GraphQL errors.

    Without this, a bad status or a deleted card surfaced as an unhandled
    TypeError and a 500. Clients now get a message in the ``errors`` array.
    """
    try:
        return call(*args, **kwargs)
    except ValidationError as exc:
        raise GraphQLError(str(exc)) from exc
    except CardNotFound as exc:
        raise GraphQLError(str(exc)) from exc


class CardType(graphene.ObjectType):
    """A single card on the board."""

    id = graphene.String(required=True)
    title = graphene.String(required=True)
    description = graphene.String()
    status = graphene.String(required=True)
    created_at = graphene.String()
    updated_at = graphene.String()

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> CardType:
        """Build a CardType from a repository dict, tolerating absent fields.

        The original indexed every key directly, so a card written before a
        field existed crashed the whole query.
        """
        return cls(
            id=item.get("id"),
            title=item.get("title"),
            description=item.get("description", ""),
            status=item.get("status", lanes.DEFAULT_LANE_ID),
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
        )


class LaneType(graphene.ObjectType):
    """A column on the board. Driven by :mod:`boards.lanes`."""

    id = graphene.String(required=True)
    title = graphene.String(required=True)
    position = graphene.Int(required=True)


class CardPage(graphene.ObjectType):
    """One page of cards plus the cursor for the next one."""

    cards = graphene.List(graphene.NonNull(CardType), required=True)
    next_cursor = graphene.String()
    has_next_page = graphene.Boolean(required=True)


class Query(graphene.ObjectType):
    all_cards = graphene.List(
        graphene.NonNull(CardType),
        limit=graphene.Int(),
        cursor=graphene.String(),
        required=True,
        description="Cards on the board. Bounded; use `cardPage` to paginate.",
    )
    card_page = graphene.Field(
        CardPage,
        limit=graphene.Int(),
        cursor=graphene.String(),
        description="A page of cards with a cursor for the next page.",
    )
    card = graphene.Field(CardType, id=graphene.ID(required=True))
    lanes = graphene.List(
        graphene.NonNull(LaneType),
        required=True,
        description="The board's columns, in order.",
    )

    def resolve_all_cards(self, info, limit=None, cursor=None):
        page = _handle(service.list_cards, limit=limit, cursor=cursor)
        return [CardType.from_item(item) for item in page]

    def resolve_card_page(self, info, limit=None, cursor=None):
        page = _handle(service.list_cards, limit=limit, cursor=cursor)
        return CardPage(
            cards=[CardType.from_item(item) for item in page],
            next_cursor=page.next_cursor,
            has_next_page=bool(page.next_cursor),
        )

    def resolve_card(self, info, id):
        # Returns null for an unknown id. The original subscripted None here
        # and raised TypeError.
        item = _handle(service.get_card, id)
        return CardType.from_item(item) if item else None

    def resolve_lanes(self, info):
        return [
            LaneType(id=lane.id, title=lane.title, position=lane.position)
            for lane in lanes.LANES
        ]


class CreateCard(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String()
        status = graphene.String()

    card = graphene.Field(CardType)

    def mutate(self, info, title, description=None, status=None):
        item = _handle(service.create_card, title=title, description=description, status=status)
        return CreateCard(card=CardType.from_item(item))


class UpdateCard(graphene.Mutation):
    class Arguments:
        card_id = graphene.String(required=True)
        title = graphene.String()
        description = graphene.String()
        status = graphene.String()

    card = graphene.Field(CardType)

    def mutate(self, info, card_id, title=None, description=None, status=None):
        item = _handle(
            service.update_card,
            card_id,
            title=title,
            description=description,
            status=status,
        )
        return UpdateCard(card=CardType.from_item(item))


class DeleteCard(graphene.Mutation):
    class Arguments:
        card_id = graphene.String(required=True)

    success = graphene.Boolean(required=True)

    def mutate(self, info, card_id):
        # The original always reported success, even for an id that never
        # existed, so the UI could not tell a delete from a no-op.
        return DeleteCard(success=_handle(service.delete_card, card_id))


class Mutation(graphene.ObjectType):
    create_card = CreateCard.Field()
    update_card = UpdateCard.Field()
    delete_card = DeleteCard.Field()
