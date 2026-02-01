<template>
  <el-config-provider :locale="locale">
    <el-container class="app-container">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar">
        <div class="logo">
          <el-icon v-if="isCollapsed" :size="24"><Monitor /></el-icon>
          <span v-else>金融风控监控</span>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapsed"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          
          <el-menu-item index="/alerts">
            <el-icon><Bell /></el-icon>
            <span>告警中心</span>
          </el-menu-item>
          
          <el-menu-item index="/metrics">
            <el-icon><TrendCharts /></el-icon>
            <span>监控指标</span>
          </el-menu-item>
          
          <el-sub-menu index="config">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统配置</span>
            </template>
            <el-menu-item index="/datasources">数据源</el-menu-item>
            <el-menu-item index="/rules">告警规则</el-menu-item>
            <el-menu-item index="/notify">通知渠道</el-menu-item>
          </el-sub-menu>
          
          <el-menu-item index="/reports">
            <el-icon><Document /></el-icon>
            <span>报告管理</span>
          </el-menu-item>
          
          <el-menu-item index="/admin">
            <el-icon><User /></el-icon>
            <span>系统管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-icon @click="toggleSidebar" class="toggle-icon">
              <Fold v-if="!isCollapsed" />
              <Expand v-else />
            </el-icon>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-badge :value="unreadAlerts" :hidden="unreadAlerts === 0" class="alert-badge">
              <el-icon :size="20" @click="$router.push('/alerts')">
                <Bell />
              </el-icon>
            </el-badge>
            
            <el-dropdown>
              <el-icon :size="20" class="user-icon">
                <User />
              </el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>个人信息</el-dropdown-item>
                  <el-dropdown-item>修改密码</el-dropdown-item>
                  <el-dropdown-item divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            
            <span class="username">管理员</span>
          </div>
        </el-header>
        
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Monitor, DataAnalysis, Bell, TrendCharts, Setting, Document, User, Fold, Expand } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const locale = zhCn
const route = useRoute()
const isCollapsed = ref(false)
const unreadAlerts = ref(3)

const activeMenu = computed(() => route.path)
const currentPageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/alerts': '告警中心',
    '/metrics': '监控指标',
    '/datasources': '数据源配置',
    '/rules': '告警规则',
    '/notify': '通知渠道',
    '/reports': '报告管理',
    '/admin': '系统管理'
  }
  return titles[route.path] || ''
})

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 16px;
    font-weight: bold;
    background-color: #263445;
  }
  
  .sidebar-menu {
    border-right: none;
    background-color: transparent;
    
    :deep(.el-menu-item),
    :deep(.el-sub-menu__title) {
      color: #bfcbd9;
      
      &:hover {
        background-color: #263445;
      }
    }
    
    :deep(.el-menu-item.is-active) {
      color: #409eff;
      background-color: #1f2d3d;
    }
  }
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  
  .header-left {
    display: flex;
    align-items: center;
    
    .toggle-icon {
      margin-right: 16px;
      cursor: pointer;
      font-size: 20px;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
    
    .alert-badge {
      cursor: pointer;
    }
    
    .user-icon {
      cursor: pointer;
    }
    
    .username {
      color: #333;
    }
  }
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
