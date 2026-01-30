<template>
	<section class="mt-10">
		<div class="container">

			<!-- Title -->
			<h1 class="text-3xl font-bold text-brand-primary mb-6">
				Products
			</h1>

			<!-- Product Grid -->
			<div class="grid grid-cols-2 md:grid-cols-4 gap-6">

				<NuxtLink v-for="item in products" :key="item.id" :to="{ name: 'products-id', params: { id: item.id } }"
					class="border rounded-lg overflow-hidden block hover:shadow-lg transition">
					<img :src="item.image" class="w-full h-40 object-cover" />

					<div class="p-4">
						<h3 class="font-semibold text-brand-text">
							{{ item.name }}
						</h3>

						<p class="text-brand-accent font-semibold mt-2">
							{{ item.selling_price ? `₹ ${item.selling_price}` : 'N/A' }}
						</p>

						<!-- Stop click from navigating -->
						<button @click.stop="addToCart(item.id)"
							class="w-full mt-3 bg-brand-primary text-white py-2 rounded-lg hover:bg-brand-primaryLight">
							Add to Cart
						</button>
					</div>
				</NuxtLink>

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

const addToCart = async (productId) => {
	try {
		await $axios.post("/api/inventory/cart/", {
			product_id: productId,
			quantity: 1,
		});

		alert("Added to cart!");
	} catch (err) {
		console.error(err);
		alert("Please login to add items to cart");
	}
};

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
