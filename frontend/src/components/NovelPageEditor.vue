<script setup lang="ts">
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const model = defineModel<string>({ required: true })
const emit = defineEmits<{ position: [] }>()
const viewport = ref<HTMLElement>()
const mirror = ref<HTMLElement>()
const field = ref<HTMLTextAreaElement>()
const pageHeight = ref(0)
const textHeight = ref(0)
const page = ref(0)
const pages = computed(() => pageHeight.value ? Math.max(1, Math.ceil(textHeight.value / pageHeight.value)) : 1)
let observer: ResizeObserver | undefined
let composing = false
let wheelDistance = 0
let lastWheelEvent = 0
let lastWheelTurn = -Infinity

function pageAt(offset: number) {
  const text = mirror.value?.firstChild
  if (!text || !pageHeight.value || !mirror.value) return 0
  const range = document.createRange()
  range.setStart(text, offset)
  // The next character identifies the visual line at a soft wrap. The mirror
  // includes a zero-width character to locate the caret at the very end.
  range.setEnd(text, offset + 1)
  const character = range.getClientRects()[0]
  if (!character) return page.value
  const lineCenter = character.top + character.height / 2 - mirror.value.getBoundingClientRect().top
  return Math.min(pages.value - 1, Math.max(0, Math.floor(lineCenter / pageHeight.value)))
}

function followCaret() {
  const input = field.value
  if (!input || composing || input.value !== model.value) return
  const offset = input.selectionDirection === 'backward' ? input.selectionStart : input.selectionEnd
  page.value = pageAt(offset)
}

function recordCaret() {
  if (composing) return
  followCaret()
  emit('position')
}

function startComposition() {
  composing = true
}

function endComposition() {
  composing = false
}

function measure() {
  if (!field.value || !mirror.value || !viewport.value) return
  const lineHeight = parseFloat(getComputedStyle(field.value).lineHeight)
  const availableHeight = viewport.value.getBoundingClientRect().height
  pageHeight.value = Math.max(1, Math.floor(availableHeight / lineHeight)) * lineHeight
  textHeight.value = mirror.value.getBoundingClientRect().height
  field.value.scrollTop = 0
  followCaret()
}

function turn(nextPage: number) {
  const input = field.value
  if (!input || composing || nextPage < 0 || nextPage >= pages.value || nextPage === page.value) return
  let low = 0
  let high = model.value.length
  while (low < high) {
    const middle = Math.floor((low + high) / 2)
    if (pageAt(middle) < nextPage) low = middle + 1
    else high = middle
  }
  input.setSelectionRange(low, low)
  page.value = nextPage
  emit('position')
}

function turnWithKeyboard(event: KeyboardEvent) {
  if (event.shiftKey || event.ctrlKey || event.metaKey || event.altKey || event.isComposing) return
  if (event.key !== 'PageUp' && event.key !== 'PageDown') return
  event.preventDefault()
  turn(page.value + (event.key === 'PageDown' ? 1 : -1))
}

function turnWithWheel(event: WheelEvent) {
  if (event.ctrlKey || event.shiftKey || Math.abs(event.deltaY) < Math.abs(event.deltaX) || pages.value < 2) return
  event.preventDefault()
  const now = performance.now()
  if (now - lastWheelEvent > 180) wheelDistance = 0
  lastWheelEvent = now
  if (now - lastWheelTurn < 300) return
  const delta = event.deltaMode === 0 ? event.deltaY : event.deltaY * 50
  if (Math.sign(wheelDistance) !== Math.sign(delta)) wheelDistance = 0
  wheelDistance += delta
  if (Math.abs(wheelDistance) < 55) return
  turn(page.value + Math.sign(wheelDistance))
  wheelDistance = 0
  lastWheelTurn = now
}

function getPosition() {
  const input = field.value
  if (!input) return
  return { start: input.selectionStart, end: input.selectionEnd, direction: input.selectionDirection }
}

function restorePosition(start: number, end: number, direction?: 'forward' | 'backward' | 'none') {
  field.value?.setSelectionRange(start, end, direction)
  followCaret()
}

defineExpose({ getPosition, restorePosition })
watch(model, measure, { flush: 'post' })
onMounted(() => {
  // Keep the first page visible when opening a chapter with no saved position.
  field.value?.setSelectionRange(0, 0)
  measure()
  observer = new ResizeObserver(measure)
  if (viewport.value) observer.observe(viewport.value)
  if (mirror.value) observer.observe(mirror.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col pt-4 sm:pt-6">
    <div ref="viewport" class="relative min-h-0 flex-1 overflow-clip font-serif text-lg leading-8 sm:text-xl sm:leading-9" @wheel="turnWithWheel">
      <div ref="mirror" v-text="model + '\u200b'" aria-hidden="true" class="manuscript-text invisible pointer-events-none" />
      <div class="relative overflow-clip" :style="{ height: pageHeight ? `${pageHeight}px` : '100%' }">
        <textarea
          ref="field" v-model="model" aria-label="章节正文" placeholder="从这里开始写…" spellcheck="false"
          class="manuscript-text resize-none overflow-hidden outline-none"
          :style="{ height: pageHeight ? `${pages * pageHeight}px` : '100%', transform: `translateY(${-page * pageHeight}px)` }"
          @select="recordCaret" @keyup="recordCaret" @click="recordCaret" @blur="recordCaret"
          @keydown="turnWithKeyboard" @compositionstart="startComposition" @compositionend="endComposition"
        />
      </div>
    </div>
    <nav aria-label="正文分页" class="flex h-12 shrink-0 items-center justify-between gap-2 border-t border-slate-200 text-sm text-slate-600">
      <button type="button" class="page-button" :disabled="page === 0" @click="turn(page - 1)">
        <ChevronLeft :size="17" aria-hidden="true" /> 上一页
      </button>
      <span role="status" aria-live="polite" class="tabular-nums">第 {{ page + 1 }} 页 / 共 {{ pages }} 页</span>
      <button type="button" class="page-button" :disabled="page + 1 >= pages" @click="turn(page + 1)">
        下一页 <ChevronRight :size="17" aria-hidden="true" />
      </button>
    </nav>
  </div>
</template>

<style scoped>
.manuscript-text {
  position: absolute;
  inset: 0 0 auto;
  width: 100%;
  border: 0;
  padding: 0;
  font: inherit;
  letter-spacing: inherit;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  tab-size: 4;
}

.page-button {
  display: inline-flex;
  min-height: 2.5rem;
  align-items: center;
  gap: 0.25rem;
  padding-inline: 0.5rem;
  border-radius: 0.5rem;
}

.page-button:hover:not(:disabled) {
  background-color: #e0eeec;
}

.page-button:focus-visible {
  outline: 2px solid #0f766e;
  outline-offset: 2px;
}

.page-button:disabled {
  opacity: 0.45;
}
</style>
