<script setup>
import { ref, watch } from "vue";
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
</script>

<template>
    <div class="flex">
        <div class="lg:block hidden p-4 w-64 h-full fixed top-0 left-0 shadow-lg">
            <div class="text-lg font-semibold mb-4">Sidebar</div>
            <RouterLink to="/" class="block mb-2 p-2 rounded">Home</RouterLink>
            <RouterLink to="/about" class="block mb-2 p-2 rounded">About
            </RouterLink>
            <Button @click="handleLogout" icon="pi pi-sign-out" />
        </div>

        <div>
            <Sidebar v-model:visible="internalVisible" header="Sidebar">
                <RouterLink to="/" class="block mb-2 p-2 rounded">Home
                </RouterLink>
                <RouterLink to="/about" class="block mb-2 p-2 rounded">About
                </RouterLink>
                <Button @click="handleLogout" icon="pi pi-sign-out" />
            </Sidebar>
        </div>

        <!-- <div class="lg:hidden absolute top-0 left-0 m-4">
            <Button icon="pi pi-arrow-right" @click="visible = true" />
        </div> -->
    </div>
</template>
