import { isAxiosError } from 'axios'

let database: Promise<IDBDatabase> | undefined

function openCache() {
  database ??= new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(`random-notes-novels:${import.meta.env.BASE_URL}`, 1)
    request.onupgradeneeded = () => request.result.createObjectStore('snapshots')
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
  return database
}

export async function readNovelCache<T>(userId: number, key: string): Promise<T | undefined> {
  try {
    const db = await openCache()
    return await new Promise<T | undefined>((resolve, reject) => {
      const request = db.transaction('snapshots').objectStore('snapshots').get(`${userId}:${key}`)
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  } catch {
    return undefined
  }
}

export async function cacheNovelData<T>(userId: number, key: string, data: T) {
  try {
    const db = await openCache()
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction('snapshots', 'readwrite')
      transaction.oncomplete = () => resolve()
      transaction.onabort = () => reject(transaction.error)
      transaction.objectStore('snapshots').put(data, `${userId}:${key}`)
    })
  } catch {
    // The live editor and recovery drafts can still work without cached server data.
  }
}

export async function loadNovelData<T>(userId: number, key: string, request: () => Promise<T>) {
  if (navigator.onLine) {
    try {
      const value = await request()
      void cacheNovelData(userId, key, value)
      return value
    } catch (error) {
      if (!isAxiosError(error) || error.response) throw error
    }
  }
  const cached = await readNovelCache<T>(userId, key)
  if (cached !== undefined) return cached
  throw new Error('暂无本机副本，请联网后打开。')
}
