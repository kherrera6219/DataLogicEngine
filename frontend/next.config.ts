import type { NextConfig } from "next";

const cdnUrl = process.env.NEXT_PUBLIC_CDN_URL ?? process.env.CDN_URL ?? "";
const normalizedCdnUrl = cdnUrl ? cdnUrl.replace(/\/$/, "") : "";

const cdnConfig: Pick<NextConfig, "assetPrefix" | "images"> = {};

if (normalizedCdnUrl) {
  cdnConfig.assetPrefix = normalizedCdnUrl;

  try {
    const cdn = new URL(normalizedCdnUrl);
    cdnConfig.images = {
      remotePatterns: [
        {
          protocol: cdn.protocol.replace(":", ""),
          hostname: cdn.hostname,
          port: cdn.port || undefined,
          pathname: "/**",
        },
      ],
    };
  } catch {
    cdnConfig.images = undefined;
  }
}

const nextConfig: NextConfig = {
  ...cdnConfig,
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
