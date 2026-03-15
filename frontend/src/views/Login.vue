<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const username = ref('')
const password = ref('')
const nickname = ref('')
const error = ref('')
const loading = ref(false)

const title = computed(() => isRegister.value ? '注册账号' : '登录')
const submitText = computed(() => isRegister.value ? '立即注册' : '登录')
const switchText = computed(() => isRegister.value ? '已有账号？去登录' : '没有账号？去注册')

const toggleMode = () => {
  console.log('Toggling mode, current:', isRegister.value)
  isRegister.value = !isRegister.value
  error.value = ''
  // Keep username if it exists, clear others
  password.value = ''
  nickname.value = ''
}

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    error.value = '请输入账号和密码'
    return
  }

  if (isRegister.value && !nickname.value) {
    error.value = '请输入昵称'
    return
  }
  
  error.value = ''
  loading.value = true

  try {
    if (isRegister.value) {
      await authStore.register({
        username: username.value,
        password: password.value,
        nickname: nickname.value
      })
      // 注册成功后自动登录或提示去登录
      // 这里为了简单，注册成功后直接切换到登录模式，并填入用户名
      isRegister.value = false
      password.value = '' // 清空密码
      error.value = '注册成功，请登录' // 借用 error 显示成功消息，或者可以用 toast
      // 实际上最好有一个 success 状态
    } else {
      await authStore.login({
        username: username.value,
        password: password.value
      })
      router.push('/')
    }
  } catch (err: any) {
    // 处理错误消息
    error.value = err.response?.data?.message || err.message || '操作失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-cyan-50 font-sans">
    <div class="w-full max-w-md p-8 space-y-8 bg-white rounded-3xl shadow-xl transform transition-all duration-300 hover:shadow-2xl">
      <div class="text-center">
        <h2 class="mt-6 text-3xl font-bold text-gray-900 tracking-wide">随心记</h2>
        <p class="mt-2 text-sm text-gray-500">{{ title }}</p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="rounded-md shadow-sm space-y-4">
          <div>
            <label for="username" class="sr-only">账号</label>
            <input
              v-model="username"
              id="username"
              name="username"
              type="text"
              autocomplete="username"
              required
              class="appearance-none rounded-xl relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="请输入账号"
            />
          </div>

          <div v-if="isRegister">
            <label for="nickname" class="sr-only">昵称</label>
            <input
              v-model="nickname"
              id="nickname"
              name="nickname"
              type="text"
              required
              class="appearance-none rounded-xl relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="请输入昵称"
            />
          </div>

          <div>
            <label for="password" class="sr-only">密码</label>
            <input
              v-model="password"
              id="password"
              name="password"
              type="password"
              autocomplete="current-password"
              required
              class="appearance-none rounded-xl relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="请输入密码"
            />
          </div>
        </div>

        <div v-if="error" class="text-red-500 text-sm text-center font-medium">{{ error }}</div>

        <div>
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-xl text-white bg-cyan-600 hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 transition duration-150 ease-in-out transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading">处理中...</span>
            <span v-else>{{ submitText }}</span>
          </button>
        </div>
        
        <div class="flex items-center justify-end">
          <div class="text-sm">
            <button 
              type="button"
              @click="toggleMode"
              class="font-medium text-cyan-600 hover:text-cyan-500 transition-colors focus:outline-none"
            >
              {{ switchText }}
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>
