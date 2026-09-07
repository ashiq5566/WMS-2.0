<template>
	<Card class="!border !border-slate-200/80 dark:!border-slate-800/80 !shadow-sm !bg-white dark:!bg-slate-900 !rounded-xl overflow-hidden transition-colors">
		<template #title>
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1 border-b border-slate-100 dark:border-slate-800/60">
				<div class="flex items-center gap-2.5">
					<div class="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-sm">
						<i class="pi pi-chart-pie"></i>
					</div>
					<div>
						<h3 class="text-base font-semibold text-slate-800 dark:text-slate-100 leading-tight">Monthly Turnover</h3>
						<p class="text-xs text-slate-500 dark:text-slate-400 font-normal">Sales vs. Purchase breakdown</p>
					</div>
				</div>
				<div class="w-full sm:w-auto">
					<DatePicker
						v-model="selectedMonth"
						view="month"
						dateFormat="mm/yy"
						placeholder="Select Month"
						show-icon
						class="w-full sm:w-44 !text-xs"
						inputClass="!py-1.5 !text-xs dark:!bg-slate-800 dark:!border-slate-700"
					/>
				</div>
			</div>
		</template>

		<template #content>
			<div class="pt-2 min-h-[320px] flex flex-col justify-center">
				<!-- Loading State -->
				<div v-if="isLoading" class="flex flex-col items-center justify-center space-y-4 p-8">
					<Skeleton shape="circle" size="180px" class="dark:!bg-slate-800" />
					<div class="flex gap-4">
						<Skeleton width="80px" height="16px" class="dark:!bg-slate-800" />
						<Skeleton width="80px" height="16px" class="dark:!bg-slate-800" />
					</div>
				</div>

				<!-- Empty State -->
				<div v-else-if="isEmpty" class="flex flex-col items-center justify-center py-12 text-center text-slate-400 dark:text-slate-500">
					<i class="pi pi-calendar-times text-3xl mb-2"></i>
					<p class="text-sm font-medium">No order transactions found</p>
					<span class="text-xs text-slate-400">Try selecting a different month</span>
				</div>

				<!-- Chart Display -->
				<div v-else class="w-full">
					<apexchart
						width="100%"
						height="320"
						type="donut"
						:options="chartOptions"
						:series="series"
					/>
				</div>
			</div>
		</template>
	</Card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import axios from '@/plugins/axios';
import Skeleton from 'primevue/skeleton';

const orders = ref([]);
const selectedMonth = ref(new Date());
const series = ref([]);
const isLoading = ref(true);
const isDark = ref(false);
let themeObserver = null;

const checkTheme = () => {
	isDark.value = document.documentElement.classList.contains('dark') ||
		document.documentElement.classList.contains('my-app-dark');
};

const isEmpty = computed(() => {
	return !series.value || series.value.length === 0 || series.value.every(v => v === 0);
});

const formatCurrency = (amount) => {
	return new Intl.NumberFormat('en-IN', {
		style: 'currency',
		currency: 'INR',
		maximumFractionDigits: 0
	}).format(amount || 0);
};

const chartOptions = computed(() => {
	const textColor = isDark.value ? '#e2e8f0' : '#334155';

	return {
		chart: {
			id: 'turnover-donut-chart',
			type: 'donut',
			fontFamily: 'inherit',
			background: 'transparent'
		},
		theme: {
			mode: isDark.value ? 'dark' : 'light'
		},
		labels: ['Sales Orders', 'Purchase Orders'],
		colors: ['#06b6d4', '#8b5cf6'],
		stroke: {
			colors: [isDark.value ? '#0f172a' : '#ffffff'],
			width: 2
		},
		plotOptions: {
			pie: {
				donut: {
					size: '72%',
					labels: {
						show: true,
						name: {
							show: true,
							fontSize: '13px',
							color: textColor
						},
						value: {
							show: true,
							fontSize: '16px',
							fontWeight: 700,
							color: textColor,
							formatter: (val) => formatCurrency(val)
						},
						total: {
							show: true,
							label: 'Total Turnover',
							fontSize: '12px',
							color: isDark.value ? '#94a3b8' : '#64748b',
							formatter: (w) => {
								const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
								return formatCurrency(total);
							}
						}
					}
				}
			}
		},
		dataLabels: {
			enabled: false
		},
		legend: {
			position: 'bottom',
			horizontalAlign: 'center',
			labels: {
				colors: textColor
			},
			markers: {
				radius: 12
			}
		},
		tooltip: {
			theme: isDark.value ? 'dark' : 'light',
			y: {
				formatter: (val) => formatCurrency(val)
			}
		}
	};
});

const fetchOrders = async () => {
	isLoading.value = true;
	try {
		const month = selectedMonth.value ? selectedMonth.value.getMonth() + 1 : new Date().getMonth() + 1;
		const response = await axios.get('/api/inventory/orders/', {
			params: {
				order_month: month
			}
		});
		orders.value = response.data || [];

		const totalSalesAmount = orders.value
			.filter(order => order.order_type === 'SO')
			.reduce((sum, order) => sum + parseFloat(order.net_amount || 0), 0);

		const totalPurchaseAmount = orders.value
			.filter(order => order.order_type === 'PO')
			.reduce((sum, order) => sum + parseFloat(order.net_amount || 0), 0);

		series.value = [totalSalesAmount, totalPurchaseAmount];
	} catch (error) {
		console.error('Error fetching turnover orders:', error);
	} finally {
		isLoading.value = false;
	}
};

watch(selectedMonth, () => {
	fetchOrders();
});

onMounted(async () => {
	checkTheme();
	themeObserver = new MutationObserver(checkTheme);
	themeObserver.observe(document.documentElement, {
		attributes: true,
		attributeFilter: ['class']
	});

	await fetchOrders();
});

onUnmounted(() => {
	if (themeObserver) {
		themeObserver.disconnect();
	}
});
</script>