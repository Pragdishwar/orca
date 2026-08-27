# Build Stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package configurations
COPY package.json package-lock.json ./

# Install dependencies cleanly
RUN npm ci

# Copy the rest of the frontend application
COPY . .

# Build the Vite SPA
RUN npm run build

# Production Stage (Nginx)
FROM nginx:alpine

# Copy built assets to Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Optional: Add custom nginx configuration for SPA routing
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
