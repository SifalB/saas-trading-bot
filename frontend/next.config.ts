import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static HTML/JS export (./out) so the FastAPI backend can serve the
  // frontend from the same instance — one service, same origin, no CORS.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
