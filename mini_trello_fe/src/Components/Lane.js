import React from "react";
import { Droppable } from "react-beautiful-dnd";

import { CardTile } from "./CardTile";

export const Lane = ({ lane, onEdit, onDelete }) => (
  <Droppable droppableId={lane.id}>
    {(provided, snapshot) => (
      <section
        className={`lane${snapshot.isDraggingOver ? " lane--active" : ""}`}
        aria-label={lane.title}
      >
        <header className="lane__header">
          <h2 className="lane__title">{lane.title}</h2>
          <span className="lane__count" aria-label={`${lane.cards.length} cards`}>
            {lane.cards.length}
          </span>
        </header>

        <div className="lane__cards" ref={provided.innerRef} {...provided.droppableProps}>
          {lane.cards.map((card, index) => (
            <CardTile
              key={card.id}
              card={card}
              index={index}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
          {provided.placeholder}
          {lane.cards.length === 0 ? (
            <p className="lane__empty">Drop a card here</p>
          ) : null}
        </div>
      </section>
    )}
  </Droppable>
);
