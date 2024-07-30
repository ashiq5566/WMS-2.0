<script setup>
import { ref, watch, defineEmits } from "vue";
import { RouterLink, RouterView, useRouter } from 'vue-router'
import Sidebar from "primevue/sidebar";
import store from "../stores/stores.js"

const router = useRouter();
const props = defineProps(['visible']);
const emit = defineEmits(['update:visible']);

const internalVisible = ref(props.visible);

watch(() => props.visible, (newValue) => {
    internalVisible.value = newValue;
});

const handleLogout = async () => {
    store.methods.logout();
    router.push('/login');
};

const routes = [
    { path: '/', name: 'Home' },
    { path: '/stakeholders', name: 'Stakeholders' }
]

</script>

<template>
    <div class="flex">
        <div class="lg:block hidden p-4 w-64 h-full fixed top-0 left-0 shadow-lg">
            <div class="mb-4">
                <img src="../assets/logo.webp" alt="">
            </div>
            <div v-for="route in routes" :key="route.path">
                <RouterLink :to="route.path" class="block mb-2 p-2 rounded">{{ route.name }}</RouterLink>
            </div>
            <Button @click="handleLogout" icon="pi pi-sign-out" />
        </div>

        <div>
            <Sidebar v-model:visible="internalVisible" header="Sidebar">
                <div v-for="route in routes" :key="route.path">
                    <RouterLink :to="route.path" class="block mb-2 p-2 rounded">{{ route.name }}</RouterLink>
                </div>
                <Button @click="handleLogout" icon="pi pi-sign-out" />
            </Sidebar>
        </div>
    </div>
</template>
