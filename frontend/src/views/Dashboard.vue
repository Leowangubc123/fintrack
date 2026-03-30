<template>
  <div class="dashboard">
    <!-- KPI 卡片 -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">本月在售产品</div>
        <div class="kpi-value">{{ summary.active_products || 0 }}</div>
        <div class="kpi-sub">个产品募集中</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">本年度已发售</div>
        <div class="kpi-value">{{ summary.year_products || 0 }}</div>
        <div class="kpi-sub">个重点产品</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">本年度销售额</div>
        <div class="kpi-value kpi-value-sales">¥{{ summary.total_sales.toFixed(1) }}万</div>
        <div class="kpi-sub" v-if="summary.week_sales > 0">
          <span class="trend-up">↑</span> 近7日 ¥{{ summary.week_sales.toFixed(1) }}万
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">整体完成率</div>
        <div class="kpi-value" :class="getRateClass(summary.completion_rate)">
          {{ summary.completion_rate || 0 }}%
        </div>
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-segment" :class="getProgressColor(summary.completion_rate)"
              :style="{ width: Math.min(summary.completion_rate || 0, 100) + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 在售产品卡片（每个产品一张，动态堆叠） -->
    <div v-if="activeProducts.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <div class="empty-text">当前暂无在售产品</div>
    </div>

    <div v-for="product in activeProducts" :key="product.id" class="product-card">
      <!-- 卡片顶部 -->
      <div class="card-topbar">
        <div class="topbar-left">
          <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          <span class="card-title">在售产品</span>
        </div>
        <div class="active-badge">
          <span class="active-dot"></span>
          募集中
        </div>
      </div>

      <!-- 卡片主体 -->
      <div class="card-body">
        <!-- 左：产品信息 -->
        <div class="product-detail">
          <div class="product-name" :title="product.name">{{ product.name }}</div>
          <div class="product-meta">
            <span class="product-code">{{ product.code || '—' }}</span>
            <span class="deadline-tag" :class="{ urgent: product.days_left <= 7 && product.days_left >= 0, ended: product.days_left < 0 }">
              {{ product.days_left < 0 ? '已结束' : `剩 ${product.days_left} 天` }}
            </span>
          </div>
          <div class="completion-block">
            <div class="completion-row">
              <span class="completion-pct" :style="{ color: getRateColor(product.completion_rate) }">
                {{ product.completion_rate }}%
              </span>
              <span class="completion-label">整体完成率</span>
            </div>
            <div class="progress-bar-thick">
              <div class="progress-fill" :class="getProgressColor(product.completion_rate)"
                :style="{ width: Math.min(product.completion_rate, 100) + '%' }"></div>
            </div>
            <div class="amount-grid">
              <div class="amount-item">
                <div class="amount-val">¥{{ formatNumber(product.target) }}万</div>
                <div class="amount-lbl">全公司目标</div>
              </div>
              <div class="amount-item">
                <div class="amount-val blue">¥{{ formatNumber(product.sales) }}万</div>
                <div class="amount-lbl">已完成销量</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右：营业部完成情况 -->
        <div class="groups-section">
          <div class="groups-header">
            <span class="groups-title">各营业部完成情况</span>
            <span class="groups-sub">按完成率排序</span>
          </div>
          <div class="group-rows">
            <div v-for="(group, idx) in productGroupsMap[product.id] || []" :key="group.id" class="group-row">
              <div class="rank-col">
                <div class="medal" :class="getMedalClass(idx)">{{ idx + 1 }}</div>
              </div>
              <div class="g-name">{{ group.name }}</div>
              <div class="g-rate-block">
                <div class="g-rate-label">完成率</div>
                <div v-if="group.target > 0" class="g-rate-val" :style="{ color: getRateColor(group.completion_rate) }">
                  {{ group.completion_rate }}%
                </div>
                <div v-else class="g-rate-val g-no-task">无任务</div>
              </div>
              <div class="g-sales-block">
                <div class="g-sales-label">销量</div>
                <div class="g-sales-val">¥{{ formatNumber(group.sales) }}万</div>
              </div>
              <div class="g-bar-wrap">
                <div class="g-bar-track">
                  <div v-if="group.target > 0" class="g-bar-fill" :class="getProgressColor(group.completion_rate)"
                    :style="{ width: Math.min(group.completion_rate, 100) + '%' }"></div>
                </div>
              </div>
            </div>
            <div v-if="!productGroupsMap[product.id]" class="groups-loading">加载中...</div>
          </div>
        </div>
      </div>
    </div>
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
const productGroupsMap = ref({})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  try {
    const [summaryRes, productsRes] = await Promise.all([
      dashboardApi.summary(),
      dashboardApi.products()
    ])
    summary.value = summaryRes
    activeProducts.value = productsRes

    // 并行加载每个产品的营业部数据
    await Promise.all(productsRes.map(async (p) => {
      const rankings = await dashboardApi.groupsRanking(p.id)
      // 按完成率降序排列
      const sorted = [...rankings].sort((a, b) => b.completion_rate - a.completion_rate)
      productGroupsMap.value = { ...productGroupsMap.value, [p.id]: sorted }
    }))
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

function formatNumber(num) {
  if (!num) return '0'
  return Math.round(Number(num) * 10) / 10
}


function getRateColor(rate) {
  if (!rate || rate < 50) return '#FF3B30'
  if (rate < 100) return '#FF9500'
  return '#34C759'
}

function getRateClass(rate) {
  if (!rate || rate < 50) return 'rate-danger'
  if (rate < 80) return 'rate-warning'
  return 'rate-success'
}

function getProgressColor(rate) {
  if (!rate || rate < 50) return 'progress-red'
  if (rate < 100) return 'progress-orange'
  return 'progress-green'
}

function getMedalClass(idx) {
  if (idx === 0) return 'medal-1'
  if (idx === 1) return 'medal-2'
  if (idx === 2) return 'medal-3'
  return 'medal-n'
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

/* ── KPI 卡片 ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}
.kpi-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0,0,0,.06);
  text-align: center;
  transition: transform .2s ease, box-shadow .2s ease;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0,0,0,.1);
}
.kpi-label  { font-size: 14px; color: #6E6E73; margin-bottom: 12px; font-weight: 500; }
.kpi-value  { font-size: 36px; font-weight: 700; color: #1D1D1F; margin-bottom: 8px; letter-spacing: -.5px; }
.kpi-value-sales { font-size: 26px; }
.kpi-value.rate-danger  { color: #FF3B30; }
.kpi-value.rate-warning { color: #FF9500; }
.kpi-value.rate-success { color: #34C759; }
.kpi-sub    { font-size: 13px; color: #34C759; font-weight: 500; }
.trend-up   { font-weight: 700; }
.progress-container { margin-top: 12px; padding: 0 20px; }

/* 公用进度条 */
.progress-bar {
  height: 8px; background: #E5E5EA; border-radius: 4px; overflow: hidden;
}
.progress-segment { height: 100%; transition: width .3s ease; border-radius: 4px; }
.progress-red    { background: #FF3B30; }
.progress-orange { background: #FF9500; }
.progress-green  { background: #34C759; }

/* ── 空状态 ── */
.empty-state {
  text-align: center;
  padding: 60px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 20px rgba(0,0,0,.06);
}
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-text { font-size: 15px; color: #8E8E93; }

/* ── 产品卡片 ── */
.product-card {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 20px rgba(0,0,0,.07);
  overflow: hidden;
  margin-bottom: 20px;
}

/* 卡片顶部 */
.card-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 15px 24px;
  border-bottom: 1px solid #F0F0F0;
}
.topbar-left { display: flex; align-items: center; gap: 8px; }
.card-icon   { width: 19px; height: 19px; color: #007AFF; flex-shrink: 0; }
.card-title  { font-size: 15px; font-weight: 600; color: #1D1D1F; }
.active-badge {
  display: inline-flex; align-items: center; gap: 5px;
  background: #E3F5E8; color: #1A9E3F;
  font-size: 12px; font-weight: 600;
  padding: 3px 10px; border-radius: 20px;
}
.active-dot {
  width: 6px; height: 6px; border-radius: 50%; background: #34C759;
  animation: pulse 1.5s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }

/* 卡片主体：左右 */
.card-body { display: flex; }

/* 左：产品信息 */
.product-detail {
  width: 270px; flex-shrink: 0;
  padding: 20px 22px;
  border-right: 1px solid #F0F0F0;
  display: flex; flex-direction: column; gap: 14px;
}
.product-name {
  font-size: 15px; font-weight: 700; color: #1D1D1F; line-height: 1.35;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.product-meta { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.product-code {
  font-family: "SF Mono","Menlo",monospace;
  font-size: 12px; color: #007AFF; font-weight: 600;
  background: #F0F7FF; padding: 3px 10px; border-radius: 6px;
}
.deadline-tag {
  font-size: 12px; font-weight: 600;
  color: #FF9500; background: #FFF4E0;
  padding: 3px 10px; border-radius: 20px;
  border: 1px solid rgba(255,149,0,.2); white-space: nowrap;
}
.deadline-tag.urgent {
  color: #FF3B30; background: #FFF0EF;
  border-color: rgba(255,59,48,.2);
}
.deadline-tag.ended {
  color: #8E8E93; background: #F2F2F7;
  border-color: rgba(142,142,147,.3);
}

/* 完成率大字 */
.completion-block { display: flex; flex-direction: column; gap: 8px; }
.completion-row   { display: flex; align-items: flex-end; gap: 6px; }
.completion-pct   { font-size: 44px; font-weight: 800; line-height: 1; letter-spacing: -2px; }
.completion-label { font-size: 12px; color: #8E8E93; padding-bottom: 7px; }
.progress-bar-thick {
  height: 8px; background: #E5E5EA; border-radius: 4px; overflow: hidden;
}
.progress-fill { height: 100%; border-radius: 4px; transition: width .4s ease; }

/* 金额两格 */
.amount-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.amount-item { background: #F9F9FB; border-radius: 10px; padding: 10px 12px; }
.amount-val  { font-size: 15px; font-weight: 700; color: #1D1D1F; }
.amount-val.blue { color: #007AFF; }
.amount-lbl  { font-size: 11px; color: #8E8E93; margin-top: 2px; }

/* 右：营业部 */
.groups-section {
  flex: 1; min-width: 0;
  padding: 18px 0 18px 22px;
  display: flex; flex-direction: column;
}
.groups-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px; padding-right: 24px;
}
.groups-title { font-size: 12px; font-weight: 600; color: #8E8E93; text-transform: uppercase; letter-spacing: .5px; }
.groups-sub   { font-size: 12px; color: #AEAEB2; }
.groups-loading { padding: 16px; color: #AEAEB2; font-size: 13px; }

.group-rows { display: flex; flex-direction: column; }
.group-row {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid #F8F8FA;
}
.group-row:last-child { border-bottom: none; }

/* 排名徽章 */
.rank-col { width: 28px; flex-shrink: 0; }
.medal {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}
.medal-1 { background: linear-gradient(135deg,#FFD700,#FFA500); color:#fff; }
.medal-2 { background: linear-gradient(135deg,#C0C0C0,#A0A0A0); color:#fff; }
.medal-3 { background: linear-gradient(135deg,#CD7F32,#B87333); color:#fff; }
.medal-n { background: #EBEBEF; color: #6E6E73; }

/* 营业部名 */
.g-name { width: 95px; flex-shrink: 0; font-size: 14px; font-weight: 600; color: #1D1D1F; }

/* 完成率（上标签 下数值） */
.g-rate-block { width: 72px; flex-shrink: 0; display: flex; flex-direction: column; gap: 2px; }
.g-rate-label { font-size: 10px; color: #AEAEB2; font-weight: 500; }
.g-rate-val   { font-size: 17px; font-weight: 800; }
.g-no-task    { font-size: 12px; font-weight: 500; color: #AEAEB2; }

/* 销量（上标签 下数值） */
.g-sales-block { width: 80px; flex-shrink: 0; display: flex; flex-direction: column; gap: 2px; }
.g-sales-label { font-size: 10px; color: #AEAEB2; font-weight: 500; }
.g-sales-val   { font-size: 14px; font-weight: 700; color: #007AFF; }

/* 进度条延伸到右边缘 */
.g-bar-wrap {
  flex: 1; padding-right: 24px;
  display: flex; align-items: center;
}
.g-bar-track { flex: 1; height: 10px; background: #EBEBEF; border-radius: 5px; overflow: hidden; }
.g-bar-fill  { height: 100%; border-radius: 5px; transition: width .4s ease; }
</style>
