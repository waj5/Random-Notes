<script setup lang="ts">
import type { NoteBlock } from '../stores/notes'

defineProps<{ block: NoteBlock }>()
</script>

<template>
  <div class="mb-8">
    <!-- Text Only -->
    <div v-if="block.type === 'text-only'" class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap break-words">
      {{ block.content }}
    </div>

    <!-- Image Top -->
    <div v-else-if="block.type === 'image-top'" class="space-y-6">
      <div v-if="block.images.length > 0" class="overflow-hidden rounded-xl shadow-md">
        <img :src="block.images[0]" class="w-full h-auto object-cover transform hover:scale-105 transition-transform duration-700" />
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
      <div v-if="block.images.length > 0" class="overflow-hidden rounded-xl shadow-md">
        <img :src="block.images[0]" class="w-full h-auto object-cover transform hover:scale-105 transition-transform duration-700" />
      </div>
    </div>

    <!-- Split Left -->
    <div v-else-if="block.type === 'split-left'" class="clearfix relative mb-2">
      <div class="float-left w-5/12 mr-6 mb-2 relative z-10 space-y-4">
        <div v-for="(img, idx) in block.images" :key="idx" class="overflow-hidden rounded-xl shadow-md rotate-1 hover:rotate-0 transition-transform duration-300 bg-white p-2 pb-8">
           <img :src="img" class="w-full h-auto object-cover rounded-lg" />
        </div>
      </div>
      <div class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap break-words">
        {{ block.content }}
      </div>
    </div>

    <!-- Split Right -->
    <div v-else-if="block.type === 'split-right'" class="clearfix relative mb-2">
      <div class="float-right w-5/12 ml-6 mb-2 relative z-10 space-y-4">
        <div v-for="(img, idx) in block.images" :key="idx" class="overflow-hidden rounded-xl shadow-md -rotate-1 hover:rotate-0 transition-transform duration-300 bg-white p-2 pb-8">
           <img :src="img" class="w-full h-auto object-cover rounded-lg" />
        </div>
      </div>
      <div class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap break-words">
        {{ block.content }}
      </div>
    </div>

    <!-- Gallery Grid -->
    <div v-else-if="block.type === 'gallery-grid'" class="space-y-6">
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div v-for="(img, idx) in block.images" :key="idx" class="relative aspect-square overflow-hidden rounded-xl shadow-sm hover:shadow-md transition-shadow group">
            <img :src="img" class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500" />
        </div>
      </div>
      <div v-if="block.content" class="prose prose-lg max-w-none text-gray-800 font-serif leading-relaxed whitespace-pre-wrap text-center italic text-gray-600">
        {{ block.content }}
      </div>
    </div>
  </div>
</template>
