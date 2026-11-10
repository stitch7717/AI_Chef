# 前端多阶段构建：Node 构建 → Nginx 托管静态文件并反代 API
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json .npmrc ./
RUN npm install --no-fund --no-audit
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
