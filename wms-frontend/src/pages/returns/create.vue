<script setup>
import { onMounted, ref, watch } from 'vue';
import axios from '@/plugins/axios';
import { useToast } from 'primevue/usetoast';
import { useRouter } from 'vue-router';

const toast = useToast();
const router = useRouter();
const orders = ref([]);
const selectedProduct = ref();
const returnAmount = ref(0);
const selectedOrder = ref(null);
const orderItems = ref([]);
const productTotal = ref('');
const orderPrice = ref('');
const orderQuantity = ref('');
const returnOrders = ref([]);
const readyToCreate = ref(false);


const blankData =
{
	product: '',
	quantity: '',
	total: '',
	price_at_return: '',
};
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const orderlankData = {
	return_type: '',
	original_order: '',
	total_amount: '',
}
const returnData = ref(JSON.parse(JSON.stringify(orderlankData)));
const itemsData = ref([])


const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders');
		orders.value = response.data;

	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}

const fetchOrderItems = async (order) => {
	try {
		const response = await axios.get('/api/inventory/order-items/', {
			params: { order_id: order },
		});
		const alteredData = response.data.map(item => (
			{
				id: item.id,
				price_at_time_of_order: item.price_at_time_of_order,
				quantity: item.quantity,
				total: item.total,
				unit: item.product_obj.unit,
				product_id: item.product_obj.id,
				product_name: item.product_obj.name,
				order_type: item.order_obj.order_type
			}
		));
		orderItems.value = alteredData;

	} catch (error) {
		console.error('Error fetching order items:', error);
	}
}
const selectRow = (data) => {
	const removedProduct = data.product_name
	itemsData.value = itemsData.value.filter(item => item.product !== data.product);
	toast.add({ severity: 'info', summary: 'Info', detail: `${removedProduct} is Removed Succesfully`, life: 3000 });
};


// function addItem to add order items
const addItem = async () => {
	//check if product going to add is already exist in itemsData
	if (itemsData.value.some(item => item.product === selectedProduct.value)) {
		toast.add({ severity: 'error', summary: 'Error', detail: 'Product already added', life: 3000 });
		return;
	}
	// check if product selected is not blank
	if (!selectedProduct.value) {
		toast.add({ severity: 'error', summary: 'Error', detail: 'Please select a product', life: 3000 });
		return;
	}

	try {
		const product = orderItems.value.find(p => p.product_id === selectedProduct.value);
		if (!formData.value.quantity) {
			toast.add({ severity: 'error', summary: 'Error', detail: 'Please fill in all fields', life: 3000 });
			return;
		}
		if (formData.value.quantity > orderQuantity.value) {
			toast.add({ severity: 'error', summary: 'Error', detail: 'Entered Quantity exeeds the order quantity!', life: 3000 });
			return;
		}
		formData.value.product = product.product_id
		formData.value.product_name = product.product_name
		formData.value.price_at_return = orderPrice.value;
		if (formData.value.quantity > 0 && formData.value.price_at_return > 0) {
			// calculate total price of each and save it in variable
			formData.value.total = formData.value.quantity * orderPrice.value;
		}
		returnAmount.value = returnAmount.value + formData.value.total;
		itemsData.value.push(JSON.parse(JSON.stringify(formData.value)));
		formData.value = JSON.parse(JSON.stringify(blankData));
		selectedProduct.value = '';

	} catch (error) {
		console.error('Error adding item:', error);
	}
};

const fetchReturns = async (order) => {
	try {
		const response = await axios.get('/api/inventory/returns', {
			params: {
				original_order: order
			},
		});
		returnOrders.value = response.data;

	} catch (error) {
		console.error('Error fetching return orders:', error);
	}
}

const onSubmit = async () => {
	try {
		returnData.value.original_order = selectedOrder.value;

		if (orderItems.value.length > 0 && orderItems.value[0].order_type == 'PO') {
			returnData.value.return_type = 'PR';
		} else if (orderItems.value.length > 0 && orderItems.value[0].order_type == 'SO') {
			returnData.value.return_type = 'SR';
		}

		returnData.value.total_amount = returnAmount.value;
		const response = await axios.post('/api/inventory/returns/', {
			return: returnData.value,
			items: itemsData.value
		});
		console.log('Return created:', response.data)
		toast.add({ severity: 'info', summary: 'Info', detail: 'Return Created SuccessFully', life: 3000 });
		router.push('/returns');
	} catch (error) {
		console.error('Error creating return:', error.response?.data)
		const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred';
		toast.add({ severity: 'error', summary: 'Error Message', detail: errorMessage, life: 3000 });
	}
}


watch(selectedOrder, async (newValue) => {
	await fetchReturns(newValue)
	if (returnOrders.value.length > 0) {
		toast.add({ severity: 'error', summary: 'Error', detail: 'Return already created for this order', life: 3000 });
		return;
	} else {
		readyToCreate.value = true;
		fetchOrderItems(newValue);
	}
})

watch(selectedProduct, (newValue) => {
	orderPrice.value = orderItems.value.find(p => p.product_id === newValue)?.price_at_time_of_order;
	productTotal.value = orderItems.value.find(p => p.product_id === newValue)?.total;
	orderQuantity.value = orderItems.value.find(p => p.product_id === newValue)?.quantity;
})

watch(itemsData, (newValue) => {
	const amount = newValue.reduce((acc, item) => acc + (item.total || 0), 0);
	returnAmount.value = amount;
}, { deep: true });

onMounted(() => {
	fetchOrders();
})
</script>
<template>
	<div>
		<div class="flex justify-end mb-4">
			<Select v-model="selectedOrder" :options="orders" optionLabel="order_number" option-value="id"
				placeholder="Select Order" class="mr-4" />
		</div>
		<div v-if="readyToCreate" class="mb-4 flex">
			<div class="flex flex-col">
				<label for="product-select" class="mb-1">Product</label>
				<Select id="product-select" v-model="selectedProduct" :options="orderItems" optionLabel="product_name"
					option-value="product_id" placeholder="Select product" class="mr-4" />
			</div>
			<div class="flex flex-col">
				<label for="order-quantity" class="mb-1">Order Quantity</label>
				<InputText id="order-quantity" class="mr-4" type="text" v-model="orderQuantity" disabled />
			</div>
			<div class="flex flex-col">
				<label for="order-price" class="mb-1">Order Price</label>
				<InputText id="order-price" class="mr-4" type="text" v-model="orderPrice" disabled />
			</div>
			<div class="flex flex-col">
				<label for="return-quantity" class="mb-1">Return Quantity</label>
				<InputText id="return-quantity" class="mr-4" type="text" v-model="formData.quantity"
					placeholder="Return Quantity" />
			</div>
			<div class="flex items-end">
				<Button icon="pi pi-plus" aria-label="Save" @click="addItem" />
			</div>
		</div>
		<Card>
			<template #content>
				<DataTable :value="itemsData" tableStyle="min-width: 50rem">
					<Column field="product" header="Product">
						<template #body="slotProps">
							<span>{{ slotProps.data.product_name }}</span>
						</template>
					</Column>
					<Column field="quantity" header="Return Quantity">
					</Column>
					<Column field="price_at_return" header="Unit Price"></Column>
					<Column field="total" header="Total"></Column>
					<Column class="w-24 !text-end">
						<template #body="{ data }">
							<Button icon="pi pi-times" @click="selectRow(data)" severity="secondary" rounded></Button>
						</template>
					</Column>
					<template #empty>
						<span class="flex justify-center">No Orders found.</span>
					</template>
				</DataTable>
				<div v-if="itemsData.length" class="flex justify-end mt-4">
					<Button label="Confirm" @click="onSubmit" />
				</div>
			</template>
		</Card>
	</div>
</template>