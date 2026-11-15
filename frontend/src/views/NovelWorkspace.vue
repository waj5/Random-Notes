<script setup lang="ts">
import { isAxiosError } from 'axios'
import { ArrowDown, ArrowLeft, ArrowUp, Download, List, Maximize2, Minimize2, Plus, X } from 'lucide-vue-next'
import { computed, nextTick, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { novelsApi, type Chapter, type ChapterEntry, type Novel } from '../api/novels'
import NovelPageEditor from '../components/NovelPageEditor.vue'
import { useAuthStore } from '../stores/auth'
import { novelWordCount, useNovelDrafts } from '../stores/novelDrafts'
import { cacheNovelData, loadNovelData, readNovelCache } from '../utils/novelCache'

const props = defineProps<{ novelId: number }>()
const auth = useAuthStore()
const drafts = useNovelDrafts()
const route = useRoute()
const router = useRouter()
const novel = shallowRef<Novel>()
const chapter = shallowRef<Chapter>()
const selected = ref<number>()
const editor = ref<InstanceType<typeof NovelPageEditor>>()
const directoryButton = ref<HTMLButtonElement>()
const directoryClose = ref<HTMLButtonElement>()
const directoryOpen = ref(false)
const focused = ref(false)
const offline = ref(!navigator.onLine)
const busy = ref(false)
const loading = ref(true)
const loadingChapter = ref(false)
const error = ref('')
const viewportHeight = ref<number>()
let bookRequest = 0
let chapterRequest = 0

const userId = computed(() => auth.user?.id)
const novelKey = computed(() => `novel:${props.novelId}`)
const activeKey = computed(() => userId.value && selected.value
  ? drafts.key(userId.value, props.novelId, selected.value) : '')
const remoteChapter = computed(() => drafts.saved.get(activeKey.value) ?? chapter.value)
const pending = computed(() => drafts.drafts.get(activeKey.value))
const conflict = computed(() => drafts.conflicts.get(activeKey.value))
const localStorageFailed = computed(() => drafts.storageErrors.has(activeKey.value))
const syncError = computed(() => drafts.errors.get(activeKey.value))
const current = computed(() => pending.value ?? remoteChapter.value)
const savingLabel = computed(() => {
  if (conflict.value) return '有两份稿件'
  if (localStorageFailed.value) return '本机保存失败'
  if (drafts.saving.has(activeKey.value)) return '保存中…'
  if (syncError.value) return syncError.value
  if (pending.value) return '已暂存本机'
  return '已同步'
})

function edit(field: 'title' | 'body', value: string) {
  if (!current.value || !userId.value || !selected.value || value === current.value[field]) return
  const { title, body, version } = current.value
  drafts.edit(userId.value, props.novelId, selected.value, { title, body, version, [field]: value })
}

const title = computed({
  get: () => current.value?.title ?? '',
  set: value => edit('title', value),
})
const body = computed({
  get: () => current.value?.body ?? '',
  set: value => edit('body', value),
})
const count = computed(() => novelWordCount(body.value))
const countFormat = new Intl.NumberFormat('zh-CN')

function directoryTitle(entry: ChapterEntry) {
  if (!userId.value) return entry.title
  const key = drafts.key(userId.value, props.novelId, entry.id)
  return drafts.drafts.get(key)?.title.trim() || drafts.saved.get(key)?.title ||
    (chapter.value?.id === entry.id ? chapter.value.title : entry.title)
}

function cursorKey(id: number) {
  return `novel-position:${import.meta.env.BASE_URL}:${userId.value}:${props.novelId}:${id}`
}

function rememberPosition(id = selected.value) {
  if (!id || id !== selected.value || !userId.value) return
  const position = editor.value?.getPosition()
  if (!position) return
  try {
    localStorage.setItem(cursorKey(id), JSON.stringify(position))
  } catch {
    // The cursor can be restored independently of draft recovery.
  }
}

function restorePosition(id: number) {
  const field = editor.value
  if (!field || id !== selected.value) return
  try {
    const position = JSON.parse(localStorage.getItem(cursorKey(id)) ?? 'null')
    if (!position) return
    field.restorePosition(position.start, position.end, position.direction)
  } catch {
    // Use the browser's default position when the snapshot is unavailable.
  }
}

function closeDirectory(restoreFocus = false) {
  directoryOpen.value = false
  if (restoreFocus) void nextTick(() => directoryButton.value?.focus())
}

function toggleDirectory() {
  directoryOpen.value = !directoryOpen.value
  if (directoryOpen.value) void nextTick(() => directoryClose.value?.focus())
}

async function openChapter(id: number, supplied?: Chapter) {
  if (!userId.value) return
  if (selected.value === id && chapter.value && !supplied) {
    closeDirectory(true)
    return
  }
  const account = userId.value
  const bookId = props.novelId
  const request = ++chapterRequest
  const key = drafts.key(account, bookId, id)
  rememberPosition()
  closeDirectory(directoryOpen.value)
  selected.value = id
  chapter.value = undefined
  loadingChapter.value = true
  error.value = ''
  void router.replace({ query: { ...route.query, chapter: String(id) } })
  try {
    let data = supplied
    if (!data) {
      try {
        data = await loadNovelData(account, key, () => novelsApi.chapter(bookId, id))
      } catch (cause) {
        const local = drafts.drafts.get(key)
        const entry = novel.value?.chapters.find(item => item.id === id)
        if (!local || !entry || (isAxiosError(cause) && cause.response)) throw cause
        data = { ...entry, ...local, novel_id: bookId, updated_at: '' }
      }
    } else {
      void cacheNovelData(account, key, data)
    }
    if (request !== chapterRequest || userId.value !== account) return
    if ((drafts.saved.get(key)?.version ?? 0) <= data.version) drafts.saved.delete(key)
    const local = drafts.drafts.get(key)
    if (local && local.version < data.version && !drafts.saving.has(key) &&
        (local.title.trim() !== data.title || local.body !== data.body)) {
      const previous = drafts.conflicts.get(key)
      if (!previous || previous.version < data.version) drafts.conflicts.set(key, data)
    }
    chapter.value = data
  } catch (cause) {
    if (request === chapterRequest) {
      error.value = offline.value && cause instanceof Error ? cause.message : '章节加载失败，请重试。'
    }
  } finally {
    if (request === chapterRequest) loadingChapter.value = false
  }
}

async function loadBook() {
  const account = userId.value
  if (!account) return
  const request = ++bookRequest
  const id = props.novelId
  try {
    error.value = ''
    const value = await loadNovelData(account, novelKey.value, () => novelsApi.get(id))
    if (request !== bookRequest || userId.value !== account) return
    novel.value = value
    const requested = Number(route.query.chapter)
    const local = [...drafts.drafts.values()]
      .filter(draft => draft.novelId === id)
      .sort((first, second) => second.editedAt - first.editedAt)[0]
    const next = [selected.value, requested, local?.chapterId, value.last_chapter_id, value.chapters[0]?.id]
      .find(candidate => value.chapters.some(entry => entry.id === candidate))
    if (next && !chapter.value) await openChapter(next)
  } catch (cause) {
    if (request === bookRequest) {
      error.value = offline.value && cause instanceof Error ? cause.message : '作品加载失败，请重试。'
    }
  } finally {
    if (request === bookRequest) loading.value = false
  }
}

function updateDirectory(entries: ChapterEntry[]) {
  if (!novel.value || !userId.value) return
  novel.value = { ...novel.value, chapters: entries }
  void cacheNovelData(userId.value, novelKey.value, novel.value)
}

async function addChapter() {
  if (busy.value || offline.value || !novel.value) return
  busy.value = true
  error.value = ''
  try {
    const added = await novelsApi.addChapter(props.novelId)
    await loadBook()
    await openChapter(added.id, added)
  } catch {
    error.value = '新建章节失败，请重试。'
  } finally {
    busy.value = false
  }
}

async function moveChapter(index: number, offset: number) {
  if (busy.value || offline.value || !novel.value) return
  const order = [...novel.value.chapters]
  const from = order[index]
  const to = order[index + offset]
  if (!from || !to) return
  order[index] = to
  order[index + offset] = from
  busy.value = true
  error.value = ''
  try {
    await novelsApi.reorder(props.novelId, order.map(entry => entry.id))
    updateDirectory(order.map((entry, position) => ({ ...entry, position })))
  } catch (cause) {
    if (isAxiosError(cause) && cause.response?.status === 409) {
      await loadBook()
      error.value = '目录已有变动，已刷新，请重新排序。'
    } else {
      error.value = '调整章节顺序失败，请重试。'
    }
  } finally {
    busy.value = false
  }
}

async function downloadManuscript() {
  if (busy.value || !novel.value || !userId.value) return
  const account = userId.value
  busy.value = true
  error.value = ''
  try {
    const entries = offline.value ? novel.value.chapters : await novelsApi.manuscript(props.novelId)
    const parts = await Promise.all(entries.map(async entry => {
      const key = drafts.key(account, props.novelId, entry.id)
      const text = drafts.drafts.get(key) ?? ('body' in entry ? entry :
        drafts.saved.get(key) ?? await readNovelCache<Chapter>(account, key))
      if (!text) throw new Error('章节尚未全部保存在本机，请联网后导出。')
      return `${text.title.trim() || entry.title}\n\n${text.body}`
    }))
    const blob = new Blob([novel.value.title, '\n\n', parts.join('\n\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${novel.value.title.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')}.txt`
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (cause) {
    error.value = offline.value && cause instanceof Error ? cause.message : '导出失败，请重试。'
  } finally {
    busy.value = false
  }
}

function resolve(useLocal: boolean) {
  if (!userId.value || (!useLocal && !window.confirm('使用服务器稿并舍弃这份本机稿？'))) return
  drafts.resolve(userId.value, activeKey.value, useLocal)
}

function retry() {
  if (userId.value) void drafts.sync(userId.value, activeKey.value)
}

function onNetworkChange() {
  offline.value = !navigator.onLine
  if (!offline.value) void loadBook()
}

function resizeEditor() {
  const viewport = window.visualViewport
  viewportHeight.value = viewport?.scale === 1 ? Math.min(window.innerHeight, viewport.height) : undefined
}

function onPageHide() {
  rememberPosition()
}

onBeforeRouteLeave(() => {
  rememberPosition()
  if (localStorageFailed.value) return window.confirm('这份稿件未能保存在本机。仍要离开？')
})
watch(editor, field => {
  if (field && selected.value) restorePosition(selected.value)
}, { flush: 'post' })
watch(() => props.novelId, () => {
  chapterRequest++
  novel.value = undefined
  chapter.value = undefined
  selected.value = undefined
  loading.value = true
  void loadBook()
})
onMounted(() => {
  void loadBook()
  resizeEditor()
  window.visualViewport?.addEventListener('resize', resizeEditor)
  window.addEventListener('online', onNetworkChange)
  window.addEventListener('offline', onNetworkChange)
  window.addEventListener('pagehide', onPageHide)
})
onUnmounted(() => {
  bookRequest++
  chapterRequest++
  window.removeEventListener('online', onNetworkChange)
  window.removeEventListener('offline', onNetworkChange)
  window.removeEventListener('pagehide', onPageHide)
  window.visualViewport?.removeEventListener('resize', resizeEditor)
})
</script>

<template>
  <main
    class="novel-workspace bg-[#fbfaf7] text-slate-800"
    :style="viewportHeight ? { height: `${viewportHeight}px` } : undefined"
    @keydown.esc="directoryOpen ? closeDirectory(true) : focused = false"
  >
    <header class="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 sm:h-16 sm:px-6">
      <div class="flex min-w-0 items-center gap-3">
        <RouterLink :to="{ name: 'novels' }" class="workspace-button shrink-0" aria-label="返回我的小说" title="返回我的小说">
          <ArrowLeft :size="19" aria-hidden="true" />
        </RouterLink>
        <h1 v-if="novel" class="truncate font-serif text-lg font-semibold sm:text-xl">{{ novel.title }}</h1>
      </div>
      <div class="flex shrink-0 items-center gap-1 sm:gap-3">
        <button
          ref="directoryButton" type="button" class="workspace-button mobile-directory-control gap-1.5"
          :aria-expanded="directoryOpen" aria-controls="chapter-directory" @click="toggleDirectory"
        ><List :size="19" aria-hidden="true" /> 目录</button>
        <button
          v-if="novel" type="button" class="workspace-button gap-1.5" :disabled="busy"
          aria-label="导出 TXT" title="导出 TXT" @click="downloadManuscript"
        ><Download :size="18" aria-hidden="true" /><span class="hidden sm:inline">导出 TXT</span></button>
        <button
          v-if="novel" type="button" class="workspace-button gap-1.5" :aria-pressed="focused"
          aria-label="专注模式" title="专注模式" @click="focused = !focused; closeDirectory()"
        >
          <component :is="focused ? Minimize2 : Maximize2" :size="18" aria-hidden="true" />
          <span class="hidden sm:inline">{{ focused ? '退出专注' : '专注' }}</span>
        </button>
      </div>
    </header>

    <p v-if="error" role="alert" class="shrink-0 border-b border-red-100 bg-red-50 px-5 py-2.5 text-sm text-red-800">
      {{ error }}
      <button v-if="!chapter && !offline" type="button" class="ml-2 underline" @click="loadBook">重试</button>
    </p>

    <div class="relative flex min-h-0 flex-1">
      <button
        v-if="directoryOpen" type="button" class="absolute inset-0 z-10 bg-slate-950/30 lg:hidden"
        aria-label="关闭章节目录" @click="closeDirectory(true)"
      />
      <aside
        id="chapter-directory"
        class="absolute inset-y-0 left-0 z-20 w-72 max-w-[85vw] flex-col border-r border-slate-200 bg-[#f5f8f8] lg:static"
        :class="directoryOpen ? 'flex' : focused ? 'hidden' : 'hidden lg:flex'"
        aria-label="章节目录"
      >
        <div class="flex shrink-0 items-center justify-between gap-2 px-4 py-4">
          <h2 class="text-sm font-semibold text-slate-700">章节目录</h2>
          <div class="flex items-center gap-1">
            <button
              type="button" class="workspace-button gap-1 bg-teal-100 text-teal-900"
              :disabled="busy || offline || !novel" @click="addChapter"
            ><Plus :size="16" aria-hidden="true" /> 新增章节</button>
            <button
              ref="directoryClose" type="button" class="workspace-button mobile-directory-control" aria-label="关闭目录"
              @click="closeDirectory(true)"
            ><X :size="18" aria-hidden="true" /></button>
          </div>
        </div>
        <ol v-if="novel" class="min-h-0 flex-1 space-y-1 overflow-y-auto px-2 pb-3 sm:px-3">
          <li
            v-for="(entry, index) in novel.chapters" :key="entry.id"
            class="flex items-center gap-0.5 rounded-lg"
            :class="selected === entry.id ? 'bg-teal-100/80 text-teal-950' : 'hover:bg-white'"
          >
            <button
              type="button" :aria-current="selected === entry.id ? 'true' : undefined"
              class="min-w-0 flex-1 truncate rounded-lg px-2 py-2.5 text-left text-sm"
              @click="openChapter(entry.id)"
            >{{ directoryTitle(entry) }}</button>
            <button
              type="button" class="workspace-button px-1!" :disabled="busy || offline || index === 0"
              :aria-label="`上移 ${directoryTitle(entry)}`" title="上移" @click="moveChapter(index, -1)"
            ><ArrowUp :size="15" aria-hidden="true" /></button>
            <button
              type="button" class="workspace-button mr-1 px-1!" :disabled="busy || offline || index === novel.chapters.length - 1"
              :aria-label="`下移 ${directoryTitle(entry)}`" title="下移" @click="moveChapter(index, 1)"
            ><ArrowDown :size="15" aria-hidden="true" /></button>
          </li>
        </ol>
      </aside>

      <section class="min-w-0 flex-1" aria-label="章节编辑器">
        <p v-if="loading || loadingChapter" class="mx-auto max-w-3xl p-6 text-sm text-slate-600">加载章节中…</p>
        <div v-else-if="chapter && current" class="mx-auto flex h-full max-w-3xl flex-col px-4 sm:px-9">
          <div class="shrink-0 border-b border-slate-200/90 pb-2 pt-4 sm:pb-3 sm:pt-7">
            <input
              :key="chapter.id" v-model="title" aria-label="章节标题" maxlength="100" placeholder="章节标题"
              class="w-full rounded-sm bg-transparent font-serif text-2xl font-semibold outline-offset-4 focus-visible:outline-teal-700 sm:text-3xl"
              @blur="!title.trim() && remoteChapter && (title = remoteChapter.title)"
            />
            <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-600 sm:text-sm">
              <span>{{ countFormat.format(count) }} 字</span>
              <span role="status" :class="{ 'text-red-800': localStorageFailed || syncError, 'text-amber-800': conflict }">{{ savingLabel }}</span>
              <span v-if="offline">离线</span>
              <button v-if="pending && !conflict && !offline" class="font-medium text-teal-800 underline" type="button" @click="retry">立即同步</button>
            </div>
            <p v-if="localStorageFailed" role="alert" class="mt-2 text-sm text-red-800">
              本机空间不足或不可用。请先同步，或导出 TXT 保存副本。
            </p>
          </div>

          <details v-if="conflict" class="my-2 max-h-[42%] shrink-0 overflow-auto rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm">
            <summary class="cursor-pointer font-semibold text-amber-950">服务器上有新版本，查看两份稿件</summary>
            <div class="mt-3 grid gap-2 sm:grid-cols-2">
              <label class="min-w-0">
                <span class="block truncate pb-1 font-medium">本机稿 · {{ title }}</span>
                <textarea :value="body" readonly aria-label="本机稿" class="h-28 w-full resize-none rounded border border-amber-200 bg-white p-2" />
              </label>
              <label class="min-w-0">
                <span class="block truncate pb-1 font-medium">服务器稿 · {{ conflict.title }}</span>
                <textarea :value="conflict.body" readonly aria-label="服务器稿" class="h-28 w-full resize-none rounded border border-amber-200 bg-white p-2" />
              </label>
            </div>
            <div class="mt-2 flex flex-wrap gap-2">
              <button type="button" class="workspace-button bg-teal-800 text-white hover:bg-teal-900!" @click="resolve(true)">使用本机稿</button>
              <button type="button" class="workspace-button border border-amber-300 bg-white" @click="resolve(false)">使用服务器稿</button>
            </div>
          </details>

          <NovelPageEditor :key="chapter.id" ref="editor" v-model="body" @position="rememberPosition(chapter.id)" />
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.novel-workspace {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

.workspace-button {
  display: inline-flex;
  min-height: 2.25rem;
  min-width: 1.5rem;
  align-items: center;
  justify-content: center;
  padding-inline: 0.5rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.workspace-button:hover:not(:disabled) {
  background-color: #e0eeec;
}

.workspace-button:disabled {
  opacity: 0.35;
}

@media (min-width: 64rem) {
  .mobile-directory-control {
    display: none;
  }
}

button:focus-visible,
a:focus-visible,
summary:focus-visible {
  outline: 2px solid #0f766e;
  outline-offset: 2px;
}
</style>
