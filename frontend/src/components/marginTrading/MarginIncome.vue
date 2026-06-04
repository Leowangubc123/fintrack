<template>
  <div class="margin-income">
    <div class="annotation">
      统计各营业部的两融息费收入数据，按周更新，展示本周收入及年度累计收入。
    </div>

    <div class="filter-bar">
      <el-select v-model="selectedYear" style="width: 120px">
        <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
      </el-select>
      <el-select v-model="recordWeek" style="width: 200px">
        <el-option v-for="w in weekOptions" :key="w" :label="w" :value="w" />
      </el-select>
      <el-button type="primary" @click="exportToExcel">
        <el-icon><Download /></el-icon>导出Excel
      </el-button>
      <el-button type="danger" plain @click="handleDeleteWeek">
        <el-icon><Delete /></el-icon>删除本周数据
      </el-button>
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">各营业部本周息费收入</div>
        <div ref="incomePieChart" class="chart-content" style="height: 260px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">年度息费收入累计趋势</div>
        <div ref="trendChart" class="chart-content" style="height: 260px;"></div>
      </div>
    </div>

    <div class="table-container" style="margin-top: 20px;">
      <el-table :data="tableData" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="group_name" label="营业部" min-width="120" />
        <el-table-column prop="income_amount" label="本周息费收入(万)" align="right" min-width="150">
          <template #default="{ row }">
            <strong>{{ formatNumber(row.income_amount) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="年度累计(万)" align="right" min-width="140">
          <template #default="{ row }">
            {{ formatNumber(row.year_total) }}
          </template>
        </el-table-column>
        <el-table-column label="较上周" align="right" width="120">
          <template #default="{ row }">
            <span :class="getChangeClass(row.week_change)">{{ formatChange(row.week_change) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="占全公司" align="right" width="100">
          <template #default="{ row }">
            {{ row.percentage }}%
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import { marginTradingApi } from '../../api/marginTrading.js'

const incomeData = ref([])
const yearIncomeData = ref([])
const prevWeekData = ref({})
const loading = ref(false)
const selectedYear = ref(new Date().getFullYear())
const recordWeek = ref('')

const incomePieChart = ref(null)
const trendChart = ref(null)
let pieInstance = null
let trendInstance = null

const yearOptions = computed(() => {
  const current = new Date().getFullYear()
  return [current, current - 1]
})

const weekOptions = computed(() => {
  const weeks = new Set(incomeData.value.map(d => d.record_week))
  return Array.from(weeks).sort().reverse()
})

const totalIncome = computed(() => {
  return tableData.value.reduce((sum, r) => sum + (r.income_amount || 0), 0)
})

// 营业部固定排序顺序
const GROUP_ORDER = { '上一': 1, '上二': 2, '上三': 3, '上四': 4, '上五': 5, '上六': 6, '上海分公司': 7 }

const sortByGroup = (data) => {
  return data.sort((a, b) => {
    const orderA = GROUP_ORDER[a.group_name] || 99
    const orderB = GROUP_ORDER[b.group_name] || 99
    return orderA - orderB
  })
}

const tableData = computed(() => {
  let data = incomeData.value.filter(d => d.record_week === recordWeek.value)
  data = data.map(item => {
    const prev = prevWeekData.value[item.group_id]
    const week_change = prev && prev.income_amount > 0
      ? ((item.income_amount - prev.income_amount) / prev.income_amount * 100) : 0
    const year_total = yearIncomeData.value
      .filter(y => y.group_id === item.group_id)
      .reduce((sum, y) => sum + y.income_amount, 0)
    const percentage = totalIncome.value > 0 ? ((item.income_amount / totalIncome.value) * 100).toFixed(1) : 0
    return { ...item, week_change, year_total, percentage }
  })
  return sortByGroup(data)
})

const fetchData = async () => {
  loading.value = true
  try {
    const [weekRes, yearRes] = await Promise.all([
      marginTradingApi.getIncome({ year: selectedYear.value }),
      marginTradingApi.getIncome({ year: selectedYear.value })
    ])
    incomeData.value = weekRes
    yearIncomeData.value = yearRes
    if (!recordWeek.value && weekOptions.value.length > 0) {
      recordWeek.value = weekOptions.value[0]
    }
    await fetchPrevWeekData()
  } catch (error) {
    console.error('Failed to fetch income:', error)
    ElMessage.error('获取息费收入数据失败')
  } finally {
    loading.value = false
  }
}

const fetchPrevWeekData = async () => {
  if (!recordWeek.value) return
  const parts = recordWeek.value.split('-W')
  const y = parseInt(parts[0]), w = parseInt(parts[1])
  const prevWeek = w > 1 ? `${y}-W${String(w - 1).padStart(2, '0')}` : `${y - 1}-W52`
  try {
    const res = await marginTradingApi.getIncome({ record_week: prevWeek })
    prevWeekData.value = {}
    res.forEach(item => { prevWeekData.value[item.group_id] = item })
  } catch (error) {
    console.error('Failed to fetch prev week income:', error)
  }
}

const initCharts = () => {
  if (incomePieChart.value) pieInstance = echarts.init(incomePieChart.value)
  if (trendChart.value) trendInstance = echarts.init(trendChart.value)
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  pieInstance?.resize()
  trendInstance?.resize()
}

const updateCharts = () => {
  if (!pieInstance || !trendInstance) return
  const data = tableData.value
  if (data.length === 0) return

  // Pie chart
  const colors = ['#D97706', '#F59E0B', '#FBBF24', '#FDE68A', '#FEF3C7']
  pieInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}万 ({d}%)' },
    color: colors,
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
      data: data.map((item, idx) => ({
        name: item.group_name, value: item.income_amount || 0,
        itemStyle: { color: colors[idx % colors.length] }
      }))
    }]
  }, true)

  // Trend chart - weekly cumulative
  const weeklyData = {}
  yearIncomeData.value.forEach(item => {
    if (!weeklyData[item.record_week]) weeklyData[item.record_week] = 0
    weeklyData[item.record_week] += item.income_amount
  })
  const sortedWeeks = Object.keys(weeklyData).sort()
  let cumulative = 0
  const cumulativeData = sortedWeeks.map(w => {
    cumulative += weeklyData[w]
    return cumulative
  })

  trendInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: sortedWeeks.map(w => w.split('-W')[1] + '周'),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    yAxis: {
      type: 'value', name: '累计(万)',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#374151', fontSize: 10 }
    },
    series: [
      {
        name: '周收入', type: 'bar',
        data: sortedWeeks.map(w => weeklyData[w]),
        itemStyle: { color: '#F59E0B', borderRadius: [4, 4, 0, 0] },
        barWidth: '40%'
      },
      {
        name: '累计收入', type: 'line',
        data: cumulativeData,
        smooth: true, symbol: 'circle', symbolSize: 6,
        lineStyle: { color: '#EA580C', width: 3 },
        itemStyle: { color: '#EA580C', borderWidth: 2, borderColor: '#fff' }
      }
    ]
  }, true)
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return parseFloat(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getChangeClass = (val) => {
  if (val > 0) return 'change-up'
  if (val < 0) return 'change-down'
  return 'change-flat'
}

const formatChange = (val) => {
  if (val > 0) return `+${val.toFixed(1)}% ↑`
  if (val < 0) return `${val.toFixed(1)}% ↓`
  return '0.0% -'
}

const exportToExcel = () => {
  const exportData = tableData.value.map(row => ({
    '营业部': row.group_name,
    '本周息费收入(万)': row.income_amount,
    '年度累计(万)': row.year_total,
    '较上周': row.week_change ? row.week_change.toFixed(2) + '%' : '0%',
    '占全公司': row.percentage + '%'
  }))
  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '息费收入')
  XLSX.writeFile(wb, `两融息费收入_${recordWeek.value}.xlsx`)
  ElMessage.success('导出成功')
}

const handleDeleteWeek = async () => {
  if (!recordWeek.value) {
    ElMessage.warning('请先选择要删除的周')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除 ${recordWeek.value} 的息费收入数据吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await marginTradingApi.deleteIncome(recordWeek.value)
    ElMessage.success(`已删除 ${recordWeek.value} 的数据`)
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

watch([selectedYear, recordWeek], () => {
  fetchPrevWeekData().then(() => {
    nextTick(() => updateCharts())
  })
})

const onDataImported = () => {
  fetchData().then(() => {
    nextTick(() => updateCharts())
  })
}

onMounted(() => {
  fetchData().then(() => {
    nextTick(() => {
      initCharts()
      updateCharts()
    })
  })
  window.addEventListener('margin-data-imported', onDataImported)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('margin-data-imported', onDataImported)
  pieInstance?.dispose()
  trendInstance?.dispose()
})
</script>

<style scoped>
.margin-income { padding: 0; }
.annotation {
  background: #FFF7ED; border-left: 3px solid #EA580C;
  padding: 12px 16px; border-radius: 0 8px 8px 0;
  margin-bottom: 20px; font-size: 13px; color: #9A3412;
}
.filter-bar {
  display: flex; gap: 12px; margin-bottom: 20px; align-items: center;
}
.charts-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
}
.chart-card {
  background: white; border-radius: 12px; padding: 20px;
  border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.chart-title {
  font-size: 15px; font-weight: 600; color: #111827; margin-bottom: 16px;
}
.chart-content { width: 100%; }
.table-container {
  background: white; border-radius: 12px; border: 1px solid #E5E7EB; overflow: hidden;
}
:deep(.el-button--primary) { background: #EA580C; border-color: #EA580C; }
.change-up { color: #EF4444; font-weight: 500; }
.change-down { color: #10B981; font-weight: 500; }
.change-flat { color: #9CA3AF; font-weight: 500; }
@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
}
</style>