<template>
	<div>
		<div class="mb-4">
			<div class="grid grid-cols-3 gap-4 mb-4">
				<div v-for="(item, index) in summaryData" :key="index"
					class="border border-gray-300 rounded-lg p-4 flex">
					<div class="bg-[#E5FAFB] w-[52px] h-[52px] mr-4 flex justify-center items-center"><i
							:class="item.icon"></i>
					</div>
					<div>
						<h3 class="text-2xl" style="font-weight:600;">{{ item.value }}</h3>
						<span>{{ item.label }}</span>
					</div>
				</div>
			</div>
			<div class="grid grid-cols-2 gap-4">
				<div class="flex flex-col gap-4 col-span-1">
					<!-- sales statistics -->
					<div class="grid grid-cols-2 gap-2">
						<div v-for="(item, index) in salesData" :key="index"
							class="border border-gray-300 rounded-lg p-4 flex">
							<div class="bg-[#FFF5EB] w-[52px] h-[52px] mr-4 flex justify-center items-center"><i
									:class="item.icon"></i>
							</div>
							<div>
								<h3 class="text-2xl" style="font-weight:600;">{{ item.value }}</h3>
								<span>{{ item.label }}</span>
							</div>
						</div>
					</div>
					<!-- purchase statistics -->
					<div class="grid grid-cols-2 gap-2">
						<div v-for="(item, index) in purchaseData" :key="index"
							class="border border-gray-300 rounded-lg p-4 flex">
							<div class="bg-[#F2EEFF] w-[52px] h-[52px] mr-4 flex justify-center items-center"><i
									:class="item.icon"></i>
							</div>
							<div>
								<h3 class="text-2xl" style="font-weight:600;">{{ item.value }}</h3>
								<span>{{ item.label }}</span>
							</div>
						</div>
					</div>
				</div>
				<div class="col-span-1">
					<stockChart />
				</div>
			</div>
		</div>
		<div class="grid grid-cols-3 gap-4">
			<turnOverChart />
			<salesPaymentChart />
			<purchasePaymentChart />

		</div>
	</div>
</template>

<script setup>
import { onMounted, ref, computed, watch } from 'vue';
import axios from '@/plugins/axios'
import stockChart from '@/components/home/stockChart.vue';
import salesPaymentChart from '@/components/home/salesPaymentChart.vue';
import purchasePaymentChart from '@/components/home/purchasePaymentChart.vue';
import turnOverChart from '@/components/home/turnOverChart.vue';

const salesRevenue = ref()
const purchaseCredit = ref();
const orders = ref([]);
const totalCustomers = ref(0);
const totalSuppliers = ref(0);
const salesOrders = ref([]);
const purchaseOrders = ref([]);
// const selectedMonth = ref(new Date())
const pendingRecievables = ref();
const collectedRecievables = ref();
const outstandingPayables = ref();
const setteledPayables = ref();
const totalProducts = ref();



const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders');
		orders.value = response.data
		// Sales order
		salesOrders.value = orders.value.filter(order => order.order_type == "SO")
		salesRevenue.value = salesOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);
		pendingRecievables.value = salesOrders.value.reduce((sum, order) => sum + parseFloat(order.pending_amount), 0);
		collectedRecievables.value = salesRevenue.value - pendingRecievables.value;

		// Purchase order
		purchaseOrders.value = orders.value.filter(order => order.order_type == "PO")
		purchaseCredit.value = purchaseOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);
		outstandingPayables.value = purchaseOrders.value.reduce((sum, order) => sum + parseFloat(order.pending_amount), 0);
		setteledPayables.value = purchaseCredit.value - outstandingPayables.value;


	} catch (error) {
		console.log(error);

	}
}

const fetchCustomers = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders');
		totalCustomers.value = response.data.length;

		totalCustomers.value = response.data
			.filter(item => item.type == "Customer")

		totalSuppliers.value = response.data
			.filter(item => item.type == "Supplier")

	} catch (error) {
		console.error('Error fetching customers:', error);
	}
};

const fetchProducts = async () => {
	try {
		const response = await axios.get('/api/inventory/products');
		totalProducts.value = response.data.length;

	} catch (error) {
		console.error('Error fetching customers:', error);
	}
};

const salesData = computed(() => [
	{ value: salesOrders.value.length, label: 'Sales Orders', icon: 'pi pi-arrow-circle-down' },
	{ value: salesRevenue.value, label: 'Sales Revenue', icon: 'pi pi-indian-rupee' },
	{ value: pendingRecievables.value, label: 'Pending Recievables', icon: 'pi pi-indian-rupee' },
	{ value: collectedRecievables.value, label: 'Collected Recievables', icon: 'pi pi-indian-rupee' },
]);

const purchaseData = computed(() => [
	{ value: purchaseOrders.value.length, label: 'Purchase Orders', icon: 'pi pi-arrow-circle-up' },
	{ value: purchaseCredit.value, label: 'Purchase Credit', icon: 'pi pi-indian-rupee' },
	{ value: outstandingPayables.value, label: 'Outstanding Payables', icon: 'pi pi-indian-rupee' },
	{ value: setteledPayables.value, label: 'Setteled Payables', icon: 'pi pi-users' }
]);

const summaryData = computed(() => [
	{ value: totalProducts.value, label: 'Total Products', icon: 'pi pi-cart-plus' },
	{ value: totalCustomers.value.length, label: 'Total Customers', icon: 'pi pi-users' },
	{ value: totalSuppliers.value.length, label: 'Total Suppliers', icon: 'pi pi-users' }
]);

onMounted(async () => {
	await fetchOrders()
	fetchCustomers();
	fetchProducts();
})

</script>