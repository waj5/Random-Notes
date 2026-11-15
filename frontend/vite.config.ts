import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'

// https://vite.dev/config/
const base = (process.env.VITE_BASE || '/').replace(/\/?$/, '/') as `/${string}`

export default defineConfig({
  base,
  plugins: [
    vue(),
    {
      name: 'novel-offline-shell',
      apply: 'build',
      enforce: 'post',
      generateBundle(_, bundle) {
        const assets = Object.keys(bundle).filter(file => /\.(?:js|css)$/.test(file)).sort()
        const worker = readFileSync(new URL('./novel-offline.js', import.meta.url), 'utf8')
        const version = createHash('sha256').update(assets.join('\n')).update(worker).digest('hex').slice(0, 16)
        this.emitFile({
          type: 'asset',
          fileName: 'novel-offline.js',
          source: `const offlineAssets = ${JSON.stringify(assets)}\nconst offlineVersion = '${version}'\n${worker}`,
        })
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
