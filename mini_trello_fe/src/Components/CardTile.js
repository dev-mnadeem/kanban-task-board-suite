import React from "react";
import { Draggable } from "react-beautiful-dnd";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPen, faTrash } from "@fortawesome/free-solid-svg-icons";

export const CardTile = ({ card, index, onEdit, onDelete }) => (
  <Draggable draggableId={card.id} index={index}>
    {(provided, snapshot) => (
      <article
        ref={provided.innerRef}
        {...provided.draggableProps}
        {...provided.dragHandleProps}
        className={`card${snapshot.isDragging ? " card--dragging" : ""}`}
        aria-label={card.title}
      >
        <div className="card__header">
          <h3 className="card__title">{card.title}</h3>
          <div className="card__actions">
            <button
              type="button"
              className="icon-button"
              onClick={() => onEdit(card)}
              aria-label={`Edit ${card.title}`}
            >
              <FontAwesomeIcon icon={faPen} />
            </button>
            <button
              type="button"
              className="icon-button icon-button--danger"
              onClick={() => onDelete(card.id)}
              aria-label={`Delete ${card.title}`}
            >
              <FontAwesomeIcon icon={faTrash} />
            </button>
          </div>
        </div>
        {card.description ? (
          <p className="card__description">{card.description}</p>
        ) : null}
      </article>
    )}
  </Draggable>
);
