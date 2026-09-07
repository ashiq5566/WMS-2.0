<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import { debounce } from 'lodash';
import { useToast } from "primevue/usetoast";
import AddProductModal from "@/components/products/AddProductModal.vue";

const products = ref([]);
const searchInput = ref('');
const editingRows = ref([]);
const toast = useToast()

const fetchProducts = async (search = searchInput.value) => {
	try {
		const response = await axios.get('/api/inventory/products/', {
			params: {
				search,
			},
		});

		products.value = response.data;
	} catch (error) {
		console.error('Error fetching products:', error);
		toast.add({ severity: 'error', summary: 'Unable to load stock', detail: 'Please try again.', life: 3000 });
	}
}
const reloadTable = () => {
	fetchProducts(searchInput.value);
};

const debouncedFetchProducts = debounce(fetchProducts, 300)
watch(searchInput, (newVal) => {
	debouncedFetchProducts(newVal);
});

onBeforeUnmount(() => debouncedFetchProducts.cancel());

onMounted(() => {
	fetchProducts();
})

const onRowEditSave = async (event) => {
	const product = event.newData;
	try {
		const payload = {
			name: product.name,
			selling_price: product.selling_price,
			price_at_time_of_purchase: product.price_at_time_of_purchase
		};
		await axios.put(`/api/inventory/products/${product.id}/`, payload);
		toast.add({ severity: 'success', summary: 'Success', detail: 'Product updated successfully', life: 3000 });
		fetchProducts();
	} catch (error) {
		console.error('Error updating product:', error);
		toast.add({ severity: 'error', summary: 'Update failed', detail: 'Stock details were not saved.', life: 3000 });
		fetchProducts();
	}
};
</script>

<template>
	<div class="">
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
							<AddProductModal @instance-added="reloadTable" class="ml-4" />
						</div>
					</template>
					<Column field="product_id" header="ID"></Column>
					<Column header="Image">
						<template #body="slotProps">
							<img v-if="slotProps.data.image" :src="slotProps.data.image" :alt="slotProps.data.name"
								class="shadow-lg object-cover" width="64" height="64" />
							<span v-else class="text-sm text-surface-500">No image</span>
						</template>
					</Column>
					<Column field="name" header="Name">
						<template #editor="{ data, field }">
							<InputText v-model="data[field]" fluid />
						</template>
					</Column>
					<Column field="selling_price" header="Selling Price">
						<template #editor="{ data, field }">
							<InputNumber v-model="data[field]" :min="0" fluid />
						</template>
					</Column>
					<Column field="price_at_time_of_purchase" header="Purchased Price">
						<template #editor="{ data, field }">
							<InputNumber v-model="data[field]" :min="0" fluid />
						</template>
					</Column>
					<Column field="qty_available" header="Total Stock">
						<template #body="slotProps">
							<span>{{ slotProps.data.qty_available }}</span>
						</template>
					</Column>
					<Column header="Size Stock">
						<template #body="slotProps">
							<span v-if="slotProps.data.sizes?.length">
								{{slotProps.data.sizes.map((size) => `${size.size}: ${size.stock}`).join(', ')}}
							</span>
							<span v-else class="text-sm text-surface-500">Not sized</span>
						</template>
					</Column>
					<Column :rowEditor="true" style="width: 10%; min-width: 8rem" bodyStyle="text-align:center">
					</Column>
					<template #empty>
						<span class="flex justify-center">No products found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>
