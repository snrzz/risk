<template>
  <div class="metrics-page">
    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="分类">
          <el-select v-model="selectedCategory" placeholder="全部" clearable @change="loadMetrics">
            <el-option 
              v-for="cat in categories" 
              :key="cat.name" 
              :label="`${cat.name} (${cat.count})`" 
              :value="cat.name" 
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadMetrics">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 指标列表 -->
    <el-card>
      <el-table :data="metricsList" stripe style="width: 100%">
        <el-table-column prop="code" label="指标编码" width="180" />
        <el-table-column prop="name" label="指标名称" width="200" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getCategoryText(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="100" />
        <el-table-column prop="field_type" label="数据类型" width="100" />
        <el-table-column prop="aggregation_type" label="聚合方式" width="100" />
        <el-table-column prop="description" label="说明" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewData(row)">查看数据</el-button>
            <el-button type="primary" link @click="handleViewChart(row)">趋势图</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadMetrics"
        />
      </div>
    </el-card>
    
    <!-- 数据查看对话框 -->
    <el-dialog v-model="dataDialogVisible" title="指标数据" width="90%">
      <div class="metric-header">
        <span class="metric-name">{{ currentMetric?.name }}</span>
        <span class="metric-code">{{ currentMetric?.code }}</span>
      </div>
      
      <el-date-picker
        v-model="dateRange"
        type="datetimerange"
        range-separator="至"
        start-placeholder="开始时间"
        end-placeholder="结束时间"
        @change="loadMetricData"
      />
      
      <div ref="dataChartRef" class="data-chart"></div>
      
      <el-table :data="metricDataList" max-height="400" style="margin-top: 20px;">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="value" label="值">
          <template #default="{ row }">
            {{ row.value?.toFixed(6) }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { metricsApi } from '@/api'

const metricsList = ref([])
const categories = ref([])
const selectedCategory = ref('')
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const dataDialogVisible = ref(false)
const currentMetric = ref(null)
const dateRange = ref([])
const metricDataList = ref([])
const dataChartRef = ref(null)
let dataChart = null

const loadCategories = async () => {
  try {
    const res = await metricsApi.getCategories()
    categories.value = res.categories || []
  } catch (e) {
    console.error('加载分类失败:', e)
  }
}

const loadMetrics = async () => {
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      category: selectedCategory.value || undefined
    }
    const res = await metricsApi.getList(params)
    metricsList.value = res.items
    pagination.total = res.total
  } catch (e) {
    console.error('加载指标失败:', e)
  }
}

const handleViewData = (metric) => {
  currentMetric.value = metric
  dataDialogVisible.value = true
  
  // 默认查看最近24小时数据
  const end = new Date()
  const start = new Date(end - 24 * 60 * 60 * 1000)
  dateRange.value = [start, end]
  
  setTimeout(() => {
    loadMetricData()
  }, 100)
}

const handleViewChart = (metric) => {
  handleViewData(metric)
}

const loadMetricData = async () => {
  if (!currentMetric.value || !dateRange.value) return
  
  try {
    const [start, end] = dateRange.value
    const res = await metricsApi.getData(currentMetric.value.code, {
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      limit: 1000
    })
    
    metricDataList.value = res.data || []
    
    if (dataChart && metricDataList.value.length > 0) {
      const times = metricDataList.value.map(d => formatTime(d.timestamp))
      const values = metricDataList.value.map(d => d.value)
      
      dataChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: times },
        yAxis: { type: 'value' },
        series: [{
          data: values,
          type: 'line',
          smooth: true
        }]
      })
    }
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

const initChart = () => {
  if (dataChartRef.value) {
    dataChart = echarts.init(dataChartRef.value)
  }
}

const getCategoryText = (category) => {
  const texts = {
    trading: '交易',
    valuation: '估值',
    risk: '风控',
    non_standard: '非标',
    related_party: '关联交易',
    ta: 'TA',
    cop: 'COP'
  }
  return texts[category] || category || '未分类'
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadCategories()
  loadMetrics()
  setTimeout(initChart, 100)
})

onUnmounted(() => {
  dataChart?.dispose()
})
</script>

<style lang="scss" scoped>
.metrics-page {
  .filter-card {
    margin-bottom: 20px;
  }
  
  .pagination-wrap {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}

.metric-header {
  margin-bottom: 16px;
  
  .metric-name {
    font-size: 18px;
    font-weight: bold;
    margin-right: 12px;
  }
  
  .metric-code {
    color: #999;
  }
}

.data-chart {
  height: 300px;
  margin-top: 16px;
}
</style>
