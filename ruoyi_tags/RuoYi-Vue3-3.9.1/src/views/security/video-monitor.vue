<template>
  <div class="app-container">
    <!-- 顶部操作栏 -->
    <el-card class="mb-4">
      <div class="flex justify-between items-center">
        <div class="flex gap-10">
          <el-button type="primary" @click="handlePreview">实时预览</el-button>
          <el-button @click="handlePlayback">回放</el-button>
          <el-button @click="handleCapture">抓拍</el-button>
          <el-button @click="handleExport">导出</el-button>
          <el-button @click="handlePtz">云台控制</el-button>
        </div>
        <div class="flex gap-10">
          <el-select v-model="viewMode" placeholder="多画面" @change="handleViewModeChange">
            <el-option label="单画面" value="single" />
            <el-option label="4画面" value="4" />
            <el-option label="9画面" value="9" />
            <el-option label="16画面" value="16" />
          </el-select>
          <el-select v-model="resolution" placeholder="清晰度" @change="handleResolutionChange">
            <el-option label="标清" value="sd" />
            <el-option label="高清" value="hd" />
            <el-option label="超清" value="uhd" />
          </el-select>
          <el-button @click="handleFavorite">我的收藏</el-button>
        </div>
      </div>
    </el-card>

    <!-- 搜索和筛选 -->
    <el-card class="mb-4">
      <el-form :model="searchForm" label-width="100px" size="small">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="快速搜索">
              <el-input v-model="searchForm.keyword" placeholder="设备名称/设备SN码/所属区域" clearable>
                <template #append>
                  <el-button type="primary" @click="handleSearch">搜索</el-button>
                  <el-button @click="resetSearch">重置</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="设备状态">
              <el-select v-model="searchForm.status" multiple placeholder="选择状态" clearable>
                <el-option label="正常" value="normal" />
                <el-option label="离线" value="offline" />
                <el-option label="故障" value="fault" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="设备类型">
              <el-select v-model="searchForm.deviceType" multiple placeholder="选择类型" clearable>
                <el-option label="高清摄像头" value="camera" />
                <el-option label="球机" value="dome" />
                <el-option label="半球摄像头" value="half" />
                <el-option label="云台摄像头" value="ptz" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="所属区域">
              <el-select v-model="searchForm.area" multiple placeholder="选择区域" clearable>
                <el-option label="园区核心区域" value="core" />
                <el-option label="重要区域" value="important" />
                <el-option label="普通区域" value="normal" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 视频预览区域 -->
    <el-card>
      <div class="video-grid" :class="`video-grid-${viewMode}`">
        <div v-for="device in filteredDeviceList" :key="device.id" class="video-item" @click="handleDeviceClick(device)">
          <div class="video-placeholder">
            <el-icon :size="60" color="#909399"><VideoCamera /></el-icon>
            <div class="video-title">{{ device.name }}</div>
            <div class="video-status">
              <el-tag :type="getStatusType(device.status)" size="small">{{ getStatusText(device.status) }}</el-tag>
            </div>
          </div>
          <div class="video-overlay" v-if="device.status !== 'normal'">
            <el-icon :size="40" color="red"><Warning /></el-icon>
            <div class="overlay-text">{{ getStatusText(device.status) }}</div>
          </div>
          <div class="video-overlay" v-if="device.favorite">
            <el-icon :size="20" color="gold"><StarFilled /></el-icon>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 云台控制面板 -->
    <el-card v-if="activeDevice" class="mt-4">
      <div class="ptz-header">
        <div class="ptz-title">云台控制 - {{ activeDevice.name }}</div>
        <div class="ptz-status">
          <el-tag :type="getStatusType(activeDevice.status)" size="small">{{ getStatusText(activeDevice.status) }}</el-tag>
        </div>
      </div>
      <div class="ptz-controls">
        <div class="ptz-direction">
          <el-button @click="handlePtzUp">↑</el-button>
          <el-button @click="handlePtzDown">↓</el-button>
          <el-button @click="handlePtzLeft">←</el-button>
          <el-button @click="handlePtzRight">→</el-button>
        </div>
        <div class="ptz-zoom">
          <div class="zoom-label">变焦</div>
          <el-slider v-model="zoomLevel" @change="handleZoomChange" :min="0" :max="100" />
        </div>
        <div class="ptz-focus">
          <div class="focus-label">聚焦</div>
          <el-slider v-model="focusLevel" @change="handleFocusChange" :min="0" :max="100" />
        </div>
      </div>
      <div class="ptz-actions">
        <el-button @click="handlePreset">预设点位</el-button>
        <el-button @click="handleCruise">巡航</el-button>
        <el-button @click="handleSavePosition">保存位置</el-button>
      </div>
    </el-card>

    <!-- 统计查看 -->
    <el-card class="mt-4">
      <div class="stat-header">
        <div class="stat-title">视频设备统计</div>
        <div class="stat-filter">
          <el-select v-model="statMode" placeholder="统计维度" @change="handleStatModeChange">
            <el-option label="设备类型" value="type" />
            <el-option label="区域" value="area" />
            <el-option label="状态" value="status" />
          </el-select>
          <el-date-picker
            v-model="statTimeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            clearable
            size="small"
          />
          <el-button @click="handleStatExport" size="small">导出</el-button>
        </div>
      </div>
      <div class="stat-chart">
        <div class="chart-container">
          <div class="chart-item" v-for="item in statData" :key="item.name">
            <div class="chart-label">{{ item.name }}</div>
            <div class="chart-bar">
              <div class="chart-fill" :style="{ width: item.percentage + '%', backgroundColor: item.color }" />
            </div>
            <div class="chart-value">{{ item.value }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 参数配置 -->
    <el-card class="mt-4">
      <div class="config-header">
        <div class="config-title">参数配置</div>
        <el-button type="primary" @click="handleConfigSave">保存配置</el-button>
      </div>
      <el-tabs v-model="configTab" type="border-card">
        <el-tab-pane name="device" label="设备参数">
          <el-form :model="configForm.device" label-width="140px">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="预览清晰度">
                  <el-select v-model="configForm.device.resolution" placeholder="选择清晰度">
                    <el-option label="标清" value="sd" />
                    <el-option label="高清" value="hd" />
                    <el-option label="超清" value="uhd" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="录像分辨率">
                  <el-select v-model="configForm.device.recordResolution" placeholder="选择分辨率">
                    <el-option label="720P" value="720p" />
                    <el-option label="1080P" value="1080p" />
                    <el-option label="4K" value="4k" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="抓拍频率">
                  <el-select v-model="configForm.device.captureFrequency" placeholder="选择频率">
                    <el-option label="1秒" value="1s" />
                    <el-option label="5秒" value="5s" />
                    <el-option label="10秒" value="10s" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>
        <el-tab-pane name="storage" label="视频存储">
          <el-form :model="configForm.storage" label-width="140px">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="本地存储时长">
                  <el-input v-model="configForm.storage.localDuration" placeholder="天" />天
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="云端备份时长">
                  <el-input v-model="configForm.storage.cloudDuration" placeholder="天" />天
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="存储路径">
                  <el-input v-model="configForm.storage.path" placeholder="路径" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>
        <el-tab-pane name="linkage" label="联动设置">
          <el-form :model="configForm.linkage" label-width="140px">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="告警触发自动调取视频">
                  <el-switch v-model="configForm.linkage.autoCallVideo" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="告警触发自动抓拍">
                  <el-switch v-model="configForm.linkage.autoCapture" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="告警触发自动录像">
                  <el-switch v-model="configForm.linkage.autoRecord" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup name="VideoMonitor">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera, Warning, StarFilled, Monitor } from '@element-plus/icons-vue'

// 响应式数据
const searchForm = reactive({
  keyword: '',
  status: [],
  deviceType: [],
  area: []
})

const viewMode = ref('single')
const resolution = ref('hd')
const activeDevice = ref(null)
const zoomLevel = ref(50)
const focusLevel = ref(50)
const statMode = ref('type')
const statTimeRange = ref([])
const configTab = ref('device')

const configForm = reactive({
  device: {
    resolution: 'hd',
    recordResolution: '1080p',
    captureFrequency: '5s'
  },
  storage: {
    localDuration: 30,
    cloudDuration: 90,
    path: '/mnt/video'
  },
  linkage: {
    autoCallVideo: true,
    autoCapture: true,
    autoRecord: true
  }
})

// 设备列表数据
const deviceList = ref([
  {
    id: 1,
    name: '园区主入口摄像头',
    sn: 'CAM-20240101-001',
    type: 'camera',
    status: 'normal',
    area: 'core',
    favorite: true,
    resolution: '1080P',
    position: '主入口'
  },
  {
    id: 2,
    name: '消防控制室摄像头',
    sn: 'CAM-20240101-002',
    type: 'dome',
    status: 'normal',
    area: 'core',
    favorite: true,
    resolution: '4K',
    position: '消防控制室'
  },
  {
    id: 3,
    name: '配电室摄像头',
    sn: 'CAM-20240101-003',
    type: 'ptz',
    status: 'offline',
    area: 'core',
    favorite: false,
    resolution: '1080P',
    position: '配电室'
  },
  {
    id: 4,
    name: '园区主干道摄像头',
    sn: 'CAM-20240101-004',
    type: 'camera',
    status: 'normal',
    area: 'important',
    favorite: false,
    resolution: '1080P',
    position: '主干道'
  },
  {
    id: 5,
    name: '1号楼门禁摄像头',
    sn: 'CAM-20240101-005',
    type: 'half',
    status: 'fault',
    area: 'important',
    favorite: false,
    resolution: '720P',
    position: '1号楼'
  },
  {
    id: 6,
    name: '地下车库摄像头',
    sn: 'CAM-20240101-006',
    type: 'camera',
    status: 'normal',
    area: 'normal',
    favorite: false,
    resolution: '1080P',
    position: '地下车库'
  },
  {
    id: 7,
    name: '园区周界摄像头',
    sn: 'CAM-20240101-007',
    type: 'ptz',
    status: 'normal',
    area: 'core',
    favorite: true,
    resolution: '4K',
    position: '周界'
  },
  {
    id: 8,
    name: '贵重设施存放区摄像头',
    sn: 'CAM-20240101-008',
    type: 'camera',
    status: 'normal',
    area: 'core',
    favorite: false,
    resolution: '4K',
    position: '贵重设施存放区'
  }
])

// 统计数据
const statData = ref([
  { name: '高清摄像头', value: '6台', percentage: 75, color: '#67c23a' },
  { name: '球机', value: '1台', percentage: 12.5, color: '#67c23a' },
  { name: '半球摄像头', value: '1台', percentage: 12.5, color: '#67c23a' },
  { name: '云台摄像头', value: '2台', percentage: 25, color: '#67c23a' }
])

// 计算属性
const filteredDeviceList = computed(() => {
  const filtered = deviceList.value.filter(device => {
    const keywordMatch = !searchForm.keyword || 
      device.name.includes(searchForm.keyword) || 
      device.sn.includes(searchForm.keyword) || 
      device.area.includes(searchForm.keyword)
    const statusMatch = !searchForm.status.length || searchForm.status.includes(device.status)
    const typeMatch = !searchForm.deviceType.length || searchForm.deviceType.includes(device.type)
    const areaMatch = !searchForm.area.length || searchForm.area.includes(device.area)
    return keywordMatch && statusMatch && typeMatch && areaMatch
  })
  // 按区域优先级排序：核心区域 > 重要区域 > 普通区域
  return filtered.sort((a, b) => {
    const areaPriority = { core: 3, important: 2, normal: 1 }
    return areaPriority[b.area] - areaPriority[a.area]
  })
})

// 方法
const handleSearch = () => {
  ElMessage.success('搜索功能已触发')
}

const resetSearch = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = Array.isArray(searchForm[key]) ? [] : ''
  })
}

const handlePreview = () => {
  ElMessage.success('实时预览功能已触发')
}

const handlePlayback = () => {
  ElMessage.success('回放功能已触发')
}

const handleCapture = () => {
  ElMessage.success('抓拍功能已触发')
}

const handleExport = () => {
  ElMessage.success('导出功能已触发')
}

const handlePtz = () => {
  ElMessage.success('云台控制功能已触发')
}

const handleViewModeChange = () => {
  // 多画面切换逻辑
  const videoGrid = document.querySelector('.video-grid')
  if (videoGrid) {
    // 移除所有视图模式类
    videoGrid.classList.remove('video-grid-single', 'video-grid-4', 'video-grid-9', 'video-grid-16')
    // 添加当前视图模式类
    videoGrid.classList.add(`video-grid-${viewMode.value}`)
  }
  ElMessage.info(`多画面切换至: ${viewMode.value}`)
}

// 全屏功能
const isFullscreen = ref(false)

const toggleFullscreen = (el) => {
  if (!document.fullscreenElement) {
    el.requestFullscreen().catch(err => {
      ElMessage.error(`全屏请求失败: ${err.message}`)
    })
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// 单个画面点击放大至全屏
const handleVideoClick = (event, device) => {
  event.stopPropagation()
  const videoItem = event.currentTarget
  toggleFullscreen(videoItem)
  activeDevice.value = device
}

// 清晰度调节功能
const handleResolutionChange = () => {
  // 清晰度切换逻辑
  const resolutionText = { sd: '标清', hd: '高清', uhd: '超清' }
  ElMessage.info(`清晰度切换至: ${resolutionText[resolution.value]}`)
  
  // 模拟视频流短暂中断（≤1秒）
  const videoPlaceholders = document.querySelectorAll('.video-placeholder')
  videoPlaceholders.forEach(placeholder => {
    placeholder.style.opacity = '0.5'
    setTimeout(() => {
      placeholder.style.opacity = '1'
    }, 500)
  })
  
  // 切换完成后自动续播
  setTimeout(() => {
    ElMessage.success('清晰度切换完成，视频自动续播')
  }, 1000)
}

// 我的收藏功能（已移动到设备切换功能部分）

// 设备切换功能
const currentDeviceIndex = ref(0)

const handleDeviceClick = (device) => {
  activeDevice.value = device
  // 记录当前设备索引
  const index = filteredDeviceList.value.findIndex(d => d.id === device.id)
  if (index !== -1) {
    currentDeviceIndex.value = index
  }
  ElMessage.info(`选中设备: ${device.name}`)
}

// 左右滑动切换相邻设备
const switchDevice = (direction) => {
  const total = filteredDeviceList.value.length
  if (total === 0) return
  
  if (direction === 'left') {
    currentDeviceIndex.value = (currentDeviceIndex.value - 1 + total) % total
  } else if (direction === 'right') {
    currentDeviceIndex.value = (currentDeviceIndex.value + 1) % total
  }
  
  activeDevice.value = filteredDeviceList.value[currentDeviceIndex.value]
  ElMessage.info(`切换至设备: ${activeDevice.value.name}`)
}

// 我的收藏功能（已修复重复声明）
const favoriteDevices = ref([])

const handleFavorite = () => {
  // 筛选收藏的设备
  favoriteDevices.value = deviceList.value.filter(device => device.favorite)
  if (favoriteDevices.value.length === 0) {
    ElMessage.info('暂无收藏的设备')
    return
  }
  // 显示收藏设备列表
  ElMessageBox.alert(
    favoriteDevices.value.map((device, index) => `${index + 1}. ${device.name}`).join('<br>'),
    '我的收藏',
    { dangerouslyUseHTMLString: true }
  )
}

// 收藏图标点击跳转
const handleFavoriteClick = (device) => {
  activeDevice.value = device
  ElMessage.info(`跳转到收藏设备: ${device.name}`)
}

const getStatusType = (status) => {
  switch (status) {
    case 'normal': return 'success'
    case 'offline': return 'warning'
    case 'fault': return 'danger'
    default: return ''
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'normal': return '正常'
    case 'offline': return '离线'
    case 'fault': return '故障'
    default: return status
  }
}

const handlePtzUp = () => {
  ElMessage.info('云台向上控制')
}

const handlePtzDown = () => {
  ElMessage.info('云台向下控制')
}

const handlePtzLeft = () => {
  ElMessage.info('云台向左控制')
}

const handlePtzRight = () => {
  ElMessage.info('云台向右控制')
}

const handleZoomChange = () => {
  ElMessage.info(`变焦调整至: ${zoomLevel.value}`)
}

const handleFocusChange = () => {
  ElMessage.info(`聚焦调整至: ${focusLevel.value}`)
}

const handlePreset = () => {
  ElMessage.info('预设点位功能已触发')
}

const handleCruise = () => {
  ElMessage.info('巡航功能已触发')
}

const handleSavePosition = () => {
  ElMessage.info('保存位置功能已触发')
}

const handleStatModeChange = () => {
  ElMessage.info(`统计维度切换至: ${statMode.value}`)
}

const handleStatExport = () => {
  ElMessage.success('统计导出功能已触发')
}

const handleConfigSave = () => {
  ElMessage.success('配置保存成功')
}

// 异常提醒功能
const showAbnormalAlert = (device) => {
  const alertText = {
    offline: '设备离线',
    fault: '设备故障',
    noStream: '无视频流'
  }
  
  // 预览画面标红
  const videoItems = document.querySelectorAll('.video-item')
  videoItems.forEach(item => {
    const deviceId = item.dataset.deviceId
    if (deviceId && deviceId === device.id.toString()) {
      item.style.borderColor = '#f56c6c'
      item.style.boxShadow = '0 0 8px rgba(245, 108, 108, 0.5)'
    }
  })
  
  // 显示异常提示
  const alertContent = `设备: ${device.name}<br>异常: ${alertText[device.status] || '未知异常'}`
  ElMessageBox.alert(alertContent, '设备异常', { dangerouslyUseHTMLString: true })
  
  // 推送系统消息提醒
  ElMessage.warning(`设备异常: ${device.name} - ${alertText[device.status] || '未知异常'}`)
}

// 查看异常详情
const handleAbnormalClick = (device) => {
  const detailContent = `
    设备名称: ${device.name}<br>
    设备类型: ${getDeviceTypeText(device.type)}<br>
    所属区域: ${device.area}<br>
    异常状态: ${getStatusText(device.status)}<br>
    最后更新: ${device.lastUpdateTime}
  `
  ElMessageBox.alert(detailContent, '异常详情', { dangerouslyUseHTMLString: true })
}

// 生命周期
onMounted(() => {
  // 初始化时检查异常设备
  const abnormalDevices = deviceList.value.filter(device => device.status !== 'normal')
  if (abnormalDevices.length > 0) {
    ElMessage.warning(`发现 ${abnormalDevices.length} 台异常设备`)
  }
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.flex {
  display: flex;
}

.justify-between {
  justify-content: space-between;
}

.items-center {
  align-items: center;
}

.gap-10 {
  gap: 10px;
}

/* 视频网格 */
.video-grid {
  display: grid;
  gap: 16px;
}

.video-grid-single {
  grid-template-columns: repeat(1, 1fr);
}

.video-grid-4 {
  grid-template-columns: repeat(2, 1fr);
}

.video-grid-9 {
  grid-template-columns: repeat(3, 1fr);
}

.video-grid-16 {
  grid-template-columns: repeat(4, 1fr);
}

.video-item {
  position: relative;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.video-item:hover {
  border-color: #409eff;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.3);
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  background: #f5f7fa;
}

.video-title {
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
  font-weight: bold;
}

.video-status {
  margin-top: 10px;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.overlay-text {
  margin-top: 10px;
}

/* 云台控制 */
.ptz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ptz-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.ptz-status {
  margin-right: 20px;
}

.ptz-controls {
  display: flex;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
}

.ptz-direction {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
}

.ptz-zoom,
.ptz-focus {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
}

.zoom-label,
.focus-label {
  font-size: 12px;
  color: #606266;
}

.ptz-actions {
  display: flex;
  gap: 10px;
}

/* 统计查看 */
.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stat-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.stat-filter {
  display: flex;
  gap: 10px;
}

.stat-chart {
  padding: 20px;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-item {
  display: flex;
  align-items: center;
  gap: 20px;
}

.chart-label {
  width: 100px;
  font-size: 14px;
  color: #606266;
}

.chart-bar {
  flex: 1;
  height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.chart-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s;
}

.chart-value {
  width: 80px;
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  text-align: right;
}

/* 参数配置 */
.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.config-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
</style>
