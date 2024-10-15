<script setup>
import { onMounted, ref } from 'vue';
import axios from '@/plugins/axios';

const selectedProduct = ref();
const orderItems = ref();
const products = ref();

const blankData =
	{ order: '', product: '', quantity: '', price_at_time_of_order: '', };
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const orderBlankData = {
	order_number: 'jsdfsdfj12133',
	order_type: 'PO',
	order_status: 'Closed'
}
const orderData = ref(JSON.parse(JSON.stringify(orderBlankData)));

const itemsData = ref([])


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
		formData.value.product = selectedProduct.value
		itemsData.value.push(JSON.parse(JSON.stringify(formData.value)));
		console.log("Added order items", itemsData.value);

	} catch (error) {
		console.error('Error adding item:', error);
	}
};

const onSubmit = async () => {
	try {
		const response = await axios.post('/api/inventory/orders/', {
			order: orderData.value,
			items: itemsData.value
		})
		console.log('Order created:', response.data)
	} catch (error) {
		console.error('Error creating order:', error.response?.data)
	}
}

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
				<DataTable :value="itemsData" tableStyle="min-width: 50rem">
					<Column field="product" header="Product"></Column>
					<Column field="quantity" header="Quantity"></Column>
					<Column field="price_at_time_of_order" header="Unit Price"></Column>
					<Column field="total" header="Total"></Column>
					<template #empty>
						<span class="flex justify-center">No Orders found.</span>
					</template>
				</DataTable>
				<Button label="add" @click="onSubmit" />

			</template>
		</Card>
	</div>
</template>