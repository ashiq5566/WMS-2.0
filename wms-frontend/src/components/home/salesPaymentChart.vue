<template>
	<Card class="!border !border-slate-200/80 dark:!border-slate-800/80 !shadow-sm !bg-white dark:!bg-slate-900 !rounded-xl overflow-hidden transition-colors">
		<template #title>
			<div class="flex items-center justify-between gap-2 pb-1 border-b border-slate-100 dark:border-slate-800/60">
				<div class="flex items-center gap-2.5">
					<div class="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center text-sm">
						<i class="pi pi-arrow-down-left"></i>
					</div>
					<div>
						<h3 class="text-base font-semibold text-slate-800 dark:text-slate-100 leading-tight">Accounts Receivable</h3>
						<p class="text-xs text-slate-500 dark:text-slate-400 font-normal">Pending payments from customers</p>
					</div>
				</div>
				<span v-if="!isLoading && customers.length > 0" class="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
					{{ customers.length }} Clients
				</span>
			</div>
		</template>

		<template #content>
			<div class="pt-2 min-h-[320px] flex flex-col justify-center">
				<!-- Loading State -->
				<div v-if="isLoading" class="space-y-3 p-4">
					<div class="flex items-center gap-3" v-for="n in 5" :key="n">
						<Skeleton width="28%" height="16px" class="dark:!bg-slate-800" />
						<Skeleton :width="(75 - n * 8) + '%'" height="20px" class="dark:!bg-slate-800" />
					</div>
				</div>

				<!-- Empty State -->
				<div v-else-if="isEmpty" class="flex flex-col items-center justify-center py-12 text-center text-slate-400 dark:text-slate-500">
					<i class="pi pi-check-circle text-3xl mb-2 text-emerald-500/60"></i>
					<p class="text-sm font-medium">No pending receivables</p>
					<span class="text-xs text-slate-400">All customer accounts are currently settled</span>
				</div>

				<!-- Chart Display -->
				<div v-else class="w-full">
					<apexchart
						width="100%"
						height="320"
						type="bar"
						:options="chartOptions"
						:series="series"
					/>
				</div>
			</div>
		</template>
	</Card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import axios from '@/plugins/axios';
import Skeleton from 'primevue/skeleton';

const customers = ref([]);
const labels = ref([]);
const paymentDetails = ref([]);
const isLoading = ref(true);
const isDark = ref(false);
let themeObserver = null;

const checkTheme = () => {
	isDark.value = document.documentElement.classList.contains('dark') ||
		document.documentElement.classList.contains('my-app-dark');
};

const isEmpty = computed(() => {
	return !series.value[0]?.data || series.value[0].data.length === 0 || series.value[0].data.every(v => v === 0);
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
	const borderColor = isDark.value ? '#334155' : '#f1f5f9';

	return {
		chart: {
			id: 'sales-receivable-chart',
			type: 'bar',
			toolbar: { show: false },
			fontFamily: 'inherit',
			background: 'transparent'
		},
		theme: {
			mode: isDark.value ? 'dark' : 'light'
		},
		colors: ['#0d9488'],
		plotOptions: {
			bar: {
				horizontal: true,
				borderRadius: 4,
				barHeight: '65%',
				distributed: false
			}
		},
		dataLabels: {
			enabled: true,
			textAnchor: 'start',
			style: {
				colors: [isDark.value ? '#f1f5f9' : '#1e293b'],
				fontSize: '11px',
				fontWeight: 600
			},
			formatter: (val) => formatCurrency(val),
			offsetX: 5
		},
		xaxis: {
			categories: labels.value,
			labels: {
				style: {
					colors: textColor,
					fontSize: '11px'
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
					fontSize: '12px'
				}
			}
		},
		grid: {
			borderColor: borderColor,
			strokeDashArray: 3,
			xaxis: { lines: { show: true } },
			yaxis: { lines: { show: false } }
		},
		tooltip: {
			theme: isDark.value ? 'dark' : 'light',
			y: {
				formatter: (val) => formatCurrency(val)
			}
		}
	};
});

const fetchCustomersAndOrders = async () => {
	isLoading.value = true;
	try {
		const response = await axios.get('/api/accounts/stakeholders', {
			params: {
				type: 'Customer'
			}
		});
		customers.value = response.data || [];
		labels.value = customers.value.map(item => item.name);

		if (customers.value.length > 0) {
			const orderResponse = await axios.get('/api/inventory/orders/get_total_by_stakeholders', {
				params: {
					stakeholder_ids: customers.value.map(item => item.id)
				}
			});
			paymentDetails.value = orderResponse.data || [];

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
	checkTheme();
	themeObserver = new MutationObserver(checkTheme);
	themeObserver.observe(document.documentElement, {
		attributes: true,
		attributeFilter: ['class']
	});

	await fetchCustomersAndOrders();
});

onUnmounted(() => {
	if (themeObserver) {
		themeObserver.disconnect();
	}
});
</script>