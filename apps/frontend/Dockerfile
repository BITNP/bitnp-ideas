FROM node:24-alpine AS build
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY packages ./packages
COPY apps/frontend ./apps/frontend
RUN corepack enable && pnpm install --frozen-lockfile=false
RUN pnpm --filter @bitnp-ideas/frontend build

FROM nginx:1.29-alpine
COPY apps/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/frontend/dist /usr/share/nginx/html
EXPOSE 80

