<template>
	<div class="border border-slate-200/80 dark:border-slate-800/80 shadow-sm bg-white dark:bg-slate-900 rounded-2xl p-5 overflow-hidden transition-all duration-200 hover:shadow-md">
		<div class="flex items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800/60">
			<div class="flex items-center gap-3">
				<div class="w-9 h-9 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20 flex items-center justify-center text-sm shadow-sm">
					<i class="pi pi-box"></i>
				</div>
				<div>
					<h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 leading-tight">Stock Availability</h3>
					<p class="text-xs text-slate-500 dark:text-slate-400 font-normal">Top products by on-hand inventory</p>
				</div>
			</div>
			<div v-if="!isLoading && topProducts.length > 0" class="flex items-center gap-2">
				<span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/40">
					{{ totalStockUnits.toLocaleString() }} Units
				</span>
				<span class="text-xs font-medium px-2 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
					{{ products.length }} SKUs
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
			<div v-else-if="topProducts.length === 0" class="flex flex-col items-center justify-center py-12 text-center text-slate-400 dark:text-slate-500">
				<div class="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 mb-3">
					<i class="pi pi-inbox text-xl"></i>
				</div>
				<p class="text-sm font-semibold text-slate-700 dark:text-slate-300">No stock data available</p>
				<span class="text-xs text-slate-400 mt-0.5">Add products to track inventory levels</span>
			</div>

			<!-- Chart Display -->
			<div v-else class="w-full">
				<apexchart
					:key="`${isDark ? 'dark' : 'light'}-${topProducts.length}`"
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
const products = ref([]);
const topProducts = ref([]);
const labels = ref([]);
const isLoading = ref(true);
const isDark = computed(() => isDarkMode.value);

const totalStockUnits = computed(() => {
	return products.value.reduce((sum, p) => sum + (parseFloat(p.qty_available) || 0), 0);
});

const series = ref([
	{
		name: 'Available Stock',
		data: []
	}
]);

const chartOptions = computed(() => {
	const textColor = isDark.value ? '#94a3b8' : '#64748b';
	const titleColor = isDark.value ? '#f8fafc' : '#0f172a';
	const borderColor = isDark.value ? '#1e293b' : '#f1f5f9';

	return {
		chart: {
			id: 'stock-level-chart',
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
		colors: ['#10b981'],
		fill: {
			type: 'gradient',
			gradient: {
				shade: 'dark',
				type: 'horizontal',
				shadeIntensity: 0.2,
				gradientToColors: ['#0d9488'],
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
				barHeight: topProducts.value.length > 5 ? '58%' : '40%',
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
			formatter: (val) => `${Number(val).toLocaleString()} units`,
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
				formatter: (val) => Number(val).toLocaleString()
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
				formatter: (val) => `${Number(val).toLocaleString()} units available`
			}
		}
	};
});

const fetchProducts = async () => {
	isLoading.value = true;
	try {
		const response = await axios.get('/api/inventory/products');
		products.value = response.data || [];

		// Filter products with available quantity and sort descending
		const sorted = [...products.value]
			.filter(p => (parseFloat(p.qty_available) || 0) > 0)
			.sort((a, b) => (parseFloat(b.qty_available) || 0) - (parseFloat(a.qty_available) || 0))
			.slice(0, 8); // Top 8 for clean visual presentation

		topProducts.value = sorted;
		labels.value = sorted.map(product => product.name || `Product #${product.id}`);
		series.value = [
			{
				name: 'Available Stock',
				data: sorted.map(product => parseFloat(product.qty_available) || 0)
			}
		];
	} catch (error) {
		console.error('Error fetching products:', error);
	} finally {
		isLoading.value = false;
	}
};

onMounted(async () => {
	await fetchProducts();
});
</script>