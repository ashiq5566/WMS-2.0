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
				<apexchart width="400" type="pie" :options="options" :series="series">
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
		type: 'pie', // Set chart type to 'pie'
	},
	labels: ['Sales', 'Purchase'],  // Labels for each data point
	colors: ['#26D4DF', '#966CFF'],  // Colors for each section of the pie
});

const series = ref([]);

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

		series.value = [totalSalesAmount, totalPurchaseAmount]


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