<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpen, ChevronDown, FileText, Heart, Images, LogOut, Plus, Settings, UserRound } from 'lucide-vue-next'
import { useNotesStore } from '../stores/notes'
import { useAuthStore } from '../stores/auth'
import NoteCard from '../components/NoteCard.vue'

type MyTab = 'posts' | 'activity' | 'albums' | 'favorites'
type MyFilter = 'all' | 'published' | 'draft'

const route = useRoute()
const router = useRouter()
const notesStore = useNotesStore()
const authStore = useAuthStore()

const notes = computed(() => notesStore.myNotes)
const user = computed(() => authStore.user)
const publishedCount = computed(() => notes.value.filter(note => note.status === 'published').length)
const draftCount = computed(() => notes.value.filter(note => note.status !== 'published').length)
const imageCount = computed(() => notes.value.reduce((total, note) => total + note.blocks.reduce((sum, block) => sum + block.images.length, 0), 0))
const activeTab = ref<MyTab>('posts')
const activeFilter = ref<MyFilter>('all')
const profileOpen = ref(false)
const profileMenuOpen = ref(false)
const profileForm = ref({
  nickname: '',
  phone: '',
  email: '',
  avatar_url: '',
  profile_background_url: '',
  current_password: '',
  new_password: '',
})
const profileSaving = ref(false)
const profileMessage = ref('')

const validTabs: MyTab[] = ['posts', 'activity', 'albums', 'favorites']
const validFilters: MyFilter[] = ['all', 'published', 'draft']

const syncStateFromRoute = () => {
  const tab = route.query.tab
  const filter = route.query.filter

  activeTab.value = typeof tab === 'string' && validTabs.includes(tab as MyTab)
    ? tab as MyTab
    : 'posts'

  activeFilter.value = typeof filter === 'string' && validFilters.includes(filter as MyFilter)
    ? filter as MyFilter
    : 'all'
}

const syncRouteFromState = () => {
  router.replace({
    path: '/mine',
    query: {
      tab: activeTab.value,
      filter: activeFilter.value,
    },
  })
}

const setTab = (tab: MyTab) => {
  activeTab.value = tab
  if (tab !== 'posts') {
    activeFilter.value = 'all'
  }
  syncRouteFromState()
}

const setFilter = (filter: MyFilter) => {
  activeFilter.value = filter
  syncRouteFromState()
}

const filteredNotes = computed(() => {
  if (activeFilter.value === 'published') {
    return notes.value.filter(note => note.status === 'published')
  }
  if (activeFilter.value === 'draft') {
    return notes.value.filter(note => note.status !== 'published')
  }
  return notes.value
})

const publishedNotes = computed(() => notes.value.filter(note => note.status === 'published'))

const albumItems = computed(() =>
  notes.value
    .map(note => {
      const images = note.blocks.flatMap(block => block.images)
      return {
        id: note.id,
        noteId: note.id,
        title: note.title || '无题',
        images,
        imageCount: images.length,
      }
    })
    .filter(item => item.imageCount > 0)
)

const headerBackgroundStyle = computed(() => (
  user.value?.profile_background_url
    ? {
        backgroundImage: `linear-gradient(rgba(255,255,255,0.08), rgba(255,255,255,0.08)), url(${user.value.profile_background_url})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    : {}
))

const openProfile = () => {
  profileForm.value = {
    nickname: user.value?.nickname || '',
    phone: user.value?.phone || '',
    email: user.value?.email || '',
    avatar_url: user.value?.avatar_url || '',
    profile_background_url: user.value?.profile_background_url || '',
    current_password: '',
    new_password: '',
  }
  profileMessage.value = ''
  profileMenuOpen.value = false
  profileOpen.value = true
}

const saveProfile = async () => {
  profileSaving.value = true
  profileMessage.value = ''
  try {
    await authStore.updateProfile(profileForm.value)
    profileMessage.value = '资料已更新'
    profileForm.value.current_password = ''
    profileForm.value.new_password = ''
  } catch (error: any) {
    profileMessage.value = error.response?.data?.detail || error.response?.data?.message || error.message || '更新失败'
  } finally {
    profileSaving.value = false
  }
}

const logout = async () => {
  profileMenuOpen.value = false
  await authStore.logout()
  router.push('/login')
}

const handleWindowClick = () => {
  profileMenuOpen.value = false
}

onMounted(async () => {
  window.addEventListener('click', handleWindowClick)
  syncStateFromRoute()
  await notesStore.fetchMyNotes()
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleWindowClick)
})

watch(() => route.query, () => {
  syncStateFromRoute()
})
</script>

<template>
  <div class="min-h-screen bg-[#f6f7fb] font-sans">
    <div class="sticky top-0 z-30 border-b border-white/60 bg-white/85 backdrop-blur-xl">
      <div class="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 md:px-6">
        <div class="flex items-center gap-8">
          <button class="text-2xl font-black tracking-tight text-sky-500">随心记</button>
          <nav class="hidden items-center gap-6 text-sm text-slate-600 md:flex">
            <button @click="router.push('/')" class="hover:text-sky-500">首页</button>
            <button @click="router.push('/dynamic')" class="hover:text-sky-500">动态</button>
            <button class="font-semibold text-slate-900">我的</button>
          </nav>
        </div>

        <div class="flex items-center gap-3">
          <button
            @click="router.push('/create')"
            class="flex items-center gap-2 rounded-full bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(14,165,233,0.28)] transition-colors hover:bg-sky-600"
          >
            <Plus :size="18" />
            <span>新建笔记</span>
          </button>
          <div class="relative" @click.stop>
            <button
              @click="profileMenuOpen = !profileMenuOpen"
              class="flex h-11 items-center gap-2 rounded-full border border-slate-200 bg-white pl-1 pr-3 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:border-sky-300 hover:text-sky-500"
            >
              <div v-if="user?.avatar_url" class="h-9 w-9 overflow-hidden rounded-full bg-slate-100">
                <img :src="user.avatar_url" class="h-full w-full object-cover" />
              </div>
              <div v-else class="flex h-9 w-9 items-center justify-center rounded-full bg-sky-50 text-sm font-bold text-sky-500">
                {{ (user?.nickname || user?.username || '我').slice(0, 1) }}
              </div>
              <ChevronDown :size="16" />
            </button>

            <div
              v-if="profileMenuOpen"
              class="absolute right-0 top-14 z-40 w-48 rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_18px_40px_rgba(56,84,130,0.12)]"
            >
              <button
                @click="openProfile"
                class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-600 transition-colors hover:bg-sky-50 hover:text-sky-500"
              >
                <Settings :size="16" />
                <span>个人中心</span>
              </button>
              <button
                @click="logout"
                class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-red-500 transition-colors hover:bg-red-50"
              >
                <LogOut :size="16" />
                <span>退出登录</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-[1500px] px-4 py-6">
      <section class="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_18px_40px_rgba(56,84,130,0.08)]">
        <div class="h-48 bg-[linear-gradient(120deg,#67d6ff_0%,#90b8ff_40%,#f4c8ff_100%)]" :style="headerBackgroundStyle"></div>
        <div class="px-6 pb-6">
          <div class="-mt-14 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div class="flex items-end gap-4">
              <div v-if="user?.avatar_url" class="h-28 w-28 overflow-hidden rounded-full border-4 border-white bg-white shadow-lg">
                <img :src="user.avatar_url" class="h-full w-full object-cover" />
              </div>
              <div v-else class="flex h-28 w-28 items-center justify-center rounded-full border-4 border-white bg-white text-3xl font-bold text-sky-500 shadow-lg">
                {{ (user?.nickname || user?.username || '我').slice(0, 1) }}
              </div>
              <div class="pb-2">
                <h1 class="text-3xl font-bold text-slate-900">{{ user?.nickname || user?.username || '我的空间' }}</h1>
                <p class="mt-2 text-sm text-slate-500">这里只展示你自己的内容，草稿和已发布都会保留在这里。</p>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-6 rounded-3xl border border-white/30 bg-white/15 px-5 py-4 text-center backdrop-blur-md">
              <div>
                <div class="text-2xl font-bold text-slate-900">{{ notes.length }}</div>
                <div class="mt-1 text-xs text-slate-400">全部动态</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-slate-900">{{ publishedCount }}</div>
                <div class="mt-1 text-xs text-slate-400">已发布</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-slate-900">{{ imageCount }}</div>
                <div class="mt-1 text-xs text-slate-400">图片数</div>
              </div>
            </div>
          </div>

          <div class="mt-6 flex flex-wrap items-center gap-3 border-b border-slate-100 pb-4 text-sm">
            <button
              @click="setTab('posts')"
              class="px-1 pb-2 transition-colors"
              :class="activeTab === 'posts' ? 'rounded-full border-b-2 border-sky-500 font-semibold text-sky-500' : 'text-slate-500 hover:text-sky-500'"
            >
              投稿
            </button>
            <button
              @click="setTab('activity')"
              class="px-1 pb-2 transition-colors"
              :class="activeTab === 'activity' ? 'rounded-full border-b-2 border-sky-500 font-semibold text-sky-500' : 'text-slate-500 hover:text-sky-500'"
            >
              动态
            </button>
            <button
              @click="setTab('albums')"
              class="px-1 pb-2 transition-colors"
              :class="activeTab === 'albums' ? 'rounded-full border-b-2 border-sky-500 font-semibold text-sky-500' : 'text-slate-500 hover:text-sky-500'"
            >
              相册
            </button>
            <button
              @click="setTab('favorites')"
              class="px-1 pb-2 transition-colors"
              :class="activeTab === 'favorites' ? 'rounded-full border-b-2 border-sky-500 font-semibold text-sky-500' : 'text-slate-500 hover:text-sky-500'"
            >
              收藏
            </button>
          </div>
        </div>
      </section>

      <div class="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <main class="space-y-5">
          <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div v-if="activeTab === 'posts'" class="flex items-center gap-3">
                <button
                  @click="setFilter('all')"
                  class="rounded-full px-4 py-2 text-sm font-semibold transition-colors"
                  :class="activeFilter === 'all' ? 'bg-sky-500 text-white' : 'bg-slate-100 text-slate-600'"
                >
                  全部
                </button>
                <button
                  @click="setFilter('published')"
                  class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                  :class="activeFilter === 'published' ? 'bg-sky-500 text-white' : 'bg-slate-100 text-slate-600'"
                >
                  已发布 {{ publishedCount }}
                </button>
                <button
                  @click="setFilter('draft')"
                  class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                  :class="activeFilter === 'draft' ? 'bg-sky-500 text-white' : 'bg-slate-100 text-slate-600'"
                >
                  草稿 {{ draftCount }}
                </button>
              </div>
              <div v-else class="text-sm font-medium text-slate-500">
                {{
                  activeTab === 'activity'
                    ? `已发布动态 ${publishedCount}`
                    : activeTab === 'albums'
                      ? `相册数量 ${albumItems.length}`
                      : '收藏内容'
                }}
              </div>
              <button
                @click="router.push('/create')"
                class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:border-sky-300 hover:text-sky-500"
              >
                新增随笔
              </button>
            </div>
          </section>

          <div v-if="activeTab === 'posts' && filteredNotes.length > 0" class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            <NoteCard v-for="note in filteredNotes" :key="note.id" :note="note" show-delete />
          </div>

          <div v-else-if="activeTab === 'activity' && publishedNotes.length > 0" class="space-y-4">
            <NoteCard v-for="note in publishedNotes" :key="note.id" :note="note" variant="feed" />
          </div>

          <div v-else-if="activeTab === 'albums' && albumItems.length > 0" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <button
              v-for="item in albumItems"
              :key="item.id"
              @click="router.push({ path: `/album/${item.noteId}`, query: { source: 'mine' } })"
              class="group overflow-hidden rounded-3xl border border-slate-200 bg-white text-left shadow-[0_18px_40px_rgba(56,84,130,0.06)] transition-transform hover:-translate-y-1"
            >
              <div class="grid aspect-square grid-cols-2 gap-1 overflow-hidden bg-slate-100 p-1">
                <div
                  v-for="(src, index) in item.images.slice(0, 4)"
                  :key="`${item.id}-${index}`"
                  class="overflow-hidden rounded-2xl bg-slate-100"
                  :class="item.images.length === 1 ? 'col-span-2' : ''"
                >
                  <img :src="src" class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
                </div>
              </div>
              <div class="p-4">
                <p class="line-clamp-1 text-sm font-semibold text-slate-800">{{ item.title }}</p>
                <p class="mt-1 text-xs text-slate-400">{{ item.imageCount }} 张图片</p>
              </div>
            </button>
          </div>

          <div v-else class="rounded-3xl border border-slate-200 bg-white px-8 py-24 text-center text-gray-400 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            <button
              @click="router.push('/create')"
              class="mb-6 mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-sky-50 text-sky-400 transition-colors hover:bg-sky-100"
            >
              <Plus :size="40" stroke-width="2" />
            </button>
            <p class="mb-2 text-xl font-bold text-gray-800">
              {{
                activeTab === 'favorites'
                  ? '还没有收藏内容'
                  : activeTab === 'albums'
                    ? '还没有相册内容'
                    : activeTab === 'activity'
                      ? '还没有已发布动态'
                      : '这里是我的空间'
              }}
            </p>
            <p class="text-sm text-gray-500">
              {{
                activeTab === 'favorites'
                  ? '收藏功能还没接后端，先给你做了可切换的页面状态'
                  : activeTab === 'albums'
                    ? '发布带图片的内容后，这里会自动聚合展示'
                    : activeTab === 'activity'
                      ? '发布后，这里会展示你自己的公开动态'
                      : '只有你自己能看到未发布和已发布的全部内容'
              }}
            </p>
            <button
              v-if="activeTab !== 'favorites'"
              @click="router.push('/create')"
              class="mt-5 rounded-full bg-sky-500 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-sky-600"
            >
              新增随笔
            </button>
          </div>
        </main>

        <aside class="space-y-5">
          <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            <h2 class="mb-4 text-base font-bold text-slate-900">创作数据</h2>
            <div class="space-y-3">
              <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <div class="flex items-center gap-3 text-slate-600">
                  <FileText :size="18" class="text-sky-500" />
                  <span class="text-sm">草稿数量</span>
                </div>
                <span class="text-sm font-semibold text-slate-900">{{ draftCount }}</span>
              </div>
              <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <div class="flex items-center gap-3 text-slate-600">
                  <BookOpen :size="18" class="text-sky-500" />
                  <span class="text-sm">发布数量</span>
                </div>
                <span class="text-sm font-semibold text-slate-900">{{ publishedCount }}</span>
              </div>
              <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <div class="flex items-center gap-3 text-slate-600">
                  <Images :size="18" class="text-sky-500" />
                  <span class="text-sm">累计图片</span>
                </div>
                <span class="text-sm font-semibold text-slate-900">{{ imageCount }}</span>
              </div>
            </div>
          </section>

          <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            <h2 class="mb-4 text-base font-bold text-slate-900">个人资料</h2>
            <div class="space-y-3 text-sm text-slate-500">
              <div class="flex items-center justify-between">
                <span>昵称</span>
                <span class="font-medium text-slate-800">{{ user?.nickname || '-' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span>用户名</span>
                <span class="font-medium text-slate-800">{{ user?.username || '-' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span>手机号</span>
                <span class="font-medium text-slate-800">{{ user?.phone || '-' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span>偏好</span>
                <span class="flex items-center gap-1 font-medium text-pink-500">
                  <Heart :size="14" />
                  <span>随心记录</span>
                </span>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="profileOpen" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/45 p-4" @click="profileOpen = false">
        <div class="w-full max-w-xl rounded-[28px] bg-white p-6 shadow-2xl" @click.stop>
          <div class="mb-5 flex items-center gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-full bg-sky-50 text-sky-500">
              <UserRound :size="20" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-slate-900">个人中心</h2>
              <p class="text-sm text-slate-400">修改昵称、联系方式和密码</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <input v-model="profileForm.nickname" type="text" placeholder="昵称" class="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400" />
            <input v-model="profileForm.phone" type="tel" placeholder="手机号" class="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400" />
            <input v-model="profileForm.email" type="email" placeholder="邮箱" class="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400 sm:col-span-2" />
            <input v-model="profileForm.avatar_url" type="text" placeholder="头像链接" class="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400 sm:col-span-2" />
            <input v-model="profileForm.profile_background_url" type="text" placeholder="顶部背景链接" class="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400 sm:col-span-2" />
            <input v-model="profileForm.current_password" type="password" placeholder="当前密码（修改密码时必填）" class="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400 sm:col-span-2" />
            <input v-model="profileForm.new_password" type="password" placeholder="新密码" class="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400 sm:col-span-2" />
          </div>

          <p v-if="profileMessage" class="mt-4 text-sm" :class="profileMessage === '资料已更新' ? 'text-emerald-500' : 'text-red-500'">
            {{ profileMessage }}
          </p>

          <div class="mt-6 flex justify-end gap-3">
            <button @click="profileOpen = false" class="rounded-full bg-slate-100 px-5 py-2 text-sm font-medium text-slate-600">
              关闭
            </button>
            <button
              @click="saveProfile"
              :disabled="profileSaving"
              class="rounded-full bg-sky-500 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {{ profileSaving ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
