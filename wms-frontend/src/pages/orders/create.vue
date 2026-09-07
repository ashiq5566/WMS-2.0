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
const showSizeModal = ref(false);
const selectedProductData = ref(null);
const selectedSize = ref(null);
const sizeQuantity = ref(1);

const blankData =
{
	product: '',
	product_name: '',
	size: '',
	quantity: '',
	price_at_time_of_order: '',
	total: '',
	unit: '',
	stock: '',
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
	const removedProduct = `${data.product_name} (${data.size})`
	itemsData.value = itemsData.value.filter(item => !(item.product === data.product && item.size === data.size));
	toast.add({ severity: 'info', summary: 'Info', detail: `${removedProduct} is Removed Successfully`, life: 3000 });
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
	const item = itemsData.value.find(p => p.product === data.product && p.size === data.size)
	if (item) {
		item.quantity = Number(data.quantity) || 0;
		item.price_at_time_of_order = Number(item.price_at_time_of_order) || 0;
		item.total = item.quantity * item.price_at_time_of_order;
	}
}

const addProduct = (id) => {
	if (!selectedStakeholder.value || !selectedType.value || !orderDate.value) {
		toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please Ensure Order Type, Stakeholder, Order Date are entered', life: 3000 });
		return
	}
	try {
		const product = products.value.find(p => p.id === id);
		if (!product || !product.sizes || product.sizes.length === 0) {
			toast.add({ severity: 'error', summary: 'Error', detail: 'Product has no sizes available', life: 3000 });
			return;
		}
		selectedProductData.value = product;
		selectedSize.value = null;
		sizeQuantity.value = 1;
		showSizeModal.value = true;

	} catch (error) {
		console.error('Error opening size modal:', error);
	}
}

const addProductWithSize = () => {
	if (!selectedSize.value || !sizeQuantity.value) {
		toast.add({ severity: 'error', summary: 'Error', detail: 'Please select size and quantity', life: 3000 });
		return;
	}

	try {
		const product = selectedProductData.value;
		const size = selectedSize.value;
		const pricePerUnit = Number(size.price) || 0;
		const quantity = Number(sizeQuantity.value) || 0;

		// Validate stock for Sales Orders (SO)
		if (selectedType.value === 'SO') {
			if (size.stock < quantity) {
				toast.add({
					severity: 'error',
					summary: 'Insufficient Stock',
					detail: `Available stock for ${product.name} (Size ${size.size}): ${size.stock}, Requested: ${quantity}`,
					life: 3000
				});
				return;
			}
		}

		const itemKey = `${product.id}-${size.size}`;
		const existingItem = itemsData.value.find(item => item.product === product.id && item.size === size.size);

		if (existingItem) {
			// For SO, validate total quantity against available stock
			if (selectedType.value === 'SO') {
				const newTotalQuantity = Number(existingItem.quantity) + quantity;
				if (size.stock < newTotalQuantity) {
					toast.add({
						severity: 'error',
						summary: 'Insufficient Stock',
						detail: `Available stock for ${product.name} (Size ${size.size}): ${size.stock}, Total Requested: ${newTotalQuantity}`,
						life: 3000
					});
					return;
				}
			}
			existingItem.quantity = Number(existingItem.quantity) + quantity;
			existingItem.price_at_time_of_order = Number(existingItem.price_at_time_of_order) || 0;
			existingItem.total = existingItem.quantity * existingItem.price_at_time_of_order;
		} else {
			const newItem = {
				product: product.id,
				product_name: product.name,
				product_size: size.id,  // Add ProductSize ID for backend
				size: size.size,
				quantity: quantity,
				price_at_time_of_order: pricePerUnit,
				total: quantity * pricePerUnit,
				unit: product.unit,
				stock: size.stock,
			};
			itemsData.value.push(newItem);
		}

		showSizeModal.value = false;
		selectedSize.value = null;
		sizeQuantity.value = 1;
		selectedProductData.value = null;
		toast.add({ severity: 'success', summary: 'Success', detail: 'Item added to order', life: 3000 });

	} catch (error) {
		console.error('Error adding item with size:', error);
		toast.add({ severity: 'error', summary: 'Error', detail: 'Error adding item', life: 3000 });
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

			<!-- Size Selection Modal -->
			<Dialog :visible="showSizeModal" @update:visible="showSizeModal = $event" modal
				:header="`Select Size for ${selectedProductData?.name}`" style="width: 40rem">
				<div v-if="selectedProductData" class="space-y-4">
					<div>
						<label class="block font-semibold mb-2">Available Sizes</label>
						<div class="grid grid-cols-1 gap-2">
							<div v-for="size in selectedProductData.sizes" :key="size.size"
								class="border p-3 rounded cursor-pointer hover:bg-gray-100"
								:class="{ 'bg-blue-100 border-blue-500': selectedSize?.size === size.size }"
								@click="selectedSize = size">
								<div class="flex justify-between items-center">
									<div>
										<p class="font-semibold">Size: {{ size.size }}</p>
										<p class="text-sm text-gray-600">Price: ₹{{ size.price }} | Stock: {{ size.stock
											}}</p>
									</div>
									<span v-if="selectedSize?.size === size.size"
										class="text-blue-600 font-bold">✓</span>
								</div>
							</div>
						</div>
					</div>

					<div>
						<label class="block font-semibold mb-2">Quantity</label>
						<InputNumber v-model="sizeQuantity" :min="1"
							:max="selectedType === 'SO' ? Math.max(0, selectedSize?.stock - (itemsData.find(item => item.product === selectedProductData?.id && item.size === selectedSize?.size)?.quantity || 0)) : (selectedSize?.stock || 999)"
							placeholder="Enter quantity" class="w-full" />
						<p v-if="selectedType === 'SO'" class="text-sm text-gray-500 mt-1">
							Available: {{Math.max(0, selectedSize?.stock - (itemsData.find(item => item.product ===
								selectedProductData?.id && item.size === selectedSize?.size)?.quantity || 0)) }}
						</p>
					</div>

					<div v-if="selectedSize" class="bg-gray-50 p-3 rounded">
						<p><strong>Total Price:</strong> ₹{{ (Number(selectedSize.price) *
							Number(sizeQuantity)).toFixed(2) }}</p>
					</div>

					<div class="flex justify-end gap-2">
						<Button label="Cancel" severity="secondary" @click="showSizeModal = false" />
						<Button label="Add to Order" @click="addProductWithSize" :disabled="!selectedSize" />
					</div>
				</div>
			</Dialog>

			<div>
				<Card>
					<template #content>
						<DataTable :value="itemsData" tableStyle="min-width: 80rem" scrollable
							scroll-direction="horizontal">
							<Column field="product" header="Product" style="width: 20%">
								<template #body="slotProps">
									<span>{{ slotProps.data.product_name }}</span>
								</template>
							</Column>
							<Column field="size" header="Size" style="width: 12%">
								<template #body="slotProps">
									<span>{{ slotProps.data.size }}</span>
								</template>
							</Column>
							<Column field="stock" header="Available Stock" style="width: 15%">
								<template #body="slotProps">
									<span>{{ slotProps.data.stock }}</span>
								</template>
							</Column>
							<Column field="quantity" header="Quantity" style="width: 12%">
								<template #body="slotProps">
									<input type="number" v-model.number="slotProps.data.quantity" style="width: 100%"
										class="p-inputtext p-component" @input="onUpdateQty(slotProps.data)" />
								</template>
							</Column>
							<Column field="price_at_time_of_order" header="Unit Price" style="width: 13%">
								<template #body="slotProps">
									<span>₹{{ Number(slotProps.data.price_at_time_of_order).toFixed(2) }}</span>
								</template>
							</Column>
							<Column field="total" header="Total Price" style="width: 13%">
								<template #body="slotProps">
									<span>₹{{ Number(slotProps.data.total).toFixed(2) }}</span>
								</template>
							</Column>
							<Column style="width: 8%; text-align: right">
								<template #body="{ data }">
									<Button icon="pi pi-times" @click="selectRow(data)" severity="secondary" rounded
										text></Button>
								</template>
							</Column>
							<template #empty>
								<span class="flex justify-center">No Orders found.</span>
							</template>
						</DataTable>
						<div v-if="itemsData.length" class="flex justify-end mt-4 gap-4">
							<div class="text-right">
								<p class="font-semibold text-lg">Gross Amount: ₹{{ Number(grossAmount).toFixed(2) }}</p>
							</div>
							<OrderConfirmModal @order-confirmed="onSubmit" :items="itemsData"
								:gross-amount="grossAmount" />
						</div>
					</template>
				</Card>
			</div>
		</div>
	</div>
</template>