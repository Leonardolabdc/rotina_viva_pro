import type { NextConfig } from "next";

const apiOrigin = (
  process.env.ROTINA_API_URL ||
  process.env.NEXT_PUBLIC_ROTINA_API_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api-proxy/:path*",
        destination: `${apiOrigin}/:path*`,
      },
    ];
  },
};

export default nextConfig;
