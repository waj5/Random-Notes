<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotesStore, Note, NoteBlock, LayoutType } from '../stores/notes'
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
    images: []
  })
}

const updateBlock = (id: string, field: keyof NoteBlock, value: any) => {
  const index = blocks.value.findIndex(b => b.id === id)
  if (index !== -1) {
    blocks.value[index] = { ...blocks.value[index], [field]: value }
  }
}

const removeBlock = (id: string) => {
  blocks.value = blocks.value.filter(b => b.id !== id)
}

const isSaving = ref(false)

const isPublishing = ref(false)

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
    const note: Note = {
      id: isEditing.value ? noteId.value : Date.now().toString(),
      title: title.value || '无题',
      createdAt: isEditing.value ? (await notesStore.getNoteById(noteId.value)?.createdAt || Date.now()) : Date.now(),
      blocks: blocks.value,
      theme: 'book-classic'
    }

    if (isEditing.value) {
      await notesStore.updateNote(note.id, note)
    } else {
      await notesStore.addNote(note)
    }
    
    router.push('/')
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

    <div class="flex-1 flex overflow-hidden">
      <!-- Toolbar Sidebar -->
      <aside class="w-20 bg-white/80 backdrop-blur border-r border-gray-100 flex flex-col items-center py-8 gap-6 z-40 hidden md:flex">
        <button @click="addBlock('text-only')" class="p-3 rounded-xl hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors group relative" title="纯文字">
          <Type :size="24" stroke-width="1.5" />
          <span class="absolute left-16 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none shadow-lg">纯文字</span>
        </button>
        <button @click="addBlock('image-top')" class="p-3 rounded-xl hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors group relative" title="单图置顶">
          <Image :size="24" stroke-width="1.5" />
          <span class="absolute left-16 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none shadow-lg">单图置顶</span>
        </button>
        <button @click="addBlock('split-left')" class="p-3 rounded-xl hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors group relative" title="左图右文">
          <Layout :size="24" stroke-width="1.5" />
          <span class="absolute left-16 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none shadow-lg">左图右文</span>
        </button>
        <button @click="addBlock('split-right')" class="p-3 rounded-xl hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors group relative" title="右图左文">
          <Layout :size="24" class="transform rotate-180" stroke-width="1.5" />
          <span class="absolute left-16 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none shadow-lg">右图左文</span>
        </button>
        <button @click="addBlock('gallery-grid')" class="p-3 rounded-xl hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors group relative" title="照片墙">
          <Grid :size="24" stroke-width="1.5" />
          <span class="absolute left-16 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none shadow-lg">照片墙</span>
        </button>
      </aside>

      <!-- Mobile Toolbar (Bottom) -->
      <div class="md:hidden fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white/90 backdrop-blur rounded-full shadow-lg shadow-blue-900/10 border border-gray-100 px-6 py-3 flex gap-6 z-50">
        <button @click="addBlock('text-only')" class="p-2 text-gray-400 hover:text-blue-600"><Type :size="20" /></button>
        <button @click="addBlock('image-top')" class="p-2 text-gray-400 hover:text-blue-600"><Image :size="20" /></button>
        <button @click="addBlock('split-left')" class="p-2 text-gray-400 hover:text-blue-600"><Layout :size="20" /></button>
        <button @click="addBlock('gallery-grid')" class="p-2 text-gray-400 hover:text-blue-600"><Grid :size="20" /></button>
      </div>

      <!-- Main Editor Area -->
      <main class="flex-1 overflow-y-auto p-4 md:p-6">
        <div class="max-w-4xl mx-auto space-y-8 pb-32">
          <div class="bg-white/80 backdrop-blur-sm rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-8 md:p-12 min-h-[calc(100vh-10rem)]">
            <input
              v-model="title"
              placeholder="请输入标题..."
              class="w-full text-4xl font-bold bg-transparent border-none outline-none placeholder-gray-300 text-gray-800 font-sans tracking-tight mb-8"
            />
            
            <div class="space-y-8">
              <BlockRenderer 
                v-for="block in blocks" 
                :key="block.id" 
                :block="block" 
                @update="updateBlock"
                @remove="removeBlock"
              />
            </div>

            <div v-if="blocks.length === 0" class="text-center py-20 text-gray-300 border-2 border-dashed border-gray-100 rounded-xl mt-8">
              <p>点击左侧工具栏添加内容模块</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
