<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { BellRing, Plus, Sparkles, UserPlus } from 'lucide-vue-next'
import { useNotesStore } from '../stores/notes'
import { useAuthStore } from '../stores/auth'
import NoteCard from '../components/NoteCard.vue'

const router = useRouter()
const notesStore = useNotesStore()
const authStore = useAuthStore()

const notes = computed(() => notesStore.followingNotes)
const followingCount = computed(() => authStore.followingIds.length)
const featuredNote = computed(() => notes.value[0])

onMounted(async () => {
  await Promise.all([
    authStore.fetchFollowingIds(),
    notesStore.fetchFollowingNotes(),
  ])
})
</script>

<template>
  <div class="min-h-screen bg-[#dff3f7] font-sans">
    <div class="sticky top-0 z-30 border-b border-white/60 bg-white/80 backdrop-blur-xl">
      <div class="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 md:px-6">
        <div class="flex items-center gap-8">
          <button class="text-2xl font-black tracking-tight text-sky-500">随心记</button>
          <nav class="hidden items-center gap-6 text-sm text-slate-600 md:flex">
            <button @click="router.push('/')" class="hover:text-sky-500">首页</button>
            <button class="font-semibold text-slate-900">动态</button>
            <button @click="router.push('/mine')" class="hover:text-sky-500">我的</button>
          </nav>
        </div>

        <div class="flex items-center gap-3">
          <button
            @click="router.push('/mine')"
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:border-sky-300 hover:text-sky-500"
          >
            我的
          </button>
          <button
            @click="router.push('/create')"
            class="flex items-center gap-2 rounded-full bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(14,165,233,0.28)] transition-colors hover:bg-sky-600"
          >
            <Plus :size="18" />
            <span>发布动态</span>
          </button>
        </div>
      </div>
    </div>

    <div class="mx-auto grid max-w-[1500px] gap-6 px-4 py-6 lg:grid-cols-[260px_minmax(0,760px)_300px]">
      <aside class="space-y-4 lg:sticky lg:top-24 lg:h-fit">
        <section class="overflow-hidden rounded-3xl border border-white/60 bg-white/70 shadow-[0_18px_40px_rgba(74,144,164,0.10)] backdrop-blur">
          <div class="bg-gradient-to-br from-sky-300 via-cyan-200 to-white px-5 py-6">
            <div class="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/85 text-sky-500 shadow-sm">
              <BellRing :size="26" />
            </div>
            <h2 class="text-lg font-bold text-slate-800">关注动态</h2>
            <p class="mt-2 text-sm leading-6 text-slate-600">这里只显示你关注的人发布的公开内容。</p>
          </div>
          <div class="space-y-3 p-4">
            <div class="flex items-center justify-between rounded-2xl bg-sky-50 px-4 py-3 text-sm font-medium text-sky-600">
              <span>已关注用户</span>
              <span>{{ followingCount }}</span>
            </div>
            <button
              @click="router.push('/')"
              class="flex w-full items-center justify-between rounded-2xl bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
            >
              <span>去首页发现更多</span>
              <span>></span>
            </button>
          </div>
        </section>

        <section v-if="featuredNote" class="rounded-3xl border border-white/60 bg-white/80 p-4 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Sparkles :size="16" class="text-sky-500" />
            <span>最新关注动态</span>
          </div>
          <h3 class="line-clamp-2 text-base font-semibold leading-7 text-slate-900">
            {{ featuredNote.title || '无题动态' }}
          </h3>
          <p class="mt-2 line-clamp-3 text-sm leading-6 text-slate-500">
            {{ featuredNote.summary || '你关注的人刚刚发布了新内容。' }}
          </p>
        </section>
      </aside>

      <main class="space-y-4">
        <div class="rounded-3xl border border-white/60 bg-white/82 px-5 py-4 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="flex items-center gap-3">
            <button class="rounded-full bg-sky-500 px-4 py-2 text-sm font-semibold text-white">关注中</button>
            <button @click="router.push('/')" class="rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600">去首页发现</button>
          </div>
        </div>

        <div v-if="notes.length > 0" class="space-y-4">
          <NoteCard v-for="note in notes" :key="note.id" :note="note" variant="feed" />
        </div>

        <div v-else class="rounded-3xl border border-white/60 bg-white/82 px-8 py-24 text-center text-gray-400 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="mb-6 mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-sky-50 text-sky-400">
            <UserPlus :size="40" stroke-width="2" />
          </div>
          <p class="mb-2 text-xl font-bold text-gray-800">你的动态还是空的</p>
          <p class="text-sm text-gray-500">先去首页关注一些人，这里才会出现内容</p>
        </div>
      </main>

      <aside class="space-y-4 lg:sticky lg:top-24 lg:h-fit">
        <section class="rounded-3xl border border-white/60 bg-white/82 p-4 shadow-[0_18px_40px_rgba(74,144,164,0.08)] backdrop-blur">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-base font-bold text-slate-800">关注建议</h2>
            <span class="text-xs text-slate-400">基于首页</span>
          </div>
          <ul class="space-y-2 text-sm leading-6 text-slate-500">
            <li>在首页卡片右上角可以直接关注作者。</li>
            <li>取消关注后，这里的内容会立即消失。</li>
            <li>这里只展示已发布且公开的内容。</li>
          </ul>
        </section>
      </aside>
    </div>
  </div>
</template>
