import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TicketFormModal } from "../Components/TicketFormModal";

const setup = (props = {}) => {
  const onSubmit = jest.fn().mockResolvedValue(undefined);
  const onClose = jest.fn();
  render(
    <TicketFormModal card={null} onSubmit={onSubmit} onClose={onClose} {...props} />
  );
  return { onSubmit, onClose };
};

describe("TicketFormModal", () => {
  it("refuses to submit without a title", async () => {
    const user = userEvent.setup();
    const { onSubmit } = setup();

    await user.click(screen.getByRole("button", { name: "Add card" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("A title is required.");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("treats a whitespace-only title as empty", async () => {
    const user = userEvent.setup();
    const { onSubmit } = setup();

    await user.type(screen.getByLabelText("Title"), "   ");
    await user.click(screen.getByRole("button", { name: "Add card" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the draft and closes", async () => {
    const user = userEvent.setup();
    const { onSubmit, onClose } = setup();

    await user.type(screen.getByLabelText("Title"), "New card");
    await user.type(screen.getByLabelText("Description"), "Some detail");
    await user.click(screen.getByRole("button", { name: "Add card" }));

    expect(onSubmit).toHaveBeenCalledWith({
      title: "New card",
      description: "Some detail",
    });
    expect(onClose).toHaveBeenCalled();
  });

  it("surfaces a server error instead of closing", async () => {
    const user = userEvent.setup();
    const onSubmit = jest.fn().mockRejectedValue(new Error("Unknown status 'nowhere'."));
    const onClose = jest.fn();
    render(<TicketFormModal card={null} onSubmit={onSubmit} onClose={onClose} />);

    await user.type(screen.getByLabelText("Title"), "Doomed");
    await user.click(screen.getByRole("button", { name: "Add card" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Unknown status");
    expect(onClose).not.toHaveBeenCalled();
  });

  it("shows Save changes when editing an existing card", () => {
    setup({ card: { id: "1", title: "Existing", description: "detail" } });

    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
    expect(screen.getByLabelText("Title")).toHaveValue("Existing");
  });

  it("closes without submitting when cancelled", async () => {
    const user = userEvent.setup();
    const { onSubmit, onClose } = setup();

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalled();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
