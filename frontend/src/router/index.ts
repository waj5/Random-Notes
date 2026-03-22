import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Login from '../views/Login.vue'
import Home from '../views/Home.vue'
import Dynamic from '../views/Dynamic.vue'
import MyNotes from '../views/MyNotes.vue'
import UserSpace from '../views/UserSpace.vue'
import AlbumDetail from '../views/AlbumDetail.vue'
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
      path: '/dynamic',
      name: 'dynamic',
      component: Dynamic,
      meta: { requiresAuth: true }
    },
    {
      path: '/mine',
      name: 'mine',
      component: MyNotes,
      meta: { requiresAuth: true }
    },
    {
      path: '/space/:userId',
      name: 'user-space',
      component: UserSpace,
      meta: { requiresAuth: true }
    },
    {
      path: '/album/:id',
      name: 'album-detail',
      component: AlbumDetail,
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
      component: NoteDetail
    }
  ]
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  if (!authStore.initialized) {
    await authStore.initialize()
  }
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
