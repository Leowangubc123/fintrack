<template>
  <div class="main-layout">
    <!-- 左侧导航栏 - 玻璃拟态 -->
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span>FinTrack</span>
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
import { DataLine, UserFilled, Box, Upload, TrendCharts } from '@element-plus/icons-vue'

const menuItems = ref([
  { path: '/', title: '数据看板', icon: DataLine },
  { path: '/analysis', title: '数据分析', icon: TrendCharts },
  { path: '/products', title: '产品管理', icon: Box },
  { path: '/organization', title: '营销人员', icon: UserFilled },
  { path: '/import', title: '数据导入', icon: Upload },
])
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
  padding: 0 20px;
  gap: 10px;
  font-size: 20px;
  font-weight: 600;
  color: #1D1D1F;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-icon svg {
  width: 20px;
  height: 20px;
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

.content-wrapper {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}
</style>
