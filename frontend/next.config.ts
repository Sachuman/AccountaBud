import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://accountabud.ngrok.app/api/:path*',
      },
    ];
  },
};

export default nextConfig;

export const runtimeVersion = 'v2';
