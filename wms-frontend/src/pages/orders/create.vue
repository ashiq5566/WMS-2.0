<script setup>
import { onMounted, ref, watch } from 'vue';
import axios from '@/plugins/axios';
import { useToast } from 'primevue/usetoast';
import OrderConfirmModal from '@/components/orders/OrderConfirmModal.vue';

const toast = useToast();

const products = ref();
const selectedProduct = ref();
const grossAmount = ref(0);
const selectedType = ref(null);
const selectedStakeholder = ref('');
const stakeholderOptions = ref([]);
const selectedProductUnit = ref('');
const selectedProductStock = ref('');
const orderDate = ref('');

const blankData =
{
	product: '',
	product_name: '',
	quantity: '',
	price_at_time_of_order: '',
	total: '',
	unit: '',
};
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const orderBlankData = {
	stakeholder: '',
	order_number: '',
	order_type: '',
	gross_amount: '',
	discount: '',
	net_amount: '',
	order_date: '',
}
const orderData = ref(JSON.parse(JSON.stringify(orderBlankData)));
const itemsData = ref([])
const order_types = [
	{ value: 'PO', name: 'Purhase Order' },
	{ value: 'SO', name: 'Sales Order' },
]

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
				orderData.value.order_number = 'PO' + (response.data.filter(order => order.order_type == 'PO').length + 1);
			} else if (selectedType.value === 'SO') {
				orderData.value.order_number = 'SO' + (response.data.filter(order => order.order_type == 'SO').length + 1);
			}
		}
	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}

const selectRow = (data) => {
	const removedProduct = data.product_name
	itemsData.value = itemsData.value.filter(item => item.product !== data.product);
	toast.add({ severity: 'info', summary: 'Info', detail: `${removedProduct} is Removed Succesfully`, life: 3000 });
	if (selectedType.value === 'PO') {
		selectedProductStock.value = parseInt(selectedProductStock.value) - parseInt(data.quantity)
	} else if (selectedType.value == 'SO') {
		selectedProductStock.value = parseInt(selectedProductStock.value) + parseInt(data.quantity)
	}
};


const fetchProducts = async () => {
	try {
		const response = await axios.get('/api/inventory/products');

		products.value = response.data
	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}
// function addItem to add order items
const addItem = async () => {
	if (itemsData.value.some(item => item.product === selectedProduct.value)) {
		toast.add({ severity: 'error', summary: 'Error', detail: 'Product already added', life: 3000 });
		return;
	}
	try {
		const product = products.value.find(p => p.id === selectedProduct.value);
		if (!product || !formData.value.quantity || !formData.value.price_at_time_of_order) {
			toast.add({ severity: 'error', summary: 'Error', detail: 'Please fill in all fields', life: 3000 });
			return;
		}
		formData.value.product = product.id
		formData.value.product_name = product.name
		if (formData.value.quantity > 0 && formData.value.price_at_time_of_order > 0) {
			// calculate total price of each and save it in variable
			formData.value.total = formData.value.quantity * formData.value.price_at_time_of_order;


		}
		grossAmount.value = grossAmount.value + formData.value.total;
		itemsData.value.push(JSON.parse(JSON.stringify(formData.value)));
		formData.value = JSON.parse(JSON.stringify(blankData));
		// selectedProduct.value = '';

	} catch (error) {
		console.error('Error adding item:', error);
	}
};

const onSubmit = async (discountAmount, updatedGrossAmount, downPayment, paymentType) => {
	try {
		fetchOrders()
		orderData.value.order_type = selectedType.value;
		orderData.value.stakeholder = selectedStakeholder.value;
		orderData.value.gross_amount = grossAmount.value;
		orderData.value.discount = discountAmount;
		orderData.value.net_amount = updatedGrossAmount;
		orderData.value.order_date = new Date(orderDate.value).toISOString();
		const response = await axios.post('/api/inventory/orders/', {
			order: orderData.value,
			items: itemsData.value
		})
		// save initial order payment if any
		if (downPayment > 0 && response.status == 201) {
			const paymentResponse = await axios.post('/api/inventory/payments/',
				{
					order: response.data.order.id,
					company: response.data.order.stakeholder,
					amount: downPayment,
					payment_date: orderData.value.order_date,
					payment_method: paymentType
				}
			)
		}
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
		fetchProducts()
	} else if (newValue == 'SO') {
		fetchStakeholders('Customer');
		products.value = products.value.filter(product => product.qty_available > 0);
	}
})

watch(selectedProduct, (newValue) => {
	if (products.value.length > 0) {
		selectedProductUnit.value = products.value.find(p => p.id === newValue).unit;
		selectedProductStock.value = products.value.find(p => p.id === newValue).qty_available;
	}
})

watch(itemsData, (newValue) => {
	const totalAmount = newValue.reduce((acc, item) => acc + (item.total || 0), 0);
	grossAmount.value = totalAmount;
}, { deep: true });

const onUpdateQty = (data) => {
	const item = itemsData.value.find(p => p.product === data.product)
	item.quantity = data.quantity
	item.total = data.quantity * data.price_at_time_of_order;
}

const addProduct = (id) => {
	if (!selectedStakeholder.value || !selectedType.value || !orderDate.value) {
		toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please Ensure Order Type, Stakeholder, Order Date are entered', life: 3000 });
		return
	}
	try {
		const product = products.value.find(p => p.id === id);

		formData.value.product = product.id
		formData.value.product_name = product.name
		formData.value.price_at_time_of_order = product.selling_price
		formData.value.quantity = 1
		formData.value.total = formData.value.quantity * product.selling_price
		// // real time update of stock
		// if (selectedType.value == 'PO') {
		// 	selectedProductStock.value = parseInt(selectedProductStock.value) + parseInt(formData.value.quantity)
		// } else if (selectedType.value == 'SO') {
		// 	selectedProductStock.value = parseInt(selectedProductStock.value) - parseInt(formData.value.quantity)
		// }


		grossAmount.value = grossAmount.value + formData.value.total;
		const existingItem = itemsData.value.find(item => item.product === formData.value.product);
		if (existingItem) {
			existingItem.quantity = parseFloat(existingItem.quantity) + parseFloat(formData.value.quantity);
		} else {
			itemsData.value.push(JSON.parse(JSON.stringify(formData.value)));
		}

		formData.value = JSON.parse(JSON.stringify(blankData));

	} catch (error) {
		console.error('Error adding item:', error);
	}
}

onMounted(() => {
	fetchProducts();
})
</script>
<template>
	<div>
		<div class="flex mb-4">
			<Select v-model="selectedType" :options="order_types" optionLabel="name" option-value="value"
				placeholder="Select type" class="mr-4" />
			<Select v-model="selectedStakeholder" :options="stakeholderOptions" optionLabel="name" option-value="id"
				placeholder="Select Company" class="mr-4" />
			<DatePicker v-model="orderDate" show-icon />
			<InputText class="ml-4" type="text" v-model="orderData.order_number" placehoder="Order Number" disabled />
		</div>
		<div class="">
			<div class="grid grid-cols-7 gap-2">
				<div v-for="product in products" :key="product.id">
					<div class="border p-4 cursor-pointer h-48 w-full flex flex-col justify-between items-center"
						@click="addProduct(product.id)">
						<div class="h-32 w-32 flex items-center justify-center">
							<img :src="product.image" alt="Image" class="block w-full h-full object-cover" />
						</div>
						<div class="mt-4">
							<span>{{ product.name }}</span>
						</div>
					</div>
				</div>
			</div>
			<div>
				<Card>
					<template #content>
						<DataTable :value="itemsData" tableStyle="min-width: 50rem">
							<Column field="product" header="Product">
								<template #body="slotProps">
									<span>{{ slotProps.data.product_name }}</span>
								</template>
							</Column>
							<Column field="quantity" header="Quantity">
								<template #body="slotProps">
									<input type="number" v-model="slotProps.data.quantity" style="width: 100px"
										class="p-inputtext p-component" @input="onUpdateQty(slotProps.data)" />
								</template>
							</Column>
							<Column field="price_at_time_of_order" header="Unit Price"></Column>
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
							<OrderConfirmModal @order-confirmed="onSubmit" :items="itemsData" :gross-amount="grossAmount" />
						</div>
					</template>
				</Card>
			</div>
		</div>
	</div>
</template>