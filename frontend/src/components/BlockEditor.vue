<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { type GalleryTemplate, type NoteBlock } from '../stores/notes'
import ImageUploader from './ImageUploader.vue'
import { Trash2 } from 'lucide-vue-next'

const props = defineProps<{ block: NoteBlock }>()
const emit = defineEmits(['update', 'remove'])

const leftTextEditor = ref<HTMLDivElement | null>(null)
const rightTextEditor = ref<HTMLDivElement | null>(null)
const textOnlyEditor = ref<HTMLDivElement | null>(null)

const galleryTemplates: Array<{ value: GalleryTemplate; label: string }> = [
  { value: 'grid', label: '经典' },
  { value: 'mosaic', label: '拼贴' },
  { value: 'spotlight', label: '聚焦' },
  { value: 'film', label: '胶片' },
  { value: 'heart', label: '心形' }
]

const HEART_MIN_IMAGES = 9
const galleryTemplate = computed<GalleryTemplate>(() => props.block.galleryTemplate || 'grid')

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

const addImage = (src: string | string[]) => {
  const imagesToAdd = Array.isArray(src) ? src : [src]
  const newImages = [...props.block.images, ...imagesToAdd]
  emit('update', props.block.id, 'images', newImages)
}

const removeImage = (index: number) => {
  const newImages = [...props.block.images]
  newImages.splice(index, 1)
  emit('update', props.block.id, 'images', newImages)
}

const updateGalleryTemplate = (template: GalleryTemplate) => {
  emit('update', props.block.id, 'galleryTemplate', template)
}

const getGalleryContainerClass = () => {
  switch (galleryTemplate.value) {
    case 'mosaic':
      return 'grid grid-cols-3 auto-rows-[96px] gap-2'
    case 'spotlight':
      return 'grid grid-cols-4 auto-rows-[88px] gap-2'
    case 'film':
      return 'grid grid-cols-2 md:grid-cols-4 gap-3 rounded-[28px] bg-[#1f1f1f] p-4'
    case 'heart':
      return 'heart-gallery mx-auto grid aspect-square w-full max-w-[420px] overflow-hidden bg-rose-50/70'
    default:
      return 'grid grid-cols-3 gap-2'
  }
}

const getGalleryItemClass = (index: number) => {
  switch (galleryTemplate.value) {
    case 'mosaic': {
      const pattern = index % 5
      if (pattern === 0) return 'relative col-span-2 row-span-2 group/img overflow-hidden rounded-2xl'
      if (pattern === 4) return 'relative col-span-2 row-span-1 group/img overflow-hidden rounded-2xl'
      return 'relative col-span-1 row-span-1 group/img overflow-hidden rounded-2xl'
    }
    case 'spotlight':
      return index % 4 === 0
        ? 'relative col-span-2 row-span-2 group/img overflow-hidden rounded-2xl'
        : 'relative col-span-2 row-span-1 group/img overflow-hidden rounded-2xl'
    case 'film':
      return 'relative aspect-[3/4] group/img overflow-hidden rounded-2xl border border-white/10 bg-black/30 p-1.5 shadow-sm'
    case 'heart':
      return 'relative group/img overflow-hidden'
    default:
      return 'relative aspect-square group/img overflow-hidden rounded-lg'
  }
}

const getGalleryImageClass = () => {
  if (galleryTemplate.value === 'film') {
    return 'w-full h-full object-cover rounded-xl'
  }
  return 'w-full h-full object-cover'
}

const getGalleryUploaderClass = () => {
  switch (galleryTemplate.value) {
    case 'mosaic':
      return 'col-span-1 row-span-1'
    case 'spotlight':
      return 'col-span-2 row-span-1'
    case 'film':
      return 'aspect-[3/4]'
    default:
      return 'aspect-square'
  }
}

const getHeartGridStyle = () => {
  const count = Math.max(props.block.images.length, 1)
  const cols = Math.ceil(Math.sqrt(count))
  const rows = Math.ceil(count / cols)
  const gap = count <= 2 ? '4px' : count <= 6 ? '3px' : '2px'

  return {
    gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
    gridTemplateRows: `repeat(${rows}, minmax(0, 1fr))`,
    gap
  }
}

const heartTemplateHint = computed(() => {
  if (galleryTemplate.value !== 'heart') return ''
  if (props.block.images.length >= HEART_MIN_IMAGES) {
    return `当前 ${props.block.images.length} 张，心形效果会更稳定`
  }
  return `心形照片墙建议至少 ${HEART_MIN_IMAGES} 张图片，当前 ${props.block.images.length} 张`
})
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
      <div class="flex flex-wrap gap-2">
        <button
          v-for="item in galleryTemplates"
          :key="item.value"
          type="button"
          @click="updateGalleryTemplate(item.value)"
          class="px-3 py-1.5 rounded-full text-sm transition-colors border"
          :class="galleryTemplate === item.value ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'"
        >
          {{ item.label }}
        </button>
      </div>

      <p v-if="heartTemplateHint" class="text-sm text-amber-600">
        {{ heartTemplateHint }}
      </p>

      <div :class="getGalleryContainerClass()" :style="galleryTemplate === 'heart' ? getHeartGridStyle() : undefined">
        <div v-for="(img, idx) in block.images" :key="idx" :class="getGalleryItemClass(idx)">
            <img :src="img" :class="getGalleryImageClass()" />
            <button @click="removeImage(idx)" class="absolute top-1 right-1 bg-white/80 p-1 rounded-full text-red-500 opacity-0 group-hover/img:opacity-100 transition-opacity z-10">
              <Trash2 :size="12" />
            </button>
        </div>
        <div v-if="galleryTemplate !== 'heart'" :class="getGalleryUploaderClass()">
          <ImageUploader multiple @upload="(src) => addImage(src)" class="w-full h-full min-h-0" />
        </div>
      </div>
      <div v-if="galleryTemplate === 'heart'" class="mx-auto max-w-[140px]">
        <ImageUploader multiple @upload="(src) => addImage(src)" class="aspect-square min-h-0" />
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

<style scoped>
.heart-gallery {
  clip-path: polygon(50% 100%, 31% 87%, 14% 70%, 5% 51%, 7% 29%, 18% 13%, 34% 7%, 50% 16%, 66% 7%, 82% 13%, 93% 29%, 95% 51%, 86% 70%, 69% 87%);
}
</style>
