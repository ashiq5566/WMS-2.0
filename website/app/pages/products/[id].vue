<template>
	<section class="mt-10">
		<div class="container grid md:grid-cols-2 gap-12">

			<!-- Image -->
			<img :src="product.image" class="w-full h-96 object-cover rounded-lg" />

			<!-- Info -->
			<div>
				<h1 class="text-3xl font-bold mb-4">{{ product.name }}</h1>

				<p class="text-xl text-brand-primary font-semibold mb-4">
					₹ {{ selectedPrice }}
				</p>


				<!-- Description -->
				<div v-if="product.description" class="my-4">
					<h3 class="font-semibold text-lg mb-1">Product Details</h3>
					<p class="text-gray-600 leading-relaxed">
						{{ product.description }}
					</p>
				</div>


				<!-- Size Selector -->
				<div class="mb-6" v-if="product?.sizes?.length > 0">
					<h3 class="font-semibold mb-2">Select Size</h3>

					<div class="flex flex-wrap gap-3">
						<button v-for="size in product.sizes" :key="size.id" :disabled="!size.is_available"
							@click="selectSize(size)" :class="[
								'px-4 py-2 rounded border',
								selectedSize?.id === size.id
									? 'bg-brand-primary text-white'
									: 'border-gray-300',
								!size.is_available && 'opacity-40 cursor-not-allowed'
							]">
							{{ size.size }}
						</button>
					</div>
				</div>

				<!-- Add to Cart -->
				<button class="bg-brand-primary text-white px-6 py-3 rounded-lg cursor-pointer hover:bg-black"
					@click="addToCart">
					Add to Cart
				</button>
			</div>

		</div>
	</section>
</template>
<script setup>
definePageMeta({
	middleware: "auth"
});
import { ref, onMounted, computed } from "vue"
const route = useRoute()
const { $axios } = useNuxtApp()

const product = ref({})
const selectedSize = ref(null)

const selectedPrice = computed(() =>
	selectedSize.value?.price || product.value.selling_price
)

const fetchProduct = async () => {
	const res = await $axios.get(`/api/inventory/products/${route.params.id}/`)
	product.value = res.data
}

const selectSize = (size) => {
	selectedSize.value = size
}

const addToCart = async () => {
	await $axios.post("/api/inventory/cart/", {
		product_id: product.value.id,
		size_id: selectedSize.value?.id || null,
		quantity: 1
	})
}

onMounted(fetchProduct)
</script>