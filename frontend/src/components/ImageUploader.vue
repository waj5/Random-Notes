<script setup lang="ts">
const emit = defineEmits(['upload'])

const MAX_UPLOAD_BYTES = 4.5 * 1024 * 1024
const MAX_DIMENSION = 2400

const blobToDataUrl = (blob: Blob) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Failed to read image blob'))
    reader.readAsDataURL(blob)
  })

const loadImage = (src: string) =>
  new Promise<HTMLImageElement>((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = src
  })

const canvasToBlob = (canvas: HTMLCanvasElement, quality: number) =>
  new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob)
          return
        }
        reject(new Error('Failed to convert canvas to blob'))
      },
      'image/jpeg',
      quality
    )
  })

const optimizeImage = async (file: File) => {
  const objectUrl = URL.createObjectURL(file)

  try {
    const image = await loadImage(objectUrl)
    const ratio = Math.min(1, MAX_DIMENSION / Math.max(image.width, image.height))
    const targetWidth = Math.max(1, Math.round(image.width * ratio))
    const targetHeight = Math.max(1, Math.round(image.height * ratio))

    const canvas = document.createElement('canvas')
    canvas.width = targetWidth
    canvas.height = targetHeight

    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('Canvas is not supported')
    }

    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, targetWidth, targetHeight)
    context.drawImage(image, 0, 0, targetWidth, targetHeight)

    let bestBlob: Blob | null = null
    for (const quality of [0.92, 0.85, 0.78, 0.7, 0.6, 0.5]) {
      const blob = await canvasToBlob(canvas, quality)
      bestBlob = blob
      if (blob.size <= MAX_UPLOAD_BYTES) {
        return await blobToDataUrl(blob)
      }
    }

    if (!bestBlob) {
      throw new Error('Image compression failed')
    }

    return await blobToDataUrl(bestBlob)
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    const optimizedImage = await optimizeImage(file)
    emit('upload', optimizedImage)
  } catch (error) {
    console.error('Failed to process image:', error)
    alert('图片处理失败')
  } finally {
    input.value = ''
  }
}
</script>

<template>
  <div class="relative w-full h-full border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer group">
    <input type="file" accept="image/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" @change="handleFileChange" />
    <div class="text-center text-gray-400 group-hover:text-gray-600">
      <div class="mb-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <span class="text-sm font-medium">点击上传图片</span>
    </div>
  </div>
</template>
