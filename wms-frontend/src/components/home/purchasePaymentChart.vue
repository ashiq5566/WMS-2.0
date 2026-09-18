<template>
	<div class="border border-slate-200/80 dark:border-slate-800/80 shadow-sm bg-white dark:bg-slate-900 rounded-2xl p-5 overflow-hidden transition-all duration-200 hover:shadow-md">
		<div class="flex items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800/60">
			<div class="flex items-center gap-3">
				<div class="w-9 h-9 rounded-xl bg-amber-500/10 dark:bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/20 flex items-center justify-center text-sm shadow-sm">
					<i class="pi pi-arrow-up-right"></i>
				</div>
				<div>
					<h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 leading-tight">Accounts Payable</h3>
					<p class="text-xs text-slate-500 dark:text-slate-400 font-normal">Pending payments to suppliers</p>
				</div>
			</div>
			<div v-if="!isLoading && labels.length > 0" class="flex items-center gap-2">
				<span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border border-amber-200/60 dark:border-amber-800/40">
					{{ formatCurrency(totalPayables) }}
				</span>
				<span class="text-xs font-medium px-2 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
					{{ labels.length }} Suppliers
				</span>
			</div>
		</div>

		<div class="pt-3 min-h-[320px] flex flex-col justify-center">
			<!-- Loading State -->
			<div v-if="isLoading" class="space-y-3.5 p-4">
				<div class="flex items-center gap-3" v-for="n in 6" :key="n">
					<Skeleton width="28%" height="16px" class="dark:!bg-slate-800 rounded-md" />
					<Skeleton :width="(75 - n * 8) + '%'" height="20px" class="dark:!bg-slate-800 rounded-md" />
				</div>
			</div>

			<!-- Empty State -->
			<div v-else-if="isEmpty" class="flex flex-col items-center justify-center py-12 text-center text-slate-400 dark:text-slate-500">
				<div class="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-emerald-500/80 mb-3">
					<i class="pi pi-check-circle text-xl"></i>
				</div>
				<p class="text-sm font-semibold text-slate-700 dark:text-slate-300">No pending payables</p>
				<span class="text-xs text-slate-400 mt-0.5">All supplier invoices are currently settled</span>
			</div>

			<!-- Chart Display -->
			<div v-else class="w-full">
				<apexchart
					:key="`${isDark ? 'dark' : 'light'}-${labels.length}`"
					width="100%"
					height="320"
					type="bar"
					:options="chartOptions"
					:series="series"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from '@/plugins/axios';
import Skeleton from 'primevue/skeleton';
import { useTheme } from '@/utils/theme';

const { isDarkMode } = useTheme();
const suppliers = ref([]);
const labels = ref([]);
const paymentDetails = ref([]);
const isLoading = ref(true);
const isDark = computed(() => isDarkMode.value);

const isEmpty = computed(() => {
	return !series.value[0]?.data || series.value[0].data.length === 0 || series.value[0].data.every(v => v === 0);
});

const totalPayables = computed(() => {
	return paymentDetails.value.reduce((sum, item) => sum + (parseFloat(item.amount) || 0), 0);
});

const formatCurrency = (val) => {
	return new Intl.NumberFormat('en-IN', {
		style: 'currency',
		currency: 'INR',
		maximumFractionDigits: 0
	}).format(val || 0);
};

const series = ref([
	{
		name: 'Pending Payables',
		data: []
	}
]);

const chartOptions = computed(() => {
	const textColor = isDark.value ? '#94a3b8' : '#64748b';
	const titleColor = isDark.value ? '#f8fafc' : '#0f172a';
	const borderColor = isDark.value ? '#1e293b' : '#f1f5f9';

	return {
		chart: {
			id: 'purchase-payable-chart',
			type: 'bar',
			toolbar: { show: false },
			fontFamily: 'inherit',
			background: 'transparent',
			animations: {
				enabled: true,
				easing: 'easeinout',
				speed: 650,
				animateGradually: { enabled: true, delay: 120 }
			}
		},
		theme: {
			mode: isDark.value ? 'dark' : 'light'
		},
		colors: ['#f59e0b'],
		fill: {
			type: 'gradient',
			gradient: {
				shade: 'dark',
				type: 'horizontal',
				shadeIntensity: 0.2,
				gradientToColors: ['#ea580c'],
				inverseColors: false,
				opacityFrom: 0.95,
				opacityTo: 0.85,
				stops: [0, 100]
			}
		},
		plotOptions: {
			bar: {
				horizontal: true,
				borderRadius: 6,
				borderRadiusApplication: 'end',
				barHeight: paymentDetails.value.length > 5 ? '58%' : '40%',
				distributed: false
			}
		},
		dataLabels: {
			enabled: true,
			textAnchor: 'start',
			style: {
				colors: [titleColor],
				fontSize: '11px',
				fontWeight: 600,
				fontFamily: 'inherit'
			},
			formatter: (val) => formatCurrency(val),
			offsetX: 6
		},
		xaxis: {
			categories: labels.value,
			labels: {
				style: {
					colors: textColor,
					fontSize: '11px',
					fontFamily: 'inherit'
				},
				formatter: (val) => formatCurrency(val)
			},
			axisBorder: { show: false },
			axisTicks: { show: false }
		},
		yaxis: {
			labels: {
				style: {
					colors: textColor,
					fontSize: '12px',
					fontFamily: 'inherit'
				}
			}
		},
		grid: {
			borderColor: borderColor,
			strokeDashArray: 4,
			xaxis: { lines: { show: true } },
			yaxis: { lines: { show: false } },
			padding: { top: 0, right: 20, bottom: 0, left: 10 }
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

const fetchSuppliersAndOrders = async () => {
	isLoading.value = true;
	try {
		const [suppRes, ordRes] = await Promise.allSettled([
			axios.get('/api/accounts/stakeholders/'),
			axios.get('/api/inventory/orders/')
		]);

		const allStakeholders = (suppRes.status === 'fulfilled' && suppRes.value?.data)
			? (Array.isArray(suppRes.value.data) ? suppRes.value.data : suppRes.value.data.results || [])
			: [];
		const allOrders = (ordRes.status === 'fulfilled' && ordRes.value?.data)
			? (Array.isArray(ordRes.value.data) ? ordRes.value.data : ordRes.value.data.results || [])
			: [];

		// Filter for suppliers (case-insensitive)
		suppliers.value = allStakeholders.filter(s => String(s.type || '').toLowerCase() === 'supplier');

		// Aggregate pending amount by supplier
		const supplierBalances = {};

		// 1. Seed from stakeholder total_pending_amount if available
		suppliers.value.forEach(s => {
			const pending = parseFloat(s.total_pending_amount || 0);
			if (pending > 0) {
				supplierBalances[s.id] = pending;
			}
		});

		// 2. Cross-check / aggregate from active Purchase Orders
		const purchaseOrders = allOrders.filter(o =>
			String(o.order_type || '').toUpperCase() === 'PO' &&
			o.order_status !== 'Cancelled' &&
			parseFloat(o.pending_amount || 0) > 0
		);

		if (purchaseOrders.length > 0) {
			const orderTotals = {};
			purchaseOrders.forEach(order => {
				const sId = order.stakeholder || order.stakeholder_id || order.stakeholder_obj?.id;
				if (sId) {
					orderTotals[sId] = (orderTotals[sId] || 0) + parseFloat(order.pending_amount || 0);
				}
			});

			Object.keys(orderTotals).forEach(sId => {
				const idNum = Number(sId) || sId;
				if (!supplierBalances[idNum] || supplierBalances[idNum] < orderTotals[sId]) {
					supplierBalances[idNum] = orderTotals[sId];
				}
			});
		}

		// Build details
		paymentDetails.value = suppliers.value
			.map(s => ({
				id: s.id,
				name: s.name || s.company_name || `Supplier #${s.id}`,
				amount: supplierBalances[s.id] || 0
			}))
			.filter(s => s.amount > 0)
			.sort((a, b) => b.amount - a.amount)
			.slice(0, 10);

		labels.value = paymentDetails.value.map(x => x.name);

		if (paymentDetails.value.length === 0) {
			series.value = [{ name: 'Pending Payables', data: [] }];
		} else {
			series.value = [
				{
					name: 'Pending Payables',
					data: paymentDetails.value.map(x => parseFloat(x.amount || 0))
				}
			];
		}
	} catch (error) {
		console.error('Error fetching payables:', error);
	} finally {
		isLoading.value = false;
	}
};

onMounted(async () => {
	await fetchSuppliersAndOrders();
});
</script>