<template>
    <section class="mt-10">
        <div class="container">

            <!-- Title -->
            <h1 class="text-3xl font-bold text-brand-primary mb-6">
                Products
            </h1>

            <!-- Product Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6">

                <div v-for="item in products" :key="item.id" class="border rounded-lg overflow-hidden">
                    <img :src="item.image" class="w-full h-40 object-cover" />

                    <div class="p-4">
                        <h3 class="font-semibold text-brand-text">
                            {{ item.name }}
                        </h3>

                        <p class="text-brand-accent font-semibold mt-2">
                            ₹{{ item.selling_price }}
                        </p>

                        <button
                            class="w-full mt-3 bg-brand-primary text-white py-2 rounded-lg hover:bg-brand-primaryLight">
                            Add to Cart
                        </button>
                    </div>
                </div>

            </div>

        </div>
    </section>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router";
const { $axios } = useNuxtApp();

const route = useRoute();
const category = route.query.category || null;
const products = ref([])

const fetchProducts = async (search) => {
    try {
        const response = await $axios.get('/api/inventory/products/', {
            params: {
                search,
            },
        });

        products.value = response.data;
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

onMounted(() => {
    fetchProducts()
})

// const filteredProducts = category
//     ? products.filter((p) => p.category === category)
//     : products;

// const title = category
//     ? category.split("-").join(" ").toUpperCase()
//     : "All Products";
</script>
