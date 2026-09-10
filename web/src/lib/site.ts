// The single place the site's identity lives; the naming pass changes these three lines.
export const SITE = {
  name: "ai-tracker",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://ai-tracker.vercel.app",
  description: "How fast AI value moves through the diffusion stages, and who keeps it. Every number traces to a dated, graded observation.",
};
