<template>
	<div class="border border-slate-200/80 dark:border-slate-800/80 shadow-sm bg-white dark:bg-slate-900 rounded-2xl p-5 overflow-hidden transition-all duration-200 hover:shadow-md">
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800/60">
			<div class="flex items-center gap-3">
				<div class="w-9 h-9 rounded-xl bg-indigo-500/10 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/20 flex items-center justify-center text-sm shadow-sm">
					<i class="pi pi-chart-pie"></i>
				</div>
				<div>
					<h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 leading-tight">Monthly Turnover</h3>
					<p class="text-xs text-slate-500 dark:text-slate-400 font-normal">Sales revenue vs. procurement spend</p>
				</div>
			</div>
			<div class="w-full sm:w-auto">
				<DatePicker
					v-model="selectedMonth"
					view="month"
					dateFormat="mm/yy"
					placeholder="Select Month"
					show-icon
					class="w-full sm:w-40 !text-xs"
					inputClass="!py-1.5 !text-xs dark:!bg-slate-800 dark:!border-slate-700 dark:!text-slate-100 rounded-lg"
				/>
			</div>
		</div>

		<div class="pt-3 min-h-[320px] flex flex-col justify-center">
			<!-- Loading State -->
			<div v-if="isLoading" class="flex flex-col items-center justify-center space-y-4 p-8">
				<Skeleton shape="circle" size="180px" class="dark:!bg-slate-800" />
				<div class="flex gap-4">
					<Skeleton width="90px" height="16px" class="dark:!bg-slate-800 rounded-md" />
					<Skeleton width="90px" height="16px" class="dark:!bg-slate-800 rounded-md" />
				</div>
			</div>

			<!-- Empty State -->
			<div v-else-if="isEmpty" class="flex flex-col items-center justify-center py-12 text-center text-slate-400 dark:text-slate-500">
				<div class="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 mb-3">
					<i class="pi pi-calendar-times text-xl"></i>
				</div>
				<p class="text-sm font-semibold text-slate-700 dark:text-slate-300">No order transactions found</p>
				<span class="text-xs text-slate-400 mt-0.5">Try selecting a different month</span>
			</div>

			<!-- Chart & Breakdown Display -->
			<div v-else class="w-full space-y-3">
				<apexchart
					:key="`${isDark ? 'dark' : 'light'}-${series.join('-')}`"
					width="100%"
					height="260"
					type="donut"
					:options="chartOptions"
					:series="series"
				/>

				<!-- Bottom Breakdown Pills -->
				<div class="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100 dark:border-slate-800/60">
					<div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<div class="w-2.5 h-2.5 rounded-full bg-cyan-500"></div>
							<div>
								<span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 block">Sales ({{ salesPercentage }}%)</span>
								<span class="text-xs font-bold text-slate-800 dark:text-slate-200">{{ formatCurrency(series[0] || 0) }}</span>
							</div>
						</div>
					</div>
					<div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<div class="w-2.5 h-2.5 rounded-full bg-violet-500"></div>
							<div>
								<span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 block">Purchases ({{ purchasePercentage }}%)</span>
								<span class="text-xs font-bold text-slate-800 dark:text-slate-200">{{ formatCurrency(series[1] || 0) }}</span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from '@/plugins/axios';
import Skeleton from 'primevue/skeleton';
import { useTheme } from '@/utils/theme';

const { isDarkMode } = useTheme();
const orders = ref([]);
const selectedMonth = ref(new Date());
const series = ref([]);
const isLoading = ref(true);
const isDark = computed(() => isDarkMode.value);

const isEmpty = computed(() => {
	return !series.value || series.value.length === 0 || series.value.every(v => v === 0);
});

const totalAmount = computed(() => {
	return (series.value || []).reduce((sum, v) => sum + (parseFloat(v) || 0), 0);
});

const salesPercentage = computed(() => {
	if (!totalAmount.value) return 0;
	return Math.round(((series.value[0] || 0) / totalAmount.value) * 100);
});

const purchasePercentage = computed(() => {
	if (!totalAmount.value) return 0;
	return Math.round(((series.value[1] || 0) / totalAmount.value) * 100);
});

const formatCurrency = (amount) => {
	return new Intl.NumberFormat('en-IN', {
		style: 'currency',
		currency: 'INR',
		maximumFractionDigits: 0
	}).format(amount || 0);
};

const chartOptions = computed(() => {
	const textColor = isDark.value ? '#f8fafc' : '#0f172a';
	const mutedColor = isDark.value ? '#94a3b8' : '#64748b';

	return {
		chart: {
			id: 'turnover-donut-chart',
			type: 'donut',
			fontFamily: 'inherit',
			background: 'transparent',
			animations: {
				enabled: true,
				easing: 'easeinout',
				speed: 650
			}
		},
		theme: {
			mode: isDark.value ? 'dark' : 'light'
		},
		labels: ['Sales Orders', 'Purchase Orders'],
		colors: ['#06b6d4', '#8b5cf6'],
		stroke: {
			colors: [isDark.value ? '#0f172a' : '#ffffff'],
			width: 3
		},
		plotOptions: {
			pie: {
				donut: {
					size: '75%',
					labels: {
						show: true,
						name: {
							show: true,
							fontSize: '12px',
							fontWeight: 500,
							color: mutedColor,
							offsetY: -4
						},
						value: {
							show: true,
							fontSize: '18px',
							fontWeight: 700,
							color: textColor,
							offsetY: 6,
							formatter: (val) => formatCurrency(val)
						},
						total: {
							show: true,
							label: 'Turnover',
							fontSize: '11px',
							fontWeight: 500,
							color: mutedColor,
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
			show: false
		},
		tooltip: {
			theme: isDark.value ? 'dark' : 'light',
			style: {
				fontSize: '12px',
				fontFamily: 'inherit'
			},
			y: {
				formatter: (val) => formatCurrency(val)
			}
		}
	};
});

const fetchOrders = async () => {
	isLoading.value = true;
	try {
		const response = await axios.get('/api/inventory/orders');
		orders.value = response.data || [];

		const targetYear = selectedMonth.value.getFullYear();
		const targetMonth = selectedMonth.value.getMonth();

		const filtered = orders.value.filter(order => {
			const orderDate = new Date(order.date_added || order.created_at || order.date);
			return orderDate.getFullYear() === targetYear && orderDate.getMonth() === targetMonth;
		});

		const totalSalesAmount = filtered
			.filter(o => o.order_type === 'SO' && o.order_status !== 'Cancelled')
			.reduce((sum, order) => sum + parseFloat(order.net_amount || 0), 0);

		const totalPurchaseAmount = filtered
			.filter(o => o.order_type === 'PO' && o.order_status !== 'Cancelled')
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
	await fetchOrders();
});
</script>