<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Trash2 } from 'lucide-vue-next'
import { useNotesStore, Note } from '../stores/notes'

const props = defineProps<{ note: Note }>()
const notesStore = useNotesStore()
const router = useRouter()

// 提取摘要：优先显示 summary，如果没有则尝试从 blocks 中提取
const previewText = computed(() => {
  if (props.note.summary) return props.note.summary
  if (props.note.blocks && props.note.blocks.length > 0) {
    const firstTextBlock = props.note.blocks.find(b => b.content)
    return firstTextBlock ? firstTextBlock.content.slice(0, 50) + (firstTextBlock.content.length > 50 ? '...' : '') : ''
  }
  return ''
})

// 提取图片：找到所有包含图片的 block，然后取出所有图片
const allImages = computed(() => {
  if (!props.note.blocks) return []
  const images: string[] = []
  props.note.blocks.forEach(block => {
    if (block.images && block.images.length > 0) {
      images.push(...block.images)
    }
  })
  return images
})

// 判断卡片类型：纯文字、单图、多图（3张及以上）
const cardType = computed(() => {
  const images = allImages.value
  if (images.length === 0) return 'text'
  if (images.length < 3) return 'image'
  return 'gallery'
})

const deleteNote = (e: Event) => {
  e.stopPropagation()
  if (confirm('确定要删除这条随想吗？')) {
    notesStore.deleteNote(props.note.id)
  }
}
</script>

<template>
  <div 
    @click="router.push(`/note/${note.id}`)"
    class="break-inside-avoid bg-white rounded-xl p-4 shadow-sm hover:shadow-lg transition-all duration-300 cursor-pointer group relative border border-gray-100 overflow-hidden"
  >
    <!-- 纯文字样式 -->
    <div v-if="cardType === 'text'" class="flex flex-col h-full justify-between min-h-[160px]">
      <div>
        <h3 v-if="note.title" class="text-lg font-bold text-gray-800 mb-3">{{ note.title }}</h3>
        <p class="text-gray-600 text-sm leading-relaxed line-clamp-5 font-serif">{{ previewText }}</p>
      </div>
      <div class="mt-4 text-xs text-gray-400">{{ new Date(note.createdAt).toLocaleDateString() }}</div>
    </div>

    <!-- 单图样式 -->
    <div v-else-if="cardType === 'image'" class="space-y-3">
      <h3 v-if="note.title" class="text-lg font-bold text-gray-800">{{ note.title }}</h3>
      <div class="relative w-full aspect-[4/3] rounded-lg overflow-hidden bg-gray-100">
        <img :src="allImages[0]" class="object-cover w-full h-full transform transition-transform duration-500 group-hover:scale-105" alt="cover" />
      </div>
      <p v-if="previewText" class="text-gray-600 text-sm leading-relaxed line-clamp-2">{{ previewText }}</p>
      <div class="text-xs text-gray-400">{{ new Date(note.createdAt).toLocaleDateString() }}</div>
    </div>

    <!-- 多图样式（拍立得/照片墙风格） -->
    <div v-else class="space-y-3">
      <div class="grid grid-cols-2 gap-2">
        <div v-for="(img, idx) in allImages.slice(0, 4)" :key="idx" class="relative aspect-square rounded-lg overflow-hidden bg-gray-100 p-1 bg-white shadow-sm border border-gray-100 transform rotate-1 hover:rotate-0 transition-transform duration-300">
           <div class="w-full h-full rounded overflow-hidden">
             <img :src="img" class="object-cover w-full h-full" alt="gallery" />
           </div>
        </div>
      </div>
      <h3 v-if="note.title" class="text-lg font-bold text-gray-800 mt-2">{{ note.title }}</h3>
      <div class="text-xs text-gray-400">{{ new Date(note.createdAt).toLocaleDateString() }}</div>
    </div>

    <!-- 删除按钮（悬浮） -->
    <button 
      @click="deleteNote"
      class="absolute top-2 right-2 p-2 text-gray-400 hover:text-red-500 bg-white/80 hover:bg-red-50 backdrop-blur rounded-full transition-all opacity-0 group-hover:opacity-100 shadow-sm"
    >
      <Trash2 :size="16" />
    </button>
  </div>
</template>
