<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import moment from 'moment';
import { debounce } from 'lodash';
import "vue3-circle-progress/dist/circle-progress.css";
import CircleProgress from "vue3-circle-progress";

const orders = ref();
const searchInput = ref('');
const filterDates = ref();
const totalOrdersCount = ref(0);
const cloedOrderCount = ref(0);
const salesOrderCount = ref(0);
const purchaseOrderCount = ref(0);


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
			params: {
				search,
				date_added__gte: filterDates.value ? filterDates.value[0] : null,
				date_added__lte: filterDates.value ? filterDates.value[1] : null,
			},
		});

		orders.value = response.data;
		totalOrdersCount.value = orders.value.length;
		salesOrderCount.value = orders.value.filter(item => item.order_type === 'SO').length;
		purchaseOrderCount.value = orders.value.filter(item => item.order_type === 'PO').length;
		cloedOrderCount.value = orders.value.filter(item => item.order_status === 'Closed').length;
	} catch (error) {
		console.error('Error fetching orders:', error);
	}
}

const debouncedFetchOrders = debounce(fetchOrders, 300);
watch(searchInput, (newVal) => {
	debouncedFetchOrders(newVal);
});

watch(filterDates, (newVal) => {
	debouncedFetchOrders();
});
onMounted(() => {
	fetchOrders();
})


</script>

<template>
	<div class="">
		<div class="flex gap-4">
			<Card>
				<template #title>
					Total Orders
				</template>
				<template #content>
					<circle-progress :percent="totalOrdersCount" show-percent fill-color="#9B59B6" empty-color="#9B59B6"
						class="custom-percent" transition="300" />
				</template>
			</Card>
			<Card>
				<template #title>
					Sales Orders
				</template>
				<template #content>
					<circle-progress :percent="salesOrderCount" show-percent fill-color="#7ED321" empty-color="#7ED321"
						class="custom-percent" transition="300" />
				</template>
			</Card>
			<Card>
				<template #title>
					Purchase Orders
				</template>
				<template #content>
					<circle-progress :percent="purchaseOrderCount" show-percent fill-color="#F5A623" empty-color="#F5A623"
						class="custom-percent" transition="300" />
				</template>
			</Card>
			<Card>
				<template #title>
					Closed Orders
				</template>
				<template #content>
					<circle-progress :percent="cloedOrderCount" show-percent fill-color="#288feb" empty-color="#288feb"
						class="custom-percent" transition="300" />
				</template>
			</Card>
		</div>
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
							<DatePicker v-model="filterDates" selectionMode="range" :manualInput="false" class="mr-4"
								placeholder="Date Range" showIcon />
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

<style>
.custom-percent {
	font-size: 25px;
	font-weight: bold;
}
</style>