<template>
	<Card>
		<template #title>
			<div class="flex justify-between">
				<span>Turn Over</span>
				<DatePicker v-model="selectedMonth" view="month" dateFormat="mm/yy" placeholder="Select Month" show-icon
					class="w-[200px]" />
			</div>
		</template>
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
import { watch } from 'vue';


const orders = ref([])
const selectedMonth = ref(new Date())
const options = ref({
	chart: {
		id: 'vuechart-example',
		type: 'bar', // Make sure the type is set to 'bar'
	},
	colors: ['#2E93fA', '#66DA26'],  // Set colors for each bar in series
	plotOptions: {
		bar: {
			columnWidth: '50%'  // Bar width
		}
	},
	xaxis: {
		categories: ['Sales', 'Purchase'],  // x-axis categories
		labels: {
			style: {
				colors: '#333',  // Label colors
				fontSize: '12px'  // Label font size
			}
		}
	},
});

const series = ref([
	{
		name: 'Turn Over',
		data: [],
		color: '#9B59B6'
	}
]);

const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders/', {
			params: {
				order_month: selectedMonth.value.getMonth() + 1
			}
		});
		orders.value = response.data

		const totalSalesAmount = orders.value
			.filter(order => order.order_type == "SO")
			.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);

		// Calculate total purchase amount
		const totalPurchaseAmount = orders.value
			.filter(order => order.order_type == "PO")
			.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);
		series.value = [
			{
				name: 'Turn Over',
				data: [totalSalesAmount, totalPurchaseAmount] // Example: use qty_available or any other field
			}
		];

	} catch (error) {

	}
}

onMounted(async () => {
	await fetchOrders()
})

watch(selectedMonth, () => {
	fetchOrders();
})
</script>