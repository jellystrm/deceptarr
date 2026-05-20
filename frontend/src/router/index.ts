import { createRouter, createWebHistory } from 'vue-router'
import Downloads from '../views/Downloads.vue'
import LinkGrabber from '../views/LinkGrabber.vue'
import Sources from '../views/Sources.vue'
import Settings from '../views/Settings.vue'
import Test from '../views/Test.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/downloads' },
    { path: '/downloads', component: Downloads },
    { path: '/linkgrabber', component: LinkGrabber },
    { path: '/sources', component: Sources },
    { path: '/settings', component: Settings },
    { path: '/test', component: Test },
  ],
})

export default router
