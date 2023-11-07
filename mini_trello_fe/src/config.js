/**
 * Runtime configuration.
 *
 * Create React App inlines REACT_APP_* variables at build time. The URL was
 * previously hardcoded to http://localhost:8001/graphql, so a build could only
 * ever talk to a developer's laptop.
 */
export const GRAPHQL_URL =
  process.env.REACT_APP_GRAPHQL_URL || "http://localhost:8001/graphql";
