<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotesStore, Note } from '../stores/notes'
import { ArrowLeft, Edit, Trash2 } from 'lucide-vue-next'
import BlockViewer from '../components/BlockViewer.vue'

const route = useRoute()
const router = useRouter()
const notesStore = useNotesStore()

const noteId = route.params.id as string
const note = ref<Note | undefined>(undefined)
const loading = ref(true)

onMounted(async () => {
  loading.value = true
  try {
    note.value = await notesStore.getNoteById(noteId)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const deleteNote = async () => {
  if (confirm('确定要删除这篇随想吗？')) {
    await notesStore.deleteNote(noteId)
    router.push('/')
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-[#EBF4FF] to-[#F0FAFF] font-sans">
    <!-- Navbar -->
    <header class="bg-white/60 backdrop-blur-md border-b border-white/50 sticky top-0 z-50 transition-all duration-300">
      <div class="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
        <button @click="router.back()" class="p-2 hover:bg-gray-100 rounded-full text-gray-600 transition-colors group">
          <ArrowLeft :size="20" class="group-hover:-translate-x-1 transition-transform" />
        </button>
        
        <div class="flex items-center gap-2" v-if="note">
          <button 
            @click="router.push(`/edit/${noteId}`)"
            class="p-2 hover:bg-blue-50 text-gray-600 hover:text-blue-600 rounded-full transition-colors"
            title="编辑"
          >
            <Edit :size="20" />
          </button>
          <button 
            @click="deleteNote"
            class="p-2 hover:bg-red-50 text-gray-600 hover:text-red-500 rounded-full transition-colors"
            title="删除"
          >
            <Trash2 :size="20" />
          </button>
        </div>
      </div>
    </header>

    <main v-if="loading" class="max-w-3xl mx-auto px-6 py-12 flex justify-center">
       <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </main>

    <main v-else-if="note" class="max-w-4xl mx-auto px-8 py-12 space-y-8 bg-white/80 backdrop-blur-sm my-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] min-h-[calc(100vh-8rem)]">
      <div class="text-center space-y-4 pb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-gray-800 tracking-tight leading-tight">{{ note.title }}</h1>
        <div class="text-sm text-gray-400 font-medium tracking-wide">
          {{ new Date(note.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}
        </div>
      </div>

      <div class="space-y-12 py-4 min-h-[40vh]">
        <BlockViewer v-for="block in note.blocks" :key="block.id" :block="block" />
      </div>
    </main>
    
    <div v-else class="flex flex-col items-center justify-center min-h-[60vh] text-gray-400">
      <p class="text-lg font-medium">找不到这篇随想</p>
      <button @click="router.push('/')" class="mt-4 text-blue-600 hover:underline font-medium">返回首页</button>
    </div>
  </div>
</template>
