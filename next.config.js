
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production' 
          ? 'http://localhost:5000/api/:path*'  // In production
          : 'http://localhost:5000/api/:path*', // In development
      },
    ];
  },
}

module.exports = nextConfig
