import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './assets/main.css'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useNovelDrafts } from './stores/novelDrafts'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const authStore = useAuthStore(pinia)
authStore.initialize().finally(() => {
  useNovelDrafts(pinia)
  app.use(router)
  app.mount('#app')
})

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  void navigator.serviceWorker.register(`${import.meta.env.BASE_URL}novel-offline.js`).catch((error) => {
    console.warn('Could not enable offline novel access', error)
  })
}
