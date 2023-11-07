import React from "react";
import { ApolloProvider } from "@apollo/client";

import client from "./apollo";
import { MiniTrelloBoard } from "./Pages/MiniTrelloBoard";

const App = () => (
  <ApolloProvider client={client}>
    <MiniTrelloBoard />
  </ApolloProvider>
);

export default App;
