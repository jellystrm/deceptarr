import { createRouter, createWebHistory } from 'vue-router'
import Downloads from '../views/Downloads.vue'
import LinkGrabber from '../views/LinkGrabber.vue'
import Sources from '../views/Sources.vue'
import Settings from '../views/Settings.vue'
import HealthMonitor from '../views/HealthMonitor.vue'
import Login from '../views/Login.vue'
import Setup from '../views/Setup.vue'
import { getAuthStatus } from '../api'

const AUTH_ROUTES = ['/login', '/setup']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',            redirect: '/downloads' },
    { path: '/downloads',   component: Downloads },
    { path: '/linkgrabber', component: LinkGrabber },
    { path: '/sources',     component: Sources },
    { path: '/settings',    component: Settings },
    { path: '/health-monitor', component: HealthMonitor },
    { path: '/test',        redirect: '/health-monitor' },
    { path: '/login',       component: Login },
    { path: '/setup',       component: Setup },
  ],
})

router.beforeEach(async (to) => {
  // Auth pages don't need a guard themselves
  if (AUTH_ROUTES.includes(to.path)) return true

  try {
    const { initialized, authenticated } = await getAuthStatus()
    if (!initialized)   return '/setup'
    if (!authenticated) return `/login?next=${encodeURIComponent(to.fullPath)}`
  } catch {
    // If the status call fails (e.g. backend down) let the page load anyway
  }
  return true
})

export default router
