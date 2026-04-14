<template>
  <div class="advisory-dashboard">
    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">累计签约户数</div>
        <div class="kpi-value">{{ formatNumber(stats.total_households) }}<span class="unit">户</span></div>
        <div class="kpi-change" :class="{ 'is-positive': stats.households_change >= 0, 'is-negative': stats.households_change < 0 }">
          较上次更新 {{ stats.households_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.households_change || 0) }}户
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">累计签约资产</div>
        <div class="kpi-value">{{ formatNumber(stats.total_assets) }}<span class="unit">万</span></div>
        <div class="kpi-change" :class="{ 'is-positive': stats.assets_change >= 0, 'is-negative': stats.assets_change < 0 }">
          较上次更新 {{ stats.assets_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.assets_change || 0) }}万
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">本年投顾收入</div>
        <div class="kpi-value">{{ formatNumber(stats.total_income) }}<span class="unit">元</span></div>
        <div class="kpi-change" :class="{ 'is-positive': stats.income_change >= 0, 'is-negative': stats.income_change < 0 }">
          较上次更新 {{ stats.income_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.income_change || 0) }}元
        </div>
      </div>
      <div class="kpi-card kpi-date">
        <div class="kpi-label">最近更新日期</div>
        <div class="kpi-value date">{{ stats.last_update_date || '-' }}</div>
        <div class="kpi-sub">数据时点更新</div>
      </div>
    </div>

    <!-- Charts -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">各产品签约分布</div>
          <div class="chart-subtitle">按签约户数统计</div>
        </div>
        <div class="product-bars">
          <div
            v-for="product in productOrder"
            :key="product"
            class="product-bar-row"
          >
            <div class="product-label">{{ product }}</div>
            <div class="product-bar-track">
              <div
                class="product-bar-fill"
                :style="{ width: getBarWidth(product), backgroundColor: getProductColor(product) }"
              >
                <span class="bar-value">{{ dataMap[product]?.households || 0 }}户</span>
              </div>
            </div>
            <div class="product-asset-text">¥{{ formatAsset(dataMap[product]?.assets || 0) }}万</div>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">年度趋势分析</div>
          <div class="chart-legend">
            <span class="legend-item"><span class="dot income"></span>投顾收入(元)</span>
            <span class="legend-item"><span class="dot line"></span>签约户数</span>
          </div>
        </div>
        <div ref="trendChart" class="chart-content" style="height: 320px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { advisoryApi } from '../../api/advisory.js'

const stats = ref({
  total_households: 0,
  total_assets: 0,
  total_income: 0,
  households_change: 0,
  assets_change: 0,
  income_change: 0,
  last_update_date: null,
  product_distribution: [],
  trend_data: []
})

const trendChart = ref(null)
let trendChartInstance = null

const productOrder = ['万2', '千1', '千3', 'ETF投顾', '量化T', 'GWT']

const productColors = {
  '万2': '#0EA5E9',
  '千1': '#10B981',
  '千3': '#F59E0B',
  'ETF投顾': '#3B82F6',
  '量化T': '#8B5CF6',
  'GWT': '#F43F5E'
}

const dataMap = computed(() => {
  const map = {}
  const distribution = stats.value.product_distribution || []
  distribution.forEach(item => {
    map[item.product_type] = {
      households: item.households || 0,
      assets: item.assets || 0
    }
  })
  productOrder.forEach(p => {
    if (!map[p]) map[p] = { households: 0, assets: 0 }
  })
  return map
})

const maxHouseholds = computed(() => {
  return Math.max(...productOrder.map(p => dataMap.value[p]?.households || 0), 1)
})

const getBarWidth = (product) => {
  const val = dataMap.value[product]?.households || 0
  if (maxHouseholds.value === 0) return '0%'
  return Math.max((val / maxHouseholds.value) * 100, 3) + '%'
}

const getProductColor = (product) => productColors[product] || '#1EAEDB'

const formatAsset = (num) => {
  if (num === null || num === undefined) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '亿'
  return num.toLocaleString('zh-CN')
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN')
}

const fetchStats = async () => {
  try {
    const res = await advisoryApi.getStats({
      year: new Date().getFullYear()
    })
    stats.value = {
      ...stats.value,
      ...res
    }
    updateCharts()
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    ElMessage.error('获取统计数据失败')
  }
}

const initCharts = () => {
  if (trendChart.value) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  trendChartInstance?.resize()
}

const updateCharts = () => {
  nextTick(() => {
    updateTrendChart()
  })
}

const updateTrendChart = () => {
  if (!trendChartInstance) return

  const trendData = stats.value.trend_data || []
  const months = trendData.map(t => t.month + '月')
  const incomeData = trendData.map(t => t.income || 0)
  const householdsData = trendData.map(t => t.households || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#374151' }
    },
    yAxis: [
      {
        type: 'value',
        name: '投顾收入(元)',
        position: 'left',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#F3F4F6' } },
        axisLabel: { color: '#374151' }
      },
      {
        type: 'value',
        name: '签约户数',
        position: 'right',
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: { color: '#374151' }
      }
    ],
    series: [
      {
        name: '投顾收入',
        type: 'bar',
        data: incomeData,
        itemStyle: { color: '#1EAEDB', borderRadius: [4, 4, 0, 0] },
        barWidth: '40%'
      },
      {
        name: '签约户数',
        type: 'line',
        yAxisIndex: 1,
        data: householdsData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#F59E0B', width: 3 },
        itemStyle: { color: '#F59E0B', borderWidth: 2, borderColor: '#fff' }
      }
    ]
  }

  trendChartInstance.setOption(option)
}

onMounted(() => {
  fetchStats()
  initCharts()
})
</script>

<style scoped>
.advisory-dashboard {
  padding: 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F3F4F6;
}

.kpi-label {
  font-size: 14px;
  color: #6B7280;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.kpi-value .unit {
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  margin-left: 4px;
}

.kpi-value.date {
  font-size: 20px;
  color: #1EAEDB;
}

.kpi-change {
  font-size: 12px;
  font-weight: 500;
}

.kpi-change.is-positive {
  color: #10B981;
}

.kpi-change.is-negative {
  color: #EF4444;
}

.kpi-sub {
  font-size: 12px;
  color: #9CA3AF;
}

.kpi-card.kpi-date {
  background: linear-gradient(135deg, #E0F7FA 0%, #B2EBF2 100%);
  border-color: #80DEEA;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F3F4F6;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.chart-subtitle {
  font-size: 13px;
  color: #9CA3AF;
  margin-top: 4px;
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6B7280;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.dot.households {
  background: #1EAEDB;
}

.dot.assets {
  background: #1EAEDB;
}

.dot.income {
  background: #1EAEDB;
}

.dot.line {
  background: #F59E0B;
  border-radius: 50%;
}

.chart-content {
  width: 100%;
}

/* Product Bar Chart */
.product-bars {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 8px 0;
}

.product-bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-label {
  width: 60px;
  font-size: 14px;
  font-weight: 500;
  color: #111827;
  text-align: right;
  flex-shrink: 0;
}

.product-bar-track {
  flex: 1;
  height: 28px;
  background: #F3F4F6;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.product-bar-fill {
  height: 100%;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
  transition: width 0.5s ease;
  min-width: 0;
}

.bar-value {
  font-size: 13px;
  font-weight: 600;
  color: white;
  white-space: nowrap;
}

.product-asset-text {
  width: 80px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  text-align: right;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .product-label {
    width: 50px;
    font-size: 13px;
  }

  .product-asset-text {
    width: 70px;
    font-size: 13px;
  }
}
</style>
