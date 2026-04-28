<template>
  <div class="app-container">
    <el-card>
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息 -->
        <el-tab-pane name="basic" label="基本信息">
          <el-form :model="deviceInfo" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="设备ID">{{ deviceInfo.id }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="设备名称">{{ deviceInfo.name }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="设备类型">{{ getDeviceTypeText(deviceInfo.type) }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="设备编号">{{ deviceInfo.assetCode || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="厂商">{{ deviceInfo.manufacturer || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="型号">{{ deviceInfo.model || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="SN码">{{ deviceInfo.sn }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="MAC地址">{{ deviceInfo.macAddress || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="IP地址">{{ deviceInfo.ipAddress || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="端口号">{{ deviceInfo.port || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="接入协议">{{ deviceInfo.protocol || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="所属区域">{{ getAreaText(deviceInfo.area) }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="楼栋">{{ deviceInfo.building || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="楼层">{{ deviceInfo.floor || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="详细安装位置">{{ deviceInfo.installLocation || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="地图点位ID">{{ deviceInfo.mapPointId || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="安装日期">{{ deviceInfo.installDate || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="维保到期日期">{{ deviceInfo.maintainDate || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="责任人">{{ deviceInfo.owner || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="联系电话">{{ deviceInfo.phone || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="启用状态">
                  <el-tag :type="deviceInfo.enabled === '1' ? 'success' : 'info'">
                    {{ deviceInfo.enabled === '1' ? '启用' : '禁用' }}
                  </el-tag>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="创建时间">{{ deviceInfo.createTime || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="更新时间">{{ deviceInfo.updateTime || '-' }}</el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="最近同步时间">{{ deviceInfo.lastSyncTime || '-' }}</el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="数据来源">{{ deviceInfo.sourceSystem || '-' }}</el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>

        <!-- 设备参数 -->
        <el-tab-pane name="params" label="设备参数">
          <el-form :model="deviceInfo" label-width="140px" v-if="deviceInfo.type">
            <!-- 监控摄像头参数 -->
            <template v-if="deviceInfo.type === 'camera'">
              <el-form-item label="摄像头类型">{{ deviceInfo.cameraType || '-' }}</el-form-item>
              <el-form-item label="分辨率">{{ deviceInfo.resolution || '-' }}</el-form-item>
              <el-form-item label="帧率">{{ deviceInfo.frameRate || '-' }}</el-form-item>
              <el-form-item label="码率">{{ deviceInfo.bitrate || '-' }}</el-form-item>
              <el-form-item label="红外距离">{{ deviceInfo.infraredDistance || '-' }}</el-form-item>
              <el-form-item label="云台支持">{{ deviceInfo.ptzSupport ? '是' : '否' }}</el-form-item>
              <el-form-item label="预置位数量">{{ deviceInfo.presetCount || '-' }}</el-form-item>
              <el-form-item label="变焦倍数">{{ deviceInfo.zoomRatio || '-' }}</el-form-item>
              <el-form-item label="存储方式">{{ getStorageTypeText(deviceInfo.storageType) }}</el-form-item>
              <el-form-item label="录像模式">{{ getRecordModeText(deviceInfo.recordMode) }}</el-form-item>
              <el-form-item label="移动侦测开关">{{ deviceInfo.moveDetect ? '是' : '否' }}</el-form-item>
              <el-form-item label="遮挡报警开关">{{ deviceInfo.coverAlarm ? '是' : '否' }}</el-form-item>
              <el-form-item label="音频支持">{{ deviceInfo.audioSupport ? '是' : '否' }}</el-form-item>
              <el-form-item label="对讲支持">{{ deviceInfo.intercomSupport ? '是' : '否' }}</el-form-item>
              <el-form-item label="供电方式">{{ getPowerTypeText(deviceInfo.powerType) }}</el-form-item>
              <el-form-item label="设备登录用户名">{{ deviceInfo.username || '-' }}</el-form-item>
              <el-form-item label="设备登录密码">********</el-form-item>
              <el-form-item label="RTSP地址">{{ deviceInfo.rtspUrl || '-' }}</el-form-item>
              <el-form-item label="ONVIF地址">{{ deviceInfo.onvifUrl || '-' }}</el-form-item>
              <el-form-item label="所属子系统">{{ deviceInfo.subSystemName || '-' }}</el-form-item>
              <el-form-item label="子系统设备ID">{{ deviceInfo.subSystemDeviceId || '-' }}</el-form-item>
            </template>

            <!-- 门禁参数 -->
            <template v-else-if="deviceInfo.type === 'access'">
              <el-form-item label="门名称">{{ deviceInfo.doorName || '-' }}</el-form-item>
              <el-form-item label="开门延时">{{ deviceInfo.openDelay || '-' }}</el-form-item>
              <el-form-item label="支持认证方式">{{ getAuthMethodText(deviceInfo.authMethod) }}</el-form-item>
              <el-form-item label="门磁检测">{{ deviceInfo.doorSensor ? '是' : '否' }}</el-form-item>
              <el-form-item label="反潜回">{{ deviceInfo.backGuard ? '是' : '否' }}</el-form-item>
              <el-form-item label="互锁">{{ deviceInfo.interlock ? '是' : '否' }}</el-form-item>
              <el-form-item label="常开模式">{{ deviceInfo.alwaysOpen ? '是' : '否' }}</el-form-item>
              <el-form-item label="密码有效期">{{ deviceInfo.passwordExpire || '-' }}</el-form-item>
              <el-form-item label="门禁控制器编号">{{ deviceInfo.controllerNo || '-' }}</el-form-item>
              <el-form-item label="端口号">{{ deviceInfo.port || '-' }}</el-form-item>
              <el-form-item label="韦根格式">{{ getWiegandFormatText(deviceInfo.wiegandFormat) }}</el-form-item>
              <el-form-item label="开门方式">{{ getOpenMethodText(deviceInfo.openMethod) }}</el-form-item>
              <el-form-item label="所属子系统">{{ deviceInfo.subSystemName || '-' }}</el-form-item>
              <el-form-item label="子系统设备ID">{{ deviceInfo.subSystemDeviceId || '-' }}</el-form-item>
            </template>

            <!-- 道闸参数 -->
            <template v-else-if="deviceInfo.type === 'gate'">
              <el-form-item label="道闸类型">{{ getGateTypeText(deviceInfo.gateType) }}</el-form-item>
              <el-form-item label="起落杆时间">{{ deviceInfo.rodTime || '-' }}</el-form-item>
              <el-form-item label="工作模式">{{ getWorkModeText(deviceInfo.workMode) }}</el-form-item>
              <el-form-item label="车检器">{{ deviceInfo.carDetector ? '是' : '否' }}</el-form-item>
              <el-form-item label="防砸功能">{{ deviceInfo.antiCrash ? '是' : '否' }}</el-form-item>
              <el-form-item label="道闸状态">{{ getGateStatusText(deviceInfo.gateStatus) }}</el-form-item>
              <el-form-item label="控制方式">{{ getControlModeText(deviceInfo.controlMode) }}</el-form-item>
              <el-form-item label="关联车牌识别设备ID">{{ deviceInfo.relatedLicenseId || '-' }}</el-form-item>
              <el-form-item label="所属子系统">{{ deviceInfo.subSystemName || '-' }}</el-form-item>
              <el-form-item label="子系统设备ID">{{ deviceInfo.subSystemDeviceId || '-' }}</el-form-item>
            </template>

            <!-- 车牌识别参数 -->
            <template v-else-if="deviceInfo.type === 'license'">
              <el-form-item label="识别率">{{ deviceInfo.recognitionRate || '-' }}</el-form-item>
              <el-form-item label="识别距离">{{ deviceInfo.recognitionDistance || '-' }}</el-form-item>
              <el-form-item label="视频流地址">{{ deviceInfo.streamUrl || '-' }}</el-form-item>
              <el-form-item label="白名单生效开关">{{ deviceInfo.whiteListEnable ? '是' : '否' }}</el-form-item>
              <el-form-item label="计费模板ID">{{ deviceInfo.chargeTemplateId || '-' }}</el-form-item>
              <el-form-item label="出场自动放行开关">{{ deviceInfo.autoPassEnable ? '是' : '否' }}</el-form-item>
              <el-form-item label="所属子系统">{{ deviceInfo.subSystemName || '-' }}</el-form-item>
              <el-form-item label="子系统设备ID">{{ deviceInfo.subSystemDeviceId || '-' }}</el-form-item>
            </template>

            <!-- 红外探测器参数 -->
            <template v-else-if="deviceInfo.type === 'infrared'">
              <el-form-item label="探测距离">{{ deviceInfo.detectionDistance || '-' }}</el-form-item>
              <el-form-item label="防拆功能">{{ deviceInfo.antiTamper ? '是' : '否' }}</el-form-item>
              <el-form-item label="灵敏度">{{ getSensitivityText(deviceInfo.sensitivity) }}</el-form-item>
              <el-form-item label="防宠物">{{ deviceInfo.petImmune ? '是' : '否' }}</el-form-item>
              <el-form-item label="报警方式">{{ getAlarmModeText(deviceInfo.alarmMode) }}</el-form-item>
              <el-form-item label="关联报警主机ID">{{ deviceInfo.relatedAlarmId || '-' }}</el-form-item>
              <el-form-item label="所属子系统">{{ deviceInfo.subSystemName || '-' }}</el-form-item>
              <el-form-item label="子系统设备ID">{{ deviceInfo.subSystemDeviceId || '-' }}</el-form-item>
            </template>

            <!-- 报警主机参数 -->
            <template v-else-if="deviceInfo.type === 'alarm'">
              <el-form-item label="防区数量">{{ deviceInfo.zoneCount || '-' }}</el-form-item>
              <el-form-item label="通讯方式">{{ getCommTypeText(deviceInfo.commType) }}</el-form-item>
              <el-form-item label="布防模式">{{ getArmModeText(deviceInfo.armMode) }}</el-form-item>
              <el-form-item label="报警联动开关">{{ deviceInfo.alarmLinkEnable ? '是' : '否' }}</el-form-item>
              <el-form-item label="报警音量">{{ getVolumeText(deviceInfo.volume) }}</el-form-item>
              <el-form-item label="电话/短信通知开关">{{ deviceInfo.notifyEnable ? '是' : '否' }}</el-form-item>
              <el-form-item label="所属子系统">{{ deviceInfo.subSystemName || '-' }}</el-form-item>
              <el-form-item label="子系统设备ID">{{ deviceInfo.subSystemDeviceId || '-' }}</el-form-item>
            </template>
          </el-form>
        </el-tab-pane>

        <!-- 状态历史 -->
        <el-tab-pane name="history" label="状态历史">
          <el-table v-loading="loading" :data="statusHistory" style="width: 100%">
            <el-table-column prop="id" label="记录ID" width="100" />
            <el-table-column prop="statusType" label="状态类型" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.statusType)">{{ getStatusText(scope.row.statusType) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="statusDesc" label="状态描述" />
            <el-table-column prop="startTime" label="开始时间" width="160" />
            <el-table-column prop="endTime" label="结束时间" width="160" />
            <el-table-column prop="duration" label="持续时长" width="100" />
            <el-table-column prop="alarmLevel" label="告警等级" width="100">
              <template #default="scope">
                <el-tag :type="getAlarmLevelType(scope.row.alarmLevel)">{{ getAlarmLevelText(scope.row.alarmLevel) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="handleStatus" label="处理状态" width="100">
              <template #default="scope">
                <el-tag :type="getHandleStatusType(scope.row.handleStatus)">{{ getHandleStatusText(scope.row.handleStatus) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="handler" label="处理人" width="100" />
            <el-table-column prop="handleRemark" label="处理备注" />
            <el-table-column prop="createTime" label="生成时间" width="160" />
          </el-table>
        </el-tab-pane>

        <!-- 远程控制（安防设备专属） -->
        <el-tab-pane v-if="isSecurityDevice" name="remote" label="远程控制">
          <el-alert title="远程控制功能" type="info" description="此处展示远程控制功能入口，包括设备控制、参数配置等" />
          <el-row :gutter="20" class="mt-4">
            <el-col :span="6">
              <el-card class="box-card" shadow="hover">
                <div class="card-icon">
                  <el-icon :size="40" color="#409eff"><Monitor /></el-icon>
                </div>
                <div class="card-title">设备控制</div>
                <div class="card-desc">远程开关设备、重启设备等</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="box-card" shadow="hover">
                <div class="card-icon">
                  <el-icon :size="40" color="#67c23a"><Setting /></el-icon>
                </div>
                <div class="card-title">参数配置</div>
                <div class="card-desc">修改设备参数、调整设备设置</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="box-card" shadow="hover">
                <div class="card-icon">
                  <el-icon :size="40" color="#e6a23c"><VideoCamera /></el-icon>
                </div>
                <div class="card-title">录像控制</div>
                <div class="card-desc">开始/停止录像、截图等</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="box-card" shadow="hover">
                <div class="card-icon">
                  <el-icon :size="40" color="#f56c6c"><Bell /></el-icon>
                </div>
                <div class="card-title">告警控制</div>
                <div class="card-desc">布防/撤防、告警测试等</div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 操作日志 -->
        <el-tab-pane name="log" label="操作日志">
          <el-table v-loading="loading" :data="operationLog" style="width: 100%">
            <el-table-column prop="id" label="日志ID" width="100" />
            <el-table-column prop="operationType" label="操作类型" width="120" />
            <el-table-column prop="operationDesc" label="操作描述" />
            <el-table-column prop="operator" label="操作人" width="100" />
            <el-table-column prop="operatorIp" label="操作IP" width="140" />
            <el-table-column prop="createTime" label="操作时间" width="160" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup name="DeviceDetail">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Setting, VideoCamera, Bell } from '@element-plus/icons-vue'

// 活动标签页
const activeTab = ref('basic')

// 设备信息
const deviceInfo = ref({
  id: 1,
  name: '园区大门摄像头',
  type: 'camera',
  assetCode: 'ASSET-20240101-001',
  manufacturer: '海康威视',
  model: 'DS-2CD2T42-I',
  sn: 'CAM-20240101-001',
  macAddress: '00:1A:2B:3C:4D:5E',
  ipAddress: '192.168.1.100',
  port: 8080,
  protocol: 'ONVIF',
  area: 'park',
  building: '园区',
  floor: '1',
  installLocation: '园区主入口',
  mapPointId: 'MAP-001',
  installDate: '2024-01-01',
  maintainDate: '2025-01-01',
  owner: '张三',
  phone: '13800138001',
  enabled: '1',
  createTime: '2024-01-01 10:00:00',
  updateTime: '2024-03-01 15:00:00',
  lastSyncTime: '2024-03-10 08:00:00',
  sourceSystem: '安防子系统',
  // 监控摄像头参数
  cameraType: '枪机',
  resolution: '1080P',
  frameRate: 25,
  bitrate: 4096,
  infraredDistance: 30,
  ptzSupport: true,
  presetCount: 8,
  zoomRatio: '3倍',
  storageType: 'nvr',
  recordMode: 'auto',
  moveDetect: true,
  coverAlarm: true,
  audioSupport: true,
  intercomSupport: false,
  powerType: 'poe',
  username: 'admin',
  rtspUrl: 'rtsp://192.168.1.100:554/stream',
  onvifUrl: 'http://192.168.1.100:8080/onvif/device_service',
  subSystemName: '安防子系统',
  subSystemDeviceId: 'SUB-DEV-001'
})

// 状态历史数据
const statusHistory = ref([
  {
    id: 1,
    statusType: 'offline',
    statusDesc: '设备离线',
    startTime: '2024-03-05 14:30:00',
    endTime: '2024-03-05 15:00:00',
    duration: '30分钟',
    alarmLevel: 'general',
    handleStatus: 'handled',
    handler: '李四',
    handleRemark: '网络恢复',
    createTime: '2024-03-05 14:30:00'
  },
  {
    id: 2,
    statusType: 'alarm',
    statusDesc: '移动侦测报警',
    startTime: '2024-03-08 09:15:00',
    endTime: '',
    duration: '进行中',
    alarmLevel: 'serious',
    handleStatus: 'processing',
    handler: '',
    handleRemark: '',
    createTime: '2024-03-08 09:15:00'
  },
  {
    id: 3,
    statusType: 'normal',
    statusDesc: '设备恢复正常',
    startTime: '2024-03-05 15:00:00',
    endTime: '',
    duration: '进行中',
    alarmLevel: 'info',
    handleStatus: 'handled',
    handler: '系统',
    handleRemark: '自动恢复',
    createTime: '2024-03-05 15:00:00'
  }
])

// 操作日志数据
const operationLog = ref([
  {
    id: 1,
    operationType: '启用',
    operationDesc: '启用设备',
    operator: '张三',
    operatorIp: '192.168.1.100',
    createTime: '2024-03-01 10:00:00'
  },
  {
    id: 2,
    operationType: '编辑',
    operationDesc: '编辑设备信息',
    operator: '李四',
    operatorIp: '192.168.1.101',
    createTime: '2024-03-02 15:30:00'
  },
  {
    id: 3,
    operationType: '远程控制',
    operationDesc: '远程重启设备',
    operator: '王五',
    operatorIp: '192.168.1.102',
    createTime: '2024-03-03 09:00:00'
  }
])

// 加载状态
const loading = ref(false)

// 计算属性
const isSecurityDevice = ref(['camera', 'access', 'gate', 'license', 'infrared', 'alarm'].includes(deviceInfo.value.type))

// 方法
const getDeviceTypeText = (type) => {
  switch (type) {
    case 'camera': return '监控摄像头'
    case 'access': return '门禁'
    case 'gate': return '道闸'
    case 'license': return '车牌识别'
    case 'infrared': return '红外探测器'
    case 'alarm': return '报警主机'
    default: return type
  }
}

const getAreaText = (area) => {
  switch (area) {
    case 'park': return '园区'
    case 'building': return '楼栋'
    case 'floor': return '楼层'
    case 'zone': return '具体区域'
    default: return area
  }
}

const getStorageTypeText = (type) => {
  switch (type) {
    case 'nvr': return 'NVR'
    case 'cloud': return '云存储'
    default: return type
  }
}

const getRecordModeText = (mode) => {
  switch (mode) {
    case 'manual': return '手动'
    case 'auto': return '自动'
    case 'event': return '事件触发'
    default: return mode
  }
}

const getPowerTypeText = (type) => {
  switch (type) {
    case 'poe': return 'POE'
    case 'dc12v': return 'DC12V'
    default: return type
  }
}

const getAuthMethodText = (method) => {
  const methods = []
  if (method.includes('card')) methods.push('卡')
  if (method.includes('password')) methods.push('密码')
  if (method.includes('face')) methods.push('人脸')
  if (method.includes('fingerprint')) methods.push('指纹')
  return methods.join('/')
}

const getWiegandFormatText = (format) => {
  switch (format) {
    case '26': return 'Wiegand26'
    case '34': return 'Wiegand34'
    default: return format
  }
}

const getOpenMethodText = (method) => {
  const methods = []
  if (method.includes('remote')) methods.push('远程')
  if (method.includes('card')) methods.push('刷卡')
  if (method.includes('password')) methods.push('密码')
  if (method.includes('face')) methods.push('人脸')
  return methods.join('/')
}

const getGateTypeText = (type) => {
  switch (type) {
    case 'straight': return '直杆'
    case 'curved': return '曲杆'
    case '栅栏': return '栅栏'
    default: return type
  }
}

const getWorkModeText = (mode) => {
  switch (mode) {
    case 'manual': return '手动'
    case 'auto': return '自动'
    case 'remote': return '远程'
    default: return mode
  }
}

const getGateStatusText = (status) => {
  switch (status) {
    case 'close': return '关'
    case 'open': return '开'
    case 'fault': return '故障'
    default: return status
  }
}

const getControlModeText = (mode) => {
  switch (mode) {
    case 'relay': return '继电器'
    case 'http': return 'HTTP'
    case 'tcp': return 'TCP'
    default: return mode
  }
}

const getSensitivityText = (level) => {
  switch (level) {
    case 'high': return '高'
    case 'medium': return '中'
    case 'low': return '低'
    default: return level
  }
}

const getAlarmModeText = (mode) => {
  switch (mode) {
    case 'normally_open': return '常开'
    case 'normally_closed': return '常闭'
    default: return mode
  }
}

const getCommTypeText = (type) => {
  switch (type) {
    case 'ethernet': return '网线'
    case '485': return '485'
    case 'lora': return 'LoRa'
    default: return type
  }
}

const getArmModeText = (mode) => {
  switch (mode) {
    case 'at_home': return '在家'
    case 'away': return '离家'
    case 'sleep': return '睡眠'
    default: return mode
  }
}

const getVolumeText = (level) => {
  switch (level) {
    case 'high': return '高'
    case 'medium': return '中'
    case 'low': return '低'
    default: return level
  }
}

const getStatusType = (type) => {
  switch (type) {
    case 'normal': return 'success'
    case 'offline': return 'warning'
    case 'alarm': return 'danger'
    case 'fault': return 'info'
    default: return ''
  }
}

const getStatusText = (type) => {
  switch (type) {
    case 'normal': return '正常'
    case 'offline': return '离线'
    case 'alarm': return '报警'
    case 'fault': return '故障'
    default: return type
  }
}

const getAlarmLevelType = (level) => {
  switch (level) {
    case 'info': return 'info'
    case 'general': return 'warning'
    case 'serious': return 'danger'
    default: return ''
  }
}

const getAlarmLevelText = (level) => {
  switch (level) {
    case 'info': return '提示'
    case 'general': return '一般'
    case 'serious': return '严重'
    default: return level
  }
}

const getHandleStatusType = (status) => {
  switch (status) {
    case 'unhandled': return 'info'
    case 'processing': return 'warning'
    case 'handled': return 'success'
    case 'ignored': return 'info'
    default: return ''
  }
}

const getHandleStatusText = (status) => {
  switch (status) {
    case 'unhandled': return '未处理'
    case 'processing': return '处理中'
    case 'handled': return '已处理'
    case 'ignored': return '已忽略'
    default: return status
  }
}

// 生命周期
onMounted(() => {
  // 模拟加载数据
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 500)
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.box-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.box-card:hover {
  transform: translateY(-5px);
}

.card-icon {
  margin-bottom: 10px;
}

.card-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.card-desc {
  color: #666;
  font-size: 12px;
}
</style>
