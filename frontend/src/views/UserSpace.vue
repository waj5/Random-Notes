<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpen, ChevronDown, FileText, Heart, Images, LogOut, Plus, Settings, UserPlus } from 'lucide-vue-next'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'
import type { Note } from '../stores/notes'
import { useNotesStore } from '../stores/notes'
import NoteCard from '../components/NoteCard.vue'

interface UserProfile {
  id: number
  username: string
  nickname: string
  avatar_url?: string
  profile_background_url?: string
  published_count: number
  image_count: number
  follower_count: number
  is_following: boolean
}

type SpaceTab = 'posts' | 'activity' | 'albums'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notesStore = useNotesStore()

const userId = computed(() => route.params.userId as string)
const profile = ref<UserProfile | null>(null)
const notes = ref<Note[]>([])
const loading = ref(true)
const activeTab = ref<SpaceTab>('posts')
const profileMenuOpen = ref(false)
const validTabs: SpaceTab[] = ['posts', 'activity', 'albums']

const isOwner = computed(() => Number(userId.value) === authStore.user?.id)
const headerBackgroundStyle = computed(() => (
  profile.value?.profile_background_url
    ? {
        backgroundImage: `linear-gradient(rgba(255,255,255,0.08), rgba(255,255,255,0.08)), url(${profile.value.profile_background_url})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    : {}
))
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

const handleWindowClick = () => {
  profileMenuOpen.value = false
}

const syncStateFromRoute = () => {
  const tab = route.query.tab
  activeTab.value = typeof tab === 'string' && validTabs.includes(tab as SpaceTab)
    ? tab as SpaceTab
    : 'posts'
}

const setTab = (tab: SpaceTab) => {
  activeTab.value = tab
  router.replace({
    path: `/space/${userId.value}`,
    query: {
      tab,
    },
  })
}

const loadData = async () => {
  loading.value = true
  try {
    const [profileResponse, notesResponse] = await Promise.all([
      apiClient.get(`/auth/users/${userId.value}/public`),
      apiClient.get(`/notes/public/user/${userId.value}`, { params: { limit: 100 } }),
    ])
    profile.value = profileResponse.data.data
    notes.value = notesResponse.data.data.items.map((n: any) => notesStore.mapNoteSummary(n))
  } finally {
    loading.value = false
  }
}

const toggleFollow = async () => {
  if (!profile.value || isOwner.value) return
  if (profile.value.is_following) {
    await authStore.unfollowUser(profile.value.id)
    profile.value.is_following = false
    profile.value.follower_count = Math.max(0, profile.value.follower_count - 1)
    return
  }
  await authStore.followUser(profile.value.id)
  profile.value.is_following = true
  profile.value.follower_count += 1
}

const logout = async () => {
  profileMenuOpen.value = false
  await authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  window.addEventListener('click', handleWindowClick)
  syncStateFromRoute()
  await loadData()
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleWindowClick)
})

watch(() => route.query.tab, () => {
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
            <button @click="router.push('/mine')" class="hover:text-sky-500">我的</button>
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
              <div v-if="authStore.user?.avatar_url" class="h-9 w-9 overflow-hidden rounded-full bg-slate-100">
                <img :src="authStore.user.avatar_url" class="h-full w-full object-cover" />
              </div>
              <div v-else class="flex h-9 w-9 items-center justify-center rounded-full bg-sky-50 text-sm font-bold text-sky-500">
                {{ (authStore.user?.nickname || authStore.user?.username || '我').slice(0, 1) }}
              </div>
              <ChevronDown :size="16" />
            </button>

            <div
              v-if="profileMenuOpen"
              class="absolute right-0 top-14 z-40 w-48 rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_18px_40px_rgba(56,84,130,0.12)]"
            >
              <button
                @click="router.push('/mine')"
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
      <section v-if="profile" class="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_18px_40px_rgba(56,84,130,0.08)]">
        <div class="h-48 bg-[linear-gradient(120deg,#67d6ff_0%,#90b8ff_40%,#f4c8ff_100%)]" :style="headerBackgroundStyle"></div>
        <div class="px-6 pb-6">
          <div class="-mt-14 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div class="flex items-end gap-4">
              <div v-if="profile.avatar_url" class="h-28 w-28 overflow-hidden rounded-full border-4 border-white bg-white shadow-lg">
                <img :src="profile.avatar_url" class="h-full w-full object-cover" />
              </div>
              <div v-else class="flex h-28 w-28 items-center justify-center rounded-full border-4 border-white bg-white text-3xl font-bold text-sky-500 shadow-lg">
                {{ (profile.nickname || profile.username || 'Ta').slice(0, 1) }}
              </div>
              <div class="pb-2">
                <h1 class="text-3xl font-bold text-slate-900">{{ profile.nickname || profile.username }}</h1>
                <p class="mt-2 text-sm text-slate-500">这里只展示对方已经发布的公开内容。</p>
              </div>
            </div>

            <div class="flex items-center gap-4">
              <div class="grid grid-cols-3 gap-6 rounded-3xl border border-white/30 bg-white/15 px-5 py-4 text-center backdrop-blur-md">
                <div>
                  <div class="text-2xl font-bold text-slate-900">{{ notes.length }}</div>
                  <div class="mt-1 text-xs text-slate-400">全部动态</div>
                </div>
                <div>
                  <div class="text-2xl font-bold text-slate-900">{{ profile.published_count }}</div>
                  <div class="mt-1 text-xs text-slate-400">已发布</div>
                </div>
                <div>
                  <div class="text-2xl font-bold text-slate-900">{{ profile.image_count }}</div>
                  <div class="mt-1 text-xs text-slate-400">图片数</div>
                </div>
              </div>

              <button
                v-if="!isOwner"
                @click="toggleFollow"
                class="rounded-full px-5 py-2.5 text-sm font-semibold transition-colors"
                :class="profile.is_following ? 'bg-slate-100 text-slate-600 hover:bg-slate-200' : 'bg-sky-500 text-white hover:bg-sky-600'"
              >
                {{ profile.is_following ? '已关注' : '关注' }}
              </button>
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
          </div>
        </div>
      </section>

      <div class="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <main class="space-y-5">
          <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div class="text-sm font-medium text-slate-500">
                {{
                  activeTab === 'activity'
                    ? `已发布动态 ${profile?.published_count || 0}`
                    : activeTab === 'albums'
                      ? `相册数量 ${albumItems.length}`
                      : `公开内容 ${notes.length}`
                }}
              </div>
              <button
                @click="router.push('/mine')"
                class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:border-sky-300 hover:text-sky-500"
              >
                返回我的空间
              </button>
            </div>
          </section>

          <div v-if="loading" class="rounded-3xl border border-slate-200 bg-white px-8 py-24 text-center text-gray-400 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            加载中...
          </div>

          <div v-else-if="activeTab === 'posts' && notes.length > 0" class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            <NoteCard v-for="note in notes" :key="note.id" :note="note" />
          </div>

          <div v-else-if="activeTab === 'activity' && notes.length > 0" class="space-y-4">
            <NoteCard v-for="note in notes" :key="note.id" :note="note" variant="feed" />
          </div>

          <div v-else-if="activeTab === 'albums' && albumItems.length > 0" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <button
              v-for="item in albumItems"
              :key="item.id"
              @click="router.push({ path: `/album/${item.noteId}`, query: { source: 'space', userId: userId } })"
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
            <div class="mb-6 mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-sky-50 text-sky-400">
              <UserPlus :size="40" stroke-width="2" />
            </div>
            <p class="mb-2 text-xl font-bold text-gray-800">
              {{ activeTab === 'albums' ? '还没有相册内容' : '还没有公开内容' }}
            </p>
            <p class="text-sm text-gray-500">对方暂时还没有可展示的公开内容</p>
          </div>
        </main>

        <aside class="space-y-5">
          <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            <h2 class="mb-4 text-base font-bold text-slate-900">空间数据</h2>
            <div class="space-y-3">
              <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <div class="flex items-center gap-3 text-slate-600">
                  <FileText :size="18" class="text-sky-500" />
                  <span class="text-sm">已发布随笔</span>
                </div>
                <span class="text-sm font-semibold text-slate-900">{{ profile?.published_count || 0 }}</span>
              </div>
              <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <div class="flex items-center gap-3 text-slate-600">
                  <BookOpen :size="18" class="text-sky-500" />
                  <span class="text-sm">粉丝数量</span>
                </div>
                <span class="text-sm font-semibold text-slate-900">{{ profile?.follower_count || 0 }}</span>
              </div>
              <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <div class="flex items-center gap-3 text-slate-600">
                  <Images :size="18" class="text-sky-500" />
                  <span class="text-sm">累计图片</span>
                </div>
                <span class="text-sm font-semibold text-slate-900">{{ profile?.image_count || 0 }}</span>
              </div>
            </div>
          </section>

          <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
            <h2 class="mb-4 text-base font-bold text-slate-900">个人资料</h2>
            <div class="space-y-3 text-sm text-slate-500">
              <div class="flex items-center justify-between">
                <span>昵称</span>
                <span class="font-medium text-slate-800">{{ profile?.nickname || '-' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span>用户名</span>
                <span class="font-medium text-slate-800">{{ profile?.username || '-' }}</span>
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
  </div>
</template>
