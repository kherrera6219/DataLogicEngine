const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Set output to export for better static generation
  output: 'standalone',
  // Transpile specific modules that might cause issues
  transpilePackages: ['d3', 'react-force-graph-2d', 'force-graph'],
  // Add environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://0.0.0.0:5000',
    NEXT_PUBLIC_CORE_UKG_URL: process.env.NEXT_PUBLIC_CORE_UKG_URL || 'http://0.0.0.0:5003',
    NEXT_PUBLIC_APP_NAME: 'Universal Knowledge Graph System',
    NEXT_PUBLIC_VERSION: '1.0.0',
  },
  // Optimize images
  images: {
    unoptimized: process.env.NODE_ENV !== 'production',
  },
  // Improve build optimization
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https:",
              "font-src 'self' data:",
              "connect-src 'self' http://localhost:* http://0.0.0.0:*",
              "frame-ancestors 'self'",
            ].join('; ')
          }
        ],
      },
    ]
  },
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

module.exports = withBundleAnalyzer(nextConfig)
