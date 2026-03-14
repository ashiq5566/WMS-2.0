<template>
    <div class="container max-w-md mt-20 flex flex-col gap-4 items-center">
        <h1 class="text-2xl font-bold mb-6">Login</h1>

        <input v-model="form.username" placeholder="Username" class="input border p-2 rounded" />
        <input v-model="form.password" type="password" placeholder="Password" class="input border p-2 rounded" />

        <button @click="login" class="bg-brand-primary mt-4 p-2 text-white rounded ">
            Login
        </button>

        <p class="mt-4 text-sm text-center text-gray-500">
            Don’t have an account?
            <NuxtLink to="/register" class="text-brand-primary hover:underline font-medium">
                Create one
            </NuxtLink>
        </p>
    </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
const router = useRouter();
const form = ref({ username: "", password: "" });

const { $axios } = useNuxtApp();

const login = async () => {
    const res = await $axios.post("/api/auth/login/", {
        username: form.value.username,
        password: form.value.password,
    });

    // Store tokens in cookies (SSR-safe)
    const access = useCookie("access");
    const refresh = useCookie("refresh");

    access.value = res.data.access;
    refresh.value = res.data.refresh;

    navigateTo("/");
};
</script>