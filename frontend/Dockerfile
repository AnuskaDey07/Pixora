# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM alpine:3.20 AS runtime
COPY --from=build /app/dist /staging
CMD ["sh", "-c", "rm -rf /out/* && cp -r /staging/. /out/ && echo 'build copied to /out' && ls -la /out"]
