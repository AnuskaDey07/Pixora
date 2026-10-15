# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

COPY . .

# Cache-bust: changing CACHE_BUST forces Docker to re-run the build step,
# which prevents stale `dist/` from being served after a source edit.
# Pass a unique value (e.g. timestamp) from Compose or the CLI:
#     docker compose build --build-arg CACHE_BUST=$(date +%s) frontend
ARG CACHE_BUST=1
RUN echo "cache-bust: $CACHE_BUST" && npm run build

FROM alpine:3.20 AS runtime
COPY --from=build /app/dist /staging
CMD ["sh", "-c", "rm -rf /out/* && cp -r /staging/. /out/ && echo 'build copied to /out' && ls -la /out"]
