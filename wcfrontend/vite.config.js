import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:6184', // 您的 Django 后端服务地址
        changeOrigin: true,               // 必须设置为 true
      }
    },
    allowedHosts: [
      'www-www-www.u2202134.nyat.app',
      'localhost',
      '127.0.0.1'// ✅ 允许的主机
    ]
  }
})
