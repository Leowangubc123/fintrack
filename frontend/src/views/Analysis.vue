<template>
  <div class="analysis-page">
    <!-- Tab 切换 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 个人分析 -->
    <div v-if="activeTab === 'personal'" class="tab-content">
      <div class="profile-header">
        <div class="profile-card">
          <div class="profile-card-header">
            <div class="profile-avatar-large">{{ selectedMember?.name?.charAt(0) || '?' }}</div>
            <div class="profile-basic-info">
              <div class="profile-name">{{ selectedMember?.name || '选择成员' }}</div>
              <div class="profile-department">{{ selectedMember?.group_name || '' }}</div>
            </div>
            <div class="profile-completion">
              <div class="profile-completion-value">{{ memberStats.completion_rate }}%</div>
              <div class="profile-completion-label">完成率</div>
            </div>
          </div>
          <div class="profile-stats-row">
            <div class="profile-stat-item">
              <div class="profile-stat-value-large">¥{{ formatNumber(memberStats.total_sales) }}</div>
              <div class="stat-label">总销售额</div>
            </div>
            <div class="profile-stat-divider"></div>
            <div class="profile-stat-item">
              <div class="profile-stat-value-large">{{ memberStats.order_count }}</div>
              <div class="stat-label">订单数</div>
            </div>
            <div class="profile-stat-divider"></div>
            <div class="profile-stat-item">
              <div class="profile-stat-value-large">{{ memberStats.large_orders }}</div>
              <div class="stat-label">大单数</div>
            </div>
          </div>
        </div>

        <div class="profile-kpi-card">
          <div class="kpi-big-value">{{ memberStats.ranking }}</div>
          <div class="kpi-big-label">业绩排名</div>
          <div class="rank-badge rank-1" v-if="memberStats.ranking <= 3">TOP{{ memberStats.ranking }}</div>
        </div>
      </div>

      <!-- 人员选择器 -->
      <div class="member-selector">
        <span class="filter-label">选择成员:</span>
        <el-select v-model="selectedMemberId" placeholder="请选择成员" style="width: 200px;"
          @change="onMemberChange">
          <el-option v-for="member in members" :key="member.id" :label="member.name" :value="member.id" />
        </el-select>
      </div>

      <!-- 热力图 -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">月度业绩热力图</div>
        </div>
        <div class="card-body">
          <div class="heatmap">
            <div v-for="month in heatmapData" :key="month.month" class="heatmap-month">
              <div class="heatmap-month-label">{{ month.month }}月</div>
              <div
                class="heatmap-cell"
                :class="`level-${month.level}`"
                :title="`${month.month}月: ¥${month.amount}万`"
              >
                {{ month.amount > 0 ? month.amount : '-' }}
              </div>
            </div>
          </div>
          <div class="heatmap-legend">
            <span>业绩水平:</span>
            <div class="legend-item">
              <div class="legend-color" style="background: #E5E5EA;"></div>
              <span>无数据</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background: #BBF7D0;"></div>
              <span>低</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background: #86EFAC;"></div>
              <span>中</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background: #22C55E;"></div>
              <span>高</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 产品矩阵 -->
    <div v-if="activeTab === 'matrix'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div class="card-title">产品销售矩阵</div>
          <div class="filter-group">
            <select v-model="matrixProduct" class="filter-select">
              <option value="">全部产品</option>
              <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
            <div class="toggle-group">
              <button class="toggle-btn" :class="{ active: matrixView === 'amount' }" @click="matrixView = 'amount'">金额</button>
              <button class="toggle-btn" :class="{ active: matrixView === 'rate' }" @click="matrixView = 'rate'">完成率</button>
            </div>
          </div>
        </div>
        <div class="card-body">
          <div class="matrix-container">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th class="fixed-left-header">成员</th>
                  <th v-for="p in matrixProducts" :key="p.id">{{ p.name }}</th>
                  <th class="fixed-right-header">合计</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in matrixData" :key="row.member.id">
                  <td class="fixed-left">
                    <div class="member-name">
                      <div class="member-avatar small">{{ row.member.name.charAt(0) }}</div>
                      <div>
                        <div style="font-weight: 600;">{{ row.member.name }}</div>
                        <div style="font-size: 12px; color: #6E6E73;">{{ row.member.group_name }}</div>
                      </div>
                    </div>
                  </td>
                  <td v-for="(value, idx) in row.values" :key="idx">
                    <span v-if="matrixView === 'rate'" class="rate-cell"
                      :class="getRateClass(value)"
                    >
                      {{ value }}%
                    </span>
                    <span v-else>{{ formatNumber(value) }}</span>
                  </td>
                  <td class="fixed-right group-total">
                    {{ matrixView === 'rate' ? row.avgRate + '%' : '¥' + formatNumber(row.total) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 营业部对比 -->
    <div v-if="activeTab === 'compare'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div class="card-title">营业部业绩对比</div>
        </div>
        <div class="card-body">
          <table class="compare-table">
            <thead>
              <tr>
                <th style="width: 80px;">排名</th>
                <th>营业部</th>
                <th>专员</th>
                <th>目标(万)</th>
                <th>完成(万)</th>
                <th>完成率</th>
                <th style="width: 200px;">趋势</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(group, index) in groupsRanking" :key="group.id">
                <td>
                  <div class="rank-badge" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
                </td>
                <td style="font-weight: 600;">{{ group.name }}</td>
                <td>{{ group.leader || '-' }}</td>
                <td>{{ formatNumber(group.target) }}</td>
                <td style="color: #007AFF; font-weight: 600;">{{ formatNumber(group.sales) }}</td>
                <td>
                  <span class="rate-cell" :class="getRateClass(group.completion_rate)">
                    {{ group.completion_rate }}%
                  </span>
                </td>
                <td>
                  <div class="trend-up">↑</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi, productsApi, membersApi } from '../api'

const activeTab = ref('personal')
const tabs = [
  { key: 'personal', label: '个人分析' },
  { key: 'matrix', label: '产品矩阵' },
  { key: 'compare', label: '营业部对比' },
]

// 个人分析
const members = ref([])
const selectedMemberId = ref('')
const selectedMember = ref(null)
const memberStats = ref({
  total_sales: 0,
  completion_rate: 0,
  order_count: 0,
  large_orders: 0,
  ranking: 1
})
const heatmapData = ref([
  { month: 1, amount: 120, level: 3 },
  { month: 2, amount: 80, level: 2 },
  { month: 3, amount: 150, level: 4 },
  { month: 4, amount: 200, level: 5 },
  { month: 5, amount: 90, level: 2 },
  { month: 6, amount: 0, level: 0 },
  { month: 7, amount: 110, level: 3 },
  { month: 8, amount: 170, level: 4 },
  { month: 9, amount: 130, level: 3 },
  { month: 10, amount: 0, level: 0 },
  { month: 11, amount: 0, level: 0 },
  { month: 12, amount: 0, level: 0 },
])

// 产品矩阵
const products = ref([])
const matrixProduct = ref('')
const matrixView = ref('amount')
const matrixProducts = ref([])
const matrixData = ref([])

// 营业部对比
const groupsRanking = ref([])

onMounted(() => {
  loadMembers()
  loadProducts()
  loadMatrixData()
  loadGroupsRanking()
})

async function loadMembers() {
  try {
    const res = await membersApi.list()
    members.value = res
    if (res.length > 0) {
      selectedMemberId.value = res[0].id
      selectedMember.value = res[0]
    }
  } catch (error) {
    console.error('加载成员失败:', error)
  }
}

function onMemberChange(memberId) {
  selectedMember.value = members.value.find(m => m.id === memberId)
}

async function loadProducts() {
  try {
    const res = await productsApi.list()
    products.value = res
  } catch (error) {
    console.error('加载产品失败:', error)
  }
}

async function loadMatrixData() {
  try {
    const res = await dashboardApi.matrix()
    matrixProducts.value = res.products.slice(0, 5)
    matrixData.value = res.members.slice(0, 10).map((member, idx) => ({
      member,
      values: res.amount_matrix[idx]?.slice(0, 5) || [],
      total: res.amount_matrix[idx]?.reduce((a, b) => a + b, 0) || 0,
      avgRate: Math.round(Math.random() * 100)
    }))
  } catch (error) {
    console.error('加载矩阵数据失败:', error)
  }
}

async function loadGroupsRanking() {
  try {
    const res = await dashboardApi.groupsRanking()
    groupsRanking.value = res.slice(0, 10)
  } catch (error) {
    console.error('加载排名失败:', error)
  }
}

function formatNumber(num) {
  if (!num) return '0'
  return Number(num).toLocaleString()
}

function getRateClass(rate) {
  if (rate >= 100) return 'rate-green'
  if (rate >= 80) return 'rate-yellow'
  if (rate >= 50) return 'rate-orange'
  return 'rate-red'
}
</script>

<style scoped>
.analysis-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* Tab 切换 */
.tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: #F5F5F7;
  border-radius: 10px;
  margin-bottom: 24px;
  width: fit-content;
}

.tab-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  background: transparent;
  color: #6E6E73;
  transition: all 0.2s ease;
}

.tab-btn.active {
  background: #FFFFFF;
  color: #007AFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tab-content {
  display: block;
}

/* 卡片 */
.card {
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-bottom: 20px;
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
}

.card-body {
  padding: 24px;
}

/* 个人档案 */
.profile-header {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.profile-card {
  flex: 1;
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.profile-card-header {
  background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
  color: white;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.profile-avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.profile-basic-info {
  flex: 1;
}

.profile-name {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.profile-department {
  font-size: 14px;
  opacity: 0.95;
}

.profile-completion {
  text-align: center;
  padding-left: 16px;
  border-left: 1px solid rgba(255, 255, 255, 0.3);
}

.profile-completion-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.profile-completion-label {
  font-size: 12px;
  opacity: 0.9;
}

.profile-stats-row {
  display: flex;
  padding: 24px;
  align-items: center;
  justify-content: space-around;
}

.profile-stat-item {
  text-align: center;
  flex: 1;
}

.profile-stat-value-large {
  font-size: 24px;
  font-weight: 700;
  color: #1D1D1F;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 13px;
  color: #6E6E73;
}

.profile-stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(0, 0, 0, 0.1);
}

.profile-kpi-card {
  width: 200px;
  background: white;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  text-align: center;
}

.kpi-big-value {
  font-size: 44px;
  font-weight: 700;
  color: #007AFF;
  margin-bottom: 8px;
}

.kpi-big-label {
  font-size: 14px;
  color: #6E6E73;
  margin-bottom: 16px;
}

/* 人员选择器 */
.member-selector {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: #F5F5F7;
  border-radius: 12px;
  align-items: center;
}

.filter-label {
  font-size: 14px;
  color: #6E6E73;
}

/* 热力图 */
.heatmap {
  display: flex;
  gap: 8px;
  justify-content: space-between;
  align-items: stretch;
  min-height: 200px;
}

.heatmap-month {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.heatmap-month-label {
  font-size: 13px;
  color: #6E6E73;
  font-weight: 600;
}

.heatmap-cell {
  width: 100%;
  min-width: 36px;
  max-width: 60px;
  flex: 1;
  border-radius: 10px;
  background: #E5E5EA;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: white;
  cursor: pointer;
  transition: transform 0.2s ease;
  min-height: 60px;
}

.heatmap-cell:hover {
  transform: scale(1.1);
}

.heatmap-cell.level-0 { background: #E5E5EA; color: #8E8E93; }
.heatmap-cell.level-1 { background: #BBF7D0; color: #059669; }
.heatmap-cell.level-2 { background: #86EFAC; color: #059669; }
.heatmap-cell.level-3 { background: #4ADE80; color: white; }
.heatmap-cell.level-4 { background: #22C55E; color: white; }
.heatmap-cell.level-5 { background: #16A34A; color: white; }

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  font-size: 13px;
  color: #6E6E73;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

/* 排名徽章 */
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  background: #F5F5F7;
  color: #6E6E73;
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: white;
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%);
  color: white;
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%);
  color: white;
}

/* 矩阵表格 */
.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 13px;
  background: #F5F5F7;
  color: #1D1D1F;
  cursor: pointer;
  outline: none;
}

.toggle-group {
  display: inline-flex;
  background: #FFFFFF;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.toggle-btn {
  padding: 8px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #6E6E73;
  transition: all 0.2s ease;
}

.toggle-btn.active {
  background: #007AFF;
  color: white;
}

.matrix-container {
  overflow-x: auto;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.matrix-table th,
.matrix-table td {
  padding: 12px 14px;
  text-align: center;
  border: 1px solid rgba(0, 0, 0, 0.05);
  white-space: nowrap;
}

.matrix-table th {
  background: #F5F5F7;
  font-weight: 600;
  color: #6E6E73;
  font-size: 12px;
}

.matrix-table .fixed-left {
  position: sticky;
  left: 0;
  background: white;
  z-index: 10;
  text-align: left;
  min-width: 140px;
}

.matrix-table .fixed-left-header {
  position: sticky;
  left: 0;
  background: #F5F5F7;
  z-index: 11;
}

.matrix-table .fixed-right {
  position: sticky;
  right: 0;
  background: white;
  z-index: 10;
  font-weight: 600;
}

.matrix-table .fixed-right-header {
  position: sticky;
  right: 0;
  background: #F5F5F7;
  z-index: 11;
}

.group-total {
  font-weight: 700;
  color: #007AFF;
}

.member-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-avatar.small {
  width: 28px;
  height: 28px;
  font-size: 12px;
}

/* 完成率颜色 */
.rate-cell {
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  display: inline-block;
}

.rate-green { color: #059669; background: #D1FAE5; }
.rate-yellow { color: #D97706; background: #FEF3C7; }
.rate-orange { color: #EA580C; background: #FFE4D6; }
.rate-red { color: #DC2626; background: #FEE2E2; }

/* 对比表格 */
.compare-table {
  width: 100%;
  border-collapse: collapse;
}

.compare-table th {
  font-size: 13px;
  font-weight: 600;
  color: #6E6E73;
  background: #F5F5F7;
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.compare-table td {
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 14px;
  color: #1D1D1F;
}

.compare-table tr:hover {
  background: #FAFAFA;
}

/* 趋势指示器 */
.trend-up {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 700;
  background: #D1FAE5;
  color: #059669;
}
</style>
