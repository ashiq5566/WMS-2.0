<template>
	<div class="space-y-6 pb-8 text-slate-800 dark:text-slate-100">
		<!-- Dashboard Header -->
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm transition-colors">
			<div>
				<div class="flex items-center gap-2 mb-1">
					<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
					<span class="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Live Operations</span>
				</div>
				<h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
					Warehouse Dashboard
				</h1>
				<p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
					Real-time inventory levels, fulfillment pipelines, and financial settlements
				</p>
			</div>

			<div class="flex items-center gap-2.5">
				<Button
					icon="pi pi-refresh"
					label="Refresh Data"
					:loading="isRefreshing"
					size="small"
					severity="secondary"
					outlined
					class="!text-xs !py-2 !px-3.5 !rounded-lg hover:!bg-slate-100 dark:hover:!bg-slate-800"
					@click="refreshAll"
				/>
			</div>
		</div>

		<!-- Section 1: Top Inventory & Stakeholder Summary -->
		<div>
			<div class="flex items-center justify-between mb-3 px-1">
				<h2 class="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
					Core Assets & Directory
				</h2>
			</div>

			<!-- Skeletons when loading -->
			<div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
				<div v-for="n in 3" :key="n" class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 space-y-3">
					<div class="flex items-center gap-4">
						<Skeleton shape="circle" size="48px" class="dark:!bg-slate-800" />
						<div class="space-y-2 flex-1">
							<Skeleton width="40%" height="24px" class="dark:!bg-slate-800" />
							<Skeleton width="60%" height="16px" class="dark:!bg-slate-800" />
						</div>
					</div>
				</div>
			</div>

			<!-- Loaded Summary Cards -->
			<div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
				<router-link
					v-for="(item, index) in summaryCards"
					:key="index"
					:to="item.route"
					class="group relative p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 hover:border-indigo-400 dark:hover:border-indigo-500/60 shadow-sm hover:shadow-md transition-all duration-200 flex items-center justify-between overflow-hidden"
				>
					<div class="flex items-center gap-4">
						<div
							class="w-12 h-12 rounded-xl flex items-center justify-center text-lg transition-transform group-hover:scale-105"
							:class="item.iconBg"
						>
							<i :class="[item.icon, item.iconColor]"></i>
						</div>
						<div>
							<div class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
								{{ formatNumber(item.value) }}
							</div>
							<div class="text-xs font-medium text-slate-500 dark:text-slate-400">
								{{ item.label }}
							</div>
						</div>
					</div>
					<div class="text-slate-300 dark:text-slate-600 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 group-hover:translate-x-1 transition-all">
						<i class="pi pi-arrow-right text-sm"></i>
					</div>
				</router-link>
			</div>
		</div>

		<!-- Section 2: Financial Streams (Sales & Procurement) -->
		<div class="space-y-4">
			<!-- Sales Stream -->
			<div class="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm transition-colors">
				<div class="flex items-center justify-between mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/60">
					<div class="flex items-center gap-2">
						<div class="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
						<h2 class="text-base font-semibold text-slate-900 dark:text-white">
							Sales & Receivables Pipeline
						</h2>
					</div>
					<router-link
						:to="{ path: '/orders' }"
						class="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
					>
						Manage Orders <i class="pi pi-arrow-up-right text-[10px]"></i>
					</router-link>
				</div>

				<!-- Sales Loading Skeleton -->
				<div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
					<div v-for="n in 4" :key="n" class="p-4 rounded-xl border border-slate-100 dark:border-slate-800/60 space-y-2">
						<Skeleton width="50%" height="14px" class="dark:!bg-slate-800" />
						<Skeleton width="70%" height="24px" class="dark:!bg-slate-800" />
					</div>
				</div>

				<!-- Sales Cards -->
				<div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
					<router-link
						v-for="(item, index) in formattedSalesData"
						:key="index"
						:to="{ path: '/orders' }"
						class="group p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-white dark:hover:bg-slate-800/90 hover:border-emerald-300 dark:hover:border-emerald-500/40 transition-all duration-200"
					>
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-medium text-slate-500 dark:text-slate-400">
								{{ item.label }}
							</span>
							<div class="w-7 h-7 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xs">
								<i :class="item.icon"></i>
							</div>
						</div>
						<div class="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
							{{ item.displayValue }}
						</div>
						<div class="mt-1 text-[11px] text-slate-400 dark:text-slate-500 flex items-center gap-1">
							<span>{{ item.sublabel }}</span>
						</div>
					</router-link>
				</div>
			</div>

			<!-- Procurement Stream -->
			<div class="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm transition-colors">
				<div class="flex items-center justify-between mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/60">
					<div class="flex items-center gap-2">
						<div class="w-2.5 h-2.5 rounded-full bg-violet-500"></div>
						<h2 class="text-base font-semibold text-slate-900 dark:text-white">
							Procurement & Payables Pipeline
						</h2>
					</div>
					<router-link
						:to="{ path: '/orders' }"
						class="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
					>
						Manage Purchase Orders <i class="pi pi-arrow-up-right text-[10px]"></i>
					</router-link>
				</div>

				<!-- Purchase Loading Skeleton -->
				<div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
					<div v-for="n in 4" :key="n" class="p-4 rounded-xl border border-slate-100 dark:border-slate-800/60 space-y-2">
						<Skeleton width="50%" height="14px" class="dark:!bg-slate-800" />
						<Skeleton width="70%" height="24px" class="dark:!bg-slate-800" />
					</div>
				</div>

				<!-- Purchase Cards -->
				<div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
					<router-link
						v-for="(item, index) in formattedPurchaseData"
						:key="index"
						:to="{ path: '/orders' }"
						class="group p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-white dark:hover:bg-slate-800/90 hover:border-violet-300 dark:hover:border-violet-500/40 transition-all duration-200"
					>
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-medium text-slate-500 dark:text-slate-400">
								{{ item.label }}
							</span>
							<div class="w-7 h-7 rounded-lg bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 flex items-center justify-center text-xs">
								<i :class="item.icon"></i>
							</div>
						</div>
						<div class="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
							{{ item.displayValue }}
						</div>
						<div class="mt-1 text-[11px] text-slate-400 dark:text-slate-500 flex items-center gap-1">
							<span>{{ item.sublabel }}</span>
						</div>
					</router-link>
				</div>
			</div>
		</div>

		<!-- Section 3: Visual Analytics (Charts Grid) -->
		<div class="space-y-6">
			<!-- Row 1: Stock Availability & Monthly Turnover -->
			<div class="grid grid-cols-1 xl:grid-cols-2 gap-5">
				<stockChart class="w-full" />
				<turnOverChart class="w-full" />
			</div>

			<!-- Row 2: Cashflow (Accounts Receivable & Accounts Payable) -->
			<div class="grid grid-cols-1 xl:grid-cols-2 gap-5">
				<salesPaymentChart class="w-full" />
				<purchasePaymentChart class="w-full" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import axios from '@/plugins/axios';
import Button from 'primevue/button';
import Skeleton from 'primevue/skeleton';
import stockChart from '@/components/home/stockChart.vue';
import salesPaymentChart from '@/components/home/salesPaymentChart.vue';
import purchasePaymentChart from '@/components/home/purchasePaymentChart.vue';
import turnOverChart from '@/components/home/turnOverChart.vue';

const salesRevenue = ref(0);
const purchaseCredit = ref(0);
const orders = ref([]);
const totalCustomers = ref([]);
const totalSuppliers = ref([]);
const salesOrders = ref([]);
const purchaseOrders = ref([]);
const pendingRecievables = ref(0);
const collectedRecievables = ref(0);
const outstandingPayables = ref(0);
const setteledPayables = ref(0);
const totalProducts = ref(0);
const isLoading = ref(true);
const isRefreshing = ref(false);

const formatNumber = (val) => {
	if (val == null || isNaN(val)) return '0';
	return new Intl.NumberFormat('en-IN').format(val);
};

const formatCurrency = (val) => {
	if (val == null || isNaN(val)) return '₹0';
	return new Intl.NumberFormat('en-IN', {
		style: 'currency',
		currency: 'INR',
		maximumFractionDigits: 0
	}).format(val);
};

const fetchOrders = async () => {
	try {
		const response = await axios.get('/api/inventory/orders');
		orders.value = response.data || [];

		// Sales order
		salesOrders.value = orders.value.filter(order => order.order_type === 'SO');
		salesRevenue.value = salesOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount || 0), 0);
		pendingRecievables.value = salesOrders.value.reduce((sum, order) => sum + parseFloat(order.pending_amount || 0), 0);
		collectedRecievables.value = salesRevenue.value - pendingRecievables.value;

		// Purchase order
		purchaseOrders.value = orders.value.filter(order => order.order_type === 'PO');
		purchaseCredit.value = purchaseOrders.value.reduce((sum, order) => sum + parseFloat(order.net_amount || 0), 0);
		outstandingPayables.value = purchaseOrders.value.reduce((sum, order) => sum + parseFloat(order.pending_amount || 0), 0);
		setteledPayables.value = purchaseCredit.value - outstandingPayables.value;
	} catch (error) {
		console.error('Error fetching orders:', error);
	}
};

const fetchCustomers = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders');
		const data = response.data || [];
		totalCustomers.value = data.filter(item => item.type === 'Customer');
		totalSuppliers.value = data.filter(item => item.type === 'Supplier');
	} catch (error) {
		console.error('Error fetching customers and suppliers:', error);
	}
};

const fetchProducts = async () => {
	try {
		const response = await axios.get('/api/inventory/products');
		totalProducts.value = (response.data || []).length;
	} catch (error) {
		console.error('Error fetching products:', error);
	}
};

const loadDashboardData = async () => {
	await Promise.allSettled([
		fetchOrders(),
		fetchCustomers(),
		fetchProducts()
	]);
};

const refreshAll = async () => {
	isRefreshing.value = true;
	await loadDashboardData();
	isRefreshing.value = false;
};

// Summary top cards
const summaryCards = computed(() => [
	{
		label: 'Total Products (SKUs)',
		value: totalProducts.value,
		icon: 'pi pi-box',
		iconBg: 'bg-blue-50 dark:bg-blue-950/40',
		iconColor: 'text-blue-600 dark:text-blue-400',
		route: { path: '/stocks' }
	},
	{
		label: 'Registered Customers',
		value: totalCustomers.value.length,
		icon: 'pi pi-users',
		iconBg: 'bg-emerald-50 dark:bg-emerald-950/40',
		iconColor: 'text-emerald-600 dark:text-emerald-400',
		route: { path: '/stakeholders' }
	},
	{
		label: 'Active Suppliers',
		value: totalSuppliers.value.length,
		icon: 'pi pi-truck',
		iconBg: 'bg-amber-50 dark:bg-amber-950/40',
		iconColor: 'text-amber-600 dark:text-amber-400',
		route: { path: '/stakeholders' }
	}
]);

// Sales metrics
const formattedSalesData = computed(() => [
	{
		label: 'Sales Orders',
		displayValue: formatNumber(salesOrders.value.length),
		sublabel: 'Total active orders',
		icon: 'pi pi-arrow-circle-down'
	},
	{
		label: 'Gross Sales Revenue',
		displayValue: formatCurrency(salesRevenue.value),
		sublabel: 'Total invoiced revenue',
		icon: 'pi pi-indian-rupee'
	},
	{
		label: 'Collected Receivables',
		displayValue: formatCurrency(collectedRecievables.value),
		sublabel: 'Settled customer payments',
		icon: 'pi pi-check-circle'
	},
	{
		label: 'Pending Receivables',
		displayValue: formatCurrency(pendingRecievables.value),
		sublabel: 'Awaiting customer payment',
		icon: 'pi pi-clock'
	}
]);

// Purchase metrics
const formattedPurchaseData = computed(() => [
	{
		label: 'Purchase Orders',
		displayValue: formatNumber(purchaseOrders.value.length),
		sublabel: 'Total procurement POs',
		icon: 'pi pi-arrow-circle-up'
	},
	{
		label: 'Purchase Credit',
		displayValue: formatCurrency(purchaseCredit.value),
		sublabel: 'Total vendor spend',
		icon: 'pi pi-indian-rupee'
	},
	{
		label: 'Settled Payables',
		displayValue: formatCurrency(setteledPayables.value),
		sublabel: 'Paid to suppliers',
		icon: 'pi pi-check-circle'
	},
	{
		label: 'Outstanding Payables',
		displayValue: formatCurrency(outstandingPayables.value),
		sublabel: 'Due to suppliers',
		icon: 'pi pi-exclamation-circle'
	}
]);

// Keep backward-compatible raw computed arrays
const salesData = computed(() => [
	{ value: salesOrders.value.length, label: 'Sales Orders', icon: 'pi pi-arrow-circle-down' },
	{ value: salesRevenue.value, label: 'Sales Revenue', icon: 'pi pi-indian-rupee' },
	{ value: pendingRecievables.value, label: 'Pending Recievables', icon: 'pi pi-indian-rupee' },
	{ value: collectedRecievables.value, label: 'Collected Recievables', icon: 'pi pi-indian-rupee' }
]);

const purchaseData = computed(() => [
	{ value: purchaseOrders.value.length, label: 'Purchase Orders', icon: 'pi pi-arrow-circle-up' },
	{ value: purchaseCredit.value, label: 'Purchase Credit', icon: 'pi pi-indian-rupee' },
	{ value: outstandingPayables.value, label: 'Outstanding Payables', icon: 'pi pi-indian-rupee' },
	{ value: setteledPayables.value, label: 'Setteled Payables', icon: 'pi pi-users' }
]);

const summaryData = computed(() => [
	{ value: totalProducts.value, label: 'Total Products', icon: 'pi pi-cart-plus', page: 'stocks' },
	{ value: totalCustomers.value.length, label: 'Total Customers', icon: 'pi pi-users', page: 'stakeholders' },
	{ value: totalSuppliers.value.length, label: 'Total Suppliers', icon: 'pi pi-users', page: 'stakeholders' }
]);

onMounted(async () => {
	isLoading.value = true;
	await loadDashboardData();
	isLoading.value = false;
});
</script>