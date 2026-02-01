<template>
  <div class="admin-page">
    <el-row :gutter="20">
      <!-- 系统信息 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">{{ systemInfo.name }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ systemInfo.version }}</el-descriptions-item>
            <el-descriptions-item label="描述">{{ systemInfo.description }}</el-descriptions-item>
            <el-descriptions-item label="功能特性">
              <el-tag v-for="feature in systemInfo.features" :key="feature" size="small" style="margin-right: 8px;">
                {{ feature }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <!-- 统计信息 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>运行统计</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="数据源">
              <span class="stat-num">{{ stats.datasources?.total || 0 }}</span>
              <span class="stat-sub"> (活跃: {{ stats.datasources?.active || 0 }})</span>
            </el-descriptions-item>
            <el-descriptions-item label="监控指标">{{ stats.metrics?.total || 0 }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ stats.timestamp }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 系统配置 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>系统配置</span>
      </template>
      
      <el-form :inline="true" :model="configForm">
        <el-form-item label="检查间隔">
          <el-input-number v-model="configForm.check_interval" :min="30" :step="30" />
          <span class="form-tip">秒</span>
        </el-form-item>
        <el-form-item label="数据保留天数">
          <el-input-number v-model="configForm.data_retention" :min="30" :step="30" />
          <span class="form-tip">天</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSaveConfig">保存配置</el-button>
          <el-button @click="loadConfig">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 系统日志 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>最近日志</span>
          <el-button type="primary" link @click="loadLogs">刷新</el-button>
        </div>
      </template>
      
      <div class="log-container">
        <div v-for="log in logs" :key="log.time" class="log-item" :class="log.level.toLowerCase()">
          <span class="log-time">{{ formatTime(log.time) }}</span>
          <span class="log-level">[{{ log.level }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api'

const systemInfo = ref({})
const stats = ref({})
const logs = ref([])
const configForm = reactive({
  check_interval: 60,
  data_retention: 90
})

const loadSystemInfo = async () => {
  try {
    const res = await adminApi.getInfo()
    systemInfo.value = res
  } catch (e) {
    console.error('加载系统信息失败:', e)
  }
}

const loadStats = async () => {
  try {
    const res = await adminApi.getStats()
    stats.value = res
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

const loadConfig = async () => {
  try {
    const res = await adminApi.getConfig()
    if (res.config) {
      configForm.check_interval = parseInt(res.config.check_interval || 60)
      configForm.data_retention = parseInt(res.config.data_retention_days || 90)
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

const loadLogs = async () => {
  try {
    const res = await adminApi.getStats()
    logs.value = res.recent_logs || []
  } catch (e) {
    console.error('加载日志失败:', e)
  }
}

const handleSaveConfig = async () => {
  try {
    await adminApi.updateConfig('check_interval', configForm.check_interval)
    await adminApi.updateConfig('data_retention_days', configForm.data_retention)
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadSystemInfo()
  loadStats()
  loadConfig()
  loadLogs()
})
</script>

<style lang="scss" scoped>
.admin-page {
  .stat-num {
    font-size: 18px;
    font-weight: bold;
    color: #409eff;
  }
  
  .stat-sub {
    color: #999;
    font-size: 12px;
  }
  
  .form-tip {
    margin-left: 8px;
    color: #999;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .log-container {
    max-height: 300px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 12px;
    background: #1e1e1e;
    padding: 12px;
    border-radius: 4px;
    
    .log-item {
      padding: 4px 0;
      border-bottom: 1px solid #333;
      
      .log-time {
        color: #888;
        margin-right: 12px;
      }
      
      .log-level {
        display: inline-block;
        width: 60px;
      }
      
      &.debug .log-level { color: #888; }
      &.info .log-level { color: #4caf50; }
      &.warning .log-level { color: #ff9800; }
      &.error .log-level { color: #f44336; }
    }
  }
}
</style>
