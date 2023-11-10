import React, { useState } from "react";
import Modal from "react-modal";

const EMPTY = { title: "", description: "" };

/**
 * One modal serves both "add" and "edit". It owns its own draft state and
 * hands a finished value back on submit, so the board does not have to track
 * half-typed input.
 *
 * The board mounts this only while it is open, so the draft starts from the
 * given card on every open and no reset effect is needed.
 */
export const TicketFormModal = ({ card, onSubmit, onClose }) => {
  const [draft, setDraft] = useState(() =>
    card ? { title: card.title, description: card.description ?? "" } : EMPTY
  );
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setDraft((previous) => ({ ...previous, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!draft.title.trim()) {
      setError("A title is required.");
      return;
    }

    setSaving(true);
    try {
      await onSubmit(draft);
      onClose();
    } catch (submitError) {
      setError(submitError.message ?? "Something went wrong. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen
      onRequestClose={onClose}
      contentLabel={card ? "Edit card" : "Add card"}
      className="modal"
      overlayClassName="modal__overlay"
      ariaHideApp={false}
    >
      <form onSubmit={handleSubmit} className="modal__form">
        <h2 className="modal__title">{card ? "Edit card" : "Add a card"}</h2>

        <label className="field" htmlFor="card-title">
          <span className="field__label">Title</span>
          <input
            id="card-title"
            name="title"
            type="text"
            value={draft.title}
            onChange={handleChange}
            placeholder="What needs doing?"
            autoFocus
          />
        </label>

        <label className="field" htmlFor="card-description">
          <span className="field__label">Description</span>
          <textarea
            id="card-description"
            name="description"
            rows={4}
            value={draft.description}
            onChange={handleChange}
            placeholder="Add any detail worth remembering"
          />
        </label>

        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}

        <div className="modal__actions">
          <button type="button" className="button button--ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="button" disabled={saving}>
            {saving ? "Saving…" : card ? "Save changes" : "Add card"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
