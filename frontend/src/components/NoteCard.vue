<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Trash2 } from 'lucide-vue-next'
import { useNotesStore, Note } from '../stores/notes'

const props = defineProps<{ note: Note }>()
const notesStore = useNotesStore()
const router = useRouter()

// Random rotation for "messy" look (-2 to 2 degrees)
const rotation = ref(0)
const randomX = ref(0)
const randomY = ref(0)

onMounted(() => {
  // 生成 -3 到 3 之间的随机旋转角度，让排列更自然
  rotation.value = Math.random() * 6 - 3
  // 随机偏移，制造散落感
  randomX.value = Math.random() * 10 - 5
  randomY.value = Math.random() * 20 - 10
})

// 提取摘要
const previewText = computed(() => {
  if (props.note.summary) return props.note.summary
  if (props.note.blocks && props.note.blocks.length > 0) {
    const firstTextBlock = props.note.blocks.find(b => b.content)
    return firstTextBlock ? firstTextBlock.content.slice(0, 100) + (firstTextBlock.content.length > 100 ? '...' : '') : ''
  }
  return ''
})

// 提取图片
const allImages = computed(() => {
  const images: string[] = []
  if (props.note.blocks) {
    props.note.blocks.forEach(block => {
      if (Array.isArray(block.images) && block.images.length > 0) {
        images.push(...block.images)
      }
    })
  }
  return images
})

const cardType = computed(() => {
  const images = allImages.value
  if (images.length === 0) return 'text'
  if (images.length === 1) return 'image'
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
    class="break-inside-avoid mb-10 w-full inline-block"
  >
    <div 
      class="relative group cursor-pointer transition-transform duration-300 hover:z-50 hover:scale-105 hover:rotate-0"
      :style="{ transform: `rotate(${rotation}deg) translate(${randomX}px, ${randomY}px)` }"
    >
      <!-- Tape Decoration -->
    <div 
      class="absolute -top-3 left-1/2 -translate-x-1/2 w-24 h-8 bg-white/30 backdrop-blur-sm z-20 shadow-sm rotate-1 opacity-80"
      style="mask-image: url('data:image/svg+xml;utf8,<svg width=\'100\' height=\'30\' viewBox=\'0 0 100 30\' xmlns=\'http://www.w3.org/2000/svg\'><path d=\'M0,5 L5,0 L95,2 L100,8 L98,25 L92,30 L5,28 L0,22 Z\' fill=\'black\'/></svg>'); -webkit-mask-image: url('data:image/svg+xml;utf8,<svg width=\'100\' height=\'30\' viewBox=\'0 0 100 30\' xmlns=\'http://www.w3.org/2000/svg\'><path d=\'M0,5 L5,0 L95,2 L100,8 L98,25 L92,30 L5,28 L0,22 Z\' fill=\'black\'/></svg>');"
    ></div>

    <!-- Polaroid / Paper Container -->
    <div class="bg-white p-3 pb-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.1)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.15)] transition-shadow duration-300 rounded-sm">
      
      <!-- Text Only (Paper Style) -->
      <div v-if="cardType === 'text'" class="min-h-[180px] flex flex-col justify-between bg-[#fffdf5] p-4 border border-gray-50 relative overflow-hidden">
        <!-- Lines background -->
        <div class="absolute inset-0 pointer-events-none" 
             style="background-image: repeating-linear-gradient(transparent, transparent 27px, #e5e7eb 28px); background-position: 0 10px;">
        </div>
        
        <div class="relative z-10">
          <h3 v-if="note.title && note.title !== '无题'" class="text-xl font-bold text-gray-800 mb-2 font-handwriting">{{ note.title }}</h3>
          <p class="text-gray-600 text-base leading-7 font-handwriting line-clamp-6 whitespace-pre-wrap">{{ previewText }}</p>
        </div>
        <div class="relative z-10 mt-4 text-right text-xs text-gray-400 font-mono">{{ new Date(note.createdAt).toLocaleDateString() }}</div>
      </div>

      <!-- Single Image (Polaroid Style) -->
      <div v-else-if="cardType === 'image'" class="flex flex-col gap-3">
        <div class="aspect-[4/3] w-full overflow-hidden bg-gray-100 shadow-inner p-1 bg-white border border-gray-100">
          <img :src="allImages[0]" class="w-full h-full object-cover filter contrast-[1.05] hover:scale-105 transition-transform duration-700" loading="lazy" />
        </div>
        <div class="px-2 pt-1">
          <h3 v-if="note.title && note.title !== '无题'" class="text-lg font-bold text-gray-800 mb-1 font-handwriting">{{ note.title }}</h3>
          <p v-if="previewText" class="text-gray-500 text-sm leading-relaxed line-clamp-2 font-handwriting">{{ previewText }}</p>
          <div class="mt-2 text-right text-xs text-gray-300 font-mono">{{ new Date(note.createdAt).toLocaleDateString() }}</div>
        </div>
      </div>

      <!-- Gallery (Collage Style) -->
      <div v-else class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-2">
          <div v-for="(img, idx) in allImages.slice(0, 4)" :key="idx" 
               class="aspect-square overflow-hidden bg-gray-100 shadow-sm border-[3px] border-white relative first:rotate-[-2deg] last:rotate-[2deg]"
               :class="{'col-span-2 aspect-[2/1]': idx === 0 && allImages.length === 3}">
             <img :src="img" class="w-full h-full object-cover hover:scale-110 transition-transform duration-500" loading="lazy" />
          </div>
        </div>
        <div class="px-2 pt-1">
           <h3 v-if="note.title && note.title !== '无题'" class="text-lg font-bold text-gray-800 mb-1 font-handwriting">{{ note.title }}</h3>
           <div class="text-right text-xs text-gray-300 font-mono">{{ new Date(note.createdAt).toLocaleDateString() }}</div>
        </div>
      </div>
    </div>

    <!-- Delete Button -->
    <button 
      @click="deleteNote"
      class="absolute -top-2 -right-2 p-2 text-gray-400 hover:text-red-500 bg-white shadow-md rounded-full opacity-0 group-hover:opacity-100 transition-all scale-75 hover:scale-100 z-30"
    >
      <Trash2 :size="16" />
    </button>
    </div>
  </div>
</template>

<style scoped>
.font-handwriting {
  font-family: 'Comic Sans MS', 'Chalkboard SE', 'Merriweather', serif;
}
</style>