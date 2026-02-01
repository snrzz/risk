<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #409eff;">
            <el-icon :size="28"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_metrics || 0 }}</div>
            <div class="stat-label">监控指标</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #67c23a;">
            <el-icon :size="28"><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.active_rules || 0 }}</div>
            <div class="stat-label">活跃规则</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #e6a23c;">
            <el-icon :size="28"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.alerts_today || 0 }}</div>
            <div class="stat-label">今日告警</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f56c6c;">
            <el-icon :size="28"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.critical_alerts || 0 }}</div>
            <div class="stat-label">严重告警</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>告警趋势</span>
              <el-radio-group v-model="trendDays" size="small" @change="loadAlertTrend">
                <el-radio-button label="7">7天</el-radio-button>
                <el-radio-button label="30">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>指标分布</span>
          </template>
          <div ref="pieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 实时告警 -->
    <el-card class="alerts-card">
      <template #header>
        <div class="card-header">
          <span>实时告警</span>
          <el-button type="primary" link @click="$router.push('/alerts')">查看全部</el-button>
        </div>
      </template>
      
      <el-table :data="recentAlerts" stripe style="width: 100%">
        <el-table-column prop="severity" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="metric_code" label="指标" width="180" />
        <el-table-column prop="alert_value" label="触发值" width="120">
          <template #default="{ row }">
            {{ row.alert_value?.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警信息" />
        <el-table-column prop="alert_time" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.alert_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { TrendCharts, Warning, CircleClose, Bell } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'
import { ElMessage } from 'element-plus'

const summary = ref({})
const recentAlerts = ref([])
const trendDays = ref(7)
const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null

const loadSummary = async () => {
  try {
    const res = await dashboardApi.getSummary()
    summary.value = res
  } catch (e) {
    console.error('加载摘要失败:', e)
  }
}

const loadRecentAlerts = async () => {
  try {
    const res = await dashboardApi.getRecentAlerts(10)
    recentAlerts.value = res
  } catch (e) {
    console.error('加载告警失败:', e)
  }
}

const loadAlertTrend = async () => {
  try {
    const res = await dashboardApi.getAlertTrend(trendDays.value)
    if (trendChart) {
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: res.categories },
        yAxis: { type: 'value' },
        series: res.series
      })
    }
  } catch (e) {
    console.error('加载趋势失败:', e)
  }
}

const loadMetricStatus = async () => {
  try {
    const res = await dashboardApi.getMetricStatus()
    if (pieChart) {
      pieChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', left: 'left' },
        series: [{
          type: 'pie',
          radius: '50%',
          data: res.series[0].data.map((value, index) => ({
            name: res.categories[index],
            value: value
          }))
        }]
      })
    }
  } catch (e) {
    console.error('加载指标分布失败:', e)
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

const initCharts = () => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
  }
}

const handleResize = () => {
  trendChart?.resize()
  pieChart?.resize()
}

onMounted(() => {
  loadSummary()
  loadRecentAlerts()
  loadAlertTrend()
  loadMetricStatus()
  setTimeout(initCharts, 100)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  .stat-cards {
    margin-bottom: 20px;
  }
  
  .stat-card {
    :deep(.el-card__body) {
      display: flex;
      align-items: center;
      padding: 20px;
    }
    
    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      margin-right: 16px;
    }
    
    .stat-info {
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #333;
      }
      
      .stat-label {
        font-size: 14px;
        color: #999;
        margin-top: 4px;
      }
    }
  }
  
  .chart-row {
    margin-bottom: 20px;
  }
  
  .chart-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .chart-container {
      height: 300px;
    }
  }
  
  .alerts-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style>
