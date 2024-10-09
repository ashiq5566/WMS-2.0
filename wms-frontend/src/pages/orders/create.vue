<script setup>
import { onMounted, ref } from 'vue';
import axios from '@/plugins/axios';

const selectedProduct = ref();
const orderItems = ref();
const products = ref();

const blankData =
	{ product: '', quantity: '', price_at_time_of_order: '', };
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const fetchOrderItems = async () => {
	try {
		const response = await axios.get('/api/inventory/order-items');

		orderItems.value = response.data;
	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}

const fetchProducts = async () => {
	try {
		const response = await axios.get('/api/inventory/products');

		products.value = response.data;

	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}
// function addItem to add order items
const addItem = async () => {
	try {
		formData.value.product = selectedProduct.value;

		const response = await axios.post('/api/inventory/order-items/', formData.value);
		console.log('Item added successfully:', response.data);
		fetchOrderItems();
	} catch (error) {
		console.error('Error adding item:', error);
	}
};

onMounted(() => {
	fetchOrderItems();
	fetchProducts();
})
</script>
<template>
	<div>
		<div class="mb-4">
			<Select v-model="selectedProduct" :options="products" optionLabel="name" option-value="id"
				placeholder="Select product" class="mr-4" />
			<InputText class="mr-4" type="text" v-model="formData.quantity" placeholder="Quantity" />
			<InputText class="mr-4" type="text" v-model="formData.price_at_time_of_order" placeholder="Unit Price" />
			<Button icon="pi pi-plus" aria-label="Save" @click="addItem" />
		</div>
		<Card>
			<template #content>
				<DataTable :value="orderItems" tableStyle="min-width: 50rem">
					<Column field="product" header="Product"></Column>
					<Column field="quantity" header="Quantity"></Column>
					<Column field="price_at_time_of_order" header="Unit Price"></Column>
					<Column field="totak" header="Total"></Column>
					<template #empty>
						<span class="flex justify-center">No Orders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>