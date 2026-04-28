import auth from '@/plugins/auth'
import router, { constantRoutes, dynamicRoutes } from '@/router'
import { getRouters } from '@/api/menu'
import Layout from '@/layout/index'
import ParentView from '@/components/ParentView'
import InnerLink from '@/layout/components/InnerLink'

// 匹配views里面所有的.vue文件
const modules = import.meta.glob('./../../views/**/*.vue')

const usePermissionStore = defineStore(
  'permission',
  {
    state: () => ({
      routes: [],
      addRoutes: [],
      defaultRoutes: [],
      topbarRouters: [],
      sidebarRouters: []
    }),
    actions: {
      setRoutes(routes) {
        this.addRoutes = routes
        this.routes = constantRoutes.concat(routes)
      },
      setDefaultRoutes(routes) {
        this.defaultRoutes = constantRoutes.concat(routes)
      },
      setTopbarRoutes(routes) {
        this.topbarRouters = routes
      },
      setSidebarRouters(routes) {
        this.sidebarRouters = routes
      },
      generateRoutes(roles) {
        return new Promise(resolve => {
          // 向后端请求路由数据
          getRouters().then(res => {
            const sdata = JSON.parse(JSON.stringify(res.data))
            const rdata = JSON.parse(JSON.stringify(res.data))
            const defaultData = JSON.parse(JSON.stringify(res.data))
            const sidebarRoutes = filterAsyncRouter(sdata)
            const rewriteRoutes = filterAsyncRouter(rdata, false, true)
            const defaultRoutes = filterAsyncRouter(defaultData)
            const asyncRoutes = filterDynamicRoutes(dynamicRoutes)
            asyncRoutes.forEach(route => { router.addRoute(route) })
            
            // 添加园区管理相关菜单（每个都是父目录）
            const assetRoute = {
              path: '/asset',
              component: Layout,
              alwaysShow: true,
              permissions: ['parking:asset:list'],
              meta: {
                title: '园区资产管理',
                icon: 'tree'
              },
              children: [
                {
                  path: 'device',
                  component: () => import('@/views/asset/device'),
                  name: 'DeviceLedger',
                  meta: {
                    title: '设备台账管理',
                    icon: 'tree',
                    noCache: false,
                    link: null
                  }
                },
                {
                  path: 'device-detail',
                  component: () => import('@/views/asset/device-detail'),
                  name: 'DeviceDetail',
                  meta: {
                    title: '设备详情',
                    icon: 'info',
                    noCache: true,
                    link: null
                  }
                }
              ]
            }
            
            const securityRoute = {
              path: '/security',
              component: Layout,
              alwaysShow: true,
              permissions: ['parking:security:list'],
              meta: {
                title: '智慧安防',
                icon: 'lock'
              },
              children: [
                {
                  path: 'video-monitor',
                  component: () => import('@/views/security/video-monitor'),
                  name: 'VideoMonitor',
                  meta: {
                    title: '视频监控',
                    icon: 'video-play',
                    noCache: false,
                    link: null
                  }
                },
                {
                  path: 'device-monitor',
                  component: () => import('@/views/security/device-monitor'),
                  name: 'DeviceMonitor',
                  meta: {
                    title: '安防设备状态监控',
                    icon: 'monitor',
                    noCache: false,
                    link: null
                  }
                }
              ]
            }
            
            const maintenanceRoute = {
              path: '/maintenance',
              component: Layout,
              alwaysShow: true,
              permissions: ['parking:maintenance:list'],
              meta: {
                title: '运维管理',
                icon: 'tool'
              },
              children: []
            }
            
            const energyRoute = {
              path: '/energy',
              component: Layout,
              alwaysShow: true,
              permissions: ['parking:energy:list'],
              meta: {
                title: '能源管理',
                icon: 'data-line'
              },
              children: []
            }
            
            const environmentRoute = {
              path: '/environment',
              component: Layout,
              alwaysShow: true,
              permissions: ['parking:environment:list'],
              meta: {
                title: '环境管理',
                icon: 'environment'
              },
              children: []
            }
            
            const tenantRoute = {
              path: '/tenant',
              component: Layout,
              alwaysShow: true,
              permissions: ['parking:tenant:list'],
              meta: {
                title: '招商与租户管理',
                icon: 'peoples'
              },
              children: []
            }
            
            const bimRoute = {
              path: '/bim',
              component: Layout,
              alwaysShow: true,
              permissions: ['parking:bim:list'],
              meta: {
                title: '数字孪生+BIM管理',
                icon: 'building'
              },
              children: []
            }
            
            // 将所有菜单添加到路由数据中
            const parkingRoutes = [assetRoute, securityRoute, maintenanceRoute, energyRoute, environmentRoute, tenantRoute, bimRoute]
            parkingRoutes.forEach(route => {
              sidebarRoutes.push(route)
              rewriteRoutes.push(route)
              defaultRoutes.push(route)
              router.addRoute(route)
            })
            
            this.setRoutes(rewriteRoutes)
            this.setSidebarRouters(constantRoutes.concat(sidebarRoutes))
            this.setDefaultRoutes(sidebarRoutes)
            this.setTopbarRoutes(defaultRoutes)
            resolve(rewriteRoutes)
          })
        })
      }
    }
  })

// 遍历后台传来的路由字符串，转换为组件对象
function filterAsyncRouter(asyncRouterMap, lastRouter = false, type = false) {
  return asyncRouterMap.filter(route => {
    if (type && route.children) {
      route.children = filterChildren(route.children)
    }
    if (route.component) {
      // Layout ParentView 组件特殊处理
      if (route.component === 'Layout') {
        route.component = Layout
      } else if (route.component === 'ParentView') {
        route.component = ParentView
      } else if (route.component === 'InnerLink') {
        route.component = InnerLink
      } else {
        route.component = loadView(route.component)
      }
    }
    if (route.children != null && route.children && route.children.length) {
      route.children = filterAsyncRouter(route.children, route, type)
    } else {
      delete route['children']
      delete route['redirect']
    }
    return true
  })
}

function filterChildren(childrenMap, lastRouter = false) {
  var children = []
  childrenMap.forEach(el => {
    el.path = lastRouter ? lastRouter.path + '/' + el.path : el.path
    if (el.children && el.children.length && el.component === 'ParentView') {
      children = children.concat(filterChildren(el.children, el))
    } else {
      children.push(el)
    }
  })
  return children
}

// 动态路由遍历，验证是否具备权限
export function filterDynamicRoutes(routes) {
  const res = []
  routes.forEach(route => {
    if (route.permissions) {
      if (auth.hasPermiOr(route.permissions)) {
        res.push(route)
      }
    } else if (route.roles) {
      if (auth.hasRoleOr(route.roles)) {
        res.push(route)
      }
    }
  })
  return res
}

export const loadView = (view) => {
  let res
  for (const path in modules) {
    const dir = path.split('views/')[1].split('.vue')[0]
    if (dir === view) {
      res = () => modules[path]()
    }
  }
  // 特殊处理empty组件
  if (view === 'empty') {
    res = () => import('@/views/empty.vue')
  }
  return res
}

export default usePermissionStore
