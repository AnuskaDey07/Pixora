# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM alpine:3.20 AS runtime
RUN mkdir -p /out
COPY --from=build /app/dist /out
CMD ["sh", "-c", "echo 'frontend build complete' && ls -la /out"]
