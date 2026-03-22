<script setup lang="ts">
import { ref } from 'vue'
import type { GalleryTemplate, NoteBlock } from '../stores/notes'

defineProps<{ block: NoteBlock }>()

const previewImage = ref('')

const openPreview = (image: string) => {
  previewImage.value = image
}

const closePreview = () => {
  previewImage.value = ''
}

const getDownloadUrl = (image: string) => image.replace('/view?', '/download?')
const inlineImageClass = 'block h-auto w-auto max-w-full max-h-[420px] object-contain cursor-zoom-in'

const getGalleryTemplate = (block: NoteBlock): GalleryTemplate => block.galleryTemplate || 'grid'

const getGalleryContainerClass = (block: NoteBlock) => {
  switch (getGalleryTemplate(block)) {
    case 'mosaic':
      return 'grid grid-cols-3 auto-rows-[120px] md:auto-rows-[140px] gap-4'
    case 'spotlight':
      return 'grid grid-cols-4 auto-rows-[100px] md:auto-rows-[120px] gap-4'
    case 'film':
      return 'grid grid-cols-2 md:grid-cols-4 gap-4 rounded-[32px] bg-[#1f1f1f] p-5'
    case 'heart':
      return 'heart-gallery mx-auto grid aspect-square w-full max-w-[480px] overflow-hidden bg-rose-50/70'
    default:
      return 'grid grid-cols-2 md:grid-cols-3 gap-4'
  }
}

const getGalleryItemClass = (block: NoteBlock, index: number) => {
  switch (getGalleryTemplate(block)) {
    case 'mosaic': {
      const pattern = index % 5
      if (pattern === 0) return 'relative col-span-2 row-span-2 overflow-hidden rounded-[28px] shadow-md'
      if (pattern === 4) return 'relative col-span-2 row-span-1 overflow-hidden rounded-[28px] shadow-md'
      return 'relative col-span-1 row-span-1 overflow-hidden rounded-[28px] shadow-md'
    }
    case 'spotlight':
      return index % 4 === 0
        ? 'relative col-span-2 row-span-2 overflow-hidden rounded-[28px] shadow-md'
        : 'relative col-span-2 row-span-1 overflow-hidden rounded-[28px] shadow-md'
    case 'film':
      return 'relative aspect-[3/4] overflow-hidden rounded-[24px] border border-white/10 bg-black/30 p-2 shadow-md'
    case 'heart':
      return 'relative overflow-hidden'
    default:
      return 'relative aspect-square overflow-hidden rounded-xl shadow-sm hover:shadow-md transition-shadow group'
  }
}

const getGalleryImageClass = (block: NoteBlock) => {
  if (getGalleryTemplate(block) === 'film') {
    return 'w-full h-full object-cover rounded-[18px] cursor-zoom-in'
  }
  return 'w-full h-full object-cover cursor-zoom-in'
}

const getHeartGridStyle = (block: NoteBlock) => {
  const count = Math.max(block.images.length, 1)
  const cols = Math.ceil(Math.sqrt(count))
  const rows = Math.ceil(count / cols)
  const gap = count <= 2 ? '6px' : count <= 6 ? '4px' : '3px'

  return {
    gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
    gridTemplateRows: `repeat(${rows}, minmax(0, 1fr))`,
    gap
  }
}
</script>

<template>
  <div class="mb-8">
    <!-- Text Only -->
    <div v-if="block.type === 'text-only'" class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap break-words">
      {{ block.content }}
    </div>

    <!-- Image Top -->
    <div v-else-if="block.type === 'image-top'" class="space-y-6">
      <div v-if="block.images.length > 0" class="inline-flex max-w-full overflow-hidden rounded-xl shadow-md">
        <img :src="block.images[0]" :class="`${inlineImageClass} transform hover:scale-105 transition-transform duration-700`" @click="block.images[0] && openPreview(block.images[0])" @contextmenu.prevent @dragstart.prevent />
      </div>
      <div v-if="block.content" class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap">
        {{ block.content }}
      </div>
    </div>

    <!-- Image Bottom -->
    <div v-else-if="block.type === 'image-bottom'" class="space-y-6">
      <div v-if="block.content" class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap">
        {{ block.content }}
      </div>
      <div v-if="block.images.length > 0" class="inline-flex max-w-full overflow-hidden rounded-xl shadow-md">
        <img :src="block.images[0]" :class="`${inlineImageClass} transform hover:scale-105 transition-transform duration-700`" @click="block.images[0] && openPreview(block.images[0])" @contextmenu.prevent @dragstart.prevent />
      </div>
    </div>

    <!-- Split Left -->
    <div v-else-if="block.type === 'split-left'" class="mb-2 flex items-start gap-6">
      <div class="relative z-10 flex max-w-[45%] shrink-0 flex-col space-y-4">
        <div v-for="(img, idx) in block.images" :key="idx" class="inline-block max-w-full overflow-hidden rounded-xl shadow-md rotate-1 hover:rotate-0 transition-transform duration-300 bg-white p-2 pb-8">
           <img :src="img" class="block h-auto w-auto max-w-full max-h-[320px] object-contain rounded-lg cursor-zoom-in" @click="openPreview(img)" @contextmenu.prevent @dragstart.prevent />
        </div>
      </div>
      <div class="min-w-0 flex-1 prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap break-words">
        {{ block.content }}
      </div>
    </div>

    <!-- Split Right -->
    <div v-else-if="block.type === 'split-right'" class="mb-2 flex items-start gap-6">
      <div class="min-w-0 flex-1 prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap break-words">
        {{ block.content }}
      </div>
      <div class="relative z-10 flex max-w-[45%] shrink-0 flex-col space-y-4">
        <div v-for="(img, idx) in block.images" :key="idx" class="inline-block max-w-full overflow-hidden rounded-xl shadow-md -rotate-1 hover:rotate-0 transition-transform duration-300 bg-white p-2 pb-8">
           <img :src="img" class="block h-auto w-auto max-w-full max-h-[320px] object-contain rounded-lg cursor-zoom-in" @click="openPreview(img)" @contextmenu.prevent @dragstart.prevent />
        </div>
      </div>
    </div>

    <!-- Gallery Grid -->
    <div v-else-if="block.type === 'gallery-grid'" class="space-y-6">
      <div :class="getGalleryContainerClass(block)" :style="getGalleryTemplate(block) === 'heart' ? getHeartGridStyle(block) : undefined">
        <div v-for="(img, idx) in block.images" :key="idx" :class="getGalleryItemClass(block, idx)">
            <img :src="img" :class="getGalleryImageClass(block)" @click="openPreview(img)" @contextmenu.prevent @dragstart.prevent />
        </div>
      </div>
      <div v-if="block.content" class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap text-center italic text-gray-600">
        {{ block.content }}
      </div>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="previewImage" class="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center p-4 cursor-zoom-out" @click="closePreview">
      <div class="relative flex max-h-[calc(100vh-2rem)] max-w-[calc(100vw-2rem)] items-center justify-center" @click.stop @contextmenu.prevent>
        <a
          :href="getDownloadUrl(previewImage)"
          class="absolute right-3 top-3 z-10 rounded-full bg-black/60 px-4 py-2 text-sm text-white transition hover:bg-black/75"
        >
          下载原图
        </a>
        <img
          :src="previewImage"
          class="block max-h-[calc(100vh-2rem)] max-w-[calc(100vw-2rem)] object-contain rounded-lg shadow-2xl"
          @contextmenu.prevent
          @dragstart.prevent
        />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.heart-gallery {
  clip-path: polygon(50% 100%, 31% 87%, 14% 70%, 5% 51%, 7% 29%, 18% 13%, 34% 7%, 50% 16%, 66% 7%, 82% 13%, 93% 29%, 95% 51%, 86% 70%, 69% 87%);
}
</style>
