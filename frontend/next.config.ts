import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produce a minimal self-contained server build (.next/standalone)
  // for a small Docker image on Railway.
  output: "standalone",
};

export default nextConfig;
