<template>
  <div class="reports-page">
    <el-row :gutter="20">
      <!-- 左侧：模板管理 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>报告模板</span>
              <el-button type="primary" size="small" @click="handleCreateTemplate">
                <el-icon><Plus /></el-icon> 新增模板
              </el-button>
            </div>
          </template>
          
          <el-table :data="templates" stripe style="width: 100%">
            <el-table-column prop="code" label="编码" width="120" />
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="report_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ getTypeText(row.report_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="schedule_cron" label="调度" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleGenerate(row)">生成</el-button>
                <el-button type="primary" link size="small" @click="handleEditTemplate(row)">编辑</el-button>
                <el-button type="danger" link size="small" @click="handleDeleteTemplate(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <!-- 右侧：报告记录 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>最近报告</span>
          </template>
          
          <el-table :data="records" stripe style="width: 100%">
            <el-table-column prop="template_code" label="模板" width="120" />
            <el-table-column prop="report_time" label="生成时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.report_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button 
                  v-if="row.status === 'generated' && row.file_path" 
                  type="primary" 
                  link 
                  size="small"
                >下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 模板编辑对话框 -->
    <el-dialog v-model="templateDialogVisible" :title="isTemplateEdit ? '编辑模板' : '新增模板'" width="700px">
      <el-form ref="templateFormRef" :model="templateForm" :rules="templateRules" label-width="100px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="templateForm.code" :disabled="isTemplateEdit" placeholder="英文唯一标识" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="templateForm.name" placeholder="模板名称" />
        </el-form-item>
        <el-form-item label="报告类型" prop="report_type">
          <el-select v-model="templateForm.report_type" placeholder="选择类型">
            <el-option v-for="t in reportTypes" :key="t.code" :label="t.name" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="调度CRON" prop="schedule_cron">
          <el-input v-model="templateForm.schedule_cron" placeholder="0 7 * * * (每天7点)" />
        </el-form-item>
        <el-form-item label="内容模板" prop="content_template">
          <el-input 
            v-model="templateForm.content_template" 
            type="textarea" 
            :rows="6" 
            placeholder="使用Jinja2模板语法，如：{{ metric_code }}: {{ value }}"
          />
        </el-form-item>
        <el-form-item label="通知渠道">
          <el-checkbox-group v-model="templateForm.notify_channels">
            <el-checkbox label="lark">飞书</el-checkbox>
            <el-checkbox label="email">邮件</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitTemplate">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 生成报告对话框 -->
    <el-dialog v-model="generateDialogVisible" title="生成报告" width="500px">
      <el-form :model="generateForm" label-width="100px">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="generateForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmGenerate">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { reportsApi } from '@/api'

const templates = ref([])
const records = ref([])
const templateDialogVisible = ref(false)
const generateDialogVisible = ref(false)
const isTemplateEdit = ref(false)
const templateFormRef = ref()
const reportTypes = ref([])

const templateForm = reactive({
  id: null,
  code: '',
  name: '',
  report_type: 'daily',
  schedule_cron: '',
  content_template: '',
  notify_channels: [],
  status: 'active'
})

const generateForm = reactive({
  templateId: null,
  dateRange: []
})

const templateRules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  report_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  content_template: [{ required: true, message: '请输入内容模板', trigger: 'blur' }]
}

const loadTemplates = async () => {
  try {
    const res = await reportsApi.getTemplates()
    templates.value = res.templates || []
  } catch (e) {
    console.error('加载模板失败:', e)
  }
}

const loadRecords = async () => {
  try {
    const res = await reportsApi.getRecords({ page: 1, page_size: 20 })
    records.value = res.items || []
  } catch (e) {
    console.error('加载记录失败:', e)
  }
}

const loadReportTypes = async () => {
  try {
    const res = await reportsApi.getTypes()
    reportTypes.value = res.types || []
  } catch (e) {
    console.error('加载类型失败:', e)
  }
}

const handleCreateTemplate = () => {
  isTemplateEdit.value = false
  Object.assign(templateForm, {
    id: null, code: '', name: '', report_type: 'daily',
    schedule_cron: '', content_template: '', notify_channels: [], status: 'active'
  })
  templateDialogVisible.value = true
}

const handleEditTemplate = (row) => {
  isTemplateEdit.value = true
  Object.assign(templateForm, row)
  templateDialogVisible.value = true
}

const handleSubmitTemplate = async () => {
  try {
    await templateFormRef.value.validate()
    
    if (isTemplateEdit.value) {
      await reportsApi.updateTemplate(templateForm.id, templateForm)
      ElMessage.success('更新成功')
    } else {
      await reportsApi.createTemplate(templateForm)
      ElMessage.success('创建成功')
    }
    
    templateDialogVisible.value = false
    loadTemplates()
  } catch (e) {
    if (e !== false) ElMessage.error('操作失败')
  }
}

const handleDeleteTemplate = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该模板?', '提示', { type: 'warning' })
    await reportsApi.deleteTemplate(row.id)
    ElMessage.success('删除成功')
    loadTemplates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const handleGenerate = (row) => {
  generateForm.templateId = row.id
  generateForm.dateRange = []
  generateDialogVisible.value = true
}

const handleConfirmGenerate = async () => {
  if (!generateForm.dateRange || generateForm.dateRange.length !== 2) {
    ElMessage.warning('请选择时间范围')
    return
  }
  
  try {
    await reportsApi.generate({
      template_id: generateForm.templateId,
      time_range_start: generateForm.dateRange[0].toISOString(),
      time_range_end: generateForm.dateRange[1].toISOString()
    })
    ElMessage.success('报告生成任务已启动')
    generateDialogVisible.value = false
    loadRecords()
  } catch (e) {
    ElMessage.error('生成失败')
  }
}

const getTypeText = (type) => {
  const texts = { daily: '日报', weekly: '周报', monthly: '月报', custom: '自定义' }
  return texts[type] || type
}

const getStatusType = (status) => {
  const types = { generated: 'success', generating: 'warning', failed: 'danger' }
  return types[status] || ''
}

const getStatusText = (status) => {
  const texts = { generated: '成功', generating: '生成中', failed: '失败' }
  return texts[status] || status
}

const formatTime = (time) => new Date(time).toLocaleString('zh-CN')

onMounted(() => {
  loadTemplates()
  loadRecords()
  loadReportTypes()
})
</script>

<style lang="scss" scoped>
.reports-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
