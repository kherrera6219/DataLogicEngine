# Frontend Dockerfile
FROM node:24-alpine AS base
ARG NPM_VERSION=11.14.1
RUN npm install -g npm@${NPM_VERSION} && npm cache clean --force

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
# The npm "postinstall" runs scripts/patch-electron-builder.mjs (a no-op off
# Windows), so the scripts dir must exist before `npm ci` or the install fails
# with "Cannot find module .../patch-electron-builder.mjs".
COPY frontend/scripts ./scripts
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
# next.config.ts resolves the repository version authority one level above /app.
COPY config/product-versions.json /config/product-versions.json
# Disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
