<template>
  <div class="rules-page">
    <!-- 操作栏 -->
    <el-card class="action-card">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新增规则
      </el-button>
      <el-button @click="loadRules">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
      <el-select v-model="selectedMetric" placeholder="按指标筛选" clearable @change="loadRules" style="margin-left: 16px;">
        <el-option v-for="m in metrics" :key="m.code" :label="m.name" :value="m.code" />
      </el-select>
    </el-card>
    
    <!-- 规则列表 -->
    <el-card>
      <el-table :data="rulesList" stripe style="width: 100%">
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="metric_code" label="关联指标" width="180" />
        <el-table-column prop="condition_type" label="条件类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getConditionText(row.condition_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" effect="dark">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.enabled"
              @change="handleToggle(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="notify_channels" label="通知渠道" width="150">
          <template #default="{ row }">
            {{ (row.notify_channels || []).join(', ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handleCopy(row)">复制</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑规则' : '新增规则'" 
      width="700px"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="formData.code" :disabled="isEdit" placeholder="英文唯一标识" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="规则名称" />
        </el-form-item>
        <el-form-item label="关联指标" prop="metric_code">
          <el-select v-model="formData.metric_code" placeholder="选择指标">
            <el-option v-for="m in metrics" :key="m.code" :label="`${m.name} (${m.code})`" :value="m.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件类型" prop="condition_type">
          <el-select v-model="formData.condition_type" placeholder="选择条件类型">
            <el-option label="阈值告警" value="threshold" />
            <el-option label="范围告警" value="range" />
            <el-option label="变化率告警" value="change_rate" />
            <el-option label="趋势告警" value="trend" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="条件配置" prop="condition_config">
          <el-input 
            v-model="conditionConfigJson" 
            type="textarea" 
            :rows="3" 
            placeholder='{"operator": ">", "threshold": 100}'
          />
          <div class="form-tip">根据条件类型填写对应的JSON配置</div>
        </el-form-item>
        
        <el-form-item label="告警级别" prop="severity">
          <el-radio-group v-model="formData.severity">
            <el-radio-button label="P1">P1 紧急</el-radio-button>
            <el-radio-button label="P2">P2 严重</el-radio-button>
            <el-radio-button label="P3">P3 警告</el-radio-button>
            <el-radio-button label="P4">P4 提示</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="通知渠道">
          <el-checkbox-group v-model="formData.notify_channels">
            <el-checkbox label="lark">飞书</el-checkbox>
            <el-checkbox label="wecom">企业微信</el-checkbox>
            <el-checkbox label="email">邮件</el-checkbox>
            <el-checkbox label="dingtalk">钉钉</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="冷却时间">
          <el-input-number v-model="formData.cooldown_minutes" :min="0" :step="5" />
          <span class="form-tip">分钟</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { rulesApi, metricsApi } from '@/api'

const rulesList = ref([])
const metrics = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const selectedMetric = ref('')

const formData = reactive({
  id: null,
  code: '',
  name: '',
  metric_code: '',
  condition_type: 'threshold',
  condition_config: { operator: '>', threshold: 100 },
  severity: 'P3',
  notify_channels: ['lark'],
  cooldown_minutes: 10,
  enabled: true
})

const conditionConfigJson = ref('{"operator": ">", "threshold": 100}')

const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  metric_code: [{ required: true, message: '请选择指标', trigger: 'change' }],
  condition_type: [{ required: true, message: '请选择条件类型', trigger: 'change' }],
  severity: [{ required: true, message: '请选择级别', trigger: 'change' }]
}

const loadRules = async () => {
  try {
    const params = { page: 1, page_size: 100 }
    if (selectedMetric.value) {
      params.metric_code = selectedMetric.value
    }
    const res = await rulesApi.getList(params)
    rulesList.value = res.items || []
  } catch (e) {
    ElMessage.error('加载规则失败')
  }
}

const loadMetrics = async () => {
  try {
    const res = await metricsApi.getList({ page: 1, page_size: 1000 })
    metrics.value = res.items || []
  } catch (e) {
    console.error('加载指标失败:', e)
  }
}

const handleCreate = () => {
  isEdit.value = false
  formData.id = null
  formData.code = ''
  formData.name = ''
  formData.metric_code = ''
  formData.condition_type = 'threshold'
  formData.condition_config = { operator: '>', threshold: 100 }
  formData.severity = 'P3'
  formData.notify_channels = ['lark']
  formData.cooldown_minutes = 10
  formData.enabled = true
  conditionConfigJson.value = '{"operator": ">", "threshold": 100}'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  conditionConfigJson.value = JSON.stringify(row.condition_config || {}, null, 2)
  dialogVisible.value = true
}

const handleCopy = (row) => {
  isEdit.value = false
  formData.code = row.code + '_copy'
  formData.name = row.name + '_副本'
  formData.metric_code = row.metric_code
  formData.condition_type = row.condition_type
  formData.condition_config = row.condition_config
  formData.severity = row.severity
  formData.notify_channels = [...(row.notify_channels || [])]
  formData.cooldown_minutes = row.cooldown_minutes
  formData.enabled = true
  conditionConfigJson.value = JSON.stringify(row.condition_config || {}, null, 2)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    try {
      formData.condition_config = JSON.parse(conditionConfigJson.value)
    } catch (e) {
      ElMessage.error('条件配置必须是有效的JSON格式')
      return
    }
    
    if (isEdit.value) {
      await rulesApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await rulesApi.create(formData)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadRules()
  } catch (e) {
    if (e !== false) {
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该规则吗?', '提示', { type: 'warning' })
    await rulesApi.delete(row.id)
    ElMessage.success('删除成功')
    loadRules()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleToggle = async (row) => {
  try {
    await rulesApi.toggle(row.id, !row.enabled)
    row.enabled = !row.enabled
    ElMessage.success(row.enabled ? '规则已启用' : '规则已禁用')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const getConditionText = (type) => {
  const texts = {
    threshold: '阈值',
    range: '范围',
    change_rate: '变化率',
    trend: '趋势'
  }
  return texts[type] || type
}

const getSeverityType = (severity) => {
  const types = { P1: 'danger', P2: 'warning', P3: 'info', P4: '' }
  return types[severity] || ''
}

onMounted(() => {
  loadRules()
  loadMetrics()
})
</script>

<style lang="scss" scoped>
.rules-page {
  .action-card {
    margin-bottom: 20px;
  }
  
  .form-tip {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
  }
}
</style>
