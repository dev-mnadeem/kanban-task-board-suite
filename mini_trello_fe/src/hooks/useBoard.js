import { useCallback, useMemo } from "react";
import { useMutation, useQuery } from "@apollo/client";

import {
  ADD_CARD,
  DELETE_CARD,
  MOVE_CARD,
  UPDATE_CARD,
} from "../graphql/mutations";
import { GET_BOARD } from "../graphql/queries";

/**
 * All of the board's data handling in one place.
 *
 * The page component previously owned the query, four mutations, a duplicated
 * copy of the server state and the reconciliation between them. Keeping it
 * here means the component only renders, and this logic can be tested on its
 * own.
 */
export function useBoard() {
  const { data, loading, error } = useQuery(GET_BOARD);

  const [addCardMutation] = useMutation(ADD_CARD, {
    refetchQueries: [{ query: GET_BOARD }],
  });
  const [updateCardMutation] = useMutation(UPDATE_CARD);
  const [moveCardMutation] = useMutation(MOVE_CARD);
  const [deleteCardMutation] = useMutation(DELETE_CARD, {
    refetchQueries: [{ query: GET_BOARD }],
  });

  /**
   * Group cards into their lanes. Derived from the server response on every
   * render rather than copied into state, which is what previously let the
   * board drift out of sync after an edit.
   */
  const lanes = useMemo(() => {
    const laneDefinitions = data?.lanes ?? [];
    const cards = data?.allCards ?? [];

    return [...laneDefinitions]
      .sort((a, b) => a.position - b.position)
      .map((lane) => ({
        ...lane,
        cards: cards.filter((card) => card.status === lane.id),
      }));
  }, [data]);

  const cardCount = data?.allCards?.length ?? 0;

  const createCard = useCallback(
    ({ title, description, status }) =>
      addCardMutation({ variables: { title, description, status } }),
    [addCardMutation]
  );

  const updateCard = useCallback(
    ({ id, title, description }) =>
      updateCardMutation({ variables: { id, title, description } }),
    [updateCardMutation]
  );

  const deleteCard = useCallback(
    (id) => deleteCardMutation({ variables: { id } }),
    [deleteCardMutation]
  );

  /**
   * Move a card to another lane. The cache is updated immediately so the card
   * does not snap back while the request is in flight.
   */
  const moveCard = useCallback(
    (id, status) =>
      moveCardMutation({
        variables: { id, status },
        optimisticResponse: {
          updateCard: {
            __typename: "UpdateCard",
            card: {
              __typename: "CardType",
              ...(data?.allCards ?? []).find((card) => card.id === id),
              id,
              status,
            },
          },
        },
      }),
    [moveCardMutation, data]
  );

  return {
    lanes,
    cardCount,
    loading: loading && !data,
    error,
    createCard,
    updateCard,
    deleteCard,
    moveCard,
  };
}
