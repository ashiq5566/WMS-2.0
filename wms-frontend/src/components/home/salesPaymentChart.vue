<template>
	<div class="border border-slate-200/80 dark:border-slate-800/80 shadow-sm bg-white dark:bg-slate-900 rounded-2xl p-5 overflow-hidden transition-all duration-200 hover:shadow-md">
		<div class="flex items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800/60">
			<div class="flex items-center gap-3">
				<div class="w-9 h-9 rounded-xl bg-teal-500/10 dark:bg-teal-500/15 text-teal-600 dark:text-teal-400 ring-1 ring-teal-500/20 flex items-center justify-center text-sm shadow-sm">
					<i class="pi pi-arrow-down-left"></i>
				</div>
				<div>
					<h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 leading-tight">Accounts Receivable</h3>
					<p class="text-xs text-slate-500 dark:text-slate-400 font-normal">Pending payments from customers</p>
				</div>
			</div>
			<div v-if="!isLoading && labels.length > 0" class="flex items-center gap-2">
				<span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-teal-50 dark:bg-teal-950/50 text-teal-700 dark:text-teal-300 border border-teal-200/60 dark:border-teal-800/40">
					{{ formatCurrency(totalReceivables) }}
				</span>
				<span class="text-xs font-medium px-2 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
					{{ labels.length }} Clients
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
				<p class="text-sm font-semibold text-slate-700 dark:text-slate-300">No pending receivables</p>
				<span class="text-xs text-slate-400 mt-0.5">All customer accounts are currently settled</span>
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
const customers = ref([]);
const labels = ref([]);
const paymentDetails = ref([]);
const isLoading = ref(true);
const isDark = computed(() => isDarkMode.value);

const isEmpty = computed(() => {
	return !series.value[0]?.data || series.value[0].data.length === 0 || series.value[0].data.every(v => v === 0);
});

const totalReceivables = computed(() => {
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
		name: 'Pending Receivables',
		data: []
	}
]);

const chartOptions = computed(() => {
	const textColor = isDark.value ? '#94a3b8' : '#64748b';
	const titleColor = isDark.value ? '#f8fafc' : '#0f172a';
	const borderColor = isDark.value ? '#1e293b' : '#f1f5f9';

	return {
		chart: {
			id: 'sales-receivable-chart',
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
		colors: ['#0d9488'],
		fill: {
			type: 'gradient',
			gradient: {
				shade: 'dark',
				type: 'horizontal',
				shadeIntensity: 0.2,
				gradientToColors: ['#06b6d4'],
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

const fetchCustomersAndOrders = async () => {
	isLoading.value = true;
	try {
		const [custRes, ordRes] = await Promise.allSettled([
			axios.get('/api/accounts/stakeholders/'),
			axios.get('/api/inventory/orders/')
		]);

		const allStakeholders = (custRes.status === 'fulfilled' && custRes.value?.data)
			? (Array.isArray(custRes.value.data) ? custRes.value.data : custRes.value.data.results || [])
			: [];
		const allOrders = (ordRes.status === 'fulfilled' && ordRes.value?.data)
			? (Array.isArray(ordRes.value.data) ? ordRes.value.data : ordRes.value.data.results || [])
			: [];

		// Filter for customers (case-insensitive)
		customers.value = allStakeholders.filter(s => String(s.type || '').toLowerCase() === 'customer');

		// Aggregate pending amount by customer
		const customerBalances = {};

		// 1. Seed from stakeholder total_pending_amount if available
		customers.value.forEach(c => {
			const pending = parseFloat(c.total_pending_amount || 0);
			if (pending > 0) {
				customerBalances[c.id] = pending;
			}
		});

		// 2. Cross-check / aggregate from active Sales Orders
		const salesOrders = allOrders.filter(o =>
			String(o.order_type || '').toUpperCase() === 'SO' &&
			o.order_status !== 'Cancelled' &&
			parseFloat(o.pending_amount || 0) > 0
		);

		if (salesOrders.length > 0) {
			const orderTotals = {};
			salesOrders.forEach(order => {
				const cId = order.stakeholder || order.stakeholder_id || order.stakeholder_obj?.id;
				if (cId) {
					orderTotals[cId] = (orderTotals[cId] || 0) + parseFloat(order.pending_amount || 0);
				}
			});

			Object.keys(orderTotals).forEach(cId => {
				const idNum = Number(cId) || cId;
				if (!customerBalances[idNum] || customerBalances[idNum] < orderTotals[cId]) {
					customerBalances[idNum] = orderTotals[cId];
				}
			});
		}

		// Build details
		paymentDetails.value = customers.value
			.map(c => ({
				id: c.id,
				name: c.name || c.company_name || `Client #${c.id}`,
				amount: customerBalances[c.id] || 0
			}))
			.filter(c => c.amount > 0)
			.sort((a, b) => b.amount - a.amount)
			.slice(0, 10); // Top 10

		labels.value = paymentDetails.value.map(x => x.name);

		if (paymentDetails.value.length === 0) {
			series.value = [{ name: 'Pending Receivables', data: [] }];
		} else {
			series.value = [
				{
					name: 'Pending Receivables',
					data: paymentDetails.value.map(x => parseFloat(x.amount || 0))
				}
			];
		}
	} catch (error) {
		console.error('Error fetching receivables:', error);
	} finally {
		isLoading.value = false;
	}
};

onMounted(async () => {
	await fetchCustomersAndOrders();
});
</script>