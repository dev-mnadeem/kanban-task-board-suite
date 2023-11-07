import gql from "graphql-tag";

import { CARD_FIELDS } from "./queries";

export const ADD_CARD = gql`
  ${CARD_FIELDS}
  mutation AddCard($title: String!, $description: String, $status: String) {
    createCard(title: $title, description: $description, status: $status) {
      card {
        ...CardFields
      }
    }
  }
`;

export const UPDATE_CARD = gql`
  ${CARD_FIELDS}
  mutation UpdateCard($id: String!, $title: String, $description: String) {
    updateCard(cardId: $id, title: $title, description: $description) {
      card {
        ...CardFields
      }
    }
  }
`;

export const MOVE_CARD = gql`
  ${CARD_FIELDS}
  mutation MoveCard($id: String!, $status: String!) {
    updateCard(cardId: $id, status: $status) {
      card {
        ...CardFields
      }
    }
  }
`;

export const DELETE_CARD = gql`
  mutation DeleteCard($id: String!) {
    deleteCard(cardId: $id) {
      success
    }
  }
`;
