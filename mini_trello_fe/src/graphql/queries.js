import gql from "graphql-tag";

export const CARD_FIELDS = gql`
  fragment CardFields on CardType {
    id
    title
    description
    status
  }
`;

/**
 * One round trip for the whole board: the lane definitions come from the
 * server's lane registry, so adding a lane needs no frontend change.
 */
export const GET_BOARD = gql`
  ${CARD_FIELDS}
  query GetBoard {
    lanes {
      id
      title
      position
    }
    allCards {
      ...CardFields
    }
  }
`;
