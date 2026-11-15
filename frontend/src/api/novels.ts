import apiClient from './client'

export interface NovelSummary {
  id: number
  title: string
  chapter_count: number
  word_count: number
  last_chapter_id: number | null
  updated_at: string
}

export interface ChapterEntry {
  id: number
  title: string
  position: number
  word_count: number
}

export interface Chapter extends ChapterEntry {
  novel_id: number
  body: string
  version: number
  updated_at: string
}

export interface Novel extends NovelSummary {
  chapters: ChapterEntry[]
}

export type Draft = Pick<Chapter, 'title' | 'body' | 'version'>
type SaveResponse =
  | { code: 0; data: Chapter }
  | { code: 409; data: { server: Chapter } }

const options = { timeout: 12000 }
const chapterPath = (novelId: number, id: number) => `/novels/${novelId}/chapters/${id}`

export const novelsApi = {
  list: async () => (await apiClient.get<{ data: NovelSummary[] }>('/novels', options)).data.data,
  create: async (title: string) =>
    (await apiClient.post<{ data: NovelSummary }>('/novels', { title }, options)).data.data,
  get: async (id: number) =>
    (await apiClient.get<{ data: Novel }>(`/novels/${id}`, options)).data.data,
  chapter: async (novelId: number, id: number) =>
    (await apiClient.get<{ data: Chapter }>(chapterPath(novelId, id), options)).data.data,
  addChapter: async (id: number) =>
    (await apiClient.post<{ data: Chapter }>(`/novels/${id}/chapters`, undefined, options)).data.data,
  reorder: async (id: number, chapterIds: number[]) =>
    apiClient.put(`/novels/${id}/chapter-order`, { chapter_ids: chapterIds }, options),
  save: async (novelId: number, id: number, draft: Draft) =>
    (await apiClient.put<SaveResponse>(chapterPath(novelId, id), draft, {
      ...options,
      validateStatus: status => status === 200 || status === 409,
    })).data,
  manuscript: async (id: number) =>
    (await apiClient.get<{ data: Chapter[] }>(`/novels/${id}/manuscript`, options)).data.data,
}
