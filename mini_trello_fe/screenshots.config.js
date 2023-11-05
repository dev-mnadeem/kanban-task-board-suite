// Playwright configuration for the README screenshots.
// Regenerate with: APP_URL=http://localhost:3000 npx playwright test -c screenshots.config.js
module.exports = {
  testDir: "./e2e",
  use: {
    baseURL: process.env.APP_URL || "http://localhost:3000",
    viewport: { width: 1440, height: 900 },
  },
  reporter: "list",
};
