<template>
  <div class="dashboard">
    <!-- KPI 卡片 -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">本月在售产品</div>
        <div class="kpi-value">{{ summary.active_products || 0 }}</div>
        <div class="kpi-sub">个产品</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">整体销售额</div>
        <div class="kpi-value">¥{{ formatNumber(summary.total_sales) }}</div>
        <div class="kpi-sub" v-if="summary.week_sales > 0">
          <span class="trend-up">↑</span> 近7日 ¥{{ formatNumber(summary.week_sales) }}
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">整体完成率</div>
        <div class="kpi-value" :class="getRateClass(summary.completion_rate)">
          {{ summary.completion_rate || 0 }}%
        </div>
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-segment progress-red" :style="{ width: getProgressWidth(summary.completion_rate, 0, 25) }"></div>
            <div class="progress-segment progress-orange" :style="{ width: getProgressWidth(summary.completion_rate, 25, 50) }"></div>
            <div class="progress-segment progress-yellow" :style="{ width: getProgressWidth(summary.completion_rate, 50, 75) }"></div>
            <div class="progress-segment progress-green" :style="{ width: getProgressWidth(summary.completion_rate, 75, 100) }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 预警信息 -->
    <div v-if="summary.nearest_deadline?.days !== null" class="alert-section">
      <el-alert
        :title="`【预警】${summary.nearest_deadline.product_name} 距离募集截止还有 ${summary.nearest_deadline.days} 天`"
        :type="summary.nearest_deadline.days <= 3 ? 'error' : 'warning'"
        show-icon
        :closable="false"
      />
    </div>

    <!-- 在售产品 + 营业部完成情况 -->
    <div class="two-col">
      <!-- 在售产品明细 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <el-icon :size="22"><Box /></el-icon>
            在售产品明细
          </div>
          <el-button text @click="$router.push('/products')">查看全部</el-button>
        </div>
        <div class="card-body">
          <div class="product-list">
            <div v-for="product in activeProducts" :key="product.id" class="product-item">
              <div class="product-header">
                <span class="product-name">{{ product.name }}</span>
                <span class="tag" :class="getStatusClass(product.days_left)">
                  剩{{ product.days_left }}天
                </span>
              </div>
              <div class="product-stats">
                <span>目标: ¥{{ formatNumber(product.target) }}万</span>
                <span>已完成: ¥{{ formatNumber(product.sales) }}万</span>
              </div>
              <div class="progress-with-label">
                <div class="progress-bar">
                  <div class="progress-segment"
                       :class="getProgressColor(product.completion_rate)"
                       :style="{ width: Math.min(product.completion_rate, 100) + '%' }">
                  </div>
                </div>
                <span class="progress-text">{{ product.completion_rate }}%</span>
              </div>
            </div>
          </div>
          <el-empty v-if="activeProducts.length === 0" description="暂无在售产品" />
        </div>
      </div>

      <!-- 营业部完成情况 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <el-icon :size="22"><OfficeBuilding /></el-icon>
            营业部完成情况
          </div>
          <select v-model="selectedProduct" class="filter-select">
            <option value="">全部产品</option>
            <option v-for="p in productsList" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="card-body">
          <div class="group-stats-grid">
            <div v-for="group in topGroups" :key="group.id" class="group-stat-card">
              <div class="group-stat-header">
                <span class="group-stat-name">{{ group.name }}</span>
                <span class="group-stat-rate" :class="getRateColorClass(group.completion_rate)">
                  {{ group.completion_rate }}%
                </span>
              </div>
              <div class="group-stat-target">目标: ¥{{ formatNumber(group.target) }}万</div>
              <div class="group-stat-sales">完成: ¥{{ formatNumber(group.sales) }}万</div>
              <div class="progress-bar">
                <div class="progress-segment"
                     :class="getProgressColor(group.completion_rate)"
                     :style="{ width: Math.min(group.completion_rate, 100) + '%' }">
                </div>
              </div>
            </div>
          </div>
          <el-empty v-if="topGroups.length === 0" description="暂无数据" />
        </div>
      </div>
    </div>

    <!-- 大单提醒 + 预警提醒 -->
    <div class="two-col">
      <!-- 大单提醒 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <el-icon :size="22"><TrendCharts /></el-icon>
            大单提醒（≥50万）
            <el-tag type="warning" size="small" style="margin-left: 8px;">{{ largeOrders.length }}笔</el-tag>
          </div>
        </div>
        <div class="card-body">
          <div v-if="largeOrders.length > 0" class="order-list">
            <div v-for="order in largeOrders" :key="order.id" class="order-item">
              <div class="order-info">
                <div class="order-product">{{ order.product_name }}</div>
                <div class="order-meta">
                  <span>{{ order.member_name }}</span>
                  <span class="divider">|</span>
                  <span>{{ order.group_name }}</span>
                  <span class="divider">|</span>
                  <span class="order-date">{{ order.sale_date }}</span>
                </div>
              </div>
              <div class="order-amount">¥{{ formatNumber(order.amount) }}万</div>
            </div>
          </div>
          <el-empty v-else description="暂无大单记录" />
        </div>
      </div>

      <!-- 预警提醒 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <el-icon :size="22"><Warning /></el-icon>
            预警提醒
          </div>
        </div>
        <div class="card-body">
          <div v-if="alerts.length > 0" class="alert-list">
            <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="alert.type">
              <el-icon :size="20">
                <Warning v-if="alert.type === 'error'" />
                <WarningFilled v-else />
              </el-icon>
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-desc">{{ alert.description }}</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无预警信息" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardApi } from '../api'
import { Box, OfficeBuilding, TrendCharts, Warning, WarningFilled } from '@element-plus/icons-vue'

const summary = ref({
  active_products: 0,
  total_sales: 0,
  total_target: 0,
  completion_rate: 0,
  week_sales: 0,
  nearest_deadline: { product_name: null, days: null }
})
const activeProducts = ref([])
const groupsRanking = ref([])
const largeOrders = ref([])
const alerts = ref([])
const selectedProduct = ref('')
const productsList = ref([])

const topGroups = computed(() => groupsRanking.value.slice(0, 6))

onMounted(async () => {
  await loadData()
})

async function loadData() {
  try {
    const [summaryRes, productsRes, rankingRes] = await Promise.all([
      dashboardApi.summary(),
      dashboardApi.products(),
      dashboardApi.groupsRanking()
    ])

    summary.value = summaryRes
    activeProducts.value = productsRes
    productsList.value = productsRes
    groupsRanking.value = rankingRes

    await loadLargeOrders()
    generateAlerts()
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

async function loadLargeOrders() {
  try {
    const res = await dashboardApi.largeOrders(50)
    largeOrders.value = res
  } catch (error) {
    console.error('加载大单数据失败:', error)
  }
}

function generateAlerts() {
  const alertList = []

  activeProducts.value.forEach(product => {
    if (product.days_left <= 3) {
      alertList.push({
        id: `deadline-${product.id}`,
        type: 'error',
        title: `${product.name} 即将截止`,
        description: `距离募集结束仅剩 ${product.days_left} 天，当前完成率 ${product.completion_rate}%`
      })
    } else if (product.days_left <= 7) {
      alertList.push({
        id: `deadline-${product.id}`,
        type: 'warning',
        title: `${product.name} 临近截止`,
        description: `距离募集结束还有 ${product.days_left} 天`
      })
    }

    if (product.completion_rate < 30 && product.days_left <= 10) {
      alertList.push({
        id: `progress-${product.id}`,
        type: 'warning',
        title: `${product.name} 进度落后`,
        description: `当前完成率仅 ${product.completion_rate}%，请加快募集进度`
      })
    }
  })

  alerts.value = alertList
}

function formatNumber(num) {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

function getRateClass(rate) {
  if (!rate || rate < 50) return 'rate-danger'
  if (rate < 80) return 'rate-warning'
  return 'rate-success'
}

function getRateColorClass(rate) {
  if (!rate || rate < 50) return 'text-red'
  if (rate < 80) return 'text-orange'
  return 'text-green'
}

function getProgressColor(rate) {
  if (!rate || rate < 50) return 'progress-red'
  if (rate < 80) return 'progress-yellow'
  return 'progress-green'
}

function getStatusClass(days) {
  if (days <= 3) return 'tag-danger'
  if (days <= 7) return 'tag-warning'
  return 'tag-success'
}

function getProgressWidth(rate, min, max) {
  if (!rate) return '0%'
  if (rate <= min) return '0%'
  if (rate >= max) return '100%'
  return ((rate - min) / (max - min) * 100) + '%'
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

/* KPI 卡片 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.kpi-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  text-align: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.kpi-label {
  font-size: 14px;
  color: #6E6E73;
  margin-bottom: 12px;
  font-weight: 500;
}

.kpi-value {
  font-size: 36px;
  font-weight: 700;
  color: #1D1D1F;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.kpi-value.rate-danger { color: #FF3B30; }
.kpi-value.rate-warning { color: #FF9500; }
.kpi-value.rate-success { color: #34C759; }

.kpi-sub {
  font-size: 13px;
  color: #34C759;
  font-weight: 500;
}

.trend-up {
  font-weight: 700;
}

/* 进度条 - 4色分段 */
.progress-container {
  margin-top: 12px;
}

.progress-bar {
  height: 8px;
  background: #E5E5EA;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
}

.progress-segment {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-red { background: #FF3B30; }
.progress-orange { background: #FF9500; }
.progress-yellow { background: #FFCC00; }
.progress-green { background: #34C759; }

/* 两列布局 */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

/* 卡片样式 - Apple风格 */
.card {
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1D1D1F;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-body {
  padding: 24px;
}

/* 在售产品列表 */
.product-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.product-item {
  background: #F5F5F7;
  border-radius: 12px;
  padding: 18px;
  transition: background 0.2s ease;
}

.product-item:hover {
  background: #E8E8ED;
}

.product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.product-name {
  font-weight: 600;
  color: #1D1D1F;
  font-size: 15px;
}

.tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.tag-danger {
  background: #FFE5E3;
  color: #FF3B30;
}

.tag-success {
  background: #E3F5E8;
  color: #34C759;
}

.tag-warning {
  background: #FFF4E0;
  color: #FF9500;
}

.product-stats {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #6E6E73;
  margin-bottom: 12px;
}

.progress-with-label {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-with-label .progress-bar {
  flex: 1;
}

.progress-text {
  font-weight: 600;
  font-size: 14px;
  min-width: 40px;
  text-align: right;
  color: #1D1D1F;
}

/* 筛选下拉框 */
.filter-select {
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 13px;
  background: #F5F5F7;
  color: #1D1D1F;
  cursor: pointer;
  outline: none;
  transition: all 0.2s ease;
}

.filter-select:focus {
  border-color: #007AFF;
  background: #FFFFFF;
}

/* 营业部完成情况 - 2×3网格 */
.group-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.group-stat-card {
  background: #F5F5F7;
  border-radius: 12px;
  padding: 16px;
  transition: transform 0.2s ease;
}

.group-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.group-stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.group-stat-name {
  font-weight: 600;
  color: #1D1D1F;
  font-size: 14px;
}

.group-stat-rate {
  font-weight: 700;
  font-size: 15px;
}

.text-red { color: #FF3B30; }
.text-orange { color: #FF9500; }
.text-green { color: #34C759; }

.group-stat-target {
  font-size: 12px;
  color: #8E8E93;
  margin-bottom: 4px;
}

.group-stat-sales {
  font-size: 13px;
  color: #007AFF;
  font-weight: 600;
  margin-bottom: 10px;
}

.group-stat-card .progress-bar {
  height: 6px;
}

/* 大单提醒 */
.order-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFF4D6 100%);
  border-radius: 12px;
  border-left: 4px solid #FFCC00;
}

.order-product {
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.order-meta {
  font-size: 13px;
  color: #6E6E73;
}

.order-meta .divider {
  margin: 0 8px;
  color: #DCDFE6;
}

.order-date {
  color: #909399;
}

.order-amount {
  font-size: 20px;
  font-weight: 700;
  color: #FF3B30;
}

/* 预警提醒 */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
}

.alert-item.error {
  background: #FEE2E2;
  border-left: 4px solid #FF3B30;
}

.alert-item.warning {
  background: #FEF3C7;
  border-left: 4px solid #FFCC00;
}

.alert-title {
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 13px;
  color: #6E6E73;
}

/* 预警信息区域 */
.alert-section {
  margin-bottom: 20px;
}

:deep(.el-alert) {
  border-radius: 12px;
}
</style>
