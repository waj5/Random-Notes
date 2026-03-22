<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Images } from 'lucide-vue-next'
import { useNotesStore } from '../stores/notes'
import type { Note } from '../stores/notes'

const route = useRoute()
const router = useRouter()
const notesStore = useNotesStore()

const noteId = route.params.id as string
const note = ref<Note | undefined>(undefined)
const loading = ref(true)

const albumImages = computed(() =>
  note.value?.blocks.flatMap((block) => block.images) || []
)

const backToAlbums = () => {
  if (route.query.source === 'space' && typeof route.query.userId === 'string') {
    router.push({
      path: `/space/${route.query.userId}`,
      query: {
        tab: 'albums',
      },
    })
    return
  }

  router.push({
    path: '/mine',
    query: {
      tab: 'albums',
      filter: 'all',
    },
  })
}

onMounted(async () => {
  loading.value = true
  try {
    note.value = await notesStore.getNoteById(noteId)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-[#f6f7fb] font-sans">
    <header class="sticky top-0 z-30 border-b border-white/60 bg-white/85 backdrop-blur-xl">
      <div class="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-4 md:px-6">
        <button @click="backToAlbums" class="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-sky-500">
          <ArrowLeft :size="18" />
          <span>返回相册</span>
        </button>
        <div class="text-sm font-medium text-slate-400">纯照片模式</div>
      </div>
    </header>

    <main v-if="loading" class="mx-auto flex max-w-5xl justify-center px-6 py-16">
      <div class="h-8 w-8 animate-spin rounded-full border-b-2 border-sky-500"></div>
    </main>

    <main v-else-if="note" class="mx-auto max-w-[1400px] px-4 py-6">
      <section class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(56,84,130,0.08)]">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold text-slate-900">{{ note.title || '无题相册' }}</h1>
            <p class="mt-2 text-sm text-slate-500">只展示这篇文章提取出来的照片，不展示正文内容。</p>
          </div>
          <div class="flex items-center gap-2 rounded-full bg-sky-50 px-4 py-2 text-sm font-medium text-sky-600">
            <Images :size="16" />
            <span>{{ albumImages.length }} 张图片</span>
          </div>
        </div>
      </section>

      <section v-if="albumImages.length > 0" class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="(src, index) in albumImages"
          :key="`${note.id}-${index}`"
          class="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_18px_40px_rgba(56,84,130,0.06)]"
        >
          <img :src="src" class="h-full w-full object-cover" />
        </div>
      </section>

      <section v-else class="mt-6 rounded-[28px] border border-slate-200 bg-white px-8 py-20 text-center text-slate-400 shadow-[0_18px_40px_rgba(56,84,130,0.06)]">
        这个相册里还没有图片
      </section>
    </main>

    <main v-else class="mx-auto max-w-4xl px-6 py-16 text-center text-slate-400">
      找不到这个相册
    </main>
  </div>
</template>
