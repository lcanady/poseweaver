FROM node:18-alpine

WORKDIR /app

# Copy package files first
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm
RUN pnpm install

# Copy source code (excluding node_modules via .dockerignore)
COPY . .

# Expose port
EXPOSE 3000

# Start the development server
CMD ["pnpm", "dev"] 