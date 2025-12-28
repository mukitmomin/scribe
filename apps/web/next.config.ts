import type { NextConfig } from 'next';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  transpilePackages: ['@scribe/types', '@scribe/ui'],
  async rewrites() {
    return [
      {
        source: '/api/v1/papers/:path*',
        destination: `${BACKEND_URL}/api/v1/papers/:path*`,
      },
      {
        source: '/api/v1/chat/sessions/:path*',
        destination: `${BACKEND_URL}/api/v1/chat/sessions/:path*`,
      },
      {
        source: '/api/v1/chat/session/:path*',
        destination: `${BACKEND_URL}/api/v1/chat/session/:path*`,
      },
      {
        source: '/api/v1/scribe/:path*',
        destination: `${BACKEND_URL}/api/v1/scribe/:path*`,
      },
    ];
  },
};

export default nextConfig;
