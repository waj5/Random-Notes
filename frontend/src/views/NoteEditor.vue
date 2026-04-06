<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotesStore } from '../stores/notes'
import type { Note, NoteBlock, LayoutType } from '../stores/notes'
import { ArrowLeft, Grid, Image, Layout, Save, Send, Type } from 'lucide-vue-next'
import BlockRenderer from '../components/BlockEditor.vue'
import PetalBackground from '../components/PetalBackground.vue'
import MoodWeatherIcons from '../components/MoodWeatherIcons.vue'
import { fetchCurrentWeatherWmoCode } from '../utils/openMeteo'

const route = useRoute()
const router = useRouter()
const notesStore = useNotesStore()

const isEditing = ref(false)
const noteId = ref('')
const title = ref('')
const blocks = ref<NoteBlock[]>([])

const moodOptions = [
  { key: 'happy', label: '开心' },
  { key: 'love', label: '喜欢' },
  { key: 'calm', label: '平静' },
  { key: 'sad', label: '低落' },
  { key: 'excited', label: '兴奋' },
  { key: 'meh', label: '一般' },
] as const

const selectedMood = ref<string>('calm')
const weatherWmoCode = ref<number | null>(null)
const weatherLoading = ref(false)
const lockedMood = ref<string | null>(null)
const lockedWeatherWmoCode = ref<number | null>(null)

onMounted(async () => {
  if (route.params.id) {
    const id = route.params.id as string
    const existingNote = await notesStore.getNoteById(id)
    if (existingNote) {
      isEditing.value = true
      noteId.value = existingNote.id
      title.value = existingNote.title
      lockedMood.value = existingNote.mood ?? null
      lockedWeatherWmoCode.value = existingNote.weatherWmoCode ?? null
      // Deep copy to avoid mutating store directly before save
      blocks.value = JSON.parse(JSON.stringify(existingNote.blocks))
    }
  } else {
    addBlock('text-only')
    weatherLoading.value = true
    fetchCurrentWeatherWmoCode().then((code) => {
      weatherWmoCode.value = code
      weatherLoading.value = false
    })
  }
})

const addBlock = (type: LayoutType) => {
  blocks.value.push({
    id: Date.now().toString() + Math.random().toString().slice(2, 5),
    type,
    content: '',
    images: [],
    galleryTemplate: type === 'gallery-grid' ? 'grid' : undefined
  })
}

const updateBlock = (id: string, field: keyof NoteBlock, value: any) => {
  const index = blocks.value.findIndex(b => b.id === id)
  if (index !== -1) {
    blocks.value[index] = { ...blocks.value[index], [field]: value } as NoteBlock
  }
}

const removeBlock = (id: string) => {
  blocks.value = blocks.value.filter(b => b.id !== id)
}

const isSaving = ref(false)

const isPublishing = ref(false)

const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0
})

const showContextMenu = (e: MouseEvent) => {
  e.preventDefault()
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY
  }
}

const hideContextMenu = () => {
  contextMenu.value.visible = false
}

const addBlockAndHide = (type: LayoutType) => {
  addBlock(type)
  hideContextMenu()
}

const publishNote = async () => {
  if (!noteId.value) {
    alert('请先保存笔记再发布');
    return;
  }

  if (!confirm('确定要发布这条随想吗？发布后将公开可见。')) return;
  
  isPublishing.value = true;
  try {
    await notesStore.publishNote(noteId.value);
    alert('发布成功！');
    router.push('/');
  } catch (error) {
    console.error('Failed to publish:', error);
    alert('发布失败');
  } finally {
    isPublishing.value = false;
  }
}

const saveNote = async () => {
  if (!title.value.trim() && blocks.value.length === 0) return
  
  isSaving.value = true
  try {
    const existingNote = isEditing.value ? await notesStore.getNoteById(noteId.value) : undefined
    const note: Note = {
      id: isEditing.value ? noteId.value : Date.now().toString(),
      title: title.value || '无题',
      createdAt: existingNote?.createdAt || Date.now(),
      blocks: blocks.value,
      theme: 'book-classic',
      ...(isEditing.value
        ? {}
        : {
            mood: selectedMood.value,
            weatherWmoCode: weatherWmoCode.value,
          }),
    }

    if (isEditing.value) {
      await notesStore.updateNote(note.id, note)
    } else {
      await notesStore.addNote(note)
    }
    
    router.push('/mine')
  } catch (error) {
    console.error('Failed to save note:', error)
    alert('保存失败，请重试')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="relative flex min-h-dvh flex-col overflow-hidden bg-[#dff3f7] font-sans">
    <PetalBackground />
    <!-- Navbar（与首页顶栏一致） -->
    <header class="sticky top-0 z-50 flex items-center justify-between border-b border-white/60 bg-white/80 px-6 py-4 backdrop-blur-xl transition-all duration-300">
      <div class="flex items-center gap-4">
        <button @click="router.back()" class="p-2 hover:bg-gray-100 rounded-full text-gray-600 transition-colors group">
          <ArrowLeft :size="20" class="group-hover:-translate-x-1 transition-transform" />
        </button>
        <h1 class="text-xl font-bold text-gray-800 tracking-tight">{{ isEditing ? '编辑随想' : '新建随想' }}</h1>
      </div>
      <div class="flex items-center gap-3">
        <button 
          v-if="isEditing"
          @click="publishNote"
          :disabled="isPublishing || isSaving"
          class="flex items-center gap-2 px-4 py-2 bg-white text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors shadow-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <Send :size="16" />
          <span>{{ isPublishing ? '发布中...' : '发布' }}</span>
        </button>
        <button 
          @click="saveNote"
          :disabled="isSaving"
          class="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-blue-500/30 font-medium disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          <Save :size="16" />
          <span>{{ isSaving ? '保存中...' : '保存' }}</span>
        </button>
      </div>
    </header>

    <div
      class="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden"
      @contextmenu.prevent="showContextMenu"
      @click="hideContextMenu"
    >
      <main class="flex min-h-0 flex-1 flex-col px-2 py-2 sm:px-4 sm:py-3">
        <div class="mx-auto flex h-full min-h-0 w-full max-w-[min(100%,56rem)] flex-1 flex-col lg:max-w-[60rem]">
          <div
            class="editor-notebook-page flex min-h-0 flex-1 flex-col rounded-2xl border border-sky-100 bg-white/92 shadow-[0_14px_36px_rgba(54,120,160,0.08)] backdrop-blur"
            style="min-height: max(360px, calc(100dvh - 5.75rem))"
          >
            <div class="mb-3 flex shrink-0 flex-col gap-2 sm:mb-3 sm:flex-row sm:items-center sm:gap-3">
              <input
                v-model="title"
                placeholder="请输入标题..."
                class="editor-title-input font-display min-w-0 flex-1 border-none bg-transparent text-2xl font-bold tracking-wide text-gray-800 outline-none placeholder-gray-300 sm:text-[1.85rem]"
              />
              <div class="flex shrink-0 flex-wrap items-center justify-end gap-2 sm:justify-end">
                <template v-if="!isEditing">
                  <label class="sr-only" for="editor-mood">心情</label>
                  <select
                    id="editor-mood"
                    v-model="selectedMood"
                    class="rounded-full border border-slate-200 bg-white py-1.5 pl-3 pr-8 text-sm font-medium text-slate-700 shadow-sm outline-none ring-sky-400/0 focus:border-sky-300 focus:ring-2 focus:ring-sky-400/25"
                  >
                    <option v-for="opt in moodOptions" :key="opt.key" :value="opt.key">
                      {{ opt.label }}
                    </option>
                  </select>
                  <span v-if="weatherLoading" class="text-xs text-slate-400">天气…</span>
                  <MoodWeatherIcons
                    v-else
                    weather-only
                    :weather-wmo-code="weatherWmoCode"
                    :size="22"
                  />
                </template>
                <MoodWeatherIcons
                  v-else-if="lockedMood != null || lockedWeatherWmoCode != null"
                  :mood-key="lockedMood"
                  :weather-wmo-code="lockedWeatherWmoCode"
                  :size="22"
                />
              </div>
            </div>

            <div class="min-h-0 flex-1 overflow-y-auto pb-3">
              <BlockRenderer
                v-for="block in blocks"
                :key="block.id"
                :block="block"
                @update="updateBlock"
                @remove="removeBlock"
              />
              <div
                v-if="blocks.length === 0"
                class="mt-2 rounded-lg border-2 border-dashed border-gray-100 py-8 text-center text-sm text-gray-300"
              >
                <p>右键点击空白处添加内容模块</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- Custom Context Menu -->
      <div 
        v-if="contextMenu.visible" 
        class="fixed z-50 bg-white/90 backdrop-blur rounded-lg shadow-xl border border-gray-100 py-2 min-w-[160px]"
        :style="{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }"
      >
        <button @click="addBlockAndHide('text-only')" class="w-full px-4 py-2 text-left text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2">
          <Type :size="16" />
          <span>纯文字</span>
        </button>
        <button @click="addBlockAndHide('image-top')" class="w-full px-4 py-2 text-left text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2">
          <Image :size="16" />
          <span>单图置顶</span>
        </button>
        <button @click="addBlockAndHide('split-left')" class="w-full px-4 py-2 text-left text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2">
          <Layout :size="16" />
          <span>左图右文</span>
        </button>
        <button @click="addBlockAndHide('split-right')" class="w-full px-4 py-2 text-left text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2">
          <Layout :size="16" class="transform rotate-180" />
          <span>右图左文</span>
        </button>
        <button @click="addBlockAndHide('gallery-grid')" class="w-full px-4 py-2 text-left text-gray-700 hover:bg-blue-50 hover:text-blue-600 flex items-center gap-2">
          <Grid :size="16" />
          <span>照片墙</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.editor-notebook-page {
  padding: 1.35rem 1.25rem 1.75rem 2.65rem;
  background-color: rgba(255, 255, 255, 0.97);
  background-image:
    linear-gradient(
      to right,
      transparent 0,
      transparent 2rem,
      rgba(251, 182, 193, 0.2) 2rem,
      rgba(251, 182, 193, 0.2) 2.14rem,
      transparent 2.14rem
    ),
    repeating-linear-gradient(
      to bottom,
      transparent 0,
      transparent calc(1.85rem - 1px),
      rgba(148, 163, 184, 0.22) calc(1.85rem - 1px),
      rgba(148, 163, 184, 0.22) 1.85rem
    );
  background-position: 0 0.85rem, 0 0.85rem;
}

.editor-title-input {
  line-height: 1.25;
}
</style>
