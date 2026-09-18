<script setup lang="ts">
import { computed, ref, onBeforeMount } from 'vue';
import { useRouter } from 'vue-router';
import SideBar from "../components/SideBar.vue";
import Header from "@/components/Header.vue";
import store from "../stores/stores.js";

const isAuthenticated = computed(() => store.state.isAuthenticated);
const visible = ref(false);
const isCollapsed = ref(false);
const router = useRouter();

const handleClick = () => {
    visible.value = !visible.value;
};

onBeforeMount(() => {
    if (!isAuthenticated.value) {
        router.push('/login');
    }
});
</script>

<template>
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 transition-colors duration-200 flex">
        <!-- Sidebar Navigation -->
        <div v-if="isAuthenticated">
            <SideBar
                :visible="visible"
                :collapsed="isCollapsed"
                @update:visible="visible = $event"
                @update:collapsed="isCollapsed = $event"
            />
        </div>

        <!-- Main Content Area -->
        <div
            :class="[
                isAuthenticated ? (isCollapsed ? 'lg:pl-20' : 'lg:pl-64') : '',
                'flex-1 min-w-0 flex flex-col transition-all duration-300 ease-in-out'
            ]"
        >
            <!-- Sticky Header -->
            <header v-if="isAuthenticated" class="sticky top-0 z-10 px-3.5 sm:px-6 lg:px-8 pt-3 sm:pt-4">
                <Header @buttonClicked="handleClick" />
            </header>

            <!-- Page Content -->
            <main class="flex-1 px-3.5 sm:px-6 lg:px-8 pt-3 sm:pt-4 pb-8">
                <RouterView />
            </main>
        </div>
    </div>
</template>