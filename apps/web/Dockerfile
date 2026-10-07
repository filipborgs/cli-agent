FROM node:24-bookworm-slim AS development
WORKDIR /workspace
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN corepack pnpm install --frozen-lockfile
COPY apps/web apps/web
WORKDIR /workspace/apps/web
CMD ["corepack", "pnpm", "dev", "--host", "0.0.0.0", "--port", "8080"]

FROM development AS build
RUN corepack pnpm build

FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html
EXPOSE 8080
