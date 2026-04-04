<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const useSmsLogin = ref(true)
const requireSms = ref(true)
const account = ref('')
const phone = ref('')
const password = ref('')
const smsCode = ref('')
const nickname = ref('')
const error = ref('')
const message = ref('')
const loading = ref(false)
const rememberPassword = ref(false)
const autoLogin = ref(true)
const countdown = ref(0)
let countdownTimer: number | null = null

const SAVED_LOGIN_KEY = 'savedLoginCredentials'
const AUTO_LOGIN_KEY = 'autoLoginEnabled'

const title = computed(() => {
  if (isRegister.value) return '手机号注册'
  if (requireSms.value && useSmsLogin.value) return '手机号验证码登录'
  return '账号密码登录'
})
const submitText = computed(() => isRegister.value ? '立即注册' : '登录')
const switchText = computed(() => isRegister.value ? '已有账号？去登录' : '没有账号？去注册')
const canSendCode = computed(() => /^1\d{10}$/.test(phone.value) && countdown.value === 0 && !loading.value)

const startCountdown = () => {
  countdown.value = 60
  if (countdownTimer) {
    window.clearInterval(countdownTimer)
  }
  countdownTimer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0 && countdownTimer) {
      window.clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
  error.value = ''
  message.value = ''
  smsCode.value = ''
  if (!rememberPassword.value) {
    password.value = ''
  }
  nickname.value = ''
  if (isRegister.value && /^1\d{10}$/.test(account.value)) {
    phone.value = account.value
  }
}

const switchLoginMode = (smsMode: boolean) => {
  useSmsLogin.value = smsMode
  error.value = ''
  message.value = ''
  smsCode.value = ''
}

onMounted(async () => {
  try {
    const r = await apiClient.get('auth/auth-options')
    requireSms.value = !!r.data.data?.require_sms_verification
    if (!requireSms.value) {
      useSmsLogin.value = false
    }
  } catch {
    requireSms.value = true
  }
  autoLogin.value = localStorage.getItem(AUTO_LOGIN_KEY) !== 'false'
  const saved = localStorage.getItem(SAVED_LOGIN_KEY)
  if (!saved) return

  try {
    const parsed = JSON.parse(saved)
    account.value = parsed.account || ''
    password.value = parsed.password || ''
    rememberPassword.value = !!parsed.rememberPassword
  } catch {
    localStorage.removeItem(SAVED_LOGIN_KEY)
  }
})

onBeforeUnmount(() => {
  if (countdownTimer) {
    window.clearInterval(countdownTimer)
  }
})

const sendCode = async () => {
  if (!requireSms.value || !canSendCode.value) return
  error.value = ''
  message.value = ''
  try {
    const result = await authStore.sendSmsCode({
      phone: phone.value,
      purpose: isRegister.value ? 'register' : 'login',
    })
    startCountdown()
    message.value = result.preview_code ? `调试验证码：${result.preview_code}` : '验证码已发送'
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.response?.data?.message || err.message || '发送验证码失败'
  }
}

const handleSubmit = async () => {
  if (isRegister.value) {
    if (!phone.value || !nickname.value) {
      error.value = '请输入手机号和昵称'
      return
    }
    if (requireSms.value && !smsCode.value) {
      error.value = '请输入验证码'
      return
    }
    if (!requireSms.value && !password.value) {
      error.value = '请设置密码'
      return
    }
  } else if (requireSms.value && useSmsLogin.value) {
    if (!phone.value || !smsCode.value) {
      error.value = '请输入手机号和验证码'
      return
    }
  } else {
    if (!account.value || !password.value) {
      error.value = '请输入账号或手机号和密码'
      return
    }
  }
  
  error.value = ''
  message.value = ''
  loading.value = true

  try {
    if (isRegister.value) {
      await authStore.register({
        phone: phone.value,
        ...(requireSms.value ? { sms_code: smsCode.value } : {}),
        nickname: nickname.value,
        password: password.value || undefined,
      })
      isRegister.value = false
      useSmsLogin.value = requireSms.value
      account.value = phone.value
      smsCode.value = ''
      message.value = '注册成功，请登录'
    } else {
      if (requireSms.value && useSmsLogin.value) {
        await authStore.login({
          phone: phone.value,
          sms_code: smsCode.value,
          auto_login: autoLogin.value,
        })
      } else {
        await authStore.login({
          account: account.value,
          password: password.value,
          auto_login: autoLogin.value,
        })
        if (rememberPassword.value) {
          localStorage.setItem(SAVED_LOGIN_KEY, JSON.stringify({
            account: account.value,
            password: password.value,
            rememberPassword: true,
          }))
        } else {
          localStorage.removeItem(SAVED_LOGIN_KEY)
        }
      }
      localStorage.setItem(AUTO_LOGIN_KEY, autoLogin.value ? 'true' : 'false')
      router.push('/')
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.response?.data?.message || err.message || '操作失败'
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
          <div v-if="!isRegister && requireSms" class="grid grid-cols-2 gap-3 rounded-2xl bg-cyan-50 p-1">
            <button
              type="button"
              @click="switchLoginMode(true)"
              class="rounded-xl px-4 py-2 text-sm font-medium transition"
              :class="useSmsLogin ? 'bg-white text-cyan-700 shadow-sm' : 'text-gray-500'"
            >
              验证码登录
            </button>
            <button
              type="button"
              @click="switchLoginMode(false)"
              class="rounded-xl px-4 py-2 text-sm font-medium transition"
              :class="!useSmsLogin ? 'bg-white text-cyan-700 shadow-sm' : 'text-gray-500'"
            >
              密码登录
            </button>
          </div>

          <div v-if="!isRegister && (!requireSms || !useSmsLogin)">
            <label for="account" class="sr-only">账号或手机号</label>
            <input
              v-model="account"
              id="account"
              name="account"
              type="text"
              autocomplete="username"
              required
              class="appearance-none rounded-xl relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="请输入账号或手机号"
            />
          </div>

          <div v-else-if="isRegister || (requireSms && useSmsLogin)">
            <label for="phone" class="sr-only">手机号</label>
            <input
              v-model="phone"
              id="phone"
              name="phone"
              type="tel"
              inputmode="numeric"
              maxlength="11"
              autocomplete="tel"
              required
              class="appearance-none rounded-xl relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="请输入手机号"
            />
          </div>

          <div v-if="requireSms && (isRegister || useSmsLogin)" class="flex gap-3">
            <input
              v-model="smsCode"
              type="text"
              inputmode="numeric"
              maxlength="6"
              required
              class="appearance-none rounded-xl relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="请输入验证码"
            />
            <button
              type="button"
              @click="sendCode"
              :disabled="!canSendCode"
              class="shrink-0 rounded-xl bg-cyan-100 px-4 text-sm font-medium text-cyan-700 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </button>
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

          <div v-if="isRegister || !requireSms || !useSmsLogin">
            <label for="password" class="sr-only">密码</label>
            <input
              v-model="password"
              id="password"
              name="password"
              type="password"
              autocomplete="current-password"
              :required="(!isRegister && (!requireSms || !useSmsLogin)) || (isRegister && !requireSms)"
              class="appearance-none rounded-xl relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm transition duration-150 ease-in-out"
              :placeholder="isRegister ? (requireSms ? '设置密码（可选）' : '设置密码') : '请输入密码'"
            />
          </div>
        </div>

        <div v-if="!isRegister && (!requireSms || !useSmsLogin)" class="flex items-center justify-between text-sm text-gray-500">
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input
              v-model="rememberPassword"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300 text-cyan-600 focus:ring-cyan-500"
            />
            <span>记住密码</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input
              v-model="autoLogin"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300 text-cyan-600 focus:ring-cyan-500"
            />
            <span>自动登录</span>
          </label>
        </div>

        <div v-if="message" class="text-emerald-600 text-sm text-center font-medium">{{ message }}</div>
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
