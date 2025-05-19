/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    // Get the API URLs from environment variables or use defaults
    const apiGatewayUrl = process.env.NEXT_PUBLIC_API_URL || 'http://0.0.0.0:5000';
    const coreUkgUrl = process.env.NEXT_PUBLIC_CORE_UKG_URL || 'http://0.0.0.0:5003';

    return [
      // API Gateway proxy
      {
        source: '/api/:path*',
        destination: `${apiGatewayUrl}/api/:path*`,
      },
      // Webhooks proxy
      {
        source: '/webhooks/:path*',
        destination: `${apiGatewayUrl}/api/webhooks/:path*`,
      },
      // Model context proxy
      {
        source: '/model/:path*',
        destination: `${apiGatewayUrl}/api/model/:path*`,
      },
      // Core UKG service direct access (only used by admin pages)
      {
        source: '/core/:path*',
        destination: `${coreUkgUrl}/:path*`,
      },
    ];
  },
}

module.exports = nextConfig