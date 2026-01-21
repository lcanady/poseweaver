/** @type {import('next').NextConfig} */
import path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const nextConfig = {
  output: 'standalone',
  // Fix for "Next.js inferred your workspace root" warning
  // pointing to the root package-lock.json
  outputFileTracingRoot: path.join(__dirname, '../'),
  allowedDevOrigins: [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000',
    'http://192.168.12.123:3000',
    'https://poseweaver.com'
  ],
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
  webpack: (config) => {
    // Add path aliases for more robust module resolution using absolute paths
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname),
      '@/lib': path.resolve(__dirname, 'lib'),
      '@/components': path.resolve(__dirname, 'components'),
      '@/utils': path.resolve(__dirname, 'utils'),
      '@/contexts': path.resolve(__dirname, 'contexts'),
      '@/hooks': path.resolve(__dirname, 'hooks')
    };
    return config;
  },
}

export default nextConfig
