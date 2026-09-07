import { createRouter, createWebHashHistory } from 'vue-router'
import { setupLayouts } from 'virtual:generated-layouts'
import generatedRoutes from '~pages'
import Layout from '@/layouts/Layout.vue'
import LoginView from '@/components/auth/Login.vue'
import { resolveRouteMeta, setPageTitle } from '@/utils/meta'

// Enrich generated routes with page titles and metadata
const enrichedRoutes = generatedRoutes.map((route) => {
  const meta = resolveRouteMeta(route.path)
  return {
    ...route,
    meta: {
      ...route.meta,
      ...meta
    }
  }
})

const routes = setupLayouts(enrichedRoutes)

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        title: 'Staff Login',
        description: 'Secure authentication portal for CoreWMS warehouse administrators and staff members.'
      }
    },
    {
      path: '/',
      component: Layout,
      children: [...routes]
    }
  ]
})

// Dynamic title and meta tag synchronizer on every route transition
router.afterEach((to) => {
  const meta = resolveRouteMeta(to.path, to.params)
  const title = to.meta?.title || meta.title
  const description = to.meta?.description || meta.description
  setPageTitle(title, description)
})

export default router
