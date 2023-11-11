const { test, expect } = require("@playwright/test");

const OUT = "../docs/screenshots";

test.describe("README screenshots", () => {
  test("board", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("region", { name: "To Do" })).toBeVisible();
    await expect(page.getByText("Remove the committed virtualenv")).toBeVisible();
    await page.screenshot({ path: `${OUT}/board.png` });
  });

  test("card form", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("region", { name: "To Do" })).toBeVisible();
    await page.getByRole("button", { name: "Edit Extract the service layer" }).click();
    await expect(page.getByLabel("Title")).toHaveValue("Extract the service layer");
    await page.screenshot({ path: `${OUT}/edit-card.png` });
  });

  test("validation error", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("region", { name: "To Do" })).toBeVisible();
    await page.getByRole("button", { name: "Add card", exact: true }).click();
    await page.getByRole("button", { name: "Add card", exact: true }).nth(1).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await page.screenshot({ path: `${OUT}/validation.png` });
  });
});
