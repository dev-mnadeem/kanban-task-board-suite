import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MiniTrelloBoard } from "../Pages/MiniTrelloBoard";
import { GET_BOARD } from "../graphql/queries";
import { boardMock, card, renderWithApollo } from "../testUtils";

const CARDS = [
  card("1", "Write the spec", "todo", "One pager"),
  card("2", "Build it", "in-progress"),
  card("3", "Ship it", "done"),
  card("4", "Review the spec", "todo"),
];

describe("MiniTrelloBoard", () => {
  it("shows a loading state before the board arrives", () => {
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    expect(screen.getByText("Fetching your cards…")).toBeInTheDocument();
  });

  it("renders every lane returned by the server", async () => {
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    expect(await screen.findByRole("region", { name: "To Do" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "In Progress" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Done" })).toBeInTheDocument();
  });

  it("puts each card in the lane matching its status", async () => {
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    const todo = await screen.findByRole("region", { name: "To Do" });

    expect(todo).toHaveTextContent("Write the spec");
    expect(todo).toHaveTextContent("Review the spec");
    expect(todo).not.toHaveTextContent("Ship it");
  });

  it("shows the number of cards in each lane", async () => {
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    const todo = await screen.findByRole("region", { name: "To Do" });

    expect(todo).toHaveTextContent("2");
  });

  it("summarises the board in the header", async () => {
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    expect(await screen.findByText("4 cards across 3 lanes")).toBeInTheDocument();
  });

  it("shows a placeholder in an empty lane", async () => {
    renderWithApollo(<MiniTrelloBoard />, [boardMock([card("1", "Only card", "todo")])]);

    await screen.findByRole("region", { name: "Done" });

    expect(screen.getAllByText("Drop a card here")).toHaveLength(2);
  });

  it("renders a card description when there is one", async () => {
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    expect(await screen.findByText("One pager")).toBeInTheDocument();
  });

  it("shows an actionable error when the API cannot be reached", async () => {
    const failing = {
      request: { query: GET_BOARD },
      error: new Error("Failed to fetch"),
    };

    renderWithApollo(<MiniTrelloBoard />, [failing]);

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not reach the API");
    expect(screen.getByText(/REACT_APP_GRAPHQL_URL/)).toBeInTheDocument();
  });

  it("opens an empty form from the Add card button", async () => {
    const user = userEvent.setup();
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    await screen.findByRole("region", { name: "To Do" });
    await user.click(screen.getByRole("button", { name: "Add card" }));

    expect(await screen.findByText("Add a card")).toBeInTheDocument();
    expect(screen.getByLabelText("Title")).toHaveValue("");
  });

  it("opens the form pre-filled when editing a card", async () => {
    const user = userEvent.setup();
    renderWithApollo(<MiniTrelloBoard />, [boardMock(CARDS)]);

    await screen.findByRole("region", { name: "To Do" });
    await user.click(screen.getByRole("button", { name: "Edit Write the spec" }));

    await waitFor(() => expect(screen.getByLabelText("Title")).toHaveValue("Write the spec"));
    expect(screen.getByLabelText("Description")).toHaveValue("One pager");
    expect(screen.getByText("Edit card")).toBeInTheDocument();
  });
});
