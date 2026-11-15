<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const model = defineModel<string>({ required: true })
const emit = defineEmits<{ position: [] }>()
const field = ref<HTMLTextAreaElement>()
const mirror = ref<HTMLElement>()
const textWidth = ref(0)
const visibleHeight = ref(0)
const pageHeight = ref(1)
const lineHeight = ref(0)
const textHeight = ref(0)
const scrollTop = ref(0)
const linesPerPage = 28
const pages = computed(() => Math.max(1, Math.ceil(textHeight.value / pageHeight.value)))
const visiblePage = computed(() => Math.min(pages.value, Math.floor(scrollTop.value / pageHeight.value) + 1))
const dividerHeight = computed(() => Math.max(0, Math.min(
  visibleHeight.value, (pages.value - 1) * pageHeight.value - scrollTop.value,
)))
let observer: ResizeObserver | undefined

function measure() {
  const input = field.value
  const layout = mirror.value
  if (!input || !layout) return
  textWidth.value = input.clientWidth
  visibleHeight.value = input.clientHeight
  lineHeight.value = parseFloat(getComputedStyle(input).lineHeight)
  pageHeight.value = linesPerPage * lineHeight.value
  textHeight.value = layout.getBoundingClientRect().height
}

function recordScroll() {
  if (field.value) scrollTop.value = Math.max(0, field.value.scrollTop)
}

function recordPosition() {
  emit('position')
}

function getPosition() {
  const input = field.value
  if (!input) return
  return { start: input.selectionStart, end: input.selectionEnd, direction: input.selectionDirection, scroll: input.scrollTop }
}

function restorePosition(start: number, end: number, direction?: 'forward' | 'backward' | 'none', scroll?: number) {
  const input = field.value
  if (!input) return
  input.setSelectionRange(start, end, direction)
  if (typeof scroll === 'number') {
    input.scrollTop = scroll
  } else {
    // Positions saved by the previous editor only have character offsets.
    const layout = mirror.value
    const text = layout?.firstChild
    if (layout && text) {
      const caret = direction === 'backward' ? input.selectionStart : input.selectionEnd
      const range = document.createRange()
      range.setStart(text, caret)
      range.setEnd(text, caret + 1)
      const character = range.getClientRects()[0]
      if (character) input.scrollTop = Math.max(0, character.top - layout.getBoundingClientRect().top - lineHeight.value * 2)
    }
  }
  recordScroll()
}

defineExpose({ getPosition, restorePosition })
watch(model, measure, { flush: 'post' })
onMounted(() => {
  if (!field.value || !mirror.value) return
  field.value.setSelectionRange(0, 0)
  measure()
  observer = new ResizeObserver(measure)
  observer.observe(field.value)
  observer.observe(mirror.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col pt-4 sm:pt-6">
    <div class="relative min-h-0 flex-1 overflow-clip font-serif text-lg leading-8 sm:text-xl sm:leading-9">
      <div
        ref="mirror" v-text="model + '\u200b'" aria-hidden="true"
        class="manuscript-text invisible pointer-events-none absolute left-0 top-0"
        :style="{ width: textWidth ? `${textWidth}px` : '100%' }"
      />
      <textarea
        ref="field" v-model="model" aria-label="章节正文" placeholder="从这里开始写…" spellcheck="false"
        class="manuscript-text block h-full w-full resize-none overflow-y-auto outline-none"
        @scroll.passive="recordScroll" @select="recordPosition" @keyup="recordPosition" @blur="recordPosition"
      />
      <div
        v-if="dividerHeight"
        aria-hidden="true" class="page-dividers pointer-events-none absolute left-0 top-0"
        :style="{
          width: `${textWidth}px`,
          height: `${dividerHeight}px`,
          backgroundPositionY: `${-scrollTop}px`,
          '--page-height': `${pageHeight}px`,
        }"
      />
    </div>
    <footer class="flex h-9 shrink-0 items-center justify-end border-t border-slate-200 pr-2 text-xs text-slate-600 tabular-nums" aria-label="正文页码">
      第 {{ visiblePage }} 页 / 共 {{ pages }} 页
    </footer>
  </div>
</template>

<style scoped>
.manuscript-text {
  border: 0;
  padding: 0;
  font: inherit;
  letter-spacing: inherit;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  tab-size: 4;
}

textarea.manuscript-text {
  scrollbar-gutter: stable;
}

.page-dividers {
  background-image: repeating-linear-gradient(
    to bottom,
    transparent 0 calc(var(--page-height) - 2px),
    #d3dbdf calc(var(--page-height) - 2px) var(--page-height)
  );
}
</style>
