<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { resolveBreadcrumbs } from '@/utils/breadcrumbs';

const route = useRoute();
const breadcrumbs = computed(() => resolveBreadcrumbs(route.path, route.params));
</script>

<template>
  <nav aria-label="Breadcrumb" class="min-w-0 overflow-hidden flex items-center">
    <ol class="flex items-center gap-1 sm:gap-1.5 text-xs text-slate-500 dark:text-slate-400">
      <li
        v-for="(crumb, idx) in breadcrumbs"
        :key="crumb.to + idx"
        class="flex items-center gap-1 sm:gap-1.5 min-w-0"
      >
        <!-- Separator -->
        <i
          v-if="idx > 0"
          class="pi pi-angle-right text-[10px] text-slate-400 dark:text-slate-600 shrink-0"
        ></i>

        <!-- Clickable Ancestor Link -->
        <router-link
          v-if="!crumb.isCurrent"
          :to="crumb.to"
          class="flex items-center gap-1.5 font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 transition-colors shrink-0"
        >
          <i v-if="crumb.icon" :class="[crumb.icon, 'text-xs']"></i>
          <span :class="idx === 0 && breadcrumbs.length > 1 ? 'hidden sm:inline' : ''">
            {{ crumb.label }}
          </span>
        </router-link>

        <!-- Current Page Indicator -->
        <span
          v-else
          class="flex items-center gap-1.5 font-semibold text-slate-900 dark:text-white truncate"
          aria-current="page"
        >
          <i
            v-if="crumb.icon"
            :class="[crumb.icon, 'text-xs text-indigo-600 dark:text-indigo-400 shrink-0']"
          ></i>
          <span class="truncate">{{ crumb.label }}</span>
        </span>
      </li>
    </ol>
  </nav>
</template>

<style scoped></style>
