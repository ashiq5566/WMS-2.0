<script setup>
import { useRoute } from 'vue-router';
import moment from 'moment';
import axios from '@/plugins/axios'
import { ref, onMounted } from 'vue'

const route = useRoute()
const returnOrder = ref({})
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

const fetchReturnOrder = async () => {
	try {
		const response = await axios.get(`/api/inventory/returns/${route.params.id}`)
		returnOrder.value = response.data
	} catch (error) {
		console.log(error);

	}
}

const fetchReturnItems = async () => {
	try {
		const response = await axios.get('/api/inventory/return-items/', {
			params: {
				return_order: route.params.id,
			},
		})
		returnItems.value = response.data
	} catch (error) {
		console.log(error);

	}
}

onMounted(() => {
	fetchReturnOrder();
	fetchReturnItems()
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
							<label class="font-bold">Return Type:</label>
							<span>{{ returnOrder.return_type }}</span>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Bill:</label>
							<router-link :to="{ name: 'orders-id', params: { id: returnOrder.order_obj?.id } }">
								<span class="font-bold">
									{{ returnOrder.order_obj?.order_number }}
								</span>
							</router-link>
						</div>
						<div class="flex justify-between w-3/4">
							<label class="font-bold">Date:</label>
							<span>{{ moment(returnOrder.created_at).format('YYYY-MM-DD') }}</span>
						</div>
					</div>
				</template>
				<template #footer>
					<Button @click="$router.back()" label="Go back" severity="warn" outlined class="mt-8" />
				</template>button
			</Card>
		</div>
		<Card>
			<template #title>
				<span>Items</span>
			</template>
			<template #content>
				<DataTable :value="returnItems" tableStyle="min-width: 30rem" scrollHeight="300px">
					<Column field="product_name" header="Product">
						<template #body="slotProps">
							{{ slotProps.data.product_obj.name }}
						</template>
					</Column>
					<Column field="quantity" header="Quantity"></Column>
					<Column field="price_at_return" header="Unit Price"></Column>
					<Column field="total" header="Total"></Column>
					<template #empty>
						<span class="flex justify-center">No Orders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>