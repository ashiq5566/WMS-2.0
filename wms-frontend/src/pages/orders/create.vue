<script setup>
import { onMounted, ref, watch } from 'vue';
import axios from '@/plugins/axios';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const orderItems = ref();
const products = ref();
const selectedProduct = ref();
const selectedType = ref(null);
const selectedStakeholder = ref('');
const stakeholderOptions = ref([]);

const blankData =
	{ product: '', quantity: '', price_at_time_of_order: '', };
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const orderBlankData = {
	stakeholder: '',
	order_number: '',
	order_type: '',
}
const orderData = ref(JSON.parse(JSON.stringify(orderBlankData)));
const itemsData = ref([])
const order_types = [
	{ value: 'PO', name: 'Purhase Order' },
	{ value: 'SO', name: 'Sales Order' },
]

const fetchOrderItems = async () => {
	try {
		const response = await axios.get('/api/inventory/order-items');

		orderItems.value = response.data;
	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}

const fetchStakeholders = async (stakeholder_type) => {
	try {
		const response = await axios.get('/api/accounts/stakeholders', {
			params: { type: stakeholder_type },
		});

		stakeholderOptions.value = response.data;
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}

const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders');
		if (response.data.length >= 0) {
			if (selectedType.value === 'PO') {
				orderData.value.order_number = 'PO' + (response.data.length + 1);
			} else if (selectedType.value === 'SO') {
				orderData.value.order_number = 'SO' + (response.data.length + 1);
			}
		}
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
		fetchOrders()
		orderData.value.order_type = selectedType.value;
		orderData.value.stakeholder = selectedStakeholder.value;
		const response = await axios.post('/api/inventory/orders/', {
			order: orderData.value,
			items: itemsData.value
		})
		console.log('Order created:', response.data)
		toast.add({ severity: 'info', summary: 'Info', detail: 'Order Created SuccessFully', life: 3000 });
	} catch (error) {
		console.error('Error creating order:', error.response?.data)
		const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred';
		toast.add({ severity: 'error', summary: 'Error Message', detail: errorMessage, life: 3000 });
	}
}

watch(selectedType, (newValue) => {
	fetchOrders();
	if (newValue == 'PO') {
		fetchStakeholders('Supplier');
	} else if (newValue == 'SO') {
		fetchStakeholders('Customer');
	}
})

onMounted(() => {
	fetchOrderItems();
	fetchProducts();
})
</script>
<template>
	<div>
		<div class="flex justify-end mb-4">
			<Select v-model="selectedType" :options="order_types" optionLabel="name" option-value="value"
				placeholder="Select type" class="mr-4" />
			<Select v-model="selectedStakeholder" :options="stakeholderOptions" optionLabel="name" option-value="id"
				placeholder="Select Company" class="mr-4" />
			<InputText class="mr-4" type="text" v-model="orderData.order_number" placehoder="Order Number" disabled />
		</div>
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
				<div class="flex justify-end mt-4">
					<Button label="Confirm Order" @click="onSubmit" />
				</div>
			</template>
		</Card>
	</div>
</template>