<template>
    <footer class="bg-brand-primary text-white mt-20">
        <div class="container py-12 grid md:grid-cols-4 gap-10">

            <!-- Brand -->
            <div>
                <h2 class="text-2xl font-bold mb-4">CulinarySteel</h2>
                <p class="text-brand-surface/80 leading-relaxed">
                    Premium stainless steel cookware crafted for chefs and home kitchens.
                </p>
            </div>

            <!-- Quick Links -->
            <div>
                <h3 class="text-lg font-semibold mb-3">Quick Links</h3>
                <ul class="space-y-2 text-brand-surface/80">
                    <li>
                        <NuxtLink class="footer-link" to="/">Home</NuxtLink>
                    </li>
                    <li>
                        <NuxtLink class="footer-link" to="/categories">Categories</NuxtLink>
                    </li>
                    <li>
                        <NuxtLink class="footer-link" to="/best-sellers">Best Sellers</NuxtLink>
                    </li>
                    <li>
                        <NuxtLink class="footer-link" to="/about">About</NuxtLink>
                    </li>
                </ul>
            </div>

            <!-- Support -->
            <div>
                <h3 class="text-lg font-semibold mb-3">Support</h3>
                <ul class="space-y-2 text-brand-surface/80">
                    <li>
                        <NuxtLink class="footer-link" to="/contact">Contact Us</NuxtLink>
                    </li>
                    <li>
                        <NuxtLink class="footer-link" to="/faq">FAQ</NuxtLink>
                    </li>
                    <li>
                        <NuxtLink class="footer-link" to="/shipping">Shipping</NuxtLink>
                    </li>
                    <li>
                        <NuxtLink class="footer-link" to="/returns">Returns</NuxtLink>
                    </li>
                </ul>
            </div>

            <!-- Social Media -->
            <div>
                <h3 class="text-lg font-semibold mb-3">Follow Us</h3>
                <div class="flex gap-4">
                    <a href="#" class="social-icon">FB</a>
                    <a href="#" class="social-icon">IG</a>
                    <a href="#" class="social-icon">YT</a>
                </div>
            </div>

        </div>

        <div class="border-t border-white/20 py-4">
            <div class="container text-center text-white/70 text-sm">
                © {{ new Date().getFullYear() }} CulinarySteel. All rights reserved.
            </div>
        </div>
    </footer>
</template>

<script setup>
</script>

<style scoped>
.footer-link {
    @apply hover:text-white transition;
}

.social-icon {
    @apply w-10 h-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition;
}
</style>
