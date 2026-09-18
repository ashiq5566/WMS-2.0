<script setup>
import { ref, watch, computed } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import Drawer from 'primevue/drawer';
import Button from 'primevue/button';
import store from '../stores/stores.js';

const router = useRouter();
const route = useRoute();
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  collapsed: {
    type: Boolean,
    default: false
  }
});
const emit = defineEmits(['update:visible', 'update:collapsed']);

const internalVisible = ref(props.visible);
const isCollapsed = ref(props.collapsed || false);

watch(
  () => props.visible,
  (newValue) => {
    internalVisible.value = newValue;
  }
);

watch(internalVisible, (newValue) => {
  emit('update:visible', newValue);
});

watch(
  () => props.collapsed,
  (newValue) => {
    isCollapsed.value = newValue;
  }
);

const handleLogout = async () => {
  store.methods.logout();
  router.push('/login');
};

const handleNavClick = () => {
  internalVisible.value = false;
};

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
  emit('update:collapsed', isCollapsed.value);
};

const userDisplayName = computed(() => {
  try {
    const raw = localStorage.getItem('user_data');
    if (!raw) return 'Operations Staff';
    const parsed = typeof raw === 'string' && raw.startsWith('{') ? JSON.parse(raw) : null;
    return parsed?.username || parsed?.name || 'Operations Staff';
  } catch {
    return 'Operations Staff';
  }
});

const navSections = [
  {
    title: 'Overview',
    items: [
      { path: '/home', name: 'Dashboard', icon: 'pi pi-chart-pie' }
    ]
  },
  {
    title: 'Inventory & Operations',
    items: [
      { path: '/stocks', name: 'Stock', icon: 'pi pi-box' },
      { path: '/orders', name: 'Orders', icon: 'pi pi-shopping-bag' },
      { path: '/returns', name: 'Returns', icon: 'pi pi-replay' }
    ]
  },
  {
    title: 'Directory & Finance',
    items: [
      { path: '/stakeholders', name: 'Stakeholders', icon: 'pi pi-users' },
      { path: '/payments', name: 'Payments', icon: 'pi pi-wallet' }
    ]
  }
];

const isItemActive = (itemPath) => {
  if (itemPath === '/home') {
    return route.path === '/home' || route.path === '/';
  }
  return route.path === itemPath || route.path.startsWith(itemPath + '/');
};
</script>

<template>
  <div>
    <!-- Desktop Persistent Sidebar -->
    <aside
      class="hidden lg:flex flex-col fixed top-0 left-0 h-screen z-20 bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800/80 transition-all duration-300 ease-in-out shadow-sm"
      :class="isCollapsed ? 'w-20' : 'w-64'"
    >
      <!-- Brand Header -->
      <div class="h-16 px-4 flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60">
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="w-9 h-9 min-w-[36px] rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/30">
            <i class="pi pi-box text-lg"></i>
          </div>
          <div v-show="!isCollapsed" class="flex flex-col overflow-hidden transition-opacity duration-200">
            <span class="text-base font-bold tracking-tight text-slate-900 dark:text-white truncate">CoreWMS</span>
            <span class="text-[10px] uppercase font-semibold tracking-wider text-indigo-600 dark:text-indigo-400 truncate">Enterprise</span>
          </div>
        </div>

        <button
          type="button"
          @click="toggleCollapse"
          :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          class="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center transition-colors"
        >
          <i :class="isCollapsed ? 'pi pi-angle-double-right text-xs' : 'pi pi-angle-double-left text-xs'"></i>
        </button>
      </div>

      <!-- Navigation Links -->
      <div class="flex-1 px-3 py-4 overflow-y-auto space-y-6">
        <div v-for="section in navSections" :key="section.title" class="space-y-1">
          <!-- Section Label (Only visible when expanded) -->
          <div
            v-show="!isCollapsed"
            class="px-3 pb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500"
          >
            {{ section.title }}
          </div>

          <!-- Section Items -->
          <div class="space-y-1">
            <RouterLink
              v-for="item in section.items"
              :key="item.path"
              :to="item.path"
              :title="isCollapsed ? item.name : ''"
              class="group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 relative"
              :class="
                isItemActive(item.path)
                  ? 'bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 font-semibold shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100/80 dark:hover:bg-slate-800/60'
              "
            >
              <!-- Active Left Border Bar -->
              <span
                v-if="isItemActive(item.path)"
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-indigo-600 dark:bg-indigo-500 rounded-r"
              ></span>

              <i
                :class="[item.icon, 'text-base transition-colors']"
                :style="{ minWidth: '20px', textAlign: 'center' }"
              ></i>

              <span v-show="!isCollapsed" class="truncate transition-opacity duration-200">
                {{ item.name }}
              </span>
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- Footer / User Profile & Logout -->
      <div class="p-3 border-t border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-900/50">
        <div class="flex items-center justify-between gap-2">
          <!-- User Info (Hidden when collapsed) -->
          <div v-show="!isCollapsed" class="flex items-center gap-2.5 min-w-0">
            <div class="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center text-xs font-bold">
              <i class="pi pi-user text-xs"></i>
            </div>
            <div class="min-w-0">
              <p class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate leading-tight">
                {{ userDisplayName }}
              </p>
              <p class="text-[10px] text-slate-400 dark:text-slate-500 truncate">
                Staff Account
              </p>
            </div>
          </div>

          <!-- Sign Out Button -->
          <Button
            @click="handleLogout"
            icon="pi pi-sign-out"
            severity="danger"
            text
            rounded
            :title="'Sign out'"
            class="!w-9 !h-9 !p-0 !text-slate-500 hover:!text-rose-600 hover:!bg-rose-50 dark:hover:!bg-rose-950/40 dark:!text-slate-400 dark:hover:!text-rose-400 transition-colors"
          />
        </div>
      </div>
    </aside>

    <!-- Mobile Drawer Sidebar -->
    <Drawer
      v-model:visible="internalVisible"
      class="!w-72 !p-0 dark:!bg-slate-900 dark:!text-slate-100"
    >
      <template #header>
        <div class="flex items-center gap-3 py-1">
          <div class="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/30">
            <i class="pi pi-box text-lg"></i>
          </div>
          <div>
            <span class="text-base font-bold tracking-tight text-slate-900 dark:text-white">CoreWMS</span>
            <span class="ml-1.5 text-[10px] uppercase font-semibold tracking-wider text-indigo-600 dark:text-indigo-400">Portal</span>
          </div>
        </div>
      </template>

      <!-- Mobile Nav Content -->
      <div class="flex flex-col h-full justify-between">
        <div class="py-2 space-y-6">
          <div v-for="section in navSections" :key="section.title" class="space-y-1">
            <div class="px-3 pb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {{ section.title }}
            </div>
            <div class="space-y-1">
              <RouterLink
                v-for="item in section.items"
                :key="item.path"
                :to="item.path"
                @click="handleNavClick"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors"
                :class="
                  isItemActive(item.path)
                    ? 'bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800'
                "
              >
                <i :class="[item.icon, 'text-base']"></i>
                <span>{{ item.name }}</span>
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- Mobile Sign Out -->
        <div class="pt-4 pb-2 border-t border-slate-100 dark:border-slate-800">
          <Button
            @click="handleLogout"
            label="Sign Out"
            icon="pi pi-sign-out"
            severity="danger"
            outlined
            class="w-full !rounded-xl !py-2.5 !text-sm"
          />
        </div>
      </div>
    </Drawer>
  </div>
</template>
