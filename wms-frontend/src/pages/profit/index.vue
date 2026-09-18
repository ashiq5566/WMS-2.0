<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import axios from "@/plugins/axios";
import moment from "moment";
import { useToast } from "primevue/usetoast";
import { useTheme } from "@/utils/theme";
import {
	calculateGrossProfit,
	calculateProfitMargin,
	getMarginBadgeSeverity,
	formatMargin,
	getProfitStatusText,
	formatCurrency,
	formatNumber,
	type ProfitKpiData,
	type ProductProfitRow,
	type OrderProfitRow,
	type MonthlyProfitTrend,
} from "@/utils/profitCalculations";

const toast = useToast();
const { isDarkMode } = useTheme();

// Loading state
const loading = ref(false);

// View Mode: 'products' | 'orders'
const activeView = ref<'products' | 'orders'>('products');

// Filters
const searchInput = ref("");
const dateRangePreset = ref<'this_month' | 'last_month' | 'this_year' | 'all' | 'custom'>('this_month');
const customDateRange = ref<any>(null);
const selectedCustomer = ref<number | null>(null);
const customers = ref<{ label: string; value: number }[]>([]);

// Data from API
const kpis = ref<ProfitKpiData>({
	total_revenue: 0,
	total_cogs: 0,
	gross_profit: 0,
	profit_margin_pct: 0,
	total_orders_count: 0,
	total_items_sold: 0,
	total_returned_units: 0,
	total_returned_revenue: 0,
	profitable_products_count: 0,
	loss_products_count: 0,
});
const productRows = ref<ProductProfitRow[]>([]);
const orderRows = ref<OrderProfitRow[]>([]);
const monthlyTrends = ref<MonthlyProfitTrend[]>([]);

// Fetch Customers for filter dropdown
const fetchCustomers = async () => {
	try {
		const res = await axios.get("/api/accounts/stakeholders/", {
			params: { type: "Customer" },
		});
		const list = res.data?.results || res.data || [];
		customers.value = list.map((c: any) => ({
			label: c.name,
			value: c.id,
		}));
	} catch (error) {
		console.error("Error fetching customers:", error);
	}
};

// Fetch Profit Analytics Data
const fetchProfitData = async () => {
	try {
		loading.value = true;
		const params: Record<string, any> = {};

		if (dateRangePreset.value !== 'custom') {
			params.date_range = dateRangePreset.value;
		} else if (customDateRange.value && customDateRange.value[0]) {
			params.start_date = moment(customDateRange.value[0]).format('YYYY-MM-DD');
			if (customDateRange.value[1]) {
				params.end_date = moment(customDateRange.value[1]).format('YYYY-MM-DD');
			}
		}

		if (selectedCustomer.value) {
			params.stakeholder_id = selectedCustomer.value;
		}

		if (searchInput.value.trim()) {
			params.search = searchInput.value.trim();
		}

		const response = await axios.get("/api/inventory/profit-analytics/", { params });
		const data = response.data || {};

		kpis.value = data.kpi || kpis.value;
		productRows.value = data.by_product || [];
		orderRows.value = data.by_order || [];
		monthlyTrends.value = data.monthly_trends || [];
	} catch (error) {
		console.error("Error loading profit analytics:", error);
		toast.add({
			severity: "error",
			summary: "Error",
			detail: "Failed to load profit analytics data.",
			life: 3000,
		});
	} finally {
		loading.value = false;
	}
};

// Search debounce
let searchTimer: any = null;
watch(searchInput, () => {
	clearTimeout(searchTimer);
	searchTimer = setTimeout(() => {
		fetchProfitData();
	}, 350);
});

watch([dateRangePreset, selectedCustomer], () => {
	if (dateRangePreset.value !== 'custom') {
		fetchProfitData();
	}
});

watch(customDateRange, (val) => {
	if (val && val[0] && val[1]) {
		fetchProfitData();
	}
});

onMounted(() => {
	fetchCustomers();
	fetchProfitData();
});

// ApexCharts Configuration
const chartSeries = computed(() => [
	{
		name: "Revenue",
		type: "column",
		data: monthlyTrends.value.map((t) => t.revenue),
	},
	{
		name: "Cost (COGS)",
		type: "column",
		data: monthlyTrends.value.map((t) => t.cogs),
	},
	{
		name: "Gross Profit",
		type: "column",
		data: monthlyTrends.value.map((t) => t.gross_profit),
	},
	{
		name: "Margin %",
		type: "line",
		data: monthlyTrends.value.map((t) => t.margin_pct),
	},
]);

const chartOptions = computed(() => {
	const dark = isDarkMode.value;
	return {
		chart: {
			height: 320,
			type: "line",
			toolbar: { show: false },
			background: "transparent",
			fontFamily: "inherit",
		},
		stroke: {
			width: [0, 0, 0, 3],
			curve: "smooth",
		},
		colors: ["#3b82f6", "#f59e0b", "#10b981", "#8b5cf6"],
		plotOptions: {
			bar: {
				columnWidth: "45%",
				borderRadius: 4,
			},
		},
		fill: {
			opacity: [0.85, 0.85, 0.85, 1],
		},
		labels: monthlyTrends.value.map((t) => t.month),
		markers: {
			size: [0, 0, 0, 4],
			strokeWidth: 2,
			hover: { size: 6 },
		},
		xaxis: {
			labels: {
				style: {
					colors: dark ? "#94a3b8" : "#64748b",
					fontSize: "12px",
				},
			},
			axisBorder: { show: false },
			axisTicks: { show: false },
		},
		yaxis: [
			{
				title: {
					text: "Amount (₹)",
					style: { color: dark ? "#94a3b8" : "#64748b", fontSize: "11px" },
				},
				labels: {
					style: { colors: dark ? "#94a3b8" : "#64748b", fontSize: "11px" },
					formatter: (val: number) => `₹${formatNumber(val)}`,
				},
			},
			{
				opposite: true,
				title: {
					text: "Margin %",
					style: { color: dark ? "#94a3b8" : "#64748b", fontSize: "11px" },
				},
				labels: {
					style: { colors: dark ? "#94a3b8" : "#64748b", fontSize: "11px" },
					formatter: (val: number) => `${val?.toFixed(1) || 0}%`,
				},
			},
		],
		grid: {
			borderColor: dark ? "#334155" : "#e2e8f0",
			strokeDashArray: 4,
		},
		legend: {
			position: "top",
			horizontalAlign: "right",
			labels: { colors: dark ? "#cbd5e1" : "#475569" },
		},
		tooltip: {
			theme: dark ? "dark" : "light",
			shared: true,
			intersect: false,
			y: {
				formatter: (val: number, opts: any) => {
					if (opts.seriesIndex === 3) return `${val?.toFixed(1)}%`;
					return formatCurrency(val);
				},
			},
		},
	};
});

// CSV Export
const exportCSV = () => {
	if (activeView.value === 'products') {
		const headers = [
			"Product ID",
			"Product Name",
			"Variant/Size",
			"Units Sold",
			"Units Returned",
			"Selling Price",
			"Purchase Cost",
			"Total Revenue",
			"Total COGS",
			"Gross Profit",
			"Margin %",
		];
		const rows = productRows.value.map((r) => [
			r.product_id,
			`"${r.product_name}"`,
			r.size,
			r.units_sold,
			r.units_returned,
			r.avg_selling_price,
			r.cost_price,
			r.total_revenue,
			r.total_cogs,
			r.gross_profit,
			`${r.profit_margin_pct}%`,
		]);
		downloadCSV("profit_by_product.csv", [headers, ...rows]);
	} else {
		const headers = [
			"Order Number",
			"Date",
			"Customer",
			"Status",
			"Items Count",
			"Revenue",
			"COGS",
			"Gross Profit",
			"Margin %",
		];
		const rows = orderRows.value.map((r) => [
			r.order_number,
			r.order_date ? moment(r.order_date).format('YYYY-MM-DD') : '',
			`"${r.stakeholder_name}"`,
			r.order_status,
			r.items_count,
			r.total_revenue,
			r.total_cogs,
			r.gross_profit,
			`${r.profit_margin_pct}%`,
		]);
		downloadCSV("profit_by_order.csv", [headers, ...rows]);
	}
};

const downloadCSV = (filename: string, data: any[][]) => {
	const csvContent = "data:text/csv;charset=utf-8," + data.map((e) => e.join(",")).join("\n");
	const encodedUri = encodeURI(csvContent);
	const link = document.createElement("a");
	link.setAttribute("href", encodedUri);
	link.setAttribute("download", filename);
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
};
</script>

<template>
	<div class="space-y-6">
		<!-- Top Bar: Header & Controls -->
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
			<div>
				<div class="flex items-center gap-2.5">
					<div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
						<i class="pi pi-chart-line text-lg"></i>
					</div>
					<div>
						<h1 class="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
							Profit Tracking & Margin Analytics
						</h1>
						<p class="text-xs text-slate-500 dark:text-slate-400">
							Real-time profitability, procurement COGS, gross margins, and RMA deductions
						</p>
					</div>
				</div>
			</div>

			<div class="flex items-center gap-2">
				<Button
					icon="pi pi-download"
					label="Export CSV"
					severity="secondary"
					outlined
					size="small"
					class="p-button-sm"
					@click="exportCSV"
				/>
				<Button
					icon="pi pi-refresh"
					label="Refresh"
					severity="primary"
					size="small"
					class="p-button-sm"
					:loading="loading"
					@click="fetchProfitData"
				/>
			</div>
		</div>

		<!-- KPI Summary Cards (4 Cards) -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- Total Sales Revenue -->
			<div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm relative overflow-hidden group">
				<div class="flex items-center justify-between">
					<span class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Total Sales Revenue</span>
					<div class="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400">
						<i class="pi pi-wallet text-sm"></i>
					</div>
				</div>
				<div class="mt-3">
					<div class="text-2xl font-black text-slate-900 dark:text-white">
						{{ formatCurrency(kpis.total_revenue) }}
					</div>
					<div class="mt-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
						<span class="font-semibold text-slate-700 dark:text-slate-300">{{ formatNumber(kpis.total_items_sold) }}</span>
						<span>units sold across</span>
						<span class="font-semibold text-slate-700 dark:text-slate-300">{{ formatNumber(kpis.total_orders_count) }}</span>
						<span>orders</span>
					</div>
				</div>
			</div>

			<!-- Total COGS -->
			<div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm relative overflow-hidden group">
				<div class="flex items-center justify-between">
					<span class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Cost of Goods (COGS)</span>
					<div class="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
						<i class="pi pi-box text-sm"></i>
					</div>
				</div>
				<div class="mt-3">
					<div class="text-2xl font-black text-slate-900 dark:text-white">
						{{ formatCurrency(kpis.total_cogs) }}
					</div>
					<div class="mt-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
						<span>Deducted returns:</span>
						<span class="font-semibold text-amber-600 dark:text-amber-400">{{ formatCurrency(kpis.total_returned_revenue) }}</span>
						<span>({{ kpis.total_returned_units }} units)</span>
					</div>
				</div>
			</div>

			<!-- Gross Profit -->
			<div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm relative overflow-hidden group">
				<div class="flex items-center justify-between">
					<span class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Net Gross Profit</span>
					<div
						class="w-8 h-8 rounded-lg flex items-center justify-center"
						:class="kpis.gross_profit >= 0 ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400' : 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400'"
					>
						<i :class="kpis.gross_profit >= 0 ? 'pi pi-arrow-up-right text-sm' : 'pi pi-arrow-down-right text-sm'"></i>
					</div>
				</div>
				<div class="mt-3">
					<div
						class="text-2xl font-black"
						:class="kpis.gross_profit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'"
					>
						{{ formatCurrency(kpis.gross_profit) }}
					</div>
					<div class="mt-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
						<span>Margin:</span>
						<span
							class="font-bold px-1.5 py-0.5 rounded text-[11px]"
							:class="kpis.profit_margin_pct >= 0 ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'"
						>
							{{ formatMargin(kpis.profit_margin_pct) }}
						</span>
					</div>
				</div>
			</div>

			<!-- Overall Margin % -->
			<div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm relative overflow-hidden group">
				<div class="flex items-center justify-between">
					<span class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Profit Margin %</span>
					<div class="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
						<i class="pi pi-percentage text-sm"></i>
					</div>
				</div>
				<div class="mt-3">
					<div class="text-2xl font-black text-slate-900 dark:text-white">
						{{ kpis.profit_margin_pct }}%
					</div>
					<div class="mt-1 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
						<span class="font-semibold text-slate-700 dark:text-slate-300">{{ getProfitStatusText(kpis.profit_margin_pct) }}</span>
						<span class="text-[11px] text-slate-400">
							{{ kpis.profitable_products_count }} profitable / {{ kpis.loss_products_count }} loss
						</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Filter Bar -->
		<div class="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
			<div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
				<!-- Date Range Presets -->
				<div class="flex flex-wrap items-center gap-1.5">
					<span class="text-xs font-semibold text-slate-400 mr-1">Period:</span>
					<button
						v-for="preset in [
							{ label: 'This Month', value: 'this_month' },
							{ label: 'Last Month', value: 'last_month' },
							{ label: 'This Year', value: 'this_year' },
							{ label: 'All Time', value: 'all' },
							{ label: 'Custom', value: 'custom' },
						]"
						:key="preset.value"
						type="button"
						class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
						:class="dateRangePreset === preset.value
							? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20 font-semibold'
							: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'"
						@click="dateRangePreset = preset.value as any"
					>
						{{ preset.label }}
					</button>
				</div>

				<!-- View Switcher -->
				<div class="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
					<button
						type="button"
						class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5"
						:class="activeView === 'products'
							? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm font-semibold'
							: 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'"
						@click="activeView = 'products'"
					>
						<i class="pi pi-box text-xs"></i>
						<span>Product & SKU</span>
						<span class="px-1.5 py-0.2 bg-slate-200 dark:bg-slate-700 rounded text-[10px]">{{ productRows.length }}</span>
					</button>
					<button
						type="button"
						class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5"
						:class="activeView === 'orders'
							? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm font-semibold'
							: 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'"
						@click="activeView = 'orders'"
					>
						<i class="pi pi-shopping-bag text-xs"></i>
						<span>Sales Orders</span>
						<span class="px-1.5 py-0.2 bg-slate-200 dark:bg-slate-700 rounded text-[10px]">{{ orderRows.length }}</span>
					</button>
				</div>
			</div>

			<!-- Second Row: Controls -->
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
				<!-- Search -->
				<div class="relative">
					<i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
					<input
						v-model="searchInput"
						type="text"
						placeholder="Search SKU, product, or order..."
						class="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
					/>
				</div>

				<!-- Customer Selector -->
				<Select
					v-model="selectedCustomer"
					:options="customers"
					optionLabel="label"
					optionValue="value"
					placeholder="Filter by Customer"
					class="w-full text-xs"
					showClear
				/>

				<!-- Custom Date Range Picker -->
				<DatePicker
					v-model="customDateRange"
					selectionMode="range"
					placeholder="Select custom date range"
					class="w-full text-xs"
					:disabled="dateRangePreset !== 'custom'"
					showIcon
				/>
			</div>
		</div>

		<!-- Trend Chart -->
		<div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm">
			<div class="flex items-center justify-between mb-4">
				<div>
					<h3 class="text-sm font-bold text-slate-900 dark:text-white">
						Profit & Margin Trajectory
					</h3>
					<p class="text-xs text-slate-500 dark:text-slate-400">
						Monthly Revenue vs. COGS vs. Gross Profit and Margin % over time
					</p>
				</div>
				<div class="flex items-center gap-3 text-xs">
					<span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-blue-500 inline-block"></span>Revenue</span>
					<span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-amber-500 inline-block"></span>COGS</span>
					<span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-500 inline-block"></span>Profit</span>
					<span class="flex items-center gap-1.5"><span class="w-3 h-1 rounded bg-purple-500 inline-block"></span>Margin %</span>
				</div>
			</div>

			<div v-if="monthlyTrends.length">
				<apexchart
					type="line"
					height="320"
					:options="chartOptions"
					:series="chartSeries"
				/>
			</div>
			<div v-else class="h-64 flex items-center justify-center text-slate-400 text-xs">
				No monthly turnover data available for selected period.
			</div>
		</div>

		<!-- Data Table Section -->
		<div class="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<h3 class="text-sm font-bold text-slate-900 dark:text-white">
						{{ activeView === 'products' ? 'Product & SKU Margin Breakdown' : 'Sales Order Profitability Journal' }}
					</h3>
					<p class="text-xs text-slate-500 dark:text-slate-400">
						{{ activeView === 'products' ? 'Detailed profitability per size variant and SKU' : 'Revenue, cost, and gross profit breakdown per commercial order' }}
					</p>
				</div>
				<span class="text-xs text-slate-400 font-medium">
					Showing {{ activeView === 'products' ? productRows.length : orderRows.length }} records
				</span>
			</div>

			<!-- Product Table -->
			<DataTable
				v-if="activeView === 'products'"
				:value="productRows"
				:loading="loading"
				paginator
				:rows="10"
				:rowsPerPageOptions="[10, 25, 50]"
				tableStyle="min-width: 60rem"
				responsiveLayout="scroll"
				class="p-datatable-sm text-xs"
			>
				<template #empty>
					<div class="p-6 text-center text-slate-400">
						No product profit records found matching criteria.
					</div>
				</template>

				<!-- Product ID -->
				<Column field="product_id" header="SKU / ID" sortable style="width: 110px">
					<template #body="slotProps">
						<span class="font-mono font-bold text-slate-700 dark:text-slate-300">
							{{ slotProps.data.product_id }}
						</span>
					</template>
				</Column>

				<!-- Product Name & Variant -->
				<Column field="product_name" header="Product Description" sortable style="min-width: 180px">
					<template #body="slotProps">
						<div>
							<span class="font-semibold text-slate-800 dark:text-slate-200">
								{{ slotProps.data.product_name }}
							</span>
							<div class="flex items-center gap-1.5 mt-0.5">
								<span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
									Size: {{ slotProps.data.size }}
								</span>
								<span class="text-[10px] text-slate-400">({{ slotProps.data.unit }})</span>
							</div>
						</div>
					</template>
				</Column>

				<!-- Units Sold -->
				<Column field="units_sold" header="Net Sold" sortable style="width: 100px">
					<template #body="slotProps">
						<span class="font-bold text-slate-900 dark:text-white">
							{{ formatNumber(slotProps.data.units_sold) }}
						</span>
						<span v-if="slotProps.data.units_returned > 0" class="block text-[10px] text-amber-600 dark:text-amber-400">
							-{{ slotProps.data.units_returned }} ret
						</span>
					</template>
				</Column>

				<!-- Selling Price -->
				<Column field="avg_selling_price" header="Selling Price" sortable style="width: 120px">
					<template #body="slotProps">
						<span class="text-slate-700 dark:text-slate-300">
							{{ formatCurrency(slotProps.data.avg_selling_price) }}
						</span>
					</template>
				</Column>

				<!-- Purchase Cost -->
				<Column field="cost_price" header="Unit Cost" sortable style="width: 110px">
					<template #body="slotProps">
						<span class="text-slate-500 dark:text-slate-400 font-mono">
							{{ formatCurrency(slotProps.data.cost_price) }}
						</span>
					</template>
				</Column>

				<!-- Total Revenue -->
				<Column field="total_revenue" header="Revenue" sortable style="width: 120px">
					<template #body="slotProps">
						<span class="font-semibold text-slate-900 dark:text-white">
							{{ formatCurrency(slotProps.data.total_revenue) }}
						</span>
					</template>
				</Column>

				<!-- Total COGS -->
				<Column field="total_cogs" header="Total COGS" sortable style="width: 120px">
					<template #body="slotProps">
						<span class="text-slate-600 dark:text-slate-400 font-mono">
							{{ formatCurrency(slotProps.data.total_cogs) }}
						</span>
					</template>
				</Column>

				<!-- Gross Profit -->
				<Column field="gross_profit" header="Gross Profit" sortable style="width: 120px">
					<template #body="slotProps">
						<span
							class="font-bold"
							:class="slotProps.data.gross_profit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'"
						>
							{{ formatCurrency(slotProps.data.gross_profit) }}
						</span>
					</template>
				</Column>

				<!-- Margin % -->
				<Column field="profit_margin_pct" header="Margin %" sortable style="width: 120px">
					<template #body="slotProps">
						<Tag
							:value="formatMargin(slotProps.data.profit_margin_pct)"
							:severity="getMarginBadgeSeverity(slotProps.data.profit_margin_pct)"
							class="text-[11px] font-bold"
						/>
					</template>
				</Column>
			</DataTable>

			<!-- Order Table -->
			<DataTable
				v-else
				:value="orderRows"
				:loading="loading"
				paginator
				:rows="10"
				:rowsPerPageOptions="[10, 25, 50]"
				tableStyle="min-width: 60rem"
				responsiveLayout="scroll"
				class="p-datatable-sm text-xs"
			>
				<template #empty>
					<div class="p-6 text-center text-slate-400">
						No order profit records found matching criteria.
					</div>
				</template>

				<!-- Order Number -->
				<Column field="order_number" header="Order #" sortable style="width: 140px">
					<template #body="slotProps">
						<router-link
							:to="`/orders/${slotProps.data.order_id}`"
							class="font-mono font-bold text-blue-600 dark:text-blue-400 hover:underline"
						>
							{{ slotProps.data.order_number }}
						</router-link>
					</template>
				</Column>

				<!-- Date -->
				<Column field="order_date" header="Date" sortable style="width: 130px">
					<template #body="slotProps">
						<span class="text-slate-600 dark:text-slate-400 font-medium">
							{{ slotProps.data.order_date ? moment(slotProps.data.order_date).format('DD MMM YYYY') : '—' }}
						</span>
					</template>
				</Column>

				<!-- Customer -->
				<Column field="stakeholder_name" header="Customer" sortable style="min-width: 160px">
					<template #body="slotProps">
						<span class="font-semibold text-slate-800 dark:text-slate-200">
							{{ slotProps.data.stakeholder_name }}
						</span>
					</template>
				</Column>

				<!-- Order Status -->
				<Column field="order_status" header="Status" style="width: 110px">
					<template #body="slotProps">
						<span
							class="px-2 py-0.5 rounded text-[11px] font-semibold"
							:class="slotProps.data.order_status === 'Closed'
								? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-400'
								: 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-400'"
						>
							{{ slotProps.data.order_status }}
						</span>
					</template>
				</Column>

				<!-- Items Count -->
				<Column field="items_count" header="Lines" style="width: 70px">
					<template #body="slotProps">
						<span class="text-slate-600 dark:text-slate-400">
							{{ slotProps.data.items_count }}
						</span>
					</template>
				</Column>

				<!-- Revenue -->
				<Column field="total_revenue" header="Revenue" sortable style="width: 130px">
					<template #body="slotProps">
						<span class="font-semibold text-slate-900 dark:text-white">
							{{ formatCurrency(slotProps.data.total_revenue) }}
						</span>
					</template>
				</Column>

				<!-- COGS -->
				<Column field="total_cogs" header="Total Cost" sortable style="width: 130px">
					<template #body="slotProps">
						<span class="text-slate-600 dark:text-slate-400 font-mono">
							{{ formatCurrency(slotProps.data.total_cogs) }}
						</span>
					</template>
				</Column>

				<!-- Gross Profit -->
				<Column field="gross_profit" header="Gross Profit" sortable style="width: 130px">
					<template #body="slotProps">
						<span
							class="font-bold"
							:class="slotProps.data.gross_profit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'"
						>
							{{ formatCurrency(slotProps.data.gross_profit) }}
						</span>
					</template>
				</Column>

				<!-- Margin % -->
				<Column field="profit_margin_pct" header="Margin %" sortable style="width: 120px">
					<template #body="slotProps">
						<Tag
							:value="formatMargin(slotProps.data.profit_margin_pct)"
							:severity="getMarginBadgeSeverity(slotProps.data.profit_margin_pct)"
							class="text-[11px] font-bold"
						/>
					</template>
				</Column>
			</DataTable>
		</div>
	</div>
</template>
