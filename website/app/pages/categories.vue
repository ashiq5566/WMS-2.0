<template>
    <section class="mt-10">
        <div class="container">
            <h1 class="text-3xl font-bold text-brand-primary mb-8">
                Shop by Category
            </h1>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-8">

                <NuxtLink v-for="cat in categories" :key="cat.name" :to="`/products?category=${cat.slug}`"
                    class="bg-white shadow rounded-lg p-5 hover:shadow-xl transition block text-center">
                    <img :src="cat.image" class="h-24 mx-auto mb-4 object-contain" />

                    <h3 class="font-semibold text-brand-text">{{ cat.name }}</h3>
                </NuxtLink>

            </div>
        </div>
    </section>
</template>

<script setup>
const categories = [
    {
        name: "Frying Pans",
        slug: "frying-pans",
        image: "/icons/pan.png",
    },
    {
        name: "Cookware Sets",
        slug: "cookware-sets",
        image: "/icons/pot.png",
    },
    {
        name: "Kitchen Tools",
        slug: "kitchen-tools",
        image: "/icons/pan.png",
    },
    {
        name: "Steel Bowls",
        slug: "steel-bowls",
        image: "/icons/pot.png",
    },
];
</script>
