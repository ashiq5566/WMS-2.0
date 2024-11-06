<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import { debounce } from 'lodash';

const products = ref();
const searchInput = ref('');

const fetchProducts = async (search) => {
	try {
		const response = await axios.get('/api/inventory/products/', {
			params: {
				search,
			},
		});

		products.value = response.data;
	} catch (error) {
		console.error('Error fetching products:', error);
	}
}
const reloadTable = () => {
	fetchProducts();
};

const debouncedFetchOrders = debounce(fetchProducts, 300)
watch(searchInput, (newVal) => {
	debouncedFetchOrders(newVal);
});

onMounted(() => {
	fetchProducts();
})


</script>

<template>
	<div class="">
		<AddStakeHolderModal @instance-added="reloadTable" />
		<Card class="mt-4">
			<template #content>
				<DataTable :value="products" tableStyle="min-width: 50rem">
					<template #header>
						<div class="flex justify-end">
							<IconField>
								<InputIcon>
									<i class="pi pi-search" />
								</InputIcon>
								<InputText v-model="searchInput" placeholder="Keyword Search" />
							</IconField>
						</div>
					</template>
					<Column field="product_id" header="ID"></Column>
					<Column field="name" header="Name">
						<template #body="slotProps">
							<router-link :to="{ name: 'stocks-id', params: { id: slotProps.data.id } }">
								<span class="font-bold">
									{{ slotProps.data.name }}
								</span>
							</router-link>
						</template>
					</Column>
					<Column field="selling_price" header="Selling Price"></Column>
					<Column field="price_at_time_of_purchase" header="Purchased Price"></Column>
					<Column field="qty_purchased" header="Qty Purchased"></Column>
					<template #empty>
						<span class="flex justify-center">No stakeholders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>
