import React, { useState } from "react";
import { DragDropContext } from "react-beautiful-dnd";

import { Lane } from "../Components/Lane";
import { TicketFormModal } from "../Components/TicketFormModal";
import { useBoard } from "../hooks/useBoard";
import "./MiniTrelloBoard.css";

export const MiniTrelloBoard = () => {
  const { lanes, cardCount, loading, error, createCard, updateCard, deleteCard, moveCard } =
    useBoard();
  const [editing, setEditing] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openAdd = () => {
    setEditing(null);
    setIsModalOpen(true);
  };

  const openEdit = (card) => {
    setEditing(card);
    setIsModalOpen(true);
  };

  const closeModal = () => setIsModalOpen(false);

  const handleSubmit = (draft) =>
    editing
      ? updateCard({ id: editing.id, ...draft })
      : createCard({ ...draft, status: lanes[0]?.id });

  const handleDragEnd = (result) => {
    const { destination, source, draggableId } = result;
    // Dropped outside a lane, or back where it started.
    if (!destination || destination.droppableId === source.droppableId) return;
    moveCard(draggableId, destination.droppableId);
  };

  return (
    <div className="board">
      <header className="board__header">
        <div>
          <h1 className="board__title">Mini Trello</h1>
          <p className="board__subtitle">
            {loading ? "Loading board…" : `${cardCount} cards across ${lanes.length} lanes`}
          </p>
        </div>
        <button type="button" className="button" onClick={openAdd}>
          Add card
        </button>
      </header>

      {error ? (
        <div className="board__state board__state--error" role="alert">
          <h2>Could not reach the API</h2>
          <p>{error.message}</p>
          <p className="board__state-hint">
            Check that the backend is running and that REACT_APP_GRAPHQL_URL points at it.
          </p>
        </div>
      ) : null}

      {loading && !error ? (
        <div className="board__state">
          <p>Fetching your cards…</p>
        </div>
      ) : null}

      {!loading && !error ? (
        <DragDropContext onDragEnd={handleDragEnd}>
          <div className="board__lanes">
            {lanes.map((lane) => (
              <Lane key={lane.id} lane={lane} onEdit={openEdit} onDelete={deleteCard} />
            ))}
          </div>
        </DragDropContext>
      ) : null}

      {isModalOpen ? (
        <TicketFormModal card={editing} onSubmit={handleSubmit} onClose={closeModal} />
      ) : null}
    </div>
  );
};
