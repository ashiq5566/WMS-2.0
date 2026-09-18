<script setup lang="ts">
import { defineEmits } from 'vue';
import Button from 'primevue/button';
import { useTheme } from '@/utils/theme';
import Breadcrumbs from '@/components/Breadcrumbs.vue';

const emit = defineEmits(['buttonClicked']);
const { isDarkMode, toggleTheme } = useTheme();

const handleClick = () => {
  emit('buttonClicked');
};
</script>

<template>
  <div
    class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm rounded-2xl px-3.5 py-2.5 sm:px-4 sm:py-2.5 transition-colors flex items-center justify-between gap-3"
  >
    <!-- Left Side: Mobile Drawer Toggle & Breadcrumbs -->
    <div class="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
      <!-- Mobile Drawer Toggle (Only visible on mobile screens when sidebar is hidden) -->
      <Button
        icon="pi pi-bars"
        severity="secondary"
        text
        rounded
        class="!w-8 !h-8 !p-0 text-slate-700 dark:text-slate-200 lg:!hidden shrink-0"
        aria-label="Toggle Navigation Menu"
        @click="handleClick"
      />

      <!-- Breadcrumbs Trail -->
      <Breadcrumbs />
    </div>

    <!-- Right Side: Dark Mode Switch Icon -->
    <div class="flex items-center gap-2 shrink-0 ml-auto">
      <Button
        :icon="isDarkMode ? 'pi pi-sun' : 'pi pi-moon'"
        :aria-label="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        :title="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        severity="secondary"
        text
        rounded
        class="!w-8 !h-8 !p-0 text-slate-600 dark:text-slate-300 hover:!bg-slate-100 dark:hover:!bg-slate-800 transition-all duration-200 hover:scale-105 active:scale-95"
        @click="toggleTheme"
      />
    </div>
  </div>
</template>

<style scoped></style>

