<template>
  <div class="margin-group">
    <div class="annotation">
      营业部层面汇总展示各营业部的时点余额、日均余额及周环比变化。
    </div>

    <div class="filter-bar">
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
        <div class="chart-title">营业部时点余额分布</div>
        <div ref="spotPieChart" class="chart-content" style="height: 260px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">营业部日均余额环比变化</div>
        <div ref="changeBarChart" class="chart-content" style="height: 260px;"></div>
      </div>
    </div>

    <div class="table-container" style="margin-top: 20px;">
      <el-table :data="tableData" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="group_name" label="营业部" min-width="120" />
        <el-table-column prop="spot_balance" label="时点余额(万)" align="right" min-width="140">
          <template #default="{ row }">
            <strong>{{ formatNumber(row.spot_balance) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="时点环比" align="right" width="120">
          <template #default="{ row }">
            <span :class="getChangeClass(row.spot_change)">{{ formatChange(row.spot_change) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="daily_balance" label="日均余额(万)" align="right" min-width="140">
          <template #default="{ row }">
            <strong>{{ formatNumber(row.daily_balance) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="日均环比" align="right" width="120">
          <template #default="{ row }">
            <span :class="getChangeClass(row.daily_change)">{{ formatChange(row.daily_change) }}</span>
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

const balanceData = ref([])
const prevWeekData = ref({})
const loading = ref(false)
const recordWeek = ref('')

const spotPieChart = ref(null)
const changeBarChart = ref(null)
let spotPieInstance = null
let changeBarInstance = null

const weekOptions = computed(() => {
  const weeks = new Set(balanceData.value.map(d => d.record_week))
  return Array.from(weeks).sort().reverse()
})

const totalSpot = computed(() => tableData.value.reduce((sum, r) => sum + (r.spot_balance || 0), 0))

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
  let data = balanceData.value.filter(d => d.record_week === recordWeek.value)
  data = data.map(item => {
    const prev = prevWeekData.value[item.group_id]
    const spot_change = prev && prev.spot_balance > 0
      ? ((item.spot_balance - prev.spot_balance) / prev.spot_balance * 100) : 0
    const daily_change = prev && prev.daily_balance > 0
      ? ((item.daily_balance - prev.daily_balance) / prev.daily_balance * 100) : 0
    const percentage = totalSpot.value > 0 ? ((item.spot_balance / totalSpot.value) * 100).toFixed(1) : 0
    return { ...item, spot_change, daily_change, percentage }
  })
  return sortByGroup(data)
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await marginTradingApi.getGroupBalances()
    balanceData.value = res
    if (!recordWeek.value && weekOptions.value.length > 0) {
      recordWeek.value = weekOptions.value[0]
    }
    await fetchPrevWeekData()
  } catch (error) {
    console.error('Failed to fetch group balances:', error)
    ElMessage.error('获取营业部余额数据失败')
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
    const res = await marginTradingApi.getGroupBalances({ record_week: prevWeek })
    prevWeekData.value = {}
    res.forEach(item => { prevWeekData.value[item.group_id] = item })
  } catch (error) {
    console.error('Failed to fetch prev week data:', error)
  }
}

const initCharts = () => {
  if (spotPieChart.value) spotPieInstance = echarts.init(spotPieChart.value)
  if (changeBarChart.value) changeBarInstance = echarts.init(changeBarChart.value)
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  spotPieInstance?.resize()
  changeBarInstance?.resize()
}

const updateCharts = () => {
  if (!spotPieInstance || !changeBarInstance) return
  const data = tableData.value
  if (data.length === 0) return

  // Pie chart
  const colors = ['#EA580C', '#FB923C', '#FDBA74', '#FED7AA', '#FFEDD5', '#FFF7ED']
  spotPieInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}万 ({d}%)' },
    color: colors,
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
      data: data.map((item, idx) => ({
        name: item.group_name, value: item.spot_balance || 0,
        itemStyle: { color: colors[idx % colors.length] }
      }))
    }]
  }, true)

  // Bar chart for daily balance changes
  const hasChangeData = data.some(d => d.daily_change !== 0)
  changeBarInstance.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.group_name),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#374151', fontSize: 11 }
    },
    yAxis: {
      type: 'value', name: '环比%',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#374151', fontSize: 11, formatter: '{value}%' }
    },
    series: [{
      type: 'bar',
      data: data.map(d => ({
        value: parseFloat(d.daily_change || 0).toFixed(2),
        itemStyle: { color: (d.daily_change || 0) >= 0 ? '#EF4444' : '#10B981', borderRadius: [4, 4, 0, 0] }
      })),
      barWidth: '40%'
    }],
    graphic: hasChangeData ? [] : [{
      type: 'text',
      left: 'center',
      top: 'middle',
      style: {
        text: '暂无环比数据（上周无数据）',
        fill: '#9CA3AF',
        fontSize: 14
      }
    }]
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
    '时点余额(万)': row.spot_balance,
    '时点环比': row.spot_change ? row.spot_change.toFixed(2) + '%' : '0%',
    '日均余额(万)': row.daily_balance,
    '日均环比': row.daily_change ? row.daily_change.toFixed(2) + '%' : '0%',
    '占全公司': row.percentage + '%'
  }))
  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '营业部余额')
  XLSX.writeFile(wb, `两融营业部余额_${recordWeek.value}.xlsx`)
  ElMessage.success('导出成功')
}

const handleDeleteWeek = async () => {
  if (!recordWeek.value) {
    ElMessage.warning('请先选择要删除的周')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除 ${recordWeek.value} 的营业部余额数据吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await marginTradingApi.deleteGroupBalances(recordWeek.value)
    ElMessage.success(`已删除 ${recordWeek.value} 的数据`)
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

watch([recordWeek], () => {
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
  spotPieInstance?.dispose()
  changeBarInstance?.dispose()
})
</script>

<style scoped>
.margin-group { padding: 0; }
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