<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotesStore } from '../stores/notes'
import type { Note, NoteBlock, LayoutType } from '../stores/notes'
import { ArrowLeft, Save, Type, Image, Layout, Grid, Send } from 'lucide-vue-next'
import BlockRenderer from '../components/BlockEditor.vue'

const route = useRoute()
const router = useRouter()
const notesStore = useNotesStore()

const isEditing = ref(false)
const noteId = ref('')
const title = ref('')
const blocks = ref<NoteBlock[]>([])

onMounted(async () => {
  if (route.params.id) {
    const id = route.params.id as string
    const existingNote = await notesStore.getNoteById(id)
    if (existingNote) {
      isEditing.value = true
      noteId.value = existingNote.id
      title.value = existingNote.title
      // Deep copy to avoid mutating store directly before save
      blocks.value = JSON.parse(JSON.stringify(existingNote.blocks))
    }
  } else {
    // Start with a text block
    addBlock('text-only')
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
      theme: 'book-classic'
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
  <div class="min-h-screen bg-gradient-to-br from-[#EBF4FF] to-[#F0FAFF] flex flex-col font-sans">
    <!-- Navbar -->
    <header class="bg-white/60 backdrop-blur-md border-b border-white/50 px-6 py-4 flex items-center justify-between sticky top-0 z-50 transition-all duration-300">
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

    <div class="flex-1 flex overflow-hidden" @contextmenu.prevent="showContextMenu" @click="hideContextMenu">
      <!-- Main Editor Area -->
      <main class="flex-1 overflow-y-auto p-4 md:p-6">
        <div class="max-w-4xl mx-auto space-y-8 pb-32">
          <div class="bg-white/80 backdrop-blur-sm rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-8 md:p-12 min-h-[calc(100vh-10rem)]">
            <input
              v-model="title"
              placeholder="请输入标题..."
              class="w-full text-4xl font-bold bg-transparent border-none outline-none placeholder-gray-300 text-gray-800 font-sans tracking-tight mb-8"
            />
            
            <div class="">
              <BlockRenderer 
                v-for="block in blocks" 
                :key="block.id" 
                :block="block" 
                @update="updateBlock"
                @remove="removeBlock"
              />
            </div>

            <div v-if="blocks.length === 0" class="text-center py-20 text-gray-300 border-2 border-dashed border-gray-100 rounded-xl mt-8">
              <p>右键点击空白处添加内容模块</p>
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
