import { createRouter, createWebHashHistory } from 'vue-router'
import { setupLayouts } from 'virtual:generated-layouts'
import generatedRoutes from '~pages'
import Layout from '@/layouts/Layout.vue';
import LoginView from '@/components/auth/Login.vue';


const routes = setupLayouts(generatedRoutes)

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  // routes: [
  //   {
  //     path: '/',
  //     name: 'home',
  //     component: HomeView,
  //     meta: { requiresAuth: true }
  //   },
  //   {
  //     path: '/login',
  //     name: 'login',
  //     component: LoginView
  //   },
  //   {
  //     path: '/stakeholders',
  //     name: 'stakeholders',
  //     component: Stakeholders,
  //     meta: { requiresAuth: true }

  //   }
  // ]
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/',
      component: Layout,
      children: [
        ...setupLayouts(routes),
      ]
    }
  ]
})


export default router
