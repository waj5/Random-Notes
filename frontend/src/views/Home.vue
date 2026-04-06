<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDown, Compass, Flame, LogOut, Plus, Search, Settings, Sparkles } from 'lucide-vue-next'
import { useNotesStore } from '../stores/notes'
import { useAuthStore } from '../stores/auth'
import NoteCard from '../components/NoteCard.vue'
import { noteMatchesQuery } from '../utils/noteSearch'

const router = useRouter()
const notesStore = useNotesStore()
const authStore = useAuthStore()

const notes = computed(() => notesStore.publicNotes)
const trendingNotes = computed(() => notesStore.hotNotes.slice(0, 8))
const searchQuery = ref('')
const filteredNotes = computed(() => {
  const q = searchQuery.value
  if (!q.trim()) return notes.value
  return notes.value.filter((n) => noteMatchesQuery(n, q))
})
const featuredNote = computed(() => {
  const q = searchQuery.value.trim()
  const list = q ? filteredNotes.value : notes.value
  return list[0]
})
const profileMenuOpen = ref(false)

const defaultHeroBgUrl = `${import.meta.env.BASE_URL}home-hero-default.svg`

const heroTitle = computed(() => {
  if (authStore.isAuthenticated && authStore.user) {
    return authStore.user.nickname?.trim() || authStore.user.username || '我'
  }
  return '随心广场'
})

const headerBackgroundStyle = computed(() => {
  const base = {
    backgroundSize: 'cover' as const,
    backgroundPosition: 'center' as const,
  }
  if (authStore.user?.profile_background_url) {
    return {
      ...base,
      backgroundImage: `linear-gradient(rgba(255,255,255,0.08), rgba(255,255,255,0.08)), url(${authStore.user.profile_background_url})`,
    }
  }
  return {
    ...base,
    backgroundImage: `linear-gradient(rgba(255,255,255,0.12), rgba(255,255,255,0.22)), url(${defaultHeroBgUrl})`,
  }
})

const handleWindowClick = () => {
  profileMenuOpen.value = false
}

const promptLogin = () => {
  window.alert('这个功能需要先登录')
  router.push('/login')
}

const goCreate = () => {
  if (!authStore.isAuthenticated) {
    promptLogin()
    return
  }
  router.push('/create')
}

const goDynamic = () => {
  if (!authStore.isAuthenticated) {
    promptLogin()
    return
  }
  router.push('/dynamic')
}

const goMine = () => {
  if (!authStore.isAuthenticated) {
    promptLogin()
    return
  }
  router.push('/mine')
}

const logout = async () => {
  profileMenuOpen.value = false
  await authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  window.addEventListener('click', handleWindowClick)
  const tasks = [
    notesStore.fetchPublicNotes(),
    notesStore.fetchHotNotes(),
  ]
  if (authStore.isAuthenticated) {
    tasks.push(authStore.fetchFollowingIds())
  }
  await Promise.all(tasks)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleWindowClick)
})
</script>

<template>
  <div class="min-h-screen bg-[#dff3f7] font-sans">
    <div class="sticky top-0 z-30 border-b border-white/60 bg-white/80 backdrop-blur-xl">
      <div class="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 md:px-6">
        <div class="flex items-center gap-8">
          <button class="text-2xl font-black tracking-tight text-sky-500">随心记</button>
          <nav class="hidden items-center gap-6 text-sm text-slate-600 md:flex">
            <button class="font-semibold text-slate-900">首页</button>
            <button @click="goDynamic" class="hover:text-sky-500">动态</button>
            <button @click="goMine" class="hover:text-sky-500">我的</button>
          </nav>
        </div>

        <div class="flex items-center gap-3">
          <button
            @click="goCreate"
            class="flex items-center gap-2 rounded-full bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(14,165,233,0.28)] transition-colors hover:bg-sky-600"
          >
            <Plus :size="18" />
            <span>发布动态</span>
          </button>
          <div v-if="authStore.isAuthenticated" class="relative" @click.stop>
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
          <button
            v-else
            @click="router.push('/login')"
            class="rounded-full border border-sky-200 bg-white px-5 py-2.5 text-sm font-semibold text-sky-500 transition-colors hover:border-sky-300 hover:bg-sky-50"
          >
            登录 / 注册
          </button>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-[1500px] px-4 py-6">
      <section class="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_18px_40px_rgba(56,84,130,0.08)]">
        <div class="h-48" :style="headerBackgroundStyle"></div>
        <div class="px-6 pb-6">
          <div class="-mt-14 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div class="flex items-end gap-4">
              <div v-if="authStore.user?.avatar_url" class="h-28 w-28 overflow-hidden rounded-full border-4 border-white bg-white shadow-lg">
                <img :src="authStore.user.avatar_url" class="h-full w-full object-cover" />
              </div>
              <div v-else class="flex h-28 w-28 items-center justify-center rounded-full border-4 border-white bg-white text-3xl font-bold text-sky-500 shadow-lg">
                {{ (authStore.user?.nickname || authStore.user?.username || '客').slice(0, 1) }}
              </div>
              <div class="pb-2">
                <h1 class="text-3xl font-bold text-slate-900">{{ heroTitle }}</h1>
                <p class="mt-2 text-sm text-slate-500">
                  {{
                    authStore.isAuthenticated
                      ? '全站公开动态信息流。关注作者后，在「动态」页查看仅关注内容。'
                      : '浏览全站公开动态；登录后可关注作者、点赞评论与发布。'
                  }}
                </p>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-6 rounded-3xl border border-white/30 bg-white/15 px-5 py-4 text-center backdrop-blur-md">
              <div>
                <div class="text-2xl font-bold text-slate-900">{{ notes.length }}</div>
                <div class="mt-1 text-xs text-slate-400">公开动态</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-slate-900">{{ authStore.followingIds.length }}</div>
                <div class="mt-1 text-xs text-slate-400">关注人数</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-slate-900">{{ trendingNotes.length }}</div>
                <div class="mt-1 text-xs text-slate-400">热门榜单</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="mt-6 grid gap-6 lg:grid-cols-[260px_minmax(0,760px)_300px]">
      <aside class="space-y-4 lg:sticky lg:top-24 lg:h-fit">
        <section class="overflow-hidden rounded-3xl border border-white/60 bg-white/70 shadow-[0_18px_40px_rgba(74,144,164,0.10)] backdrop-blur">
          <div class="bg-gradient-to-br from-sky-300 via-cyan-200 to-white px-5 py-6">
            <div class="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/85 text-sky-500 shadow-sm">
              <Compass :size="26" />
            </div>
            <h2 class="text-lg font-bold text-slate-800">动态广场</h2>
            <p class="mt-2 text-sm leading-6 text-slate-600">本页为全站公开动态；登录可关注作者，在「动态」页看关注流，右侧为热门榜单。</p>
          </div>
          <div class="space-y-3 p-4">
            <button type="button" class="flex w-full cursor-default items-center justify-between rounded-2xl bg-sky-50 px-4 py-3 text-left text-sm font-medium text-sky-600">
              <span>公开信息流</span>
              <Sparkles :size="16" />
            </button>
            <button
              @click="goDynamic"
              class="flex w-full items-center justify-between rounded-2xl bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
            >
              <span>进入关注动态</span>
              <span>></span>
            </button>
          </div>
        </section>

        <section v-if="featuredNote" class="rounded-3xl border border-white/60 bg-white/80 p-4 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Flame :size="16" class="text-orange-500" />
            <span>精选动态</span>
          </div>
          <h3 class="line-clamp-2 text-base font-semibold leading-7 text-slate-900">
            {{ featuredNote.title || '无题动态' }}
          </h3>
          <p class="mt-2 line-clamp-3 text-sm leading-6 text-slate-500">
            {{ featuredNote.summary || '刚刚发布了一条新的公开动态。' }}
          </p>
        </section>
      </aside>

      <main class="space-y-4">
        <div class="rounded-3xl border border-white/60 bg-white/82 px-5 py-4 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div class="flex shrink-0 items-center gap-3">
              <button class="rounded-full bg-sky-500 px-4 py-2 text-sm font-semibold text-white">全部</button>
              <button @click="goDynamic" class="rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600">关注动态</button>
            </div>
            <div class="relative min-w-0 flex-1 sm:max-w-md">
              <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" :size="16" />
              <input
                v-model="searchQuery"
                type="search"
                enterkeyhint="search"
                placeholder="搜索标题、正文、作者…"
                class="w-full rounded-full border border-slate-200 bg-white py-2 pl-9 pr-4 text-sm text-slate-800 placeholder:text-slate-400 shadow-sm outline-none ring-sky-400/0 transition-[box-shadow,border-color] focus:border-sky-300 focus:ring-2 focus:ring-sky-400/30"
              />
            </div>
          </div>
        </div>

        <div v-if="filteredNotes.length > 0" class="space-y-4">
          <NoteCard v-for="note in filteredNotes" :key="note.id" :note="note" variant="feed" />
        </div>

        <div
          v-else-if="notes.length > 0 && searchQuery.trim()"
          class="rounded-3xl border border-white/60 bg-white/82 px-8 py-24 text-center text-gray-400 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur"
        >
          <div class="mb-6 mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-sky-50 text-sky-400">
            <Search :size="40" stroke-width="2" />
          </div>
          <p class="mb-2 text-xl font-bold text-gray-800">没有匹配的动态</p>
          <p class="text-sm text-gray-500">换个关键词试试</p>
        </div>

        <div v-else class="rounded-3xl border border-white/60 bg-white/82 px-8 py-24 text-center text-gray-400 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="mb-6 mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-sky-50 text-sky-400">
            <Plus :size="40" stroke-width="2" />
          </div>
          <p class="mb-2 text-xl font-bold text-gray-800">还没有公开动态</p>
          <p class="text-sm text-gray-500">发布后，这里会像信息流一样连续展示</p>
        </div>
      </main>

      <aside class="space-y-4 lg:sticky lg:top-24 lg:h-fit">
        <section class="rounded-3xl border border-white/60 bg-white/82 p-4 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-base font-bold text-slate-800">热门动态</h2>
            <span class="text-xs text-slate-400">实时</span>
          </div>
          <div v-if="trendingNotes.length > 0" class="space-y-3">
            <button
              v-for="(note, index) in trendingNotes"
              :key="note.id"
              @click="router.push(`/note/${note.id}`)"
              class="flex w-full gap-3 rounded-2xl px-2 py-2 text-left transition-colors hover:bg-sky-50"
            >
              <span class="w-5 shrink-0 text-sm font-bold text-orange-500">{{ index + 1 }}</span>
              <span class="line-clamp-2 flex-1 text-sm leading-6 text-slate-600">
                {{ note.title || note.summary || '无题动态' }}
              </span>
            </button>
          </div>
          <p v-else class="text-sm leading-6 text-slate-400">暂时还没有可展示的热门动态</p>
        </section>

        <section class="rounded-3xl border border-white/60 bg-white/82 p-4 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <h2 class="mb-3 text-base font-bold text-slate-800">创作提示</h2>
          <ul class="space-y-2 text-sm leading-6 text-slate-500">
            <li>标题尽量简短，像动态一样更好刷。</li>
            <li>多图内容会自动按信息流样式展示。</li>
            <li>在这里关注作者后，动态页会只显示关注流。</li>
            <li>热门榜单会综合新鲜度、内容质量和作者热度。</li>
          </ul>
        </section>
      </aside>
      </div>
    </div>
  </div>
</template>
