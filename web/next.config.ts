import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Route handler handles /api/py/[...path] directly */
  experimental: {
    agentUpgrade: "security",
  },
};

export default nextConfig;
