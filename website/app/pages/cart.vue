<template>
	<section class="mt-12 mb-20">
		<div class="container">

			<h1 class="text-3xl font-bold text-brand-primary mb-8">
				Your Cart
			</h1>

			<!-- Empty Cart -->
			<div v-if="cartItems.length === 0" class="text-center py-20">
				<p class="text-gray-500 text-lg">Your cart is empty.</p>
			</div>

			<!-- Cart Items -->
			<div v-else class="grid md:grid-cols-3 gap-10">

				<!-- LEFT: Items -->
				<div class="md:col-span-2 space-y-6">

					<div v-for="item in cartItems" :key="item.id" class="flex gap-6 border rounded-lg p-4">
						<!-- Image -->
						<img :src="item.image" class="w-24 h-24 object-cover rounded" />

						<!-- Details -->
						<div class="flex-1">
							<h3 class="font-semibold text-lg text-brand-text">
								{{ item.product_name }}
							</h3>

							<p class="text-brand-accent font-semibold mt-1">
								₹ {{ item.price }}
							</p>

							<!-- Quantity Controls -->
							<div class="flex items-center gap-4 mt-4">
								<button @click="updateQty(item, -1)" class="w-8 h-8 border rounded">−</button>

								<span class="font-semibold">{{ item.quantity }}</span>

								<button @click="updateQty(item, 1)" class="w-8 h-8 border rounded">+</button>

								<button @click="removeItem(item.id)" class="ml-6 text-red-500 hover:underline">
									Remove
								</button>
							</div>
						</div>

						<!-- Item Total -->
						<div class="font-semibold text-lg">
							₹ {{ item.price * item.quantity }}
						</div>
					</div>
				</div>

				<!-- RIGHT: SUMMARY -->
				<div class="bg-white shadow rounded-lg p-6 h-fit">
					<h2 class="text-xl font-semibold mb-4">Order Summary</h2>

					<div class="flex justify-between mb-2">
						<span>Subtotal</span>
						<span>₹ {{ subtotal }}</span>
					</div>

					<div class="flex justify-between mb-4">
						<span>Delivery</span>
						<span class="text-green-600">Free</span>
					</div>

					<hr />

					<div class="flex justify-between mt-4 text-lg font-bold">
						<span>Total</span>
						<span>₹ {{ subtotal }}</span>
					</div>

					<button class="w-full mt-6 bg-brand-primary text-white py-3 rounded-lg hover:bg-brand-primaryLight">
						Proceed to Checkout
					</button>
				</div>

			</div>

		</div>
	</section>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";

const { $axios } = useNuxtApp();

const cartItems = ref([]);

const fetchCart = async () => {
	const res = await $axios.get("/api/inventory/cart/");
	cartItems.value = res.data[0].items;
};

const updateQty = async (item, change) => {
	const newQty = item.quantity + change;
	if (newQty <= 0) return;

	await $axios.patch(`/api/inventory/cart-items/${item.id}/`, {
		quantity: newQty
	});

	fetchCart();
};

const removeItem = async (id) => {
	await $axios.delete(`/api/inventory/cart-items/${id}/`);

	fetchCart();
};

const subtotal = computed(() =>
	cartItems.value.reduce(
		(sum, item) => sum + item.price * item.quantity,
		0
	)
);

onMounted(fetchCart);
</script>
