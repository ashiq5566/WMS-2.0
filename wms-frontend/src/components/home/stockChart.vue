<template>
	<Card>
		<template #title>Stock</template>
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


const products = ref([])
const labels = ref([])

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
		data: [], // Initialize empty; will be set dynamically
		color: '#4A90E2'
	}
]);


const fetchProducts = async () => {
	try {
		const response = await axios.get('/api/inventory/products');
		products.value = response.data;

		// Update labels and series data
		labels.value = products.value.map(product => product.name);
		series.value = [
			{
				name: 'Product Availability',
				data: products.value.map(product => product.qty_available) // Example: use qty_available or any other field
			}
		];

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

onMounted(async () => {
	await fetchProducts()
})
</script>