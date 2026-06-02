<template>
  <div class="margin-personal">
    <div class="annotation">
      个人余额数据按周更新，同一表格中并列展示每位营销人员名下开发关系客户和服务关系客户的两融余额及周环比变化。
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <el-select v-model="recordWeek" style="width: 200px">
        <el-option v-for="w in weekOptions" :key="w" :label="w" :value="w" />
      </el-select>
      <el-select v-model="filterGroup" placeholder="全部营业部" clearable style="width: 160px">
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
      </el-select>
      <el-input v-model="searchMember" placeholder="搜索员工姓名" style="width: 160px" clearable />
      <el-button type="primary" @click="exportToExcel">
        <el-icon><Download /></el-icon>导出Excel
      </el-button>
      <el-button type="danger" plain @click="handleDeleteWeek">
        <el-icon><Delete /></el-icon>删除本周数据
      </el-button>
    </div>

    <!-- 余额类型切换 -->
    <div class="balance-type-switch">
      <el-radio-group v-model="balanceType">
        <el-radio-button label="spot">时点余额</el-radio-button>
        <el-radio-button label="daily">日均余额</el-radio-button>
      </el-radio-group>
    </div>

    <!-- Table -->
    <div class="table-container">
      <el-table :data="filteredData" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="member_name" label="员工" width="100" />
        <el-table-column prop="group_name" label="营业部" width="120" />
        <el-table-column :label="balanceTypeLabel + '-开发关系(万)'" align="right" min-width="160">
          <template #default="{ row }">
            <strong>{{ formatNumber(row.development_balance) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="开发关系-环比" align="right" width="120">
          <template #default="{ row }">
            <span :class="getChangeClass(row.dev_change)">{{ formatChange(row.dev_change) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="balanceTypeLabel + '-服务关系(万)'" align="right" min-width="160">
          <template #default="{ row }">
            <strong>{{ formatNumber(row.service_balance) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="服务关系-环比" align="right" width="120">
          <template #default="{ row }">
            <span :class="getChangeClass(row.svc_change)">{{ formatChange(row.svc_change) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Delete } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { marginTradingApi } from '../../api/marginTrading.js'
import { groupsApi } from '../../api/index.js'

const groups = ref([])
const balanceData = ref([])
const prevWeekData = ref({})
const loading = ref(false)

const recordWeek = ref('')
const filterGroup = ref(null)
const searchMember = ref('')
const balanceType = ref('spot')

const balanceTypeLabel = computed(() => balanceType.value === 'spot' ? '时点余额' : '日均余额')

const weekOptions = computed(() => {
  const weeks = new Set(balanceData.value.map(d => d.record_week))
  return Array.from(weeks).sort().reverse()
})

const fetchGroups = async () => {
  try {
    const res = await groupsApi.list()
    groups.value = res
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await marginTradingApi.getMemberBalances({
      balance_type: balanceType.value
    })
    balanceData.value = res
    if (!recordWeek.value && weekOptions.value.length > 0) {
      recordWeek.value = weekOptions.value[0]
    }
    // Fetch previous week data for comparison
    await fetchPrevWeekData()
  } catch (error) {
    console.error('Failed to fetch member balances:', error)
    ElMessage.error('获取个人余额数据失败')
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
    const res = await marginTradingApi.getMemberBalances({
      balance_type: balanceType.value,
      record_week: prevWeek
    })
    prevWeekData.value = {}
    res.forEach(item => {
      prevWeekData.value[item.member_id] = item
    })
  } catch (error) {
    console.error('Failed to fetch prev week data:', error)
  }
}

const tableData = computed(() => {
  let data = balanceData.value.filter(d => d.record_week === recordWeek.value)
  data = data.map(item => {
    const prev = prevWeekData.value[item.member_id]
    const dev_change = prev && prev.development_balance > 0
      ? ((item.development_balance - prev.development_balance) / prev.development_balance * 100)
      : 0
    const svc_change = prev && prev.service_balance > 0
      ? ((item.service_balance - prev.service_balance) / prev.service_balance * 100)
      : 0
    return { ...item, dev_change, svc_change }
  })
  return data
})

const filteredData = computed(() => {
  let data = tableData.value
  if (filterGroup.value) {
    data = data.filter(d => d.group_id === filterGroup.value)
  }
  if (searchMember.value) {
    data = data.filter(d => d.member_name.includes(searchMember.value))
  }
  return data
})

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
  const exportData = filteredData.value.map(row => ({
    '员工': row.member_name,
    '营业部': row.group_name,
    [`开发关系-${balanceTypeLabel.value}(万)`]: row.development_balance,
    '开发关系-环比': row.dev_change ? row.dev_change.toFixed(2) + '%' : '0%',
    [`服务关系-${balanceTypeLabel.value}(万)`]: row.service_balance,
    '服务关系-环比': row.svc_change ? row.svc_change.toFixed(2) + '%' : '0%'
  }))
  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '个人余额')
  XLSX.writeFile(wb, `两融个人余额_${balanceTypeLabel.value}_${recordWeek.value}.xlsx`)
  ElMessage.success('导出成功')
}

const handleDeleteWeek = async () => {
  if (!recordWeek.value) {
    ElMessage.warning('请先选择要删除的周')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除 ${recordWeek.value} 的个人余额数据吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await marginTradingApi.deleteMemberBalances(recordWeek.value)
    ElMessage.success(`已删除 ${recordWeek.value} 的数据`)
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

watch([balanceType, recordWeek], () => {
  fetchData()
})

const onDataImported = () => {
  fetchData()
}

onMounted(() => {
  fetchGroups()
  fetchData()
  window.addEventListener('margin-data-imported', onDataImported)
})

onUnmounted(() => {
  window.removeEventListener('margin-data-imported', onDataImported)
})
</script>

<style scoped>
.margin-personal {
  padding: 0;
}

.annotation {
  background: #FFF7ED;
  border-left: 3px solid #EA580C;
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
  margin-bottom: 20px;
  font-size: 13px;
  color: #9A3412;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.balance-type-switch {
  margin-bottom: 16px;
}

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  overflow: hidden;
}

:deep(.el-button--primary) {
  background: #EA580C;
  border-color: #EA580C;
}

.change-up { color: #EF4444; font-weight: 500; }
.change-down { color: #10B981; font-weight: 500; }
.change-flat { color: #9CA3AF; font-weight: 500; }
</style>
