<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router';
import moment from 'moment';
import axios from '@/plugins/axios'
import paymentsLisCard from '@/components/payments/paymentsLisCard.vue';

const route = useRoute()
const order = ref({})
const orderItems = ref([])
const returnOrder = ref()
const returnItems = ref([])
const payments = ref([])

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
		console.log('Order', order.value);

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

const fetchPayments = async () => {
	try {
		const response = await axios.get('/api/inventory/payments', {
			params: {
				order_id: route.params.id,
			},
		});

		payments.value = response.data;
	} catch (error) {
		console.error('Error fetching payments:', error);
	}
}
const handlePayment = async () => {
	await fetchOrder();
	await fetchPayments();
}
onMounted(async () => {
	await fetchPayments();
	await fetchOrder();
	await fetchOrderItems();
	await fetchReturn();
	await fetchReturnItems();
})
</script>
<template>
	<div>
		<div class="grid grid-cols-5 gap-4 mb-4">
			<Card class="col-span-3">
				<template #title>
					<span>Order Details</span>
				</template>
				<template #content>
					<div class="grid grid-cols-2 gap-4">
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Order Number:</label>
							<span>{{ order.order_number }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Order Category:</label>
							<span>{{ order.order_type }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Client/Company:</label>
							<span>{{ order.stakeholder_obj?.name }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Order Date:</label>
							<span>{{ moment(order.created_at).format('YYYY-MM-DD') }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Current Status:</label>
							<Tag :value="order.order_status" :severity="getSeverity(order.order_status)" />
						</div>
					</div>
					<div class="grid grid-cols-2 gap-4 border-t mt-8 pt-8">
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Gross Amount:</label>
							<span>{{ order.gross_amount }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Discount Applied:</label>
							<span>{{ order.discount }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Net Payable:</label>
							<span>{{ order.net_amount }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Post-Return Amount:</label>
							<span>{{ order.total_amount }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Outstanding Balance:</label>
							<span>{{ order.pending_amount }}</span>
						</div>
					</div>
				</template>
				<template #footer>
					<Button @click="$router.back()" label="Go back" severity="warn" outlined class="mt-8" />
				</template>button
			</Card>
			<Card class="col-span-2">
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
		</div>
		<div class="grid grid-cols-5 gap-4">
			<Card class="col-span-2">
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
			<Card class="col-span-3">
				<template #title>
					<span>Payment History</span>
				</template>
				<template #content>
					<paymentsLisCard :payments="payments" :pendingAmount="order.pending_amount" :orderId="route.params.id"
						:companyId="order.stakeholder" @instance-added="handlePayment" />
				</template>
			</Card>
		</div>
	</div>
</template>