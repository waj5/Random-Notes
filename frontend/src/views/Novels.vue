<script setup lang="ts">
import { ArrowLeft, ArrowUpRight, BookOpen, Plus } from 'lucide-vue-next'
import { onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { novelsApi, type NovelSummary } from '../api/novels'
import { useAuthStore } from '../stores/auth'
import { cacheNovelData, loadNovelData } from '../utils/novelCache'

const auth = useAuthStore()
const router = useRouter()
const novels = shallowRef<NovelSummary[]>([])
const title = ref('')
const creating = ref(false)
const loading = ref(true)
const offline = ref(!navigator.onLine)
const error = ref('')

async function load() {
  offline.value = !navigator.onLine
  if (!auth.user) return
  try {
    error.value = ''
    novels.value = await loadNovelData(auth.user.id, 'library', novelsApi.list)
  } catch (cause) {
    error.value = offline.value && cause instanceof Error ? cause.message : '作品加载失败，请重试。'
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!title.value.trim() || creating.value || offline.value) return
  creating.value = true
  error.value = ''
  try {
    const novel = await novelsApi.create(title.value.trim())
    if (auth.user) {
      novels.value = [novel, ...novels.value]
      await cacheNovelData(auth.user.id, 'library', novels.value)
    }
    await router.push({ name: 'novel', params: { id: novel.id } })
  } catch {
    error.value = '新建作品失败，请重试。'
  } finally {
    creating.value = false
  }
}

function markOffline() {
  offline.value = true
}

onMounted(() => {
  void load()
  window.addEventListener('online', load)
  window.addEventListener('offline', markOffline)
})
onUnmounted(() => {
  window.removeEventListener('online', load)
  window.removeEventListener('offline', markOffline)
})

const dateFormat = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' })
</script>

<template>
  <main class="min-h-dvh bg-[#f5f7f7] text-slate-800">
    <header class="border-b border-slate-200/80 bg-white">
      <div class="mx-auto flex h-16 max-w-5xl items-center px-5 sm:px-8">
        <RouterLink :to="{ name: 'mine' }" class="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-teal-800">
          <ArrowLeft :size="17" aria-hidden="true" /> 返回我的
        </RouterLink>
      </div>
    </header>

    <div class="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-16">
      <div class="mb-9 flex flex-wrap items-end justify-between gap-6">
        <div class="flex items-center gap-4">
          <div class="grid size-12 shrink-0 place-items-center rounded-2xl bg-teal-100 text-teal-800">
            <BookOpen :size="24" aria-hidden="true" />
          </div>
          <h1 class="font-serif text-3xl font-semibold tracking-tight sm:text-4xl">我的小说</h1>
        </div>
        <form class="flex w-full gap-2 sm:w-auto" @submit.prevent="create">
          <input
            v-model="title" aria-label="书名" placeholder="输入书名" required maxlength="100"
            class="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-teal-700"
          />
          <button
            :disabled="!title.trim() || creating || offline"
            class="flex shrink-0 items-center gap-1.5 rounded-xl bg-teal-800 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-900 disabled:opacity-50"
          ><Plus :size="17" aria-hidden="true" />{{ creating ? '创建中' : '新建作品' }}</button>
        </form>
      </div>

      <p v-if="error" role="alert" class="mb-5 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">
        {{ error }} <button v-if="!offline" class="ml-2 underline" @click="load">重试</button>
      </p>
      <p v-if="offline" class="mb-4 text-sm text-slate-600">离线 · 可继续编辑已在本机打开过的章节</p>
      <p v-if="loading" class="text-sm text-slate-600">加载作品中…</p>
      <div v-else-if="!novels.length && !error" class="rounded-2xl border border-dashed border-slate-300 bg-white/60 px-6 py-14 text-center">
        <p class="text-slate-600">给你的第一部小说起个名字，开始写第一章。</p>
      </div>
      <ul v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <li v-for="novel in novels" :key="novel.id" class="flex flex-col rounded-2xl border border-slate-200 bg-white p-5">
          <h2 class="mb-3 break-words font-serif text-2xl font-semibold">{{ novel.title }}</h2>
          <p class="mb-1 text-sm text-slate-600">{{ novel.chapter_count }} 章 · {{ novel.word_count.toLocaleString('zh-CN') }} 字</p>
          <p class="mb-5 text-sm text-slate-500">最近编辑 {{ dateFormat.format(new Date(novel.updated_at)) }}</p>
          <RouterLink
            :to="{ name: 'novel', params: { id: novel.id } }"
            :aria-label="`继续写作：${novel.title}`"
            class="mt-auto flex w-fit items-center gap-1.5 rounded-lg bg-teal-50 px-3 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-100"
          >继续写作 <ArrowUpRight :size="15" aria-hidden="true" /></RouterLink>
        </li>
      </ul>
    </div>
  </main>
</template>
