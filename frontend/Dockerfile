FROM node:22-alpine AS build
WORKDIR /app
ARG VITE_RELEASE_ID=dev-local
ENV VITE_RELEASE_ID=$VITE_RELEASE_ID
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
