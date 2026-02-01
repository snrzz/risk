<template>
  <div class="alerts-page">
    <!-- 统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4">
        <el-card shadow="never" class="stat-item">
          <div class="stat-num">{{ stats.total || 0 }}</div>
          <div class="stat-label">全部告警</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="never" class="stat-item danger">
          <div class="stat-num">{{ stats.active || 0 }}</div>
          <div class="stat-label">活跃中</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="never" class="stat-item warning">
          <div class="stat-num">{{ stats.acknowledged || 0 }}</div>
          <div class="stat-label">已确认</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="never" class="stat-item success">
          <div class="stat-num">{{ stats.resolved || 0 }}</div>
          <div class="stat-label">已解决</div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 筛选和操作 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable>
            <el-option label="活跃" value="active" />
            <el-option label="已确认" value="acknowledged" />
            <el-option label="已解决" value="resolved" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="filterForm.severity" placeholder="全部" clearable>
            <el-option label="P1-紧急" value="P1" />
            <el-option label="P2-严重" value="P2" />
            <el-option label="P3-警告" value="P3" />
            <el-option label="P4-提示" value="P4" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      
      <div class="batch-actions">
        <el-button type="primary" plain @click="handleBatchAck">批量确认</el-button>
        <el-button type="success" plain @click="handleBatchResolve">批量解决</el-button>
      </div>
    </el-card>
    
    <!-- 告警列表 -->
    <el-card>
      <el-table 
        ref="tableRef"
        :data="alertList" 
        stripe 
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="severity" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" effect="dark">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="metric_code" label="指标编码" width="180" />
        <el-table-column prop="alert_value" label="触发值" width="120">
          <template #default="{ row }">
            {{ row.alert_value?.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column prop="threshold_value" label="阈值" width="120">
          <template #default="{ row }">
            {{ row.threshold_value?.toFixed(4) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警信息" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alert_time" label="告警时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.alert_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'active'"
              type="primary" 
              link 
              size="small" 
              @click="handleAck([row.id])"
            >确认</el-button>
            <el-button 
              v-if="row.status !== 'resolved'"
              type="success" 
              link 
              size="small" 
              @click="handleResolve([row.id])"
            >解决</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadAlerts"
          @current-change="loadAlerts"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { alertsApi } from '@/api'

const tableRef = ref()
const alertList = ref([])
const selectedRows = ref([])
const stats = ref({})

const filterForm = reactive({
  status: '',
  severity: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const loadStats = async () => {
  try {
    const res = await alertsApi.getStats(7)
    stats.value = res
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

const loadAlerts = async () => {
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filterForm
    }
    const res = await alertsApi.getList(params)
    alertList.value = res.items
    pagination.total = res.total
  } catch (e) {
    console.error('加载告警失败:', e)
  }
}

const handleFilter = () => {
  pagination.page = 1
  loadAlerts()
}

const handleReset = () => {
  filterForm.status = ''
  filterForm.severity = ''
  handleFilter()
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const handleBatchAck = () => {
  const ids = selectedRows.value.map(r => r.id)
  if (ids.length === 0) {
    ElMessage.warning('请选择要确认的告警')
    return
  }
  handleAck(ids)
}

const handleBatchResolve = () => {
  const ids = selectedRows.value.map(r => r.id)
  if (ids.length === 0) {
    ElMessage.warning('请选择要解决的告警')
    return
  }
  handleResolve(ids)
}

const handleAck = async (ids) => {
  try {
    await ElMessageBox.confirm('确认选中的告警?', '提示')
    await alertsApi.acknowledge({
      record_ids: ids,
      acknowledged_by: 'admin',
      message: '已确认'
    })
    ElMessage.success('确认成功')
    loadAlerts()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('确认失败')
    }
  }
}

const handleResolve = async (ids) => {
  try {
    await ElMessageBox.confirm('解决选中的告警?', '提示')
    await alertsApi.resolve({
      record_ids: ids,
      resolved_by: 'admin',
      message: '已解决'
    })
    ElMessage.success('解决成功')
    loadAlerts()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('解决失败')
    }
  }
}

const getSeverityType = (severity) => {
  const types = { P1: 'danger', P2: 'warning', P3: 'info', P4: '' }
  return types[severity] || ''
}

const getStatusType = (status) => {
  const types = { active: 'danger', acknowledged: 'warning', resolved: 'success' }
  return types[status] || ''
}

const getStatusText = (status) => {
  const texts = { active: '活跃', acknowledged: '已确认', resolved: '已解决' }
  return texts[status] || status
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadStats()
  loadAlerts()
})
</script>

<style lang="scss" scoped>
.alerts-page {
  .stats-row {
    margin-bottom: 20px;
    
    .stat-item {
      text-align: center;
      
      .stat-num {
        font-size: 32px;
        font-weight: bold;
        color: #333;
      }
      
      .stat-label {
        color: #999;
        margin-top: 8px;
      }
      
      &.danger .stat-num { color: #f56c6c; }
      &.warning .stat-num { color: #e6a23c; }
      &.success .stat-num { color: #67c23a; }
    }
  }
  
  .filter-card {
    margin-bottom: 20px;
    
    .batch-actions {
      margin-top: 16px;
      border-top: 1px solid #eee;
      padding-top: 16px;
    }
  }
  
  .pagination-wrap {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
