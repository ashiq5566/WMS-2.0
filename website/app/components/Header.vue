<template>
    <header class="w-full bg-white shadow sticky top-0 z-50">
        <div class="container flex justify-between items-center py-4">

            <!-- Logo / Brand -->
            <NuxtLink to="/" class="text-2xl font-bold text-brand-primary">
                KC Home Bazaar
            </NuxtLink>

            <!-- Desktop Navigation -->
            <nav class="hidden md:flex gap-8">
                <NuxtLink to="/" class="nav-link">Home</NuxtLink>
                <NuxtLink to="/products" class="nav-link">Products</NuxtLink>
                <NuxtLink to="/best-sellers" class="nav-link">Best Sellers</NuxtLink>
                <NuxtLink to="/about" class="nav-link">About</NuxtLink>
                <NuxtLink to="/contact" class="nav-link">Contact</NuxtLink>
            </nav>

            <!-- Actions -->
            <div class="hidden md:flex items-center gap-4">
                <NuxtLink to="/login"
                    class="px-4 py-2 text-sm rounded-lg text-brand-primary border border-brand-primary hover:bg-brand-primary hover:text-white transition">
                    Login
                </NuxtLink>

                <NuxtLink to="/cart"
                    class="relative px-4 py-2 text-sm rounded-lg bg-brand-primary text-white hover:bg-brand-primaryLight transition">
                    Cart
                </NuxtLink>
            </div>

            <!-- Mobile Menu Button -->
            <button class="md:hidden text-3xl" @click="open = !open">
                ☰
            </button>
        </div>

        <!-- Mobile Menu -->
        <div v-if="open" class="md:hidden bg-white shadow-inner px-6 py-4 space-y-4">
            <NuxtLink to="/" class="mobile-link">Home</NuxtLink>
            <NuxtLink to="/products" class="mobile-link">Products</NuxtLink>
            <NuxtLink to="/best-sellers" class="mobile-link">Best Sellers</NuxtLink>
            <NuxtLink to="/about" class="mobile-link">About</NuxtLink>
            <NuxtLink to="/contact" class="mobile-link">Contact</NuxtLink>

            <NuxtLink to="/login"
                class="block text-brand-primary border border-brand-primary rounded-lg px-4 py-2 text-center">
                Login
            </NuxtLink>
            <NuxtLink to="/cart" class="block bg-brand-primary text-white rounded-lg px-4 py-2 text-center">
                Cart
            </NuxtLink>
        </div>
    </header>
</template>

<script setup>
import { ref } from "vue";
const open = ref(false);
</script>

<style scoped>
.nav-link {
    @apply text-brand-textSoft hover:text-brand-primary transition;
}

.mobile-link {
    @apply block text-brand-textSoft hover:text-brand-primary transition;
}
</style>
