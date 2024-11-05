<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import moment from 'moment';
import { debounce } from 'lodash';

const orders = ref();
const searchInput = ref('');

const getSeverity = (status) => {
	switch (status) {
		case 'Issued':
			return 'warn';

		case 'Delivered':
			return 'success';

		case 'Recieved':
			return 'info';

		case 'Cancelled':
			return 'warn';

		case 'Closed':
			return 'danger';
	}
}


const fetchOrders = async (search) => {
	try {
		const response = await axios.get('/api/inventory/orders', {
			params: { search },
		});

		orders.value = response.data;
	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}

const debouncedFetchOrders = debounce(fetchOrders, 300);
watch(searchInput, (newVal) => {
	debouncedFetchOrders(newVal);
});
onMounted(() => {
	fetchOrders();
})


</script>

<template>
	<div class="">
		<div class="flex justify-end">
			<router-link :to="{ name: 'orders-create' }">
				<Button label="Create Order" />
			</router-link>
		</div>
		<Card class="mt-4">
			<template #content>
				<DataTable :value="orders" tableStyle="min-width: 50rem">
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
					<Column field="id" header="ID#">
						<template #body="slotProps">
							<router-link :to="{ name: 'orders-id', params: { id: slotProps.data.id } }">
								<span class="font-bold">
									{{ slotProps.data.id }}
								</span>
							</router-link>
						</template>
					</Column>
					<Column field="date_added" header="Order Date" sortable>
						<template #body="slotProps">
							{{ moment(slotProps.data.date_added).format('DD/MM/YYYY') }}
						</template>
					</Column>
					<Column field="order_type" header="Order Type"></Column>
					<Column field="order_number" header="Order Number"></Column>
					<Column field="stakeholder" header="Stakeholder">
						<template #body="slotProps">
							{{ slotProps.data.stakeholder_obj.name }}
						</template>
					</Column>
					<Column field="net_amount" header="Net Amount"></Column>
					<Column field="order_status" header="Status">
						<template #body="slotProps">
							<Tag :value="slotProps.data.order_status" :severity="getSeverity(slotProps.data.order_status)" />
						</template>
					</Column>
					<template #empty>
						<span class="flex justify-center">No Orders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>