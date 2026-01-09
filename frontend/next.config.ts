import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:5000/api/:path*',
      },
      {
         // Proxy auth routes if they are used
        source: '/auth/:path*',
        destination: 'http://127.0.0.1:5000/auth/:path*',
      },
      {
        // Proxy health check
        source: '/health',
        destination: 'http://127.0.0.1:5000/health',
      },
      {
        // Proxy Swagger UI JSON
        source: '/static/swagger.json',
        destination: 'http://127.0.0.1:5000/static/swagger.json',
      }
    ];
  },
};

export default nextConfig;
