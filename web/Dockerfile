FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# `output: "standalone"` (next.config.mjs) traces only the deps actually used at runtime,
# so the final image doesn't need node_modules or a package manager at all.
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Cloud Run injects $PORT; default 8080 for local `docker run` parity. Next's standalone
# server.js reads PORT directly (no shell expansion needed).
ENV PORT=8080
EXPOSE 8080
CMD ["node", "server.js"]
