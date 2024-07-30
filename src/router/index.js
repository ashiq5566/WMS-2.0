import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import Stakeholders from '../components/accounts/StakeHolders.vue'
import LoginView from '../components/auth/Login.vue'
import store from '../stores/stores.js';


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/stakeholders',
      name: 'stakeholders',
      component: Stakeholders,
      meta: { requiresAuth: true }

    }
  ]
})


export default router
