import { ApolloClient, HttpLink, InMemoryCache } from "@apollo/client";

import { GRAPHQL_URL } from "./config";

/**
 * Cards are normalised by `id` so that a mutation returning a card updates
 * every query holding that card, without a refetch.
 */
const cache = new InMemoryCache({
  typePolicies: {
    CardType: { keyFields: ["id"] },
    LaneType: { keyFields: ["id"] },
  },
});

const client = new ApolloClient({
  link: new HttpLink({ uri: GRAPHQL_URL }),
  cache,
  defaultOptions: {
    watchQuery: { fetchPolicy: "cache-and-network" },
  },
});

export default client;
