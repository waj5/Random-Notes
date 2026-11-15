import { isAxiosError } from 'axios'
import { defineStore } from 'pinia'
import { reactive, watch } from 'vue'
import { novelsApi, type Chapter, type Draft } from '../api/novels'
import { cacheNovelData } from '../utils/novelCache'
import { useAuthStore } from './auth'

interface PendingDraft extends Draft {
  novelId: number
  chapterId: number
  editId: string
  editedAt: number
}

export const novelWordCount = (body: string) => {
  let count = 0
  for (const character of body) {
    if (!/[\p{White_Space}\u001c-\u001f]/u.test(character)) count++
  }
  return count
}

export const useNovelDrafts = defineStore('novelDrafts', () => {
  const auth = useAuthStore()
  const drafts = reactive(new Map<string, PendingDraft>())
  const saved = reactive(new Map<string, Chapter>())
  const conflicts = reactive(new Map<string, Chapter>())
  const saving = reactive(new Set<string>())
  const storageErrors = reactive(new Set<string>())
  const errors = reactive(new Map<string, string>())
  const timers = new Map<string, number>()

  function prefix(userId: number) {
    return `novel-draft:${import.meta.env.BASE_URL}:${userId}:`
  }

  function key(userId: number, novelId: number, chapterId: number) {
    return `${prefix(userId)}${novelId}:${chapterId}`
  }

  function recover(userId: number) {
    try {
      for (const storageKey of Object.keys(localStorage)) {
        if (!storageKey.startsWith(prefix(userId)) || drafts.has(storageKey)) continue
        try {
          const draft: PendingDraft = JSON.parse(localStorage.getItem(storageKey) ?? 'null')
          if (draft && typeof draft.body === 'string' && typeof draft.title === 'string') {
            drafts.set(storageKey, draft)
          }
        } catch {
          // Leave unreadable entries in storage and recover the remaining drafts.
        }
      }
    } catch {
      // The first attempted edit surfaces a storage failure in the editor.
    }
  }

  function persist(storageKey: string, draft: PendingDraft) {
    drafts.set(storageKey, draft)
    try {
      localStorage.setItem(storageKey, JSON.stringify(draft))
      storageErrors.delete(storageKey)
    } catch {
      storageErrors.add(storageKey)
    }
  }

  function clear(storageKey: string, editId: string) {
    try {
      const entry = JSON.parse(localStorage.getItem(storageKey) ?? 'null')
      if (entry?.editId === editId) localStorage.removeItem(storageKey)
    } catch {
      // An already-synced copy can be reconciled on reopening.
    }
    drafts.delete(storageKey)
    storageErrors.delete(storageKey)
  }

  function schedule(userId: number, storageKey: string) {
    window.clearTimeout(timers.get(storageKey))
    timers.set(storageKey, window.setTimeout(() => {
      timers.delete(storageKey)
      void sync(userId, storageKey)
    }, 2000))
  }

  function edit(userId: number, novelId: number, chapterId: number, draft: Draft) {
    const storageKey = key(userId, novelId, chapterId)
    const editId = crypto.getRandomValues(new Uint32Array(4)).join('-')
    persist(storageKey, { ...draft, novelId, chapterId, editId, editedAt: Date.now() })
    schedule(userId, storageKey)
  }

  async function sync(userId: number, storageKey: string) {
    const draft = drafts.get(storageKey)
    if (!draft || saving.has(storageKey) || conflicts.has(storageKey) ||
        !navigator.onLine || !auth.isAuthenticated || auth.user?.id !== userId) return

    const title = draft.title.trim()
    if (!title) return
    saving.add(storageKey)
    errors.delete(storageKey)
    let sendNext = false
    try {
      const result = await novelsApi.save(draft.novelId, draft.chapterId, {
        title, body: draft.body, version: draft.version,
      })
      if (auth.user?.id !== userId) return
      if (result.code === 409) {
        conflicts.set(storageKey, result.data.server)
        void cacheNovelData(userId, storageKey, result.data.server)
        return
      }

      const chapter = result.data
      saved.set(storageKey, chapter)
      void cacheNovelData(userId, storageKey, chapter)
      const latest = drafts.get(storageKey)
      if (latest?.editId === draft.editId) clear(storageKey, draft.editId)
      else if (latest) {
        persist(storageKey, { ...latest, version: chapter.version })
        sendNext = !timers.has(storageKey)
      }
    } catch (error) {
      if (auth.user?.id === userId && navigator.onLine &&
          (!isAxiosError(error) || error.response || error.code === 'ECONNABORTED')) {
        errors.set(storageKey, '同步失败，请重试')
      }
    } finally {
      saving.delete(storageKey)
      if (sendNext) void sync(userId, storageKey)
    }
  }

  async function retryAll(userId: number) {
    recover(userId)
    for (const storageKey of drafts.keys()) {
      if (storageKey.startsWith(prefix(userId))) await sync(userId, storageKey)
    }
  }

  function resolve(userId: number, storageKey: string, useLocal: boolean) {
    const remote = conflicts.get(storageKey)
    const draft = drafts.get(storageKey)
    if (!remote || !draft) return
    conflicts.delete(storageKey)
    saved.set(storageKey, remote)
    if (useLocal) {
      persist(storageKey, { ...draft, version: remote.version })
      void sync(userId, storageKey)
    } else {
      clear(storageKey, draft.editId)
    }
  }

  watch(() => auth.user?.id, (userId) => {
    for (const timer of timers.values()) window.clearTimeout(timer)
    timers.clear()
    drafts.clear()
    saved.clear()
    conflicts.clear()
    storageErrors.clear()
    errors.clear()
    if (userId) recover(userId)
  }, { immediate: true, flush: 'sync' })

  function onOnline() {
    if (!auth.user || !navigator.onLine) return
    if (!auth.isAuthenticated) {
      void auth.fetchUser().then(onOnline).catch(() => {})
      return
    }
    void retryAll(auth.user.id)
  }

  window.addEventListener('online', onOnline)
  window.addEventListener('beforeunload', (event) => {
    if (!storageErrors.size) return
    event.preventDefault()
    event.returnValue = ''
  })
  watch(() => auth.isAuthenticated, authenticated => {
    if (authenticated && auth.user && navigator.onLine) void retryAll(auth.user.id)
  }, { immediate: true })

  return { drafts, saved, conflicts, saving, storageErrors, errors, key, edit, sync, resolve }
})
