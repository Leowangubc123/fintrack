<template>
  <div class="login-bg">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 130" class="logo-svg">
          <defs>
            <clipPath id="lensClipLogin">
              <circle cx="62" cy="58" r="34"/>
            </clipPath>
          </defs>
          <circle cx="62" cy="58" r="34" fill="#ffffff" stroke="#1E40AF" stroke-width="7"/>
          <g clip-path="url(#lensClipLogin)">
            <rect x="33" y="58" width="9" height="20" rx="1.5" fill="#007AFF"/>
            <rect x="46" y="48" width="9" height="30" rx="1.5" fill="#007AFF"/>
            <rect x="59" y="53" width="9" height="25" rx="1.5" fill="#007AFF"/>
            <rect x="72" y="40" width="9" height="38" rx="1.5" fill="#007AFF"/>
          </g>
          <line x1="88" y1="85" x2="112" y2="110" stroke="#1E40AF" stroke-width="7" stroke-linecap="round"/>
          <text x="130" y="74" font-family="Arial, Helvetica, sans-serif" font-size="52" font-weight="bold" fill="#1E40AF" letter-spacing="-1">Fintrack</text>
        </svg>
      </div>

      <p class="login-subtitle">金融产品销售管理系统</p>

      <div class="form-group">
        <label class="form-label">账号</label>
        <input
          v-model="username"
          type="text"
          class="form-input"
          placeholder="请输入账号"
          @keyup.enter="handleLogin"
        />
      </div>

      <div class="form-group">
        <label class="form-label">密码</label>
        <input
          v-model="password"
          type="password"
          class="form-input"
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
        />
      </div>

      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

      <button class="login-btn" :disabled="loading" @click="handleLogin">
        <span v-if="loading">登录中...</span>
        <span v-else>登 录</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  loading.value = true
  await new Promise(r => setTimeout(r, 400))
  if (username.value === 'admin' && password.value === 'fintrack2026') {
    localStorage.setItem('ft_auth', 'true')
    router.push('/')
  } else {
    errorMsg.value = '账号或密码错误，请重试'
  }
  loading.value = false
}
</script>

<style scoped>
.login-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #EBF4FF 0%, #F0F4FF 50%, #EEF2FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 48px 44px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1), 0 4px 16px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-logo {
  width: 220px;
  margin-bottom: 8px;
}

.logo-svg {
  width: 100%;
  height: auto;
}

.login-subtitle {
  font-size: 13px;
  color: #8E8E93;
  margin: 0 0 36px 0;
  font-weight: 500;
}

.form-group {
  width: 100%;
  margin-bottom: 18px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #6E6E73;
  margin-bottom: 7px;
}

.form-input {
  width: 100%;
  height: 46px;
  border: 1.5px solid #E5E5EA;
  border-radius: 12px;
  padding: 0 16px;
  font-size: 15px;
  color: #1D1D1F;
  background: #FAFAFA;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: #007AFF;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

.form-input::placeholder {
  color: #AEAEB2;
}

.error-msg {
  width: 100%;
  font-size: 13px;
  color: #FF3B30;
  background: #FFF0EF;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 6px;
  box-sizing: border-box;
}

.login-btn {
  width: 100%;
  height: 50px;
  background: #007AFF;
  color: #fff;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 10px;
  transition: background 0.2s, transform 0.1s;
  letter-spacing: 2px;
}

.login-btn:hover:not(:disabled) {
  background: #0066D6;
}

.login-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
