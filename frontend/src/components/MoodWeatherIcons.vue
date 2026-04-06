<script setup lang="ts">
import {
  Cloud,
  CloudFog,
  CloudLightning,
  CloudRain,
  CloudSnow,
  CloudSun,
  Coffee,
  Frown,
  Heart,
  Meh,
  Smile,
  Sun,
  Zap,
} from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps<{
  moodKey?: string | null
  weatherWmoCode?: number | null
  size?: number
  /** 仅显示天气（心情由下拉框等单独展示时使用） */
  weatherOnly?: boolean
}>()

const iconSize = computed(() => props.size ?? 22)

const moodComponent = computed(() => {
  switch (props.moodKey) {
    case 'happy':
      return Smile
    case 'love':
      return Heart
    case 'calm':
      return Coffee
    case 'sad':
      return Frown
    case 'excited':
      return Zap
    case 'meh':
      return Meh
    default:
      return null
  }
})

const weatherComponent = computed(() => {
  const c = props.weatherWmoCode
  if (c === null || c === undefined) return Cloud
  if (c === 0) return Sun
  if (c >= 1 && c <= 3) return CloudSun
  if (c >= 45 && c <= 48) return CloudFog
  if (c >= 51 && c <= 67) return CloudRain
  if (c >= 71 && c <= 77) return CloudSnow
  if (c >= 80 && c <= 82) return CloudRain
  if (c >= 85 && c <= 86) return CloudSnow
  if (c >= 95) return CloudLightning
  return Cloud
})
</script>

<template>
  <div class="flex items-center gap-2 text-slate-500">
    <component
      v-if="moodComponent && !weatherOnly"
      :is="moodComponent"
      :size="iconSize"
      class="shrink-0 text-rose-400"
      stroke-width="2"
      aria-hidden="true"
    />
    <component
      :is="weatherComponent"
      :size="iconSize"
      class="shrink-0 text-sky-500"
      stroke-width="2"
      aria-hidden="true"
    />
  </div>
</template>
