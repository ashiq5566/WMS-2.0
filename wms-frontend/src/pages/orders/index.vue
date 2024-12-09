<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue";
import axios from '@/plugins/axios';
import moment from 'moment';
import { debounce } from 'lodash';
import "vue3-circle-progress/dist/circle-progress.css";

const orders = ref();
const searchInput = ref('');
const filterDates = ref();
const totalOrdersCount = ref(0);
const cloedOrderCount = ref(0);
const salesOrderCount = ref(0);
const purchaseOrderCount = ref(0);
const selectedStakeholder = ref('');
const stakeholders = ref([]);
const selectedType = ref('');
const selectedStatus = ref('');

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

const statisticsData = computed(() => [
	{ value: totalOrdersCount.value, label: 'Total Orders', icon: 'pi pi-arrow-circle-down' },
	{ value: salesOrderCount.value, label: 'Sales Orders', icon: 'pi pi-indian-rupee' },
	{ value: purchaseOrderCount.value, label: 'Purchase Orders', icon: 'pi pi-indian-rupee' },
	{ value: cloedOrderCount.value, label: 'Closed Orders', icon: 'pi pi-indian-rupee' },
]);

const fetchOrders = async (search) => {
	try {
		const response = await axios.get('/api/inventory/orders', {
			params: {
				search,
				date_added__gte: filterDates.value ? filterDates.value[0] : null,
				date_added__lte: filterDates.value ? filterDates.value[1] : null,
				stakeholder_id: selectedStakeholder.value,
				order_type: selectedType.value,
				order_status: selectedStatus.value,
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

const fetchStakeholders = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders/');
		stakeholders.value = response.data
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}

const filterOrders = (type) => {
	if (type == "Sales Orders") {
		selectedType.value = 'SO';
	} else if (type == "Purchase Orders") {
		selectedType.value = 'PO';
	} else if (type == "Total Orders") {
		selectedType.value = null;
		selectedStatus.value = null;
	} else if (type == "Closed Orders") {
		selectedStatus.value = "Closed"
	}
	fetchOrders()
}

const debouncedFetchOrders = debounce(fetchOrders, 300);
watch(searchInput, (newVal) => {
	debouncedFetchOrders(newVal);
});

watch(selectedStakeholder, (newVal) => {
	fetchOrders();
});

watch(filterDates, (newVal) => {
	debouncedFetchOrders();
});
onMounted(() => {
	fetchOrders();
	fetchStakeholders();

})


</script>

<template>
	<div class="">
		<div class="grid grid-cols-4 gap-4 mb-4">
			<div v-for="(item, index) in statisticsData" :key="index"
				class="border border-gray-300 rounded-lg p-4 flex cursor-pointer" @click="filterOrders(item.label)">
				<div class="bg-[#FFF5EB] w-[52px] h-[52px] mr-4 flex justify-center items-center"><i :class="item.icon"></i>
				</div>
				<div>
					<h3 class="text-2xl" style="font-weight:600;">{{ item.value }}</h3>
					<span>{{ item.label }}</span>
				</div>
			</div>
		</div>
		<Card class="mt-4">
			<template #content>
				<DataTable :value="orders" tableStyle="min-width: 50rem">
					<template #header>
						<div class="flex justify-end gap-4">
							<Select v-model="selectedStakeholder" :options="stakeholders" optionLabel="name" option-value="id"
								placeholder="Select Stakeholder" class="mr-4" filter />
							<DatePicker v-model="filterDates" selectionMode="range" :manualInput="false" placeholder="Date Range"
								showIcon />
							<IconField>
								<InputIcon>
									<i class="pi pi-search" />
								</InputIcon>
								<InputText v-model="searchInput" placeholder="Keyword Search" />
							</IconField>
							<router-link :to="{ name: 'orders-create' }">
								<Button label="Create Order" />
							</router-link>
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