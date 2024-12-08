<script setup lang="ts">
import { computed, ref, onBeforeMount } from 'vue'
import { useRouter } from 'vue-router';
import SideBar from "../components/SideBar.vue"
import Header from "@/components/Header.vue"
import store from "../stores/stores.js"

const isAuthenticated = computed(() => store.state.isAuthenticated);
const visible = ref(false);
const router = useRouter();

const handleClick = () => {
    visible.value = !visible.value;
}
onBeforeMount(() => {
    if (!isAuthenticated.value) {
        router.push('/login');
    }
});
console.log(isAuthenticated.value, "================================");

</script>

<template>
    <div class="flex flex-col lg:relative">
        <div v-if="isAuthenticated" class="sticky top-0 ml-0 mt-1 z-10 lg:ml-72 lg:mt-4 mr-2">
            <Header @buttonClicked="handleClick" />
        </div>
        <div class="flex">
            <div v-if="isAuthenticated">
                <SideBar :visible="visible" />
            </div>
            <div :class="isAuthenticated ? 'ml-2 pt-12 w-full mr-2 lg:ml-72' : 'w-full'">
                <RouterView />
            </div>
        </div>
    </div>
</template>