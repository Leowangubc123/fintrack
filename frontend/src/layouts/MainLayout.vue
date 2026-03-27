<template>
  <div class="main-layout">
    <!-- 左侧导航栏 - 玻璃拟态 -->
    <aside class="sidebar">
      <div class="logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 270 80" class="logo-svg">
          <defs>
            <clipPath id="lensClip">
              <circle cx="38" cy="40" r="22"/>
            </clipPath>
          </defs>
          <circle cx="38" cy="40" r="27" fill="white" stroke="#1E40AF" stroke-width="7"/>
          <circle cx="38" cy="40" r="22" fill="none" stroke="white" stroke-width="2"/>
          <g clip-path="url(#lensClip)">
            <rect x="20" y="46" width="10" height="22" fill="#007AFF"/>
            <rect x="33" y="36" width="10" height="32" fill="#007AFF"/>
            <rect x="46" y="26" width="10" height="42" fill="#007AFF"/>
          </g>
          <line x1="57" y1="63" x2="72" y2="80" stroke="#1E40AF" stroke-width="7" stroke-linecap="round"/>
          <text x="84" y="54" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="bold" fill="#1E40AF" letter-spacing="-1">Fintrack</text>
        </svg>
      </div>

      <nav class="nav-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.title }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部标题栏 - 玻璃拟态 -->
      <header class="header">
        <h1 class="page-title">{{ $route.meta?.title || 'FinTrack' }}</h1>
        <div class="header-actions">
          <div class="user-info">
            <div class="user-avatar">管</div>
            <span>管理员</span>
          </div>
          <button class="logout-btn" @click="handleLogout">
            <el-icon :size="16"><SwitchButton /></el-icon>
            <span>退出</span>
          </button>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { DataLine, UserFilled, Box, Upload, TrendCharts, SwitchButton, Collection } from '@element-plus/icons-vue'

const router = useRouter()

const menuItems = ref([
  { path: '/', title: '数据看板', icon: DataLine },
  { path: '/analysis', title: '数据分析', icon: TrendCharts },
  { path: '/products', title: '产品管理', icon: Box },
  { path: '/organization', title: '营销人员', icon: UserFilled },
  { path: '/import', title: '数据导入', icon: Upload },
  { path: '/private-fund', title: '私募销售', icon: Collection },
])

function handleLogout() {
  localStorage.removeItem('ft_auth')
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: #FFFFFF;
}

/* 左侧导航栏 - 玻璃拟态 */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 240px;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.logo-svg {
  width: 100%;
  max-width: 192px;
  height: auto;
}

.nav-menu {
  padding: 12px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  margin: 2px 0;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: #6E6E73;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.nav-item:hover {
  background: rgba(0, 122, 255, 0.08);
  color: #007AFF;
}

.nav-item.active {
  background: #007AFF;
  color: white;
}

.nav-item .el-icon {
  opacity: 0.9;
}

/* 主内容区 */
.main-content {
  margin-left: 240px;
  flex: 1;
  min-height: 100vh;
  background: #FFFFFF;
  display: flex;
  flex-direction: column;
}

/* 顶部标题栏 - 玻璃拟态 */
.header {
  height: 64px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1D1D1F;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #6E6E73;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #007AFF, #5856D6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 13px;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 59, 48, 0.08);
  color: #FF3B30;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: rgba(255, 59, 48, 0.15);
}

.logout-btn:active {
  transform: scale(0.98);
}

.content-wrapper {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}
</style>
