# Step 1: Build the Vite app
FROM node:24-alpine AS build

WORKDIR /app

# Accept environment variable as build argument
ARG VITE_ENV=dev
ENV VITE_ENV=$VITE_ENV

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

# Build the app for the specified Vite mode (e.g. dev, staging, production)
RUN npm run build -- --mode=$VITE_ENV

# Step 2: Serve with nginx
FROM nginx:1.28-alpine

# Copy built assets to nginx's default public folder
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
