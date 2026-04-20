<template>
  <div class="advisory-dashboard" :class="scope === 'stock' ? 'stock-theme' : 'new-theme'">
    <!-- KPI Cards -->
    <div class="kpi-grid" :class="{ 'two-col': scope === 'stock' }">
      <div class="kpi-card">
        <div class="kpi-label">
          {{ scope === 'new' ? '本年签约户数' : '存量签约户数' }}
          <span class="kpi-date-sub">（最近更新：{{ stats.last_product_update_date || '-' }}）</span>
        </div>
        <div class="kpi-value" :style="{ color: themeColor }">{{ formatNumber(stats.total_households) }}<span class="unit">户</span></div>
        <div v-if="scope === 'new'" class="kpi-change" :class="{ 'is-positive': stats.households_change >= 0, 'is-negative': stats.households_change < 0 }">
          较上次更新 {{ stats.households_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.households_change || 0) }}户
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">
          {{ scope === 'new' ? '本年签约资产' : '存量签约资产' }}
          <span class="kpi-date-sub">（最近更新：{{ stats.last_product_update_date || '-' }}）</span>
        </div>
        <div class="kpi-value" :style="{ color: themeColor }">{{ formatNumber(stats.total_assets) }}<span class="unit">万</span></div>
        <div v-if="scope === 'new'" class="kpi-change" :class="{ 'is-positive': stats.assets_change >= 0, 'is-negative': stats.assets_change < 0 }">
          较上次更新 {{ stats.assets_change >= 0 ? '新增' : '减少' }} {{ Math.abs(stats.assets_change || 0) }}万
        </div>
      </div>
      <div v-if="scope === 'new'" class="kpi-card">
        <div class="kpi-label">
          本年投顾收入
          <span class="kpi-date-sub">（最近更新：{{ stats.last_income_update_date || '-' }}）</span>
        </div>
        <div class="kpi-value" style="color: #1EAEDB">{{ formatNumber((stats.total_income / 10000).toFixed(2)) }}<span class="unit">万</span></div>
        <div class="kpi-change" :class="{ 'is-positive': stats.income_change >= 0, 'is-negative': stats.income_change < 0 }">
          较上次更新 {{ stats.income_change >= 0 ? '新增' : '减少' }} {{ Math.abs((stats.income_change / 10000) || 0).toFixed(2) }}万
        </div>
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
              />
              <span
                class="bar-value"
                :class="{ 'inside-left': isBarWide(product) }"
              >{{ dataMap[product]?.households || 0 }}户</span>
            </div>
            <div class="product-asset-text">{{ formatAsset(dataMap[product]?.assets || 0) }}万</div>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">{{ scope === 'new' ? '月度趋势分析' : '年度趋势分析' }}</div>
          <div class="chart-legend">
            <span v-if="scope === 'new'" class="legend-item"><span class="dot income"></span>投顾收入(元)</span>
            <span v-if="scope === 'new'" class="legend-item"><span class="dot line"></span>签约户数</span>
            <span v-else class="legend-item"><span class="dot" :style="{ background: themeColor }"></span>签约户数</span>
          </div>
        </div>
        <div ref="trendChart" class="chart-content" style="height: 320px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { advisoryApi } from '../../api/advisory.js'

const props = defineProps({
  scope: {
    type: String,
    default: 'new',
    validator: (v) => ['new', 'stock'].includes(v)
  }
})

const themeColor = computed(() => props.scope === 'stock' ? '#10B981' : '#1EAEDB')

const stats = ref({
  total_households: 0,
  total_assets: 0,
  total_income: 0,
  households_change: 0,
  assets_change: 0,
  income_change: 0,
  last_update_date: null,
  last_product_update_date: null,
  last_income_update_date: null,
  product_distribution: [],
  trend_data: []
})

const trendChart = ref(null)
let trendChartInstance = null

const productOrder = ['万2及其他', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT']

const productColors = {
  '万2及其他': props.scope === 'stock' ? '#10B981' : '#0EA5E9',
  '千1': props.scope === 'stock' ? '#34D399' : '#10B981',
  '千3': '#F59E0B',
  'ETF投顾': props.scope === 'stock' ? '#059669' : '#3B82F6',
  '量化T策略': props.scope === 'stock' ? '#6EE7B7' : '#8B5CF6',
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
  return (val / maxHouseholds.value) * 100 + '%'
}

const isBarWide = (product) => {
  const val = dataMap.value[product]?.households || 0
  if (maxHouseholds.value === 0) return false
  return (val / maxHouseholds.value) > 0.5
}

const getProductColor = (product) => productColors[product] || themeColor.value

const formatAsset = (num) => {
  if (num === null || num === undefined) return '0'
  if (num >= 10000) return (num / 10000).toFixed(0) + '亿'
  return Math.round(num).toLocaleString('zh-CN')
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN')
}

const fetchStats = async () => {
  try {
    const res = await advisoryApi.getStats({
      year: new Date().getFullYear(),
      scope: props.scope
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
  const isNew = props.scope === 'new'

  let option

  if (isNew) {
    // 本年新增：月度柱状+折线
    const months = trendData.map(t => t.month + '月')
    const incomeData = trendData.map(t => t.income || 0)
    const householdsData = trendData.map(t => t.households || 0)

    option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
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
  } else {
    // 存量统计：近5年年度柱状
    const years = trendData.map(t => t.year + '年')
    const householdsData = trendData.map(t => t.households || 0)
    const assetsData = trendData.map(t => t.assets || 0)

    option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: {
        data: ['签约户数', '签约资产(万)'],
        top: '5%'
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
      xAxis: {
        type: 'category',
        data: years,
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisLabel: { color: '#374151' }
      },
      yAxis: [
        {
          type: 'value',
          name: '签约户数',
          position: 'left',
          axisLine: { show: false },
          splitLine: { lineStyle: { color: '#F3F4F6' } },
          axisLabel: { color: '#374151' }
        },
        {
          type: 'value',
          name: '签约资产(万)',
          position: 'right',
          axisLine: { show: false },
          splitLine: { show: false },
          axisLabel: { color: '#374151' }
        }
      ],
      series: [
        {
          name: '签约户数',
          type: 'bar',
          data: householdsData,
          itemStyle: { color: '#10B981', borderRadius: [4, 4, 0, 0] },
          barWidth: '35%'
        },
        {
          name: '签约资产(万)',
          type: 'bar',
          yAxisIndex: 1,
          data: assetsData,
          itemStyle: { color: '#34D399', borderRadius: [4, 4, 0, 0] },
          barWidth: '35%'
        }
      ]
    }
  }

  trendChartInstance.setOption(option, true)
}

watch(() => props.scope, () => {
  fetchStats()
})

onMounted(() => {
  fetchStats()
  initCharts()
  window.addEventListener('advisory-data-imported', fetchStats)
})

onBeforeUnmount(() => {
  window.removeEventListener('advisory-data-imported', fetchStats)
  window.removeEventListener('resize', handleResize)
  trendChartInstance?.dispose()
})
</script>

<style scoped>
.advisory-dashboard {
  padding: 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-grid.two-col {
  grid-template-columns: repeat(2, 1fr);
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

.kpi-date-sub {
  font-size: 12px;
  color: #9CA3AF;
  font-weight: 400;
  margin-left: 4px;
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
  position: relative;
  overflow: hidden;
}

.product-bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
}

.bar-value {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  left: calc(v-bind('getBarWidth(product)') + 8px);
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.bar-value.inside-left {
  left: 8px;
  color: white;
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
