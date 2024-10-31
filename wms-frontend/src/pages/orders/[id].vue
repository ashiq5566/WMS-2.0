<script setup>
import { useRoute } from 'vue-router';
import moment from 'moment';
import axios from '@/plugins/axios'
import { ref, onMounted } from 'vue'

const route = useRoute()
const order = ref({})
const orderItems = ref([])
const returnOrder = ref()
const returnItems = ref([])

const getSeverity = (status) => {
	switch (status) {
		case 'Issued':
			return 'warn';

		case 'Delivered':
			return 'success';

		case 'Recieved':
			return 'info';

		case 'Cancelled':
			return 'warn';

		case 'Closed':
			return 'danger';
	}
}

const fetchOrder = async () => {
	try {
		const response = await axios.get(`/api/inventory/orders/${route.params.id}`)
		order.value = response.data
	} catch (error) {
		console.log(error);

	}
}

const fetchOrderItems = async () => {
	try {
		const response = await axios.get('/api/inventory/order-items/', {
			params: {
				order_id: route.params.id,
			},
		})
		orderItems.value = response.data
	} catch (error) {
		console.log(error);

	}
}

const fetchReturn = async () => {
	try {
		const response = await axios.get('/api/inventory/returns/', {
			params: {
				original_order: route.params.id,
			},
		})
		returnOrder.value = response.data[0]
	} catch (error) {
		console.log(error);

	}
}

const fetchReturnItems = async () => {
	try {
		const response = await axios.get('/api/inventory/return-items/', {
			params: {
				return_order: returnOrder.value.id,
			},
		})
		returnItems.value = response.data
	} catch (error) {
		console.log(error);

	}
}

onMounted(async () => {
	await fetchOrder();
	await fetchOrderItems();
	await fetchReturn();
	await fetchReturnItems();
})
</script>
<template>
	<div>
		<h1>{{ route.params.id }}</h1>
		<div class="grid grid-cols-2 gap-4 mb-4">
			<Card>
				<template #title>
					<span>Order Details</span>
				</template>
				<template #content>
					<div class="grid grid-cols-2 gap-4">
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Order No:</label>
							<span>{{ order.order_number }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Order Type:</label>
							<span>{{ order.order_type }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Company Name:</label>
							<span>{{ order.stakeholder_obj?.name }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Order Date:</label>
							<span>{{ moment(order.created_at).format('YYYY-MM-DD') }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Order Status:</label>
							<Tag :value="order.order_status" :severity="getSeverity(order.order_status)" />
						</div>
					</div>
					<div class="grid grid-cols-2 gap-4 border-t mt-8 pt-8">
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Total Amount:</label>
							<span>{{ order.gross_amount }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Discount:</label>
							<span>{{ order.discount }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Net Amount:</label>
							<span>{{ order.net_amount }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Pending Amount:</label>
							<span>{{ order.pending_amount }}</span>
						</div>
					</div>
				</template>
				<template #footer>
					<Button @click="$router.back()" label="Go back" severity="warn" outlined class="mt-8" />
				</template>button
			</Card>
			<Card>
				<template #title>
					<span>Payment History</span>
				</template>
			</Card>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<Card>
				<template #title>
					<span>Items</span>
				</template>
				<template #content>
					<DataTable :value="orderItems" tableStyle="min-width: 20rem">
						<Column field="product_name" header="Product">
							<template #body="slotProps">
								{{ slotProps.data.product_obj.name }}
							</template>
						</Column>
						<Column field="quantity" header="Quantity"></Column>
						<Column field="price_at_time_of_order" header="Unit Price"></Column>
						<Column field="total" header="Total"></Column>
						<template #empty>
							<span class="flex justify-center">No Orders found.</span>
						</template>
					</DataTable>
				</template>
			</Card>
			<Card>
				<template #title>
					<span>Returned Items</span>
				</template>
				<template #content>
					<DataTable :value="returnItems" tableStyle="min-width: 20rem">
						<Column field="product_name" header="Product">
							<template #body="slotProps">
								{{ slotProps.data.product_obj.name }}
							</template>
						</Column>
						<Column field="quantity" header="Quantity"></Column>
						<Column field="total" header="Total"></Column>
						<template #empty>
							<span class="flex justify-center">No Orders found.</span>
						</template>
					</DataTable>
				</template>
			</Card>
		</div>
	</div>
</template>