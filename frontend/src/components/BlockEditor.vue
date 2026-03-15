<script setup lang="ts">
import { type NoteBlock } from '../stores/notes'
import ImageUploader from './ImageUploader.vue'
import { Trash2 } from 'lucide-vue-next'
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{ block: NoteBlock }>()
const emit = defineEmits(['update', 'remove'])

const leftTextEditor = ref<HTMLDivElement | null>(null)
const rightTextEditor = ref<HTMLDivElement | null>(null)
const textOnlyEditor = ref<HTMLDivElement | null>(null)

// Initialize content for contenteditable divs
onMounted(() => {
  if (leftTextEditor.value) {
    leftTextEditor.value.innerText = props.block.content
  }
  if (rightTextEditor.value) {
    rightTextEditor.value.innerText = props.block.content
  }
  if (textOnlyEditor.value) {
    textOnlyEditor.value.innerText = props.block.content
  }
})

// Watch for external content changes (optional, but good for consistency if data changes from outside)
watch(() => props.block.content, (newVal) => {
  if (leftTextEditor.value && leftTextEditor.value.innerText !== newVal) {
    leftTextEditor.value.innerText = newVal
  }
  if (rightTextEditor.value && rightTextEditor.value.innerText !== newVal) {
    rightTextEditor.value.innerText = newVal
  }
  if (textOnlyEditor.value && textOnlyEditor.value.innerText !== newVal) {
    textOnlyEditor.value.innerText = newVal
  }
})

const updateContent = (content: string) => {
  emit('update', props.block.id, 'content', content)
}

const addImage = (src: string) => {
  const newImages = [...props.block.images, src]
  emit('update', props.block.id, 'images', newImages)
}

const removeImage = (index: number) => {
  const newImages = [...props.block.images]
  newImages.splice(index, 1)
  emit('update', props.block.id, 'images', newImages)
}
</script>

<template>
  <div class="relative group transition-all mb-2">
    <button 
      @click="$emit('remove', block.id)"
      class="absolute -right-10 top-0 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors opacity-0 group-hover:opacity-100 z-50"
      title="删除此块"
    >
      <Trash2 :size="18" />
    </button>
    
    <!-- Text Only -->
    <div v-if="block.type === 'text-only'">
      <div
        contenteditable="true"
        @input="updateContent(($event.target as HTMLDivElement).innerText)"
        class="w-full outline-none font-serif text-lg leading-loose text-gray-700 empty:before:content-[attr(placeholder)] empty:before:text-gray-300 min-h-[1.5em] whitespace-pre-wrap transition-colors"
        placeholder="写下这一刻的想法..."
        ref="textOnlyEditor"
      ></div>
    </div>

    <!-- Image Top -->
    <div v-else-if="block.type === 'image-top'" class="space-y-4">
      <div v-if="block.images.length > 0" class="relative group/img">
        <img :src="block.images[0]" class="w-full h-64 object-cover rounded-lg shadow-sm" />
        <button @click="removeImage(0)" class="absolute top-2 right-2 bg-white/80 p-1 rounded-full text-red-500 opacity-0 group-hover/img:opacity-100 transition-opacity">
          <Trash2 :size="14" />
        </button>
      </div>
      <ImageUploader v-else @upload="(src) => addImage(src)" class="min-h-[200px]" />
      
      <textarea
        :value="block.content"
        @input="updateContent(($event.target as HTMLTextAreaElement).value)"
        placeholder="写点什么..."
        class="w-full bg-transparent resize-none outline-none font-serif text-lg leading-loose text-gray-700 placeholder-gray-300 min-h-[80px]"
      ></textarea>
    </div>

    <!-- Image Bottom -->
    <div v-else-if="block.type === 'image-bottom'" class="space-y-4">
      <textarea
        :value="block.content"
        @input="updateContent(($event.target as HTMLTextAreaElement).value)"
        placeholder="写点什么..."
        class="w-full bg-transparent resize-none outline-none font-serif text-lg leading-loose text-gray-700 placeholder-gray-300 min-h-[80px]"
      ></textarea>

      <div v-if="block.images.length > 0" class="relative group/img">
        <img :src="block.images[0]" class="w-full h-64 object-cover rounded-lg shadow-sm" />
        <button @click="removeImage(0)" class="absolute top-2 right-2 bg-white/80 p-1 rounded-full text-red-500 opacity-0 group-hover/img:opacity-100 transition-opacity">
          <Trash2 :size="14" />
        </button>
      </div>
      <ImageUploader v-else @upload="(src) => addImage(src)" class="min-h-[200px]" />
    </div>

    <!-- Split Left (Image Left, Text Right) -->
    <div v-else-if="block.type === 'split-left'" class="clearfix relative min-h-[150px]">
      <div class="float-left w-5/12 mr-4 space-y-2 mb-2 relative z-10 select-none">
         <div v-for="(img, idx) in block.images" :key="idx" class="relative group/img">
            <img :src="img" class="w-full h-auto object-cover rounded-lg shadow-sm" />
            <button @click="removeImage(idx)" class="absolute top-1 right-1 bg-white/80 p-1 rounded-full text-red-500 opacity-0 group-hover/img:opacity-100 transition-opacity cursor-pointer z-50">
              <Trash2 :size="12" />
            </button>
         </div>
         <ImageUploader v-if="block.images.length === 0" @upload="(src) => addImage(src)" class="h-32 min-h-0" />
      </div>
      <div
        contenteditable="true"
        @input="updateContent(($event.target as HTMLDivElement).innerText)"
        class="w-full outline-none font-serif text-lg leading-loose text-gray-700 empty:before:content-[attr(placeholder)] empty:before:text-gray-300 min-h-[1.5em] whitespace-pre-wrap"
        placeholder="描述左边的画面..."
        ref="leftTextEditor"
      ></div>
      <div class="clear-both"></div>
    </div>

    <!-- Split Right (Text Left, Image Right) -->
    <div v-else-if="block.type === 'split-right'" class="clearfix relative min-h-[150px]">
      <div class="float-right w-5/12 ml-4 space-y-2 mb-2 relative z-10 select-none">
         <div v-for="(img, idx) in block.images" :key="idx" class="relative group/img">
            <img :src="img" class="w-full h-auto object-cover rounded-lg shadow-sm" />
            <button @click="removeImage(idx)" class="absolute top-1 right-1 bg-white/80 p-1 rounded-full text-red-500 opacity-0 group-hover/img:opacity-100 transition-opacity cursor-pointer z-50">
              <Trash2 :size="12" />
            </button>
         </div>
         <ImageUploader v-if="block.images.length === 0" @upload="(src) => addImage(src)" class="h-32 min-h-0" />
      </div>
      <div
        contenteditable="true"
        @input="updateContent(($event.target as HTMLDivElement).innerText)"
        class="w-full outline-none font-serif text-lg leading-loose text-gray-700 empty:before:content-[attr(placeholder)] empty:before:text-gray-300 min-h-[1.5em] whitespace-pre-wrap"
        placeholder="描述右边的画面..."
        ref="rightTextEditor"
      ></div>
      <div class="clear-both"></div>
    </div>

    <!-- Gallery Grid -->
    <div v-else-if="block.type === 'gallery-grid'" class="space-y-4">
      <div class="grid grid-cols-3 gap-2">
        <div v-for="(img, idx) in block.images" :key="idx" class="relative aspect-square group/img">
            <img :src="img" class="w-full h-full object-cover rounded-lg shadow-sm" />
            <button @click="removeImage(idx)" class="absolute top-1 right-1 bg-white/80 p-1 rounded-full text-red-500 opacity-0 group-hover/img:opacity-100 transition-opacity">
              <Trash2 :size="12" />
            </button>
        </div>
        <ImageUploader @upload="(src) => addImage(src)" class="aspect-square min-h-0" />
      </div>
      <textarea
        :value="block.content"
        @input="updateContent(($event.target as HTMLTextAreaElement).value)"
        placeholder="给这些照片写个总结..."
        class="w-full bg-transparent resize-none outline-none font-serif text-lg leading-loose text-gray-700 placeholder-gray-300 min-h-[60px]"
      ></textarea>
    </div>
  </div>
</template>
