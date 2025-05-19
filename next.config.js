
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://0.0.0.0:5000/api/:path*',
      },
      {
        source: '/model/:path*',
        destination: 'http://0.0.0.0:5002/:path*',
      },
      {
        source: '/webhook/:path*',
        destination: 'http://0.0.0.0:5001/webhooks/:path*',
      },
      {
        source: '/core/:path*',
        destination: 'http://0.0.0.0:5003/:path*',
      },
    ];
  },
}

module.exports = nextConfig
