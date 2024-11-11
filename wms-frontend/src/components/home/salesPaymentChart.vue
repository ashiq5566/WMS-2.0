<template>
	<Card>
		<template #title>Accounts Receivable(Sales)</template>
		<template #content>
			<div>
				<apexchart width="700" type="bar" :options="options" :series="series">
				</apexchart>
			</div>
		</template>
	</Card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '@/plugins/axios'


const stakeHolders = ref([])
const labels = ref([])
const paymentDetails = ref([])

const options = ref({
	chart: {
		id: 'vuechart-example'
	},
	plotOptions: {
		bar: {
			horizontal: true // Set to true for horizontal bars
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
		data: [] // Initialize empty; will be set dynamically
	}
]);


const fetchStakeholders = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders', {
			params: {
				type: 'Customer'
			}
		});
		stakeHolders.value = response.data;

		// Update labels and series data
		labels.value = stakeHolders.value.map(item => item.name);
		console.log("Stakeholders labels: ", labels.value);

		// Update options
		options.value = {
			xaxis: {
				categories: labels.value
			}
		};

		console.log("labels:", labels.value);
	} catch (error) {
		console.error('Error fetching products:', error);
	}
};

const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders/get_total_by_stakeholders', {
			params: {
				stakeholder_ids: stakeHolders.value.map(item => item.id)
			}
		});
		paymentDetails.value = response.data
		console.log("Stake=", paymentDetails.value);

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
	await fetchStakeholders()
	await fetchOrders()
})
</script>