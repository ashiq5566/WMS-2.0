<template>
	<div>
		<div class="grid grid-cols-2 gap-4">
			<Card class="col-span-2">
				<template #title>Product Status</template>
				<template #content>
					<div>
						<apexchart width="500" type="bar" :options="options" :series="series">
						</apexchart>
					</div>
				</template>
			</Card>
			<!-- <Card>
				<template #title>Money Flow</template>
			</Card> -->
		</div>
		<div class="grid grid-cols-3 gap-4 mt-4">
			<Card>
				<template #title>Accounts Receivable(Sales)</template>
			</Card>
			<Card>
				<template #title>Accounts Payable(Purchases)</template>
			</Card>
			<Card>
				<template #title>Turn Over</template>
			</Card>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '@/plugins/axios'


const products = ref([])
const labels = ref([])
const fetchProducts = async () => {
	try {
		const response = await axios.get('/api/inventory/products')
		products.value = response.data
		labels.value = response.data.map(product => product.name)
		console.log("labels: " + response);
	} catch (error) {
		console.log(error);

	}
}

const options = ref({
	chart: {
		id: 'vuechart-example'
	},
	xaxis: {
		categories: labels.value,
		labels: {
			style: {
				colors: '#333', // Customize label color if needed
				fontSize: '12px'  // Customize font size
			}
		}

	}
})

const series = ref([
	{
		name: 'series-1',
		data: products.value.map(p => p.qty_available),
	}
])

onMounted(() => {
	fetchProducts()
})
</script>