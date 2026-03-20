FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

# 接收构建参数并注入到环境
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY . .
RUN npm run build

# 生产镜像
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 启动时替换 PORT（Railway 动态分配）
CMD sh -c "sed -i 's/listen 80/listen '${PORT:-80}'/g' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
