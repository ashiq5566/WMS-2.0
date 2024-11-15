<template>
	<div>
		<div class="grid grid-cols-3 gap-4 mb-4">
			<div class="flex col-span-2 gap-2">
				<Card class="w-1/2">
					<template #title>
						<div class="flex justify-between">
							<span>Sales Overview</span>
							<DatePicker v-model="selectedMonth" view="month" dateFormat="mm/yy" placeholder="Select Month" show-icon
								class="w-[200px]" />
						</div>
					</template>
					<template #content>
						<div class="flex flex-col gap-4">
							<div v-for="(item, index) in salesData" :key="index" class="border border-gray-300 rounded-lg p-4 flex">
								<div class="bg-[#FFF5EB] w-[50px] h-[50px] mr-4 flex justify-center items-center"><i
										:class="item.icon"></i></div>
								<div>
									<h3 class="text-2xl">{{ item.value }}</h3>
									<span>{{ item.label }}</span>
								</div>
							</div>
						</div>
					</template>
				</Card>
				<Card class="w-1/2">
					<template #title>
						<div class="flex justify-between">
							<span>Purchase Overview</span>
							<DatePicker v-model="selectedMonth" view="month" dateFormat="mm/yy" placeholder="Select Month" show-icon
								class="w-[200px]" />
						</div>
					</template>
					<template #content>
						<div class="flex flex-col gap-4">
							<div v-for="(item, index) in purchaseData" :key="index"
								class="border border-gray-300 rounded-lg p-4 flex">
								<div class="bg-[#F2EEFF] w-[50px] h-[50px] mr-4 flex justify-center items-center"><i
										:class="item.icon"></i></div>
								<div>
									<h3 class="text-2xl">{{ item.value }}</h3>
									<span>{{ item.label }}</span>
								</div>
							</div>
						</div>
					</template>
				</Card>
			</div>
			<div class="col-span-1">
				<turnOverChart class="col-span-1" />
			</div>
		</div>
		<div class="grid grid-cols-3 gap-4 mb-4">
			<div class="col-span-2 flex gap-2">
				<Card class="w-1/2">
					<template #title>
						Payements Overview (Sales)
					</template>
				</Card>
				<Card class="w-1/2">
					<template #title>
						Payements Overview (Purchase)
					</template>
				</Card>
			</div>
			<div class="col-span-1">
				<salesPaymentChart />
				<purchasePaymentChart />
			</div>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<stockChart class="col-span-1" />
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
const purchaseRevenue = ref();
const orders = ref([]);
const totalCustomers = ref(0);
const totalSuppliers = ref(0);
const salesOrders = ref([]);
const purchaseOrders = ref([]);
const selectedMonth = ref(new Date())


const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders', {
			params: {
				order_month: selectedMonth.value.getMonth() + 1
			}
		});
		orders.value = response.data

		salesOrders.value = orders.value.filter(order => order.order_type == "SO")
		salesRevenue.value = salesOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);

		purchaseOrders.value = orders.value.filter(order => order.order_type == "PO")
		purchaseRevenue.value = purchaseOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount), 0);


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

const salesData = computed(() => [
	{ value: salesRevenue.value, label: 'Sales Revenue', icon: 'pi pi-truck' },
	{
		value: salesOrders.value.length, label: 'Total Orders', icon: 'pi pi-cart-arrow-down'
	},
	{ value: totalCustomers.value.length, label: 'Total Customers', icon: 'pi pi-users' }
]);

const purchaseData = computed(() => [
	{ value: purchaseRevenue.value, label: 'Purchase Revenue', icon: 'pi pi-truck' },
	{
		value: purchaseOrders.value.length, label: 'Total Orders', icon: 'pi pi-cart-arrow-down'
	},
	{ value: totalSuppliers.value.length, label: 'Total Suppliers', icon: 'pi pi-users' }
]);

watch(selectedMonth, () => {
	fetchOrders();
})

onMounted(async () => {
	await fetchOrders()
	fetchCustomers();
})

</script>