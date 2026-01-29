import type { NextConfig } from "next";

// Next.js 16 Configuration
// Note: Middleware is handled via root middleware.ts
// Rewrites are used for API proxying to Flask backend

const cdnUrl = process.env.NEXT_PUBLIC_CDN_URL ?? process.env.CDN_URL ?? "";
const normalizedCdnUrl = cdnUrl ? cdnUrl.replace(/\/$/, "") : "";

const cdnConfig: Pick<NextConfig, "assetPrefix" | "images"> = {};

if (normalizedCdnUrl) {
  cdnConfig.assetPrefix = normalizedCdnUrl;

  try {
    const cdn = new URL(normalizedCdnUrl);
    cdnConfig.images = {
      unoptimized: true, // Required for static export
      remotePatterns: [
        {
          protocol: cdn.protocol.replace(":", "") as "http" | "https",
          hostname: cdn.hostname,
          port: cdn.port || '', 
          pathname: "/**",
        },
      ],
    };
  } catch {
    cdnConfig.images = { unoptimized: true };
  }
} else {
  // Even if no CDN, unoptimized is needed for export if usage exists
  cdnConfig.images = { unoptimized: true };
}

const nextConfig: NextConfig = {
  ...cdnConfig,
  ...cdnConfig,
  output: process.env.BUILD_MODE === 'electron' ? 'export' : 'standalone',
  // Rewrites are supported in standalone mode, but not export.
  async rewrites() {
     if (process.env.BUILD_MODE === 'electron') return [];
     return [
       {
         source: '/api/:path*',
         destination: 'http://127.0.0.1:5000/api/:path*',
       },
     ];
  },
};

import withBundleAnalyzer from '@next/bundle-analyzer';

const bundler = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

export default bundler(nextConfig);
