<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotesStore } from '../stores/notes'
import type { Note } from '../stores/notes'
import { useAuthStore } from '../stores/auth'
import apiClient from '../api/client'
import { ArrowLeft, Edit, Trash2 } from 'lucide-vue-next'
import BlockViewer from '../components/BlockViewer.vue'

interface NoteComment {
  id: number
  note_id: number
  user_id: number
  username: string
  nickname: string
  avatar_url?: string
  content: string
  created_at: string
}

const route = useRoute()
const router = useRouter()
const notesStore = useNotesStore()
const authStore = useAuthStore()

const noteId = route.params.id as string
const note = ref<Note | undefined>(undefined)
const loading = ref(true)
const isOwner = computed(() => note.value?.userId === authStore.user?.id)
const comments = ref<NoteComment[]>([])
const commentContent = ref('')
const isSubmittingComment = ref(false)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const editingCommentId = ref<number | null>(null)
const editingCommentContent = ref('')
const isSavingEdit = ref(false)

const loadComments = async () => {
  const response = await apiClient.get(`/notes/${noteId}/comments/`)
  comments.value = response.data.data
}

onMounted(async () => {
  loading.value = true
  try {
    note.value = await notesStore.getNoteById(noteId)
    await loadComments()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const deleteNote = async () => {
  if (confirm('确定要删除这篇随想吗？')) {
    await notesStore.deleteNote(noteId)
    router.push('/mine')
  }
}

const submitComment = async () => {
  const content = commentContent.value.trim()
  if (!content || isSubmittingComment.value) return

  isSubmittingComment.value = true
  try {
    await apiClient.post(`/notes/${noteId}/comments/`, { content })
    commentContent.value = ''
    await loadComments()
  } catch (error) {
    console.error('Failed to create comment:', error)
    alert('评论失败')
  } finally {
    isSubmittingComment.value = false
  }
}

const canDeleteComment = (comment: NoteComment) => {
  return authStore.user?.id === comment.user_id || isOwner.value
}

const canEditComment = (comment: NoteComment) => {
  return authStore.user?.id === comment.user_id
}

const startEditComment = (comment: NoteComment) => {
  editingCommentId.value = comment.id
  editingCommentContent.value = comment.content
}

const cancelEditComment = () => {
  editingCommentId.value = null
  editingCommentContent.value = ''
}

const saveEditComment = async (commentId: number) => {
  const content = editingCommentContent.value.trim()
  if (!content || isSavingEdit.value) return

  isSavingEdit.value = true
  try {
    await apiClient.put(`/notes/${noteId}/comments/${commentId}`, { content })
    cancelEditComment()
    await loadComments()
  } catch (error) {
    console.error('Failed to update comment:', error)
    alert('编辑评论失败')
  } finally {
    isSavingEdit.value = false
  }
}

const deleteComment = async (commentId: number) => {
  if (!confirm('确定要删除这条评论吗？')) return

  try {
    await apiClient.delete(`/notes/${noteId}/comments/${commentId}`)
    if (editingCommentId.value === commentId) {
      cancelEditComment()
    }
    await loadComments()
  } catch (error) {
    console.error('Failed to delete comment:', error)
    alert('删除评论失败')
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-[#EBF4FF] to-[#F0FAFF] font-sans">
    <!-- Navbar -->
    <header class="bg-white/60 backdrop-blur-md border-b border-white/50 sticky top-0 z-50 transition-all duration-300">
      <div class="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
        <button @click="router.back()" class="p-2 hover:bg-gray-100 rounded-full text-gray-600 transition-colors group">
          <ArrowLeft :size="20" class="group-hover:-translate-x-1 transition-transform" />
        </button>
        
        <div class="flex items-center gap-2" v-if="note && isOwner">
          <button 
            @click="router.push(`/edit/${noteId}`)"
            class="p-2 hover:bg-blue-50 text-gray-600 hover:text-blue-600 rounded-full transition-colors"
            title="编辑"
          >
            <Edit :size="20" />
          </button>
          <button 
            @click="deleteNote"
            class="p-2 hover:bg-red-50 text-gray-600 hover:text-red-500 rounded-full transition-colors"
            title="删除"
          >
            <Trash2 :size="20" />
          </button>
        </div>
      </div>
    </header>

    <main v-if="loading" class="max-w-3xl mx-auto px-6 py-12 flex justify-center">
       <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </main>

    <main v-else-if="note" class="max-w-4xl mx-auto px-8 py-12 space-y-8 bg-white/80 backdrop-blur-sm my-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] min-h-[calc(100vh-8rem)]">
      <div class="text-center space-y-4 pb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-gray-800 tracking-tight leading-tight">{{ note.title }}</h1>
        <div class="text-sm text-gray-400 font-medium tracking-wide">
          {{ new Date(note.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}
        </div>
      </div>

      <div class="space-y-12 py-4 min-h-[40vh]">
        <BlockViewer v-for="block in note.blocks" :key="block.id" :block="block" />
      </div>

      <section class="space-y-5 border-t border-gray-100 pt-8">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-800">评论 {{ comments.length }}</h2>
        </div>

        <div v-if="isAuthenticated" class="space-y-3 rounded-2xl border border-gray-100 bg-white/80 p-4">
          <textarea
            v-model="commentContent"
            placeholder="写下你的评论..."
            class="min-h-[100px] w-full resize-none rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm text-gray-700 outline-none"
          ></textarea>
          <div class="flex justify-end">
            <button
              @click="submitComment"
              :disabled="isSubmittingComment || !commentContent.trim()"
              class="rounded-full bg-blue-600 px-5 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {{ isSubmittingComment ? '发送中...' : '发布评论' }}
            </button>
          </div>
        </div>

        <div v-else class="rounded-2xl border border-dashed border-gray-200 bg-white/60 px-4 py-6 text-center text-sm text-gray-400">
          未登录只能查看评论，登录后才可以发表评论
        </div>

        <div v-if="comments.length > 0" class="space-y-4">
          <article v-for="comment in comments" :key="comment.id" class="rounded-2xl border border-gray-100 bg-white/80 p-4">
            <div class="flex items-start gap-3">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-600">
                {{ (comment.nickname || comment.username || '评').slice(0, 1) }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-3">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-semibold text-gray-800">{{ comment.nickname || comment.username }}</span>
                    <span class="text-xs text-gray-400">{{ new Date(comment.created_at).toLocaleString() }}</span>
                  </div>
                  <div v-if="isAuthenticated" class="flex items-center gap-3 text-xs">
                    <button
                      v-if="canEditComment(comment)"
                      @click="startEditComment(comment)"
                      class="text-blue-600 hover:underline"
                    >
                      编辑
                    </button>
                    <button
                      v-if="canDeleteComment(comment)"
                      @click="deleteComment(comment.id)"
                      class="text-red-500 hover:underline"
                    >
                      删除
                    </button>
                  </div>
                </div>
                <div v-if="editingCommentId === comment.id" class="mt-3 space-y-3">
                  <textarea
                    v-model="editingCommentContent"
                    class="min-h-[90px] w-full resize-none rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm text-gray-700 outline-none"
                  ></textarea>
                  <div class="flex justify-end gap-3">
                    <button @click="cancelEditComment" class="rounded-full bg-gray-100 px-4 py-2 text-sm text-gray-600">
                      取消
                    </button>
                    <button
                      @click="saveEditComment(comment.id)"
                      :disabled="isSavingEdit || !editingCommentContent.trim()"
                      class="rounded-full bg-blue-600 px-4 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {{ isSavingEdit ? '保存中...' : '保存' }}
                    </button>
                  </div>
                </div>
                <p v-else class="mt-2 whitespace-pre-wrap text-sm leading-7 text-gray-600">{{ comment.content }}</p>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="rounded-2xl border border-gray-100 bg-white/60 px-4 py-10 text-center text-sm text-gray-400">
          还没有评论
        </div>
      </section>
    </main>
    
    <div v-else class="flex flex-col items-center justify-center min-h-[60vh] text-gray-400">
      <p class="text-lg font-medium">找不到这篇随想</p>
      <button @click="router.push('/')" class="mt-4 text-blue-600 hover:underline font-medium">返回动态</button>
    </div>
  </div>
</template>
