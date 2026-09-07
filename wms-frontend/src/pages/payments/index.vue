<script setup lang="ts">
import { onMounted, ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import axios from "@/plugins/axios";
import moment from "moment";
import { useToast } from "primevue/usetoast";
import AddPaymentModal from "@/components/payments/AddPaymentModal.vue";
import {
	formatCurrency,
	formatNumber,
	getPaymentTypeInfo,
	getPaymentStatusSeverity,
	getPaymentMethodInfo,
	type PaymentRecord,
} from "@/utils/paymentCalculations";

const router = useRouter();
const toast = useToast();

// State
const payments = ref<PaymentRecord[]>([]);
const loading = ref(false);
const summaryLoading = ref(false);

// Filter States
const searchInput = ref("");
const selectedType = ref<string | null>(null);
const selectedStatus = ref<string | null>(null);
const selectedMethod = ref<string | null>(null);
const filterDateRange = ref<any>(null);

// Financial Summary KPIs from backend
const summary = ref({
	total_revenue: 0,
	total_purchase_expense: 0,
	total_received: 0,
	total_paid: 0,
	total_refunds: 0,
	net_cash_flow: 0,
	outstanding_receivables: 0,
	outstanding_payables: 0,
	overdue_receivables: 0,
	overdue_payables: 0,
	today_collections: 0,
	today_disbursements: 0,
	order_status_breakdown: {
		paid_orders: 0,
		partially_paid_orders: 0,
		unpaid_orders: 0,
		overdue_orders: 0,
	},
	monthly_trends: [] as { month: string; inflows: number; outflows: number; net: number }[],
});

const paymentTypeOptions = [
	{ label: "All Payment Types", value: null },
	{ label: "Customer Receipts (Inflows)", value: "INBOUND" },
	{ label: "Supplier Disbursements (Outflows)", value: "OUTBOUND" },
	{ label: "Refunds / Credits", value: "REFUND" },
];

const statusOptions = [
	{ label: "All Statuses", value: null },
	{ label: "Completed", value: "Completed" },
	{ label: "Pending", value: "Pending" },
	{ label: "Cancelled", value: "Cancelled" },
];

const methodOptions = [
	{ label: "All Methods", value: null },
	{ label: "Cash", value: "CASH" },
	{ label: "Card", value: "CARD" },
	{ label: "Bank Transfer", value: "BANK" },
	{ label: "Other", value: "OTHER" },
];

// Fetch financial summary metrics
const fetchFinancialSummary = async () => {
	try {
		summaryLoading.value = true;
		const response = await axios.get("/api/inventory/payments/financial_summary/");
		summary.value = response.data;
	} catch (error) {
		console.error("Error fetching financial summary:", error);
	} finally {
		summaryLoading.value = false;
	}
};

// Fetch payments table list
const fetchPayments = async () => {
	try {
		loading.value = true;
		const params: Record<string, any> = {};

		if (searchInput.value.trim()) params.search = searchInput.value.trim();
		if (selectedType.value) params.payment_type = selectedType.value;
		if (selectedStatus.value) params.status = selectedStatus.value;
		if (selectedMethod.value) params.payment_method = selectedMethod.value;

		if (filterDateRange.value && filterDateRange.value[0]) {
			params.payment_date__gte = new Date(filterDateRange.value[0]).toISOString();
			if (filterDateRange.value[1]) {
				params.payment_date__lte = new Date(filterDateRange.value[1]).toISOString();
			}
		}

		const response = await axios.get("/api/inventory/payments/", { params });
		payments.value = response.data;
	} catch (error) {
		console.error("Error fetching payments list:", error);
		toast.add({
			severity: "error",
			summary: "Error",
			detail: "Failed to load payment transactions.",
			life: 3000,
		});
	} finally {
		loading.value = false;
	}
};

// Search debounce
let searchTimeout: any = null;
watch(searchInput, () => {
	clearTimeout(searchTimeout);
	searchTimeout = setTimeout(() => {
		fetchPayments();
	}, 350);
});

watch([selectedType, selectedStatus, selectedMethod, filterDateRange], () => {
	fetchPayments();
});

const reloadData = () => {
	fetchPayments();
	fetchFinancialSummary();
};

const navigateToDetail = (id: number) => {
	router.push(`/payments/${id}`);
};

// ApexCharts Options for Cash Flow Visualization
const cashFlowChartOptions = computed(() => {
	const categories = summary.value.monthly_trends.map((t) => t.month);
	return {
		chart: {
			type: "bar",
			height: 280,
			toolbar: { show: false },
			fontFamily: "inherit",
		},
		plotOptions: {
			bar: {
				horizontal: false,
				columnWidth: "45%",
				borderRadius: 4,
			},
		},
		colors: ["#10b981", "#f59e0b", "#3b82f6"],
		dataLabels: { enabled: false },
		stroke: { show: true, width: 2, colors: ["transparent"] },
		xaxis: {
			categories: categories.length ? categories : ["No Data"],
			labels: { style: { colors: "#64748b", fontSize: "11px" } },
		},
		yaxis: {
			labels: {
				formatter: (val: number) => "₹" + (val >= 1000 ? (val / 1000).toFixed(0) + "k" : val),
				style: { colors: "#64748b", fontSize: "11px" },
			},
		},
		tooltip: {
			y: { formatter: (val: number) => formatCurrency(val) },
		},
		legend: {
			position: "top",
			horizontalAlign: "right",
			labels: { colors: "#64748b" },
		},
		grid: {
			borderColor: "#e2e8f0",
			strokeDashArray: 4,
		},
	};
});

const cashFlowChartSeries = computed(() => {
	return [
		{
			name: "Money Received (Inflows)",
			data: summary.value.monthly_trends.map((t) => t.inflows),
		},
		{
			name: "Money Paid (Outflows)",
			data: summary.value.monthly_trends.map((t) => t.outflows),
		},
		{
			name: "Net Position",
			data: summary.value.monthly_trends.map((t) => t.net),
		},
	];
});

// CSV Export
const exportCSV = () => {
	if (!payments.value.length) return;
	const headers = ["Payment #", "Date", "Reference", "Partner", "Type", "Amount", "Method", "Status", "Order Ref"];
	const rows = payments.value.map((p) => [
		p.payment_number || `PAY-${p.id}`,
		p.payment_date ? moment(p.payment_date).format("YYYY-MM-DD") : "",
		`"${(p.reference || "").replace(/"/g, '""')}"`,
		`"${(p.company_obj?.name || "").replace(/"/g, '""')}"`,
		p.payment_type || "INBOUND",
		p.amount || 0,
		p.payment_method,
		p.status || "Completed",
		p.order_obj?.order_number || "",
	]);
	const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
	const encodedUri = encodeURI(csvContent);
	const link = document.createElement("a");
	link.setAttribute("href", encodedUri);
	link.setAttribute("download", `wms_payments_${new Date().toISOString().slice(0, 10)}.csv`);
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
};

onMounted(() => {
	fetchFinancialSummary();
	fetchPayments();
});
</script>

<template>
	<div class="space-y-6 pb-12">
		<!-- Page Header & Action Bar -->
		<div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
			<div>
				<div class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 mb-1">
					<i class="pi pi-wallet text-xs"></i>
					<span>Finance & Accounting</span>
					<span>/</span>
					<span class="text-slate-900 dark:text-slate-200 font-medium">Financial Dashboard</span>
				</div>
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
					Money Movement & Payment Ledger
				</h1>
				<p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
					Track cash inflows, supplier disbursements, debt receivables, payables, and settlement vouchers.
				</p>
			</div>

			<div class="flex items-center gap-2.5">
				<Button
					icon="pi pi-download"
					label="Export CSV"
					severity="secondary"
					outlined
					size="small"
					@click="exportCSV"
				/>
				<AddPaymentModal @instance-added="reloadData" />
			</div>
		</div>

		<!-- Top Financial KPI Grid (10 Core Metrics in 2 Strips) -->
		<div class="space-y-3">
			<!-- Primary Row: Inflow / Outflow / Position / Balances -->
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
				<!-- Total Revenue -->
				<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Sales Invoiced</p>
					<h3 class="text-xl font-extrabold text-slate-900 dark:text-white mt-1">
						{{ formatCurrency(summary.total_revenue) }}
					</h3>
					<span class="text-xs text-slate-400 mt-0.5 block">Lifetime billing volume</span>
				</div>

				<!-- Total Inflows Received -->
				<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Money Received</p>
					<h3 class="text-xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
						{{ formatCurrency(summary.total_received) }}
					</h3>
					<span class="text-xs text-emerald-600/80 dark:text-emerald-400/80 mt-0.5 block flex items-center gap-1">
						<i class="pi pi-arrow-down-left text-[10px]"></i> Total Cash Inflows
					</span>
				</div>

				<!-- Total Outflows Paid -->
				<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Money Paid</p>
					<h3 class="text-xl font-extrabold text-amber-600 dark:text-amber-400 mt-1">
						{{ formatCurrency(summary.total_paid) }}
					</h3>
					<span class="text-xs text-amber-600/80 dark:text-amber-400/80 mt-0.5 block flex items-center gap-1">
						<i class="pi pi-arrow-up-right text-[10px]"></i> Vendor Disbursements
					</span>
				</div>

				<!-- Net Cash Flow Position -->
				<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Net Cash Position</p>
					<h3
						class="text-xl font-extrabold mt-1"
						:class="summary.net_cash_flow >= 0 ? 'text-blue-600 dark:text-blue-400' : 'text-rose-600 dark:text-rose-400'"
					>
						{{ formatCurrency(summary.net_cash_flow) }}
					</h3>
					<span class="text-xs text-slate-400 mt-0.5 block">Inflows minus Outflows</span>
				</div>

				<!-- Outstanding Receivables -->
				<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Outstanding Receivables</p>
					<h3 class="text-xl font-extrabold text-indigo-600 dark:text-indigo-400 mt-1">
						{{ formatCurrency(summary.outstanding_receivables) }}
					</h3>
					<span class="text-xs text-rose-500 mt-0.5 block">
						Overdue (>30d): {{ formatCurrency(summary.overdue_receivables) }}
					</span>
				</div>
			</div>

			<!-- Secondary Row: Today & Overdue Liquidity Focus -->
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
				<!-- Outstanding Payables -->
				<div class="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Outstanding Payables</p>
					<h4 class="text-lg font-bold text-amber-600 dark:text-amber-400 mt-0.5">
						{{ formatCurrency(summary.outstanding_payables) }}
					</h4>
					<span class="text-[11px] text-rose-500 mt-0.5 block">
						Overdue (>30d): {{ formatCurrency(summary.overdue_payables) }}
					</span>
				</div>

				<!-- Today's Collections -->
				<div class="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Today's Collections</p>
					<h4 class="text-lg font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
						{{ formatCurrency(summary.today_collections) }}
					</h4>
					<span class="text-[11px] text-slate-400 mt-0.5 block">Received today</span>
				</div>

				<!-- Today's Disbursements -->
				<div class="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Today's Disbursements</p>
					<h4 class="text-lg font-bold text-amber-600 dark:text-amber-400 mt-0.5">
						{{ formatCurrency(summary.today_disbursements) }}
					</h4>
					<span class="text-[11px] text-slate-400 mt-0.5 block">Disbursed today</span>
				</div>

				<!-- Total Refunds Issued -->
				<div class="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">RMA Refunds Issued</p>
					<h4 class="text-lg font-bold text-rose-600 dark:text-rose-400 mt-0.5">
						{{ formatCurrency(summary.total_refunds) }}
					</h4>
					<span class="text-[11px] text-slate-400 mt-0.5 block">Customer return credits</span>
				</div>

				<!-- Total Procurement Expense -->
				<div class="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Procurement Expense</p>
					<h4 class="text-lg font-bold text-slate-700 dark:text-slate-300 mt-0.5">
						{{ formatCurrency(summary.total_purchase_expense) }}
					</h4>
					<span class="text-[11px] text-slate-400 mt-0.5 block">Purchase orders booked</span>
				</div>
			</div>
		</div>

		<!-- Visual Analytics Section: Cash Flow Chart & Real-Time Status Overview -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
			<!-- Chart Card: Cash Flow Trends -->
			<Card class="lg:col-span-2 shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
				<template #title>
					<div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
						<div class="flex items-center gap-2">
							<i class="pi pi-chart-bar text-blue-500 text-sm"></i>
							<span class="text-sm font-bold text-slate-900 dark:text-white">Cash Flow Trend (Inflows vs. Outflows)</span>
						</div>
						<span class="text-xs text-slate-400">Past 6 Months</span>
					</div>
				</template>
				<template #content>
					<div class="pt-2">
						<apexchart
							v-if="summary.monthly_trends.length"
							type="bar"
							height="270"
							:options="cashFlowChartOptions"
							:series="cashFlowChartSeries"
						/>
						<div v-else class="h-64 flex items-center justify-center text-slate-400 text-sm">
							No historical transaction data available.
						</div>
					</div>
				</template>
			</Card>

			<!-- Card: Real-Time Payment Status Overview -->
			<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
				<template #title>
					<div class="flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
						<i class="pi pi-check-circle text-emerald-500 text-sm"></i>
						<span class="text-sm font-bold text-slate-900 dark:text-white">Order Settlement Status</span>
					</div>
				</template>
				<template #content>
					<div class="space-y-4 pt-2">
						<!-- Fully Paid -->
						<div class="p-3 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30">
							<div class="flex items-center justify-between text-xs font-semibold text-emerald-800 dark:text-emerald-300 mb-1">
								<span class="flex items-center gap-1.5">
									<i class="pi pi-check text-emerald-600"></i>
									Fully Settled Orders
								</span>
								<span>{{ formatNumber(summary.order_status_breakdown.paid_orders) }}</span>
							</div>
							<p class="text-[11px] text-emerald-600/80 dark:text-emerald-400/80">Pending balance completely cleared (Closed)</p>
						</div>

						<!-- Partially Paid -->
						<div class="p-3 rounded-lg bg-amber-50/50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30">
							<div class="flex items-center justify-between text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">
								<span class="flex items-center gap-1.5">
									<i class="pi pi-clock text-amber-600"></i>
									Partially Paid Orders
								</span>
								<span>{{ formatNumber(summary.order_status_breakdown.partially_paid_orders) }}</span>
							</div>
							<p class="text-[11px] text-amber-600/80 dark:text-amber-400/80">Partial payments received; remaining balance due</p>
						</div>

						<!-- Unpaid -->
						<div class="p-3 rounded-lg bg-rose-50/50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30">
							<div class="flex items-center justify-between text-xs font-semibold text-rose-800 dark:text-rose-300 mb-1">
								<span class="flex items-center gap-1.5">
									<i class="pi pi-exclamation-circle text-rose-600"></i>
									Unpaid Active Orders
								</span>
								<span>{{ formatNumber(summary.order_status_breakdown.unpaid_orders) }}</span>
							</div>
							<p class="text-[11px] text-rose-600/80 dark:text-rose-400/80">No payments received yet against issued invoices</p>
						</div>

						<!-- Overdue -->
						<div class="p-3 rounded-lg bg-slate-100/60 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
							<div class="flex items-center justify-between text-xs font-semibold text-slate-800 dark:text-slate-300 mb-1">
								<span class="flex items-center gap-1.5">
									<i class="pi pi-calendar-times text-rose-500"></i>
									Aging Overdue (> 30 Days)
								</span>
								<span class="font-bold text-rose-600 dark:text-rose-400">
									{{ formatNumber(summary.order_status_breakdown.overdue_orders) }}
								</span>
							</div>
							<p class="text-[11px] text-slate-500 dark:text-slate-400">Invoices exceeding standard payment terms</p>
						</div>
					</div>
				</template>
			</Card>
		</div>

		<!-- Enterprise Payments Ledger DataTable -->
		<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
			<template #content>
				<!-- Multi-Criteria Filter Bar -->
				<div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
					<!-- Quick Segment Pills -->
					<div class="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
						<button
							type="button"
							@click="selectedType = null"
							class="px-3 py-1.5 text-xs font-semibold rounded-md transition-all"
							:class="selectedType === null ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'"
						>
							All Flows
						</button>
						<button
							type="button"
							@click="selectedType = 'INBOUND'"
							class="px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5"
							:class="selectedType === 'INBOUND' ? 'bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'"
						>
							<i class="pi pi-arrow-down-left text-xs"></i>
							Customer Receipts
						</button>
						<button
							type="button"
							@click="selectedType = 'OUTBOUND'"
							class="px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5"
							:class="selectedType === 'OUTBOUND' ? 'bg-white dark:bg-slate-700 text-amber-600 dark:text-amber-400 shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'"
						>
							<i class="pi pi-arrow-up-right text-xs"></i>
							Supplier Disbursements
						</button>
					</div>

					<!-- Filter Controls -->
					<div class="flex flex-wrap items-center gap-3">
						<!-- Method Filter -->
						<Select
							v-model="selectedMethod"
							:options="methodOptions"
							optionLabel="label"
							optionValue="value"
							placeholder="Method"
							class="w-36 p-inputtext-sm"
							showClear
						/>

						<!-- Status Filter -->
						<Select
							v-model="selectedStatus"
							:options="statusOptions"
							optionLabel="label"
							optionValue="value"
							placeholder="Status"
							class="w-36 p-inputtext-sm"
							showClear
						/>

						<!-- Date Range -->
						<DatePicker
							v-model="filterDateRange"
							selectionMode="range"
							:manualInput="false"
							placeholder="Date Range"
							showIcon
							class="w-48 p-inputtext-sm"
						/>

						<!-- Keyword Search -->
						<IconField iconPosition="left" class="w-full sm:w-60">
							<InputIcon class="pi pi-search text-slate-400" />
							<InputText
								v-model="searchInput"
								placeholder="Search voucher, order, partner..."
								class="w-full p-inputtext-sm"
							/>
						</IconField>

						<!-- Refresh Button -->
						<Button
							icon="pi pi-refresh"
							severity="secondary"
							text
							rounded
							:loading="loading"
							@click="reloadData"
							title="Refresh records"
						/>
					</div>
				</div>

				<!-- DataTable -->
				<DataTable
					:value="payments"
					:loading="loading"
					paginator
					:rows="10"
					:rowsPerPageOptions="[10, 20, 50]"
					tableStyle="min-width: 65rem"
					responsiveLayout="scroll"
					dataKey="id"
					class="p-datatable-sm"
				>
					<!-- Payment Voucher # -->
					<Column field="payment_number" header="Voucher #" sortable style="width: 140px">
						<template #body="slotProps">
							<router-link
								:to="`/payments/${slotProps.data.id}`"
								class="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline"
							>
								{{ slotProps.data.payment_number || `PAY-${slotProps.data.id}` }}
							</router-link>
						</template>
					</Column>

					<!-- Date Column -->
					<Column field="payment_date" header="Transaction Date" sortable style="width: 160px">
						<template #body="slotProps">
							<span class="text-xs text-slate-700 dark:text-slate-300 font-medium">
								{{ slotProps.data.payment_date ? moment(slotProps.data.payment_date).format('DD MMM YYYY, hh:mm A') : '—' }}
							</span>
						</template>
					</Column>

					<!-- Reference / UTR -->
					<Column field="reference" header="Reference / UTR" style="width: 140px">
						<template #body="slotProps">
							<span class="font-mono text-xs text-slate-600 dark:text-slate-400">
								{{ slotProps.data.reference || '—' }}
							</span>
						</template>
					</Column>

					<!-- Partner / Stakeholder -->
					<Column header="Partner / Company">
						<template #body="slotProps">
							<div class="flex items-center gap-2">
								<div class="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300">
									{{ (slotProps.data.company_obj?.name || 'P').slice(0, 2).toUpperCase() }}
								</div>
								<div>
									<router-link
										v-if="slotProps.data.company_obj?.id"
										:to="`/stakeholders/${slotProps.data.company_obj.id}`"
										class="font-semibold text-xs text-slate-900 dark:text-white hover:underline"
									>
										{{ slotProps.data.company_obj?.name }}
									</router-link>
									<span v-else class="font-semibold text-xs text-slate-900 dark:text-white">
										{{ slotProps.data.company_obj?.name || 'General Account' }}
									</span>
									<span class="text-[10px] text-slate-400 block">
										{{ slotProps.data.company_obj?.type || 'Stakeholder' }}
									</span>
								</div>
							</div>
						</template>
					</Column>

					<!-- Linked Order -->
					<Column header="Linked Order" style="width: 130px">
						<template #body="slotProps">
							<router-link
								v-if="slotProps.data.order_obj?.id"
								:to="`/orders/${slotProps.data.order_obj.id}`"
								class="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
							>
								{{ slotProps.data.order_obj.order_number }}
							</router-link>
							<span v-else class="text-xs text-slate-400 italic">Unallocated / OB</span>
						</template>
					</Column>

					<!-- Flow Type -->
					<Column field="payment_type" header="Type" sortable style="width: 150px">
						<template #body="slotProps">
							<Tag
								:value="getPaymentTypeInfo(slotProps.data.payment_type).label"
								:severity="getPaymentTypeInfo(slotProps.data.payment_type).severity"
								class="text-xs font-semibold"
							/>
						</template>
					</Column>

					<!-- Amount Column -->
					<Column field="amount" header="Amount" sortable style="width: 140px">
						<template #body="slotProps">
							<div class="text-right">
								<span
									class="text-sm font-extrabold block"
									:class="slotProps.data.payment_type === 'OUTBOUND' ? 'text-amber-600 dark:text-amber-400' : (slotProps.data.payment_type === 'REFUND' ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400')"
								>
									{{ slotProps.data.payment_type === 'OUTBOUND' || slotProps.data.payment_type === 'REFUND' ? '-' : '+' }}{{ formatCurrency(slotProps.data.amount) }}
								</span>
							</div>
						</template>
					</Column>

					<!-- Payment Method -->
					<Column field="payment_method" header="Method" style="width: 130px">
						<template #body="slotProps">
							<div class="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-300">
								<i :class="getPaymentMethodInfo(slotProps.data.payment_method).icon" class="text-slate-400"></i>
								<span>{{ getPaymentMethodInfo(slotProps.data.payment_method).label }}</span>
							</div>
						</template>
					</Column>

					<!-- Status -->
					<Column field="status" header="Status" style="width: 110px">
						<template #body="slotProps">
							<Tag
								:value="slotProps.data.status || 'Completed'"
								:severity="getPaymentStatusSeverity(slotProps.data.status)"
								class="text-xs font-semibold"
							/>
						</template>
					</Column>

					<!-- Actions -->
					<Column header="Actions" style="width: 90px">
						<template #body="slotProps">
							<Button
								icon="pi pi-receipt"
								severity="secondary"
								text
								rounded
								size="small"
								@click="navigateToDetail(slotProps.data.id)"
								title="View Payment Voucher"
							/>
						</template>
					</Column>

					<!-- Empty State -->
					<template #empty>
						<div class="py-12 text-center">
							<div class="w-12 h-12 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
								<i class="pi pi-wallet text-xl"></i>
							</div>
							<h4 class="text-sm font-semibold text-slate-800 dark:text-slate-200">No payment transactions found</h4>
							<p class="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
								Record inbound customer payments or outbound supplier disbursements to track financial movements.
							</p>
						</div>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style scoped></style>
