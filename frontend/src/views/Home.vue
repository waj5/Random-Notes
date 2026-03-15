<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import { useNotesStore } from '../stores/notes'
import NoteCard from '../components/NoteCard.vue'

const router = useRouter()
const notesStore = useNotesStore()

const notes = computed(() => notesStore.notes)

onMounted(async () => {
  await notesStore.fetchNotes()
})
</script>

<template>
  <div class="min-h-screen bg-[#F2F5F8] py-12 px-6 lg:px-12 relative overflow-hidden font-sans">
    <!-- 背景装饰 -->
    <div class="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-blue-50 to-transparent -z-10"></div>
    
    <div class="max-w-7xl mx-auto">
      <header class="flex items-center justify-between mb-12">
        <div class="flex items-center gap-4">
          <div class="w-1.5 h-8 bg-blue-600 rounded-full"></div>
          <div>
            <h1 class="text-3xl font-bold text-gray-900 tracking-tight">随心记</h1>
            <div class="h-1 w-20 bg-blue-600 mt-2 rounded-full"></div>
          </div>
        </div>
        
        <button 
          @click="router.push('/create')"
          class="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 hover:shadow-blue-500/30 transition-all duration-300 font-medium"
        >
          <Plus :size="20" />
          <span>新建笔记</span>
        </button>
      </header>
      
      <!-- 风格标签栏 -->
      <div class="flex gap-8 mb-10 text-gray-600 font-medium">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-blue-500"></span>
          <span>随心文字</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-blue-500"></span>
          <span>纯图片</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-blue-500"></span>
          <span>图片+文字</span>
        </div>
      </div>
      
      <div v-if="notes.length > 0" class="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
        <NoteCard v-for="note in notes" :key="note.id" :note="note" class="mb-6 break-inside-avoid shadow-[0_2px_12px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_20px_rgba(0,0,0,0.08)]" />
      </div>
      
      <div v-else class="text-center py-32 text-gray-400 bg-white rounded-3xl border border-gray-100 shadow-sm mx-auto max-w-2xl">
        <div class="mb-6 w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto text-blue-400">
          <Plus :size="40" stroke-width="2" />
        </div>
        <p class="text-xl font-bold mb-2 text-gray-800">新建笔记</p>
        <p class="text-sm text-gray-500">点击右上角按钮，开始记录你的第一篇随心记吧</p>
      </div>
    </div>
  </div>
</template>
