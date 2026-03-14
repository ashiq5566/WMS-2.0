<template>
    <div class="container max-w-md mt-20 flex flex-col gap-4 items-center">
        <h1 class="text-2xl font-bold mb-6">Register</h1>

        <input v-model="form.username" placeholder="Username" class="input border p-2 rounded" />
        <input v-model="form.email" placeholder="Email" class="input border p-2 rounded" />
        <input v-model="form.password" type="password" placeholder="Password" class="input border p-2 rounded" />

        <button @click="register" class="bg-brand-primary p-2 text-white mt-4 rounded">
            Create Account
        </button>
    </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
const { $axios } = useNuxtApp();


const router = useRouter();
const form = ref({ username: "", email: "", password: "" });

const register = async () => {
    await $axios.post("/api/auth/register/", form.value);
    router.push("/login");
};
</script>