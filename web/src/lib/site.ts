// The single place the site's identity lives; the naming pass changes these three lines.
export const SITE = {
  name: "Slow Variables",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://slowvariables.ai",
  description: "How fast AI value moves through the diffusion stages, and who keeps it. Every number traces to a dated, graded observation.",
  operator: "Alex Brogan",
  repo: "https://github.com/brogan999/slow-variables",
  // The private address for privacy requests and rights notices only; tests/test_legal.py fails while it is empty.
  legalEmail: "",
};
