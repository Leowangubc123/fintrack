<template>
  <div class="dashboard">
    <!-- 顶部KPI卡片 -->
    <el-row :gutter="16" class="kpi-section">
      <el-col :span="8">
        <el-card class="kpi-card">
          <div class="kpi-title">本月在售产品</div>
          <div class="kpi-value">{{ summary.active_products || 0 }}</div>
          <div class="kpi-unit">个产品</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="kpi-card">
          <div class="kpi-title">整体销售额</div>
          <div class="kpi-value">¥{{ formatNumber(summary.total_sales) }}</div>
          <div class="kpi-trend" v-if="summary.week_sales > 0">
            <span class="trend-up">↑</span> 近7日 ¥{{ formatNumber(summary.week_sales) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="kpi-card">
          <div class="kpi-title">整体完成率</div>
          <div class="kpi-value" :class="getRateClass(summary.completion_rate)">
            {{ summary.completion_rate || 0 }}%
          </div>
          <div class="kpi-progress">
            <el-progress
              :percentage="Math.min(summary.completion_rate || 0, 100)"
              :color="PROGRESS_COLORS"
              :stroke-width="8"
              :show-text="false"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 预警信息 -->
    <el-row v-if="summary.nearest_deadline?.days !== null" class="alert-section">
      <el-col :span="24">
        <el-alert
          :title="`【预警】${summary.nearest_deadline.product_name} 距离募集截止还有 ${summary.nearest_deadline.days} 天`"
          :type="summary.nearest_deadline.days <= 3 ? 'error' : 'warning'"
          show-icon
          :closable="false"
        />
      </el-col>
    </el-row>

    <!-- 中部：在售产品 + 营业部排名 -->
    <el-row :gutter="16" class="main-section">
      <!-- 在售产品明细 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">在售产品明细</span>
              <el-button text @click="$router.push('/products')">查看全部</el-button>
            </div>
          </template>

          <div class="product-list">
            <div
              v-for="product in activeProducts"
              :key="product.id"
              class="product-item"
            >
              <div class="product-header">
                <span class="product-name">{{ product.name }}</span>
                <el-tag :type="getStatusType(product.days_left)" size="small">
                  剩{{ product.days_left }}天
                </el-tag>
              </div>
              <div class="product-stats">
                <span>目标: ¥{{ formatNumber(product.target) }}万</span>
                <span>已完成: ¥{{ formatNumber(product.sales) }}万</span>
              </div>
              <div class="product-progress">
                <el-progress
                  :percentage="Math.min(product.completion_rate, 100)"
                  :color="PROGRESS_COLORS"
                  :stroke-width="10"
                />
                <span class="progress-text">{{ product.completion_rate }}%</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 营业部排名 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">营业部完成情况排名</span>
            </div>
          </template>

          <div class="ranking-list">
            <div
              v-for="(group, index) in groupsRanking"
              :key="group.id"
              class="ranking-item"
            >
              <div class="rank-number" :class="`rank-${group.rank}`">
                {{ group.rank }}
              </div>
              <div class="rank-info">
                <div class="rank-name">{{ group.name }}</div>
                <div class="rank-bar">
                  <el-progress
                    :percentage="Math.min(group.completion_rate, 100)"
                    :color="PROGRESS_COLORS"
                    :stroke-width="8"
                    :show-text="false"
                  />
                </div>
              </div>
              <div class="rank-stats">
                <div class="rank-sales">¥{{ formatNumber(group.sales) }}万</div>
                <div class="rank-rate" :class="getRateClass(group.completion_rate)">
                  {{ group.completion_rate }}%
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部：大单提醒 + 预警信息 -->
    <el-row :gutter="16" class="bottom-section">
      <!-- 大单提醒 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon class="header-icon"><TrendCharts /></el-icon>
                大单提醒（≥50万）
              </span>
              <el-tag type="warning" size="small">{{ largeOrders.length }}笔</el-tag>
            </div>
          </template>

          <div class="order-list" v-if="largeOrders.length > 0">
            <div
              v-for="order in largeOrders"
              :key="order.id"
              class="order-item"
            >
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
        </el-card>
      </el-col>

      <!-- 预警信息 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon class="header-icon"><Warning /></el-icon>
                预警提醒
              </span>
            </div>
          </template>

          <div class="alert-list" v-if="alerts.length > 0">
            <div
              v-for="alert in alerts"
              :key="alert.id"
              class="alert-item"
              :class="alert.type"
            >
              <el-icon class="alert-icon">
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
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi } from '../api'

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

// 进度条颜色
const PROGRESS_COLORS = [
  { color: '#EF4444', percentage: 25 },   // 0-25% 红色
  { color: '#F97316', percentage: 50 },   // 25-50% 橙色
  { color: '#F59E0B', percentage: 75 },   // 50-75% 黄色
  { color: '#10B981', percentage: 100 }   // 75-100% 绿色
]

onMounted(async () => {
  await loadData()
})

async function loadData() {
  try {
    // 并行加载数据
    const [summaryRes, productsRes, rankingRes] = await Promise.all([
      dashboardApi.summary(),
      dashboardApi.products(),
      dashboardApi.groupsRanking()
    ])

    summary.value = summaryRes
    activeProducts.value = productsRes
    groupsRanking.value = rankingRes

    // 加载大单数据（≥50万）和预警信息
    await loadLargeOrders()
    await loadAlerts()
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

async function loadLargeOrders() {
  try {
    // 获取最近的大单数据（≥50万）
    const res = await dashboardApi.largeOrders(50)
    largeOrders.value = res
  } catch (error) {
    console.error('加载大单数据失败:', error)
    // 如果API暂时不可用，使用模拟数据
    largeOrders.value = [
      { id: 1, product_name: 'XX量化对冲1号', member_name: '张三', group_name: '财富一部', amount: 100, sale_date: '2024-03-05' },
      { id: 2, product_name: 'XX量化对冲1号', member_name: '李四', group_name: '财富二部', amount: 80, sale_date: '2024-03-04' },
      { id: 3, product_name: 'XX私募精选2号', member_name: '王五', group_name: '财富一部', amount: 60, sale_date: '2024-03-03' },
    ]
  }
}

async function loadAlerts() {
  // 生成预警信息
  const alertList = []

  // 产品即将到期预警
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

    // 完成率过低预警
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
  if (typeof rate !== 'number' || isNaN(rate)) return 'rate-danger'
  if (rate < 0) return 'rate-danger'
  if (rate > 100) return 'rate-excellent'  // 绿色
  if (rate === 100) return 'rate-good'     // 黄色
  if (rate >= 80) return 'rate-normal'
  if (rate >= 50) return 'rate-warning'
  return 'rate-danger'                     // 红色
}

function getStatusType(days) {
  if (days <= 3) return 'danger'
  if (days <= 7) return 'warning'
  return 'success'
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.kpi-section {
  margin-bottom: 16px;
}

.kpi-card {
  text-align: center;
  padding: 10px;
}

.kpi-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 32px;
  font-weight: bold;
  color: #1B3A6B;
  margin-bottom: 4px;
}

.kpi-unit {
  font-size: 12px;
  color: #909399;
}

.kpi-trend {
  font-size: 13px;
  color: #10B981;
}

.trend-up {
  font-weight: bold;
}

.kpi-progress {
  margin-top: 8px;
}

.alert-section {
  margin-bottom: 16px;
}

.main-section {
  margin-bottom: 16px;
}

.section-card {
  min-height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1B3A6B;
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.product-item {
  padding: 16px;
  background: #F5F7FA;
  border-radius: 8px;
}

.product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.product-name {
  font-weight: 600;
  color: #1B3A6B;
}

.product-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.product-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-progress .el-progress {
  flex: 1;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: #1B3A6B;
  min-width: 50px;
  text-align: right;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #F5F7FA;
  border-radius: 8px;
}

.rank-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  background: #E4E7ED;
  color: #606266;
}

.rank-1 {
  background: #F0A500;
  color: #fff;
}

.rank-2 {
  background: #C0C0C0;
  color: #fff;
}

.rank-3 {
  background: #CD7F32;
  color: #fff;
}

.rank-info {
  flex: 1;
}

.rank-name {
  font-weight: 600;
  color: #1B3A6B;
  margin-bottom: 6px;
}

.rank-bar .el-progress {
  width: 100%;
}

.rank-stats {
  text-align: right;
  min-width: 80px;
}

.rank-sales {
  font-size: 13px;
  color: #606266;
}

.rank-rate {
  font-size: 14px;
  font-weight: 600;
}

.rate-excellent { color: #10B981; }
.rate-good { color: #F59E0B; }      /* Yellow */
.rate-normal { color: #F97316; }
.rate-warning { color: #EF4444; }
.rate-danger { color: #DC2626; }

.bottom-section {
  margin-bottom: 16px;
}

.header-icon {
  margin-right: 8px;
  font-size: 18px;
  vertical-align: middle;
}

/* 大单列表样式 */
.order-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #FEF3C7;
  border-radius: 8px;
  border-left: 4px solid #F59E0B;
}

.order-info {
  flex: 1;
}

.order-product {
  font-weight: 600;
  color: #1B3A6B;
  margin-bottom: 4px;
}

.order-meta {
  font-size: 13px;
  color: #606266;
}

.order-meta .divider {
  margin: 0 8px;
  color: #DCDFE6;
}

.order-date {
  color: #909399;
}

.order-amount {
  font-size: 18px;
  font-weight: bold;
  color: #DC2626;
}

/* 预警列表样式 */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
}

.alert-item.error {
  background: #FEE2E2;
  border-left: 4px solid #EF4444;
}

.alert-item.error .alert-icon {
  color: #DC2626;
}

.alert-item.warning {
  background: #FEF3C7;
  border-left: 4px solid #F59E0B;
}

.alert-item.warning .alert-icon {
  color: #D97706;
}

.alert-icon {
  font-size: 20px;
  margin-top: 2px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  color: #1B3A6B;
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 13px;
  color: #606266;
}
</style>