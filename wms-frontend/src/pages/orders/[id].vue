<script setup>
import { useRoute } from 'vue-router';
import moment from 'moment';
import axios from '@/plugins/axios'
import { ref, onMounted } from 'vue'

const route = useRoute()
const order = ref({})

const fetchOrder = async () => {
	try {
		const response = await axios.get(`/api/inventory/orders/${route.params.id}`)
		order.value = response.data
	} catch (error) {
		console.log(error);

	}
}

onMounted(() => {
	fetchOrder();
})
</script>
<template>
	<div>
		<h1>{{ route.params.id }}</h1>
		<Card class="w-1/2">
			<template #title>
				<span>Order Details</span>
			</template>
			<template #content>
				<div class="">
					<div class="flex items-center">
						<label>Order No:</label>
						<span>{{ order.order_number }}</span>
					</div>
					<div class="flex items-center">
						<label>Company Name:</label>
						<span>{{ order.stakeholder_obj?.name }}</span>
					</div>
					<div class="flex items-center">
						<label>Order Date:</label>
						<span>{{ moment(order.created_at).format('YYYY-MM-DD') }}</span>
					</div>
					<div class="flex items-center">
						<label>Order Status</label>
						<span>{{ order.order_status }}</span>
					</div>
				</div>
			</template>
			<template #footer>
				<button @click="$router.back()">Go Back</button>
			</template>
		</Card>
	</div>
</template>