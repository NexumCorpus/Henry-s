import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vercel-optimized Vite configuration
export default defineConfig({
  plugins: [react()],
  
  // Build configuration optimized for Vercel
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable sourcemaps in production for smaller bundle
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor chunks for better caching
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          redux: ['@reduxjs/toolkit', 'react-redux'],
          ui: ['@mui/material', '@emotion/react', '@emotion/styled'],
        }
      }
    },
    // Optimize chunk size for Vercel
    chunkSizeWarningLimit: 1000,
  },
  
  // Development server configuration
  server: {
    port: 3000,
    host: true, // Allow external connections
    proxy: {
      // Proxy API calls to backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      }
    }
  },
  
  // Preview server configuration
  preview: {
    port: 3000,
    host: true,
  },
  
  // Environment variables
  define: {
    // Ensure environment variables are available at build time
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
  
  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@reduxjs/toolkit',
      'react-redux',
      'axios'
    ]
  },
  
  // Base URL for assets (Vercel handles this automatically)
  base: '/',
  
  // Enable CSS code splitting
  css: {
    devSourcemap: true,
  }
})