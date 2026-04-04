<script setup lang="ts">
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotesStore } from '../stores/notes'
import type { Note } from '../stores/notes'
import { useAuthStore } from '../stores/auth'
import apiClient from '../api/client'
import { ArrowLeft, Download, Edit, ImageUp, Share2, Sparkles, Trash2 } from 'lucide-vue-next'
import QRCode from 'qrcode'
import BlockViewer from '../components/BlockViewer.vue'
import PetalBackground from '../components/PetalBackground.vue'

interface NoteComment {
  id: number
  note_id: number
  user_id: number
  parent_id?: number | null
  username: string
  nickname: string
  avatar_url?: string
  content: string
  created_at: string
  replies: NoteComment[]
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
const commentsLoading = ref(false)
const isSubmittingComment = ref(false)
const replyingCommentId = ref<number | null>(null)
const replyContent = ref('')
const isSubmittingReply = ref(false)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const editingCommentId = ref<number | null>(null)
const editingCommentContent = ref('')
const isSavingEdit = ref(false)
const isSharing = ref(false)
const shareMessage = ref('')
const canShare = computed(() => note.value?.status === 'published' && note.value?.isPrivate === false)
const posterPreviewUrl = ref('')
const posterBlob = ref<Blob | null>(null)
const isGeneratingPoster = ref(false)
const qrCodeDataUrl = ref('')

const shareSummary = computed(() => {
  if (!note.value) return ''
  if (note.value.summary?.trim()) return note.value.summary.trim()
  const firstText = note.value.blocks.find(block => block.content?.trim())?.content?.trim() || ''
  return firstText.slice(0, 80)
})

const shareUrl = computed(() => `${window.location.origin}/note/${noteId}`)
const coverImageUrl = computed(() => note.value?.blocks.flatMap(block => block.images)[0] || '')
const authorName = computed(() => note.value?.authorNickname || note.value?.authorUsername || '随心记用户')
const totalCommentCount = computed(() => {
  const countReplies = (items: NoteComment[]): number => items.reduce((total, item) => total + 1 + countReplies(item.replies || []), 0)
  return countReplies(comments.value)
})

const loadImage = (src: string) => new Promise<HTMLImageElement>((resolve, reject) => {
  const image = new Image()
  image.crossOrigin = 'anonymous'
  image.onload = () => resolve(image)
  image.onerror = reject
  image.src = src
})

const drawRoundedRect = (
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) => {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.arcTo(x + width, y, x + width, y + height, radius)
  ctx.arcTo(x + width, y + height, x, y + height, radius)
  ctx.arcTo(x, y + height, x, y, radius)
  ctx.arcTo(x, y, x + width, y, radius)
  ctx.closePath()
}

const drawMultilineText = (
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  startY: number,
  maxWidth: number,
  lineHeight: number,
  maxLines: number,
) => {
  const chars = Array.from(text)
  const lines: string[] = []
  let currentLine = ''

  for (const char of chars) {
    const nextLine = currentLine + char
    if (ctx.measureText(nextLine).width > maxWidth && currentLine) {
      lines.push(currentLine)
      currentLine = char
      if (lines.length === maxLines - 1) break
    } else {
      currentLine = nextLine
    }
  }

  if (currentLine && lines.length < maxLines) {
    lines.push(currentLine)
  }

  const consumed = lines.join('').length
  if (consumed < chars.length && lines.length > 0) {
    const lastLine = lines[lines.length - 1]
    let shortened = lastLine
    while (shortened && ctx.measureText(`${shortened}...`).width > maxWidth) {
      shortened = shortened.slice(0, -1)
    }
    lines[lines.length - 1] = `${shortened}...`
  }

  lines.forEach((line, index) => {
    ctx.fillText(line, x, startY + index * lineHeight)
  })
}

const setPosterBlob = (blob: Blob | null) => {
  if (posterPreviewUrl.value) {
    URL.revokeObjectURL(posterPreviewUrl.value)
  }
  posterBlob.value = blob
  posterPreviewUrl.value = blob ? URL.createObjectURL(blob) : ''
}

const ensureQrCode = async () => {
  if (!qrCodeDataUrl.value) {
    qrCodeDataUrl.value = await QRCode.toDataURL(shareUrl.value, {
      width: 220,
      margin: 1,
      color: {
        dark: '#0f172a',
        light: '#ffffff',
      },
    })
  }
  return qrCodeDataUrl.value
}

const generateSharePoster = async () => {
  if (!note.value) return

  isGeneratingPoster.value = true
  try {
    const canvas = document.createElement('canvas')
    canvas.width = 1080
    canvas.height = 1440
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
    gradient.addColorStop(0, '#dff4ff')
    gradient.addColorStop(0.45, '#f7f9ff')
    gradient.addColorStop(1, '#ffe8f3')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.fillStyle = 'rgba(255,255,255,0.72)'
    drawRoundedRect(ctx, 60, 60, 960, 1320, 48)
    ctx.fill()

    ctx.save()
    drawRoundedRect(ctx, 120, 120, 840, 500, 40)
    ctx.clip()
    if (coverImageUrl.value) {
      try {
        const cover = await loadImage(coverImageUrl.value)
        const coverRatio = Math.max(840 / cover.width, 500 / cover.height)
        const coverWidth = cover.width * coverRatio
        const coverHeight = cover.height * coverRatio
        const coverX = 120 + (840 - coverWidth) / 2
        const coverY = 120 + (500 - coverHeight) / 2
        ctx.drawImage(cover, coverX, coverY, coverWidth, coverHeight)
      } catch {
        const coverGradient = ctx.createLinearGradient(120, 120, 960, 620)
        coverGradient.addColorStop(0, '#7dd3fc')
        coverGradient.addColorStop(1, '#c084fc')
        ctx.fillStyle = coverGradient
        ctx.fillRect(120, 120, 840, 500)
      }
    } else {
      const coverGradient = ctx.createLinearGradient(120, 120, 960, 620)
      coverGradient.addColorStop(0, '#60a5fa')
      coverGradient.addColorStop(1, '#f472b6')
      ctx.fillStyle = coverGradient
      ctx.fillRect(120, 120, 840, 500)
    }
    ctx.restore()

    const maskGradient = ctx.createLinearGradient(120, 380, 120, 620)
    maskGradient.addColorStop(0, 'rgba(15,23,42,0)')
    maskGradient.addColorStop(1, 'rgba(15,23,42,0.55)')
    ctx.fillStyle = maskGradient
    drawRoundedRect(ctx, 120, 120, 840, 500, 40)
    ctx.fill()

    ctx.fillStyle = 'rgba(255,255,255,0.92)'
    ctx.font = '600 34px sans-serif'
    ctx.fillText('随心记 SHARE', 160, 190)

    ctx.fillStyle = '#0f172a'
    ctx.font = 'bold 64px sans-serif'
    drawMultilineText(ctx, note.value.title || '发现一篇值得点开的内容', 120, 730, 840, 86, 3)

    ctx.fillStyle = '#475569'
    ctx.font = '34px sans-serif'
    drawMultilineText(
      ctx,
      shareSummary.value || '轻松记录日常、灵感和生活片段，点进来看看完整内容。',
      120,
      980,
      840,
      52,
      4,
    )

    ctx.fillStyle = '#e0f2fe'
    drawRoundedRect(ctx, 120, 1160, 240, 76, 38)
    ctx.fill()
    ctx.fillStyle = '#0284c7'
    ctx.font = '600 30px sans-serif'
    ctx.fillText(authorName.value, 150, 1208)

    ctx.fillStyle = '#fef3c7'
    drawRoundedRect(ctx, 380, 1160, 250, 76, 38)
    ctx.fill()
    ctx.fillStyle = '#d97706'
    ctx.fillText('点开看完整内容', 415, 1208)

    ctx.fillStyle = '#ffffff'
    drawRoundedRect(ctx, 700, 1040, 260, 260, 36)
    ctx.fill()
    ctx.fillStyle = 'rgba(15,23,42,0.06)'
    drawRoundedRect(ctx, 712, 1052, 236, 236, 28)
    ctx.fill()

    const qrCodeImage = await loadImage(await ensureQrCode())
    ctx.drawImage(qrCodeImage, 730, 1070, 200, 200)

    ctx.fillStyle = '#0f172a'
    ctx.font = '600 24px sans-serif'
    ctx.fillText('扫码直达原文', 748, 1298)

    ctx.fillStyle = '#94a3b8'
    ctx.font = '28px sans-serif'
    ctx.fillText(`分享时间 ${new Date(note.value.createdAt).toLocaleDateString()}`, 120, 1315)
    ctx.fillText('把生活里的闪光片段，留在这里。', 120, 1358)

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, 'image/png')
    })
    setPosterBlob(blob)
  } finally {
    isGeneratingPoster.value = false
  }
}

const buildSharePayload = (platform: 'xiaohongshu' | 'weibo' | 'moments') => {
  const title = note.value?.title?.trim() || '随心记'
  const body = shareSummary.value ? `${title}\n${shareSummary.value}` : title
  const platformText = platform === 'weibo'
    ? `${body}\n${shareUrl.value}`
    : `${body}\n来自随心记\n${shareUrl.value}`

  return {
    title,
    text: platformText,
    url: shareUrl.value,
  }
}

const recordShare = async (platform: 'xiaohongshu' | 'weibo' | 'moments', payload: ReturnType<typeof buildSharePayload>) => {
  if (!authStore.isAuthenticated) return
  await apiClient.post(`/notes/shares/${noteId}`, {
    platform,
    share_title: payload.title,
    share_text: payload.text,
    share_url: payload.url,
  })
}

const copyShareText = async (text: string) => {
  await navigator.clipboard.writeText(text)
}

const getPosterFile = async () => {
  if (!posterBlob.value) {
    await generateSharePoster()
  }
  if (!posterBlob.value) return null
  return new File([posterBlob.value], `note-${noteId}-share.png`, { type: 'image/png' })
}

const downloadPoster = async () => {
  const file = await getPosterFile()
  if (!file) return
  const url = URL.createObjectURL(file)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = file.name
  anchor.click()
  URL.revokeObjectURL(url)
  shareMessage.value = '分享海报已下载'
}

const shareToPlatform = async (platform: 'xiaohongshu' | 'weibo' | 'moments') => {
  if (!note.value || !canShare.value || isSharing.value) return

  isSharing.value = true
  shareMessage.value = ''

  try {
    const payload = buildSharePayload(platform)
    await recordShare(platform, payload)

    if (platform === 'weibo') {
      const shareWindowUrl = `https://service.weibo.com/share/share.php?title=${encodeURIComponent(payload.text)}&url=${encodeURIComponent(payload.url)}`
      window.open(shareWindowUrl, '_blank', 'noopener,noreferrer')
      shareMessage.value = '已打开微博分享页'
      return
    }

    const posterFile = await getPosterFile()
    if (posterFile && navigator.canShare?.({ files: [posterFile] }) && navigator.share) {
      await navigator.share({
        title: payload.title,
        text: payload.text,
        files: [posterFile],
      })
      shareMessage.value = platform === 'xiaohongshu' ? '已调起系统分享，海报图已附带' : '已调起系统分享，海报图已附带'
      return
    }

    if (navigator.share) {
      await navigator.share(payload)
      shareMessage.value = platform === 'xiaohongshu' ? '已调起系统分享，请选择小红书' : '已调起系统分享，请选择微信'
      return
    }

    await copyShareText(payload.text)
    await downloadPoster()
    shareMessage.value = platform === 'xiaohongshu'
      ? '分享文案已复制，海报也已下载'
      : '分享文案已复制，海报也已下载'
  } catch (error) {
    console.error('Failed to share note:', error)
    shareMessage.value = '分享失败'
  } finally {
    isSharing.value = false
  }
}

const loadComments = async () => {
  commentsLoading.value = true
  try {
    const response = await apiClient.get(`/notes/${noteId}/comments/`)
    comments.value = response.data.data
  } finally {
    commentsLoading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    note.value = await notesStore.getNoteById(noteId)
    loading.value = false
    void loadComments()
    void generateSharePoster()
  } catch (e) {
    console.error(e)
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (posterPreviewUrl.value) {
    URL.revokeObjectURL(posterPreviewUrl.value)
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
    await apiClient.post(`/notes/${noteId}/comments/`, { content, parent_id: null })
    commentContent.value = ''
    await loadComments()
  } catch (error) {
    console.error('Failed to create comment:', error)
    alert('评论失败')
  } finally {
    isSubmittingComment.value = false
  }
}

const startReplyComment = (comment: NoteComment) => {
  replyingCommentId.value = comment.id
  replyContent.value = ''
}

const cancelReplyComment = () => {
  replyingCommentId.value = null
  replyContent.value = ''
}

const submitReplyComment = async (parentId: number) => {
  const content = replyContent.value.trim()
  if (!content || isSubmittingReply.value) return

  isSubmittingReply.value = true
  try {
    await apiClient.post(`/notes/${noteId}/comments/`, { content, parent_id: parentId })
    cancelReplyComment()
    await loadComments()
  } catch (error) {
    console.error('Failed to create reply:', error)
    alert('回复失败')
  } finally {
    isSubmittingReply.value = false
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
  <div class="relative min-h-screen overflow-hidden bg-gradient-to-br from-white via-[#f5fbff] to-[#fff5f9] font-sans">
    <PetalBackground />
    <!-- Navbar -->
    <header class="sticky top-0 z-50 border-b border-sky-100/60 bg-white/90 backdrop-blur-md transition-all duration-300 shadow-sm shadow-sky-100/40">
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

    <main v-if="loading" class="relative z-10 mx-auto flex max-w-3xl justify-center px-6 py-12">
       <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </main>

    <main v-else-if="note" class="relative z-10 mx-auto my-6 min-h-[calc(100vh-8rem)] max-w-4xl space-y-8 px-8 py-12">
      <section class="notebook-page rounded-3xl shadow-[0_12px_48px_rgba(56,130,246,0.07)] ring-1 ring-sky-100/50">
        <div class="text-center space-y-4 pb-10 pt-6">
          <h1 class="text-3xl md:text-4xl font-bold text-gray-800 tracking-tight leading-tight">{{ note.title }}</h1>
          <div class="text-sm font-medium tracking-wide text-sky-600/55">
            {{ new Date(note.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}
          </div>
        </div>

        <div class="space-y-12 min-h-[40vh] pb-6">
          <BlockViewer v-for="block in note.blocks" :key="block.id" :block="block" />
        </div>
      </section>

      <section class="rounded-3xl border border-gray-100 bg-white/80 p-6">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 class="flex items-center gap-2 text-lg font-bold text-gray-800">
              <Sparkles :size="18" class="text-amber-500" />
              <span>分享这篇内容</span>
            </h2>
            <p class="mt-1 text-sm text-gray-400">
              {{ canShare ? '带海报图分享，更容易吸引别人点进来' : '只有公开发布后的内容才可以分享' }}
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button
              @click="shareToPlatform('xiaohongshu')"
              :disabled="!canShare || isSharing"
              class="rounded-full border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              分享到小红书
            </button>
            <button
              @click="shareToPlatform('weibo')"
              :disabled="!canShare || isSharing"
              class="rounded-full border border-orange-200 bg-orange-50 px-4 py-2 text-sm font-semibold text-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              分享到微博
            </button>
            <button
              @click="shareToPlatform('moments')"
              :disabled="!canShare || isSharing"
              class="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              分享到朋友圈
            </button>
          </div>
        </div>
        <div class="mt-5 grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
          <div class="overflow-hidden rounded-[28px] border border-slate-100 bg-gradient-to-br from-sky-50 to-pink-50 p-3 shadow-[0_10px_30px_rgba(15,23,42,0.06)]">
            <div class="mb-3 flex items-center justify-between px-2">
              <div class="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <ImageUp :size="16" class="text-sky-500" />
                <span>分享海报预览</span>
              </div>
              <button
                @click="downloadPoster"
                :disabled="isGeneratingPoster"
                class="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm disabled:opacity-50"
              >
                <Download :size="14" />
                <span>下载</span>
              </button>
            </div>
            <div class="overflow-hidden rounded-[24px] bg-white">
              <img
                v-if="posterPreviewUrl"
                :src="posterPreviewUrl"
                class="aspect-[3/4] w-full object-cover"
              />
              <div v-else class="flex aspect-[3/4] items-center justify-center text-sm text-slate-400">
                {{ isGeneratingPoster ? '海报生成中...' : '海报预览暂不可用' }}
              </div>
            </div>
          </div>
          <div class="rounded-[28px] border border-slate-100 bg-white/70 p-5">
            <h3 class="text-base font-semibold text-slate-800">当前分享亮点</h3>
            <div class="mt-4 grid gap-3 sm:grid-cols-3">
              <div class="rounded-2xl bg-rose-50 px-4 py-3">
                <div class="text-xs text-rose-400">标题吸引</div>
                <div class="mt-2 text-sm font-semibold text-rose-600">{{ note.title || '无题内容' }}</div>
              </div>
              <div class="rounded-2xl bg-sky-50 px-4 py-3">
                <div class="text-xs text-sky-400">内容摘要</div>
                <div class="mt-2 line-clamp-2 text-sm font-semibold text-sky-700">{{ shareSummary || '记录生活碎片与灵感瞬间' }}</div>
              </div>
              <div class="rounded-2xl bg-amber-50 px-4 py-3">
                <div class="text-xs text-amber-400">点开理由</div>
                <div class="mt-2 text-sm font-semibold text-amber-600">海报图 + 原文链接 + 内容氛围</div>
              </div>
            </div>
            <p class="mt-4 text-sm leading-7 text-slate-500">
              小红书和朋友圈会优先附带这张海报图；如果当前系统不支持图片分享，就自动下载海报并复制文案。
            </p>
          </div>
        </div>
        <p v-if="shareMessage" class="mt-3 flex items-center gap-2 text-sm text-blue-500">
          <Share2 :size="16" />
          <span>{{ shareMessage }}</span>
        </p>
      </section>

      <section class="space-y-5 border-t border-gray-100 pt-8">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-800">评论 {{ totalCommentCount }}</h2>
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

        <div v-if="commentsLoading" class="rounded-2xl border border-gray-100 bg-white/60 px-4 py-10 text-center text-sm text-gray-400">
          评论加载中...
        </div>

        <div v-else-if="comments.length > 0" class="space-y-4">
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
                      @click="startReplyComment(comment)"
                      class="text-slate-500 hover:underline"
                    >
                      回复
                    </button>
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

                <div v-if="replyingCommentId === comment.id" class="mt-3 space-y-3 rounded-2xl bg-slate-50 p-3">
                  <textarea
                    v-model="replyContent"
                    :placeholder="`回复 ${comment.nickname || comment.username}...`"
                    class="min-h-[88px] w-full resize-none rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm text-gray-700 outline-none"
                  ></textarea>
                  <div class="flex justify-end gap-3">
                    <button @click="cancelReplyComment" class="rounded-full bg-white px-4 py-2 text-sm text-gray-600">
                      取消
                    </button>
                    <button
                      @click="submitReplyComment(comment.id)"
                      :disabled="isSubmittingReply || !replyContent.trim()"
                      class="rounded-full bg-blue-600 px-4 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {{ isSubmittingReply ? '发送中...' : '发送回复' }}
                    </button>
                  </div>
                </div>

                <div v-if="comment.replies?.length" class="mt-4 space-y-3 rounded-2xl bg-slate-50/80 p-3">
                  <article
                    v-for="reply in comment.replies"
                    :key="reply.id"
                    class="rounded-2xl bg-white px-4 py-3"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold text-gray-800">{{ reply.nickname || reply.username }}</span>
                        <span class="text-xs text-gray-400">{{ new Date(reply.created_at).toLocaleString() }}</span>
                      </div>
                      <div v-if="isAuthenticated" class="flex items-center gap-3 text-xs">
                        <button
                          v-if="canEditComment(reply)"
                          @click="startEditComment(reply)"
                          class="text-blue-600 hover:underline"
                        >
                          编辑
                        </button>
                        <button
                          v-if="canDeleteComment(reply)"
                          @click="deleteComment(reply.id)"
                          class="text-red-500 hover:underline"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                    <div v-if="editingCommentId === reply.id" class="mt-3 space-y-3">
                      <textarea
                        v-model="editingCommentContent"
                        class="min-h-[90px] w-full resize-none rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm text-gray-700 outline-none"
                      ></textarea>
                      <div class="flex justify-end gap-3">
                        <button @click="cancelEditComment" class="rounded-full bg-gray-100 px-4 py-2 text-sm text-gray-600">
                          取消
                        </button>
                        <button
                          @click="saveEditComment(reply.id)"
                          :disabled="isSavingEdit || !editingCommentContent.trim()"
                          class="rounded-full bg-blue-600 px-4 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {{ isSavingEdit ? '保存中...' : '保存' }}
                        </button>
                      </div>
                    </div>
                    <p v-else class="mt-2 whitespace-pre-wrap text-sm leading-7 text-gray-600">{{ reply.content }}</p>
                  </article>
                </div>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="rounded-2xl border border-gray-100 bg-white/60 px-4 py-10 text-center text-sm text-gray-400">
          还没有评论
        </div>
      </section>
    </main>
    
    <div v-else class="relative z-10 flex min-h-[60vh] flex-col items-center justify-center text-gray-400">
      <p class="text-lg font-medium">找不到这篇随想</p>
      <button @click="router.push('/')" class="mt-4 text-blue-600 hover:underline font-medium">返回动态</button>
    </div>
  </div>
</template>

<style scoped>
.notebook-page {
  padding: 2.3rem 2.8rem 2.8rem 4.6rem;
  background-color: #fffefb;
  background-image:
    linear-gradient(
      to right,
      transparent 0,
      transparent 2.3rem,
      rgba(251, 182, 193, 0.22) 2.3rem,
      rgba(251, 182, 193, 0.22) 2.45rem,
      transparent 2.45rem
    ),
    repeating-linear-gradient(
      to bottom,
      transparent 0,
      transparent calc(2.4rem - 2px),
      rgba(186, 230, 253, 0.35) calc(2.4rem - 2px),
      rgba(186, 230, 253, 0.35) 2.4rem
    );
  background-position: 0 1.15rem, 0 1.15rem;
}
</style>
