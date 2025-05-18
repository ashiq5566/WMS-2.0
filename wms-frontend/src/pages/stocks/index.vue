<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import { debounce } from 'lodash';
import { useToast } from "primevue/usetoast";

const products = ref();
const searchInput = ref('');
const editingRows = ref([]);
const toast = useToast()
const formData = ref({})

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

const onRowEditSave = async (event) => {
	formData.value.name = event.newData.name
	formData.value.selling_price = event.newData.selling_price
	formData.value.qty_available = event.newData.qty_available
	formData.value.price_at_time_of_purchase = event.newData.price_at_time_of_purchase

	const response = await axios.put(`/api/inventory/products/${event.data.id}/`, formData.value);
	toast.add({ severity: 'success', summary: 'Success', detail: `Product Updated SuccessFully`, life: 3000 });
	fetchProducts()
};
</script>

<template>
	<div class="">
		<AddStakeHolderModal @instance-added="reloadTable" />
		<Card class="mt-4">
			<template #content>
				<DataTable v-model:editingRows="editingRows" :value="products" editMode="row" dataKey="id"
					@row-edit-save="onRowEditSave">
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
					<Column header="Image">
						<template #body="slotProps">
							<img :src="slotProps.data.image" alt="Image" class="shadow-lg" width="64" />
						</template>
					</Column>
					<Column field="name" header="Name">
						<template #editor="{ data, field }">
							<InputText v-model="data[field]" fluid />
						</template>
					</Column>
					<Column field="selling_price" header="Selling Price">
						<template #editor="{ data, field }">
							<InputText v-model="data[field]" fluid />
						</template>
					</Column>
					<Column field="price_at_time_of_purchase" header="Purchased Price">
						<template #editor="{ data, field }">
							<InputText v-model="data[field]" fluid />
						</template>
					</Column>
					<Column field="qty_available" header="Stock"></Column>
					<Column field="qty_purchased" header="Qty Purchased"></Column>
					<Column field="qty_sold" header="Qty Sold"></Column>
					<Column :rowEditor="true" style="width: 10%; min-width: 8rem" bodyStyle="text-align:center"></Column>
					<template #empty>
						<span class="flex justify-center">No stakeholders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>
