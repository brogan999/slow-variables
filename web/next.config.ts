import type { NextConfig } from "next";

// React needs eval only in development; production builds run without it.
const DEV = process.env.NODE_ENV !== "production";
const CSP = `default-src 'self'; script-src 'self' 'unsafe-inline'${DEV ? " 'unsafe-eval'" : ""}; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`;

const nextConfig: NextConfig = {
  // the weekly memo was retired on 27 Sep 2026; its old links land on the changelog, which records the same changes
  async redirects() {
    return [{ source: "/memos/:path*", destination: "/changelog", permanent: true }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Content-Security-Policy", value: CSP },
        ],
      },
      { source: "/futures/:path*.webp", headers: [{ key: "Cache-Control", value: "public, max-age=86400, stale-while-revalidate=604800" }] },
      { source: "/data/:path*.csv", headers: [{ key: "Cache-Control", value: "public, max-age=3600, stale-while-revalidate=86400" }] },
    ];
  },
};

export default nextConfig;
