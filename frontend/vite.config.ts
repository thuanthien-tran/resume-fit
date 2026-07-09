import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const extraAllowedHosts = (process.env.VITE_ALLOWED_HOSTS || '')
  .split(',')
  .map((host) => host.trim())
  .filter(Boolean);

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: [
      'resumematching-alb-1223673352.us-east-1.elb.amazonaws.com',
      ...extraAllowedHosts,
    ],
  },
});
