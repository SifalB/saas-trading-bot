# syntax=docker/dockerfile:1

# ---- build stage ----
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_* vars are inlined into the bundle at build time, so the
# backend URL must be present now (Railway passes service variables as
# build args). Set NEXT_PUBLIC_API_URL in the frontend service on Railway.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ---- runtime stage ----
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Bind to all interfaces so Railway can route to the container.
ENV HOSTNAME=0.0.0.0

# Standalone server + assets it does not bundle by default.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
# server.js reads PORT (Railway sets it) and HOSTNAME from the env.
CMD ["node", "server.js"]
