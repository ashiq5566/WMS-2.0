<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue";
import axios from '@/plugins/axios';
import moment from 'moment';
import { debounce } from 'lodash';
import AddPaymentModal from "@/components/payments/AddPaymentModal.vue";


const payments = ref();
const filterDates = ref();
const salesRevenue = ref()
const purchaseCredit = ref();
const orders = ref([]);
const salesOrders = ref([]);
const purchaseOrders = ref([]);
const selectedMonth = ref()
const pendingRecievables = ref();
const collectedRecievables = ref();
const outstandingPayables = ref();
const setteledPayables = ref();
const stakeholders = ref();
const selectedStakeholder = ref();
const selectedType = ref();

const orderTypes = [
	{ label: "Sales Order", value: "SO" },
	{ label: "Purchase Order", value: "PO" },
]

const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders', {
			params: {
				order_month: selectedMonth.value ? selectedMonth.value.getMonth() + 1 : null
			}
		});
		orders.value = response.data
		// Sales order
		salesOrders.value = orders.value.filter(order => order.order_type == "SO")
		salesRevenue.value = salesOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);
		pendingRecievables.value = salesOrders.value.reduce((sum, order) => sum + parseFloat(order.pending_amount), 0);

		// Purchase order
		purchaseOrders.value = orders.value.filter(order => order.order_type == "PO")
		purchaseCredit.value = purchaseOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);
		outstandingPayables.value = purchaseOrders.value.reduce((sum, order) => sum + parseFloat(order.pending_amount), 0);
	} catch (error) {
		console.log(error);

	}
}

const fetchPayments = async () => {
	try {
		const response = await axios.get('/api/inventory/payments', {
			params: {
				payment_date__gte: filterDates.value ? filterDates.value[0] : null,
				payment_date__lte: filterDates.value ? filterDates.value[1] : null,
				order__stakeholder_id: selectedStakeholder.value ? selectedStakeholder.value : null,
				order_month: selectedMonth.value ? selectedMonth.value.getMonth() + 1 : null,
				order__order_type: selectedType.value,
			}
		});

		payments.value = response.data;

		const purchasePayments = payments.value.filter(payment => payment.order_obj.order_type == "PO")
		setteledPayables.value = purchasePayments.reduce((sum, payment) => sum + parseFloat(payment.amount), 0);

		const salesPayments = payments.value.filter(payment => payment.order_obj.order_type == "SO")
		collectedRecievables.value = salesPayments.reduce((sum, payment) => sum + parseFloat(payment.amount), 0);

	} catch (error) {
		console.error('Error fetching payments:', error);
	}
}

const fetchStakeholders = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders/');
		stakeholders.value = response.data.map(item => ({ value: item.id, label: item.name }));
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}

const debouncedFetchOrders = debounce(fetchPayments, 300);

const statisticsData = computed(() => [
	{ value: pendingRecievables.value, label: 'Pendig Recievables', icon: 'pi pi-arrow-circle-down' },
	{ value: collectedRecievables.value, label: 'Collected Recievables', icon: 'pi pi-indian-rupee' },
	{ value: outstandingPayables.value, label: 'Outstanding Payables', icon: 'pi pi-indian-rupee' },
	{ value: setteledPayables.value, label: 'setteled Payables', icon: 'pi pi-indian-rupee' },
]);

watch(filterDates, (newVal) => {
	debouncedFetchOrders();
});

watch(selectedMonth, () => {
	fetchOrders();
	fetchPayments();
})

watch(selectedStakeholder, (newVal) => {
	fetchPayments();
});

watch(selectedType, (newVal) => {
	fetchPayments();
});

const reloadTable = () => {
	fetchPayments();
};

onMounted(() => {
	fetchPayments();
	fetchOrders();
	fetchStakeholders();
})


</script>

<template>
	<div class="">
		<div class="flex justify-end">
			<DatePicker v-model="selectedMonth" view="month" dateFormat="mm/yy" placeholder="Select Month" show-icon
				class="w-[200px] mb-4" />
		</div>
		<div class="grid grid-cols-4 gap-4 mb-4">
			<div v-for="(item, index) in statisticsData" :key="index" class="border border-gray-300 rounded-lg p-4 flex">
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
				<DataTable :value="payments" tableStyle="min-width: 50rem">
					<template #header>
						<div class="flex justify-end">
							<Select v-model="selectedType" :options="orderTypes" optionLabel="label" option-value="value"
								placeholder="Select Type" class="mr-4" showClear />
							<Select v-model="selectedStakeholder" :options="stakeholders" optionLabel="label" option-value="value"
								placeholder="Select Company" class="mr-4" filter show-clear />
							<DatePicker v-model="filterDates" selectionMode="range" :manualInput="false" class="mr-4"
								placeholder="Date Range" showIcon />
							<AddPaymentModal @instance-added="reloadTable" />
						</div>
					</template>
					<Column field="id" header="ID#"></Column>
					<Column field="payment_date" header="Date" sortable>
						<template #body="slotProps">
							{{ moment(slotProps.data.payment_date).format('DD/MM/YYYY') }}
						</template>
					</Column>
					<Column field="company_name" header="Company Name">
						<template #body="slotProps">
							{{ slotProps.data.company_obj?.name }}
						</template>
					</Column>
					<Column field="order" header="Order No">
						<template #body="slotProps">
							{{ slotProps.data.order_obj?.order_number }}
						</template>
					</Column>
					<Column field="amount" header="Amount"></Column>
					<Column field="payment_method" header="Method">
					</Column>
					<template #empty>
						<span class="flex justify-center">No Payments found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>