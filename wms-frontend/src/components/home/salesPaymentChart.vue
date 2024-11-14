<template>
	<Card>
		<template #title>Accounts Receivable(Sales)</template>
		<template #content>
			<div>
				<apexchart width="500" type="bar" :options="options" :series="series">
				</apexchart>
			</div>
		</template>
	</Card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '@/plugins/axios'


const customers = ref([])
const labels = ref([])
const paymentDetails = ref([])

const options = ref({
	chart: {
		id: 'vuechart-example'
	},
	plotOptions: {
		bar: {
			horizontal: true,
		}
	},
	xaxis: {
		categories: [],
		labels: {
			style: {
				colors: '#333',
				fontSize: '12px'
			}
		}
	}
});

const series = ref([
	{
		name: 'Product Availability',
		data: [], // Initialize empty; will be set dynamically
		color: '#7ED321'
	}
]);


const fetchCustomers = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders', {
			params: {
				type: 'Customer'
			}
		});
		customers.value = response.data;

		// Update labels and series data
		labels.value = customers.value.map(item => item.name);

		// Update options
		options.value = {
			xaxis: {
				categories: labels.value
			}
		};

		console.log("labels:", labels.value);
	} catch (error) {
		console.error('Error fetching customers:', error);
	}
};

const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders/get_total_by_stakeholders', {
			params: {
				stakeholder_ids: customers.value.map(item => item.id)
			}
		});
		paymentDetails.value = response.data

		series.value = [
			{
				name: 'Pending Payemnts',
				data: paymentDetails.value.map(x => x.amount) // Example: use qty_available or any other field
			}
		];

	} catch (error) {

	}
}

onMounted(async () => {
	await fetchCustomers()
	await fetchOrders()
})
</script>