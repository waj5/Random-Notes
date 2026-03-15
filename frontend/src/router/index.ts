import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Login from '../views/Login.vue'
import Home from '../views/Home.vue'
import NoteEditor from '../views/NoteEditor.vue'
import NoteDetail from '../views/NoteDetail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/',
      name: 'home',
      component: Home,
      meta: { requiresAuth: true }
    },
    {
      path: '/create',
      name: 'create',
      component: NoteEditor,
      meta: { requiresAuth: true }
    },
    {
      path: '/edit/:id',
      name: 'edit',
      component: NoteEditor,
      meta: { requiresAuth: true }
    },
    {
      path: '/note/:id',
      name: 'note-detail',
      component: NoteDetail,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
