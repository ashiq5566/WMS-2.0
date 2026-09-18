<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch, computed } from "vue";
import axios from "@/plugins/axios";
import moment from "moment";
import { debounce } from "lodash";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Card from "primevue/card";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Dialog from "primevue/dialog";
import DatePicker from "primevue/datepicker";
import Skeleton from "primevue/skeleton";
import {
	formatCurrency,
	formatNumber,
	getOrderStatusSeverity,
	getOrderTypeLabel,
} from "@/utils/orderCalculations";

interface StakeholderObj {
	id: number;
	name: string;
	type?: string;
}

interface OrderRecord {
	id: number;
	order_number: string;
	order_type: "SO" | "PO";
	stakeholder: number;
	stakeholder_obj?: StakeholderObj;
	gross_amount: number;
	discount: number;
	net_amount: number;
	total_amount: number;
	pending_amount: number;
	order_status: "Issued" | "Delivered" | "Recieved" | "Cancelled" | "Closed";
	order_date: string | null;
	date_added: string;
	created_at: string;
}

const orders = ref<OrderRecord[]>([]);
const stakeholders = ref<StakeholderObj[]>([]);
const searchInput = ref("");
const filterDates = ref<Date[] | null>(null);
const selectedType = ref("ALL");
const selectedStatus = ref("ALL");
const selectedStakeholder = ref<number | string>("ALL");
const selectedPaymentStatus = ref("ALL");

const isLoading = ref(true);
const isRefreshing = ref(false);
const toast = useToast();

// Cancellation modal state
const cancelDialogVisible = ref(false);
const orderToCancel = ref<OrderRecord | null>(null);
const isCancelling = ref(false);

const typeOptions = [
	{ label: "All Order Types", value: "ALL" },
	{ label: "Sales Orders (SO)", value: "SO" },
	{ label: "Purchase Orders (PO)", value: "PO" },
];

const statusOptions = [
	{ label: "All Statuses", value: "ALL" },
	{ label: "Issued", value: "Issued" },
	{ label: "Delivered", value: "Delivered" },
	{ label: "Recieved", value: "Recieved" },
	{ label: "Cancelled", value: "Cancelled" },
	{ label: "Closed", value: "Closed" },
];

const paymentStatusOptions = [
	{ label: "All Settlements", value: "ALL" },
	{ label: "Fully Settled", value: "SETTLED" },
	{ label: "Partially Settled", value: "PARTIAL" },
	{ label: "Outstanding / Unpaid", value: "UNPAID" },
];

const fetchStakeholders = async () => {
	try {
		const response = await axios.get("/api/accounts/stakeholders/");
		stakeholders.value = response.data || [];
	} catch (error) {
		console.error("Error fetching stakeholders:", error);
	}
};

const fetchOrders = async (search = searchInput.value) => {
	try {
		const params: Record<string, any> = {};
		if (search.trim()) params.search = search.trim();
		if (selectedStakeholder.value !== "ALL") params.stakeholder_id = selectedStakeholder.value;
		if (selectedType.value !== "ALL") params.order_type = selectedType.value;
		if (selectedStatus.value !== "ALL") params.order_status = selectedStatus.value;

		if (filterDates.value && filterDates.value[0]) {
			params.date_added__gte = moment(filterDates.value[0]).startOf("day").toISOString();
			if (filterDates.value[1]) {
				params.date_added__lte = moment(filterDates.value[1]).endOf("day").toISOString();
			}
		}

		const response = await axios.get("/api/inventory/orders", { params });
		orders.value = response.data || [];
	} catch (error) {
		console.error("Error fetching orders:", error);
		toast.add({
			severity: "error",
			summary: "Failed to Load Orders",
			detail: "Unable to retrieve orders from server.",
			life: 3000,
		});
	} finally {
		isLoading.value = false;
		isRefreshing.value = false;
	}
};

const debouncedFetchOrders = debounce(fetchOrders, 350);

const refreshData = async () => {
	isRefreshing.value = true;
	await fetchOrders();
	toast.add({ severity: "info", summary: "Refreshed", detail: "Order book updated.", life: 2000 });
};

watch(searchInput, (newVal) => {
	debouncedFetchOrders(newVal);
});

watch([selectedStakeholder, selectedType, selectedStatus, filterDates], () => {
	fetchOrders();
});

onBeforeUnmount(() => {
	debouncedFetchOrders.cancel();
});

onMounted(() => {
	fetchOrders();
	fetchStakeholders();
});

// Client-side refined filtering (e.g. payment settlement status)
const filteredOrders = computed(() => {
	return orders.value.filter((order) => {
		if (selectedPaymentStatus.value === "SETTLED" && (order.pending_amount || 0) > 0) return false;
		if (selectedPaymentStatus.value === "PARTIAL") {
			const pending = order.pending_amount || 0;
			const net = order.net_amount || 0;
			if (pending <= 0 || pending >= net) return false;
		}
		if (selectedPaymentStatus.value === "UNPAID") {
			const pending = order.pending_amount || 0;
			const net = order.net_amount || 0;
			if (net > 0 && pending < net) return false;
		}
		return true;
	});
});

const isFilterActive = computed(() => {
	return (
		searchInput.value.trim() !== "" ||
		selectedType.value !== "ALL" ||
		selectedStatus.value !== "ALL" ||
		selectedStakeholder.value !== "ALL" ||
		selectedPaymentStatus.value !== "ALL" ||
		(filterDates.value && filterDates.value.length > 0)
	);
});

const resetFilters = () => {
	searchInput.value = "";
	selectedType.value = "ALL";
	selectedStatus.value = "ALL";
	selectedStakeholder.value = "ALL";
	selectedPaymentStatus.value = "ALL";
	filterDates.value = null;
	fetchOrders("");
};

// Executive KPI Metrics
const totalOrdersCount = computed(() => orders.value.length);

const salesOrders = computed(() => orders.value.filter((o) => o.order_type === "SO"));
const salesRevenue = computed(() => salesOrders.value.reduce((sum, o) => sum + (Number(o.net_amount) || 0), 0));

const purchaseOrders = computed(() => orders.value.filter((o) => o.order_type === "PO"));
const purchaseSpend = computed(() => purchaseOrders.value.reduce((sum, o) => sum + (Number(o.net_amount) || 0), 0));

const totalPendingBalance = computed(() => {
	return orders.value
		.filter((o) => o.order_status !== "Cancelled")
		.reduce((sum, o) => sum + (Number(o.pending_amount) || 0), 0);
});

const completedOrdersCount = computed(() => {
	return orders.value.filter((o) => o.order_status === "Delivered" || o.order_status === "Recieved" || o.order_status === "Closed").length;
});

const cancelledOrdersCount = computed(() => {
	return orders.value.filter((o) => o.order_status === "Cancelled").length;
});

// Quick Filter Card Clicks
const applyQuickFilter = (type: "SO" | "PO" | "COMPLETED" | "ALL") => {
	if (type === "ALL") {
		resetFilters();
	} else if (type === "SO") {
		selectedType.value = "SO";
		selectedStatus.value = "ALL";
	} else if (type === "PO") {
		selectedType.value = "PO";
		selectedStatus.value = "ALL";
	} else if (type === "COMPLETED") {
		selectedType.value = "ALL";
		selectedStatus.value = "Delivered";
	}
};

// Order Cancellation Flow
const confirmCancelOrder = (order: OrderRecord) => {
	orderToCancel.value = order;
	cancelDialogVisible.value = true;
};

const executeCancellation = async () => {
	if (!orderToCancel.value) return;
	isCancelling.value = true;
	try {
		await axios.post(`/api/inventory/orders/${orderToCancel.value.id}/cancel/`);
		toast.add({
			severity: "success",
			summary: "Order Cancelled",
			detail: `Order ${orderToCancel.value.order_number} was cancelled and inventory stock restored.`,
			life: 3500,
		});
		cancelDialogVisible.value = false;
		orderToCancel.value = null;
		fetchOrders();
	} catch (error: any) {
		console.error("Cancellation error:", error);
		const msg = error.response?.data?.error || "Failed to cancel order.";
		toast.add({
			severity: "error",
			summary: "Cancellation Failed",
			detail: msg,
			life: 4000,
		});
	} finally {
		isCancelling.value = false;
	}
};
</script>

<template>
	<div class="space-y-6 pb-12 text-slate-800 dark:text-slate-100">
		<!-- Page Header -->
		<div
			class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm transition-colors"
		>
			<div>
				<div class="flex items-center gap-2 mb-1">
					<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
					<span class="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
						Commercial Fulfillment Pipeline
					</span>
				</div>
				<h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
					Orders & Logistics
				</h1>
				<p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
					Track inbound purchase receipts, customer shipments, real-time receivables, and stock movements
				</p>
			</div>

			<div class="flex items-center gap-3">
				<Button
					icon="pi pi-refresh"
					label="Refresh"
					:loading="isRefreshing"
					size="small"
					severity="secondary"
					outlined
					class="!text-xs !py-2 !px-3.5 !rounded-lg hover:!bg-slate-100 dark:hover:!bg-slate-800"
					@click="refreshData"
				/>
				<router-link :to="{ name: 'orders-create' }">
					<Button
						label="Create Order"
						icon="pi pi-plus"
						severity="primary"
						class="!text-xs !py-2 !px-4 !rounded-lg !bg-indigo-600 hover:!bg-indigo-700 !border-indigo-600 shadow-sm"
					/>
				</router-link>
			</div>
		</div>

		<!-- Executive KPI Cards -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- KPI 1: Total Orders -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm hover:border-indigo-400 dark:hover:border-indigo-500/60 transition-all cursor-pointer flex items-center justify-between"
				@click="applyQuickFilter('ALL')"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Total Orders
					</span>
					<div class="text-2xl font-bold text-slate-900 dark:text-white">
						{{ formatNumber(totalOrdersCount) }}
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400">
						<span class="text-emerald-600 dark:text-emerald-400 font-semibold">{{ completedOrdersCount }}</span> Fulfilled
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xl shadow-inner"
				>
					<i class="pi pi-folder"></i>
				</div>
			</div>

			<!-- KPI 2: Sales Revenue -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm hover:border-emerald-400 dark:hover:border-emerald-500/60 transition-all cursor-pointer flex items-center justify-between"
				@click="applyQuickFilter('SO')"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Sales Revenue
					</span>
					<div class="text-2xl font-bold text-slate-900 dark:text-white">
						{{ formatCurrency(salesRevenue) }}
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400">
						{{ salesOrders.length }} Sales Orders (SO)
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xl shadow-inner"
				>
					<i class="pi pi-arrow-up-right"></i>
				</div>
			</div>

			<!-- KPI 3: Procurement Spend -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm hover:border-purple-400 dark:hover:border-purple-500/60 transition-all cursor-pointer flex items-center justify-between"
				@click="applyQuickFilter('PO')"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Procurement Spend
					</span>
					<div class="text-2xl font-bold text-slate-900 dark:text-white">
						{{ formatCurrency(purchaseSpend) }}
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400">
						{{ purchaseOrders.length }} Purchase Orders (PO)
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400 flex items-center justify-center text-xl shadow-inner"
				>
					<i class="pi pi-truck"></i>
				</div>
			</div>

			<!-- KPI 4: Outstanding Balance -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex items-center justify-between"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Pending Settlement
					</span>
					<div class="text-2xl font-bold text-amber-600 dark:text-amber-400">
						{{ formatCurrency(totalPendingBalance) }}
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400">
						<span v-if="cancelledOrdersCount > 0" class="text-rose-500 font-semibold">{{ cancelledOrdersCount }} cancelled</span>
						<span v-else>Active commercial balance</span>
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 flex items-center justify-center text-xl shadow-inner"
				>
					<i class="pi pi-wallet"></i>
				</div>
			</div>
		</div>

		<!-- Main Orders Table Container -->
		<div class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm rounded-2xl p-5 overflow-hidden">
				<!-- Filters and Search Toolbar -->
				<div class="flex flex-col xl:flex-row xl:items-center justify-between gap-3 pb-5 border-b border-slate-100 dark:border-slate-800/80">
					<!-- Search Input -->
					<div class="w-full xl:w-72">
						<IconField iconPosition="left" class="w-full">
							<InputIcon class="pi pi-search text-slate-400" />
							<InputText
								v-model="searchInput"
								placeholder="Search order #, customer, ID..."
								class="w-full !text-xs !py-2 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700"
							/>
						</IconField>
					</div>

					<!-- Filter Controls -->
					<div class="flex flex-wrap items-center gap-2.5">
						<!-- Order Type Filter -->
						<Select
							v-model="selectedType"
							:options="typeOptions"
							optionLabel="label"
							optionValue="value"
							class="!text-xs !py-0.5 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 min-w-[140px]"
						/>

						<!-- Status Filter -->
						<Select
							v-model="selectedStatus"
							:options="statusOptions"
							optionLabel="label"
							optionValue="value"
							class="!text-xs !py-0.5 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 min-w-[130px]"
						/>

						<!-- Stakeholder Select -->
						<Select
							v-model="selectedStakeholder"
							:options="[{ id: 'ALL', name: 'All Stakeholders' }, ...stakeholders]"
							optionLabel="name"
							optionValue="id"
							placeholder="Stakeholder"
							filter
							class="!text-xs !py-0.5 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 min-w-[160px]"
						/>

						<!-- Settlement Status -->
						<Select
							v-model="selectedPaymentStatus"
							:options="paymentStatusOptions"
							optionLabel="label"
							optionValue="value"
							class="!text-xs !py-0.5 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 min-w-[140px]"
						/>

						<!-- Date Range Picker -->
						<DatePicker
							v-model="filterDates"
							selectionMode="range"
							:manualInput="false"
							placeholder="Date Range"
							showIcon
							class="!text-xs !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 max-w-[200px]"
						/>

						<!-- Reset Filter Button -->
						<Button
							v-if="isFilterActive"
							icon="pi pi-filter-slash"
							label="Reset"
							severity="secondary"
							text
							size="small"
							class="!text-xs !py-2 !px-2.5 !text-slate-500 hover:!text-slate-800 dark:hover:!text-white"
							@click="resetFilters"
						/>
					</div>
				</div>

				<!-- Loading Skeleton -->
				<div v-if="isLoading" class="space-y-3 py-6">
					<div v-for="n in 5" :key="n" class="flex items-center gap-4 p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl">
						<Skeleton width="90px" height="24px" class="rounded-md dark:!bg-slate-800" />
						<Skeleton width="70px" height="20px" class="rounded-md dark:!bg-slate-800" />
						<div class="flex-1 space-y-2">
							<Skeleton width="40%" height="16px" class="dark:!bg-slate-800" />
							<Skeleton width="25%" height="12px" class="dark:!bg-slate-800" />
						</div>
						<Skeleton width="100px" height="20px" class="dark:!bg-slate-800" />
						<Skeleton width="80px" height="24px" class="rounded-md dark:!bg-slate-800" />
					</div>
				</div>

				<!-- Orders DataTable -->
				<DataTable
					v-else
					:value="filteredOrders"
					dataKey="id"
					:paginator="true"
					:rows="10"
					:rowsPerPageOptions="[10, 20, 50]"
					paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
					currentPageReportTemplate="{first} to {last} of {totalRecords} orders"
					responsiveLayout="scroll"
					class="pt-2"
				>
					<!-- Column 1: Order Number / ID -->
					<Column field="order_number" header="Order #" :sortable="true" style="min-width: 140px">
						<template #body="{ data }">
							<router-link
								:to="{ name: 'orders-id', params: { id: data.id } }"
								class="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
							>
								<i class="pi pi-file text-[11px]"></i>
								{{ data.order_number || `ORD-${data.id}` }}
							</router-link>
						</template>
					</Column>

					<!-- Column 2: Order Type -->
					<Column field="order_type" header="Type" :sortable="true" style="width: 110px">
						<template #body="{ data }">
							<span
								class="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md"
								:class="data.order_type === 'SO' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60' : 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-400 border border-purple-200 dark:border-purple-800/60'"
							>
								<i :class="data.order_type === 'SO' ? 'pi pi-arrow-up-right' : 'pi pi-truck'" class="text-[9px]"></i>
								{{ data.order_type === 'SO' ? 'Sales' : 'Purchase' }}
							</span>
						</template>
					</Column>

					<!-- Column 3: Stakeholder / Company -->
					<Column header="Client / Vendor" :sortable="true" style="min-width: 180px">
						<template #body="{ data }">
							<div class="space-y-0.5">
								<div class="font-semibold text-slate-900 dark:text-white text-xs">
									{{ data.stakeholder_obj?.name || 'Unspecified Stakeholder' }}
								</div>
								<div class="text-[10px] text-slate-400 dark:text-slate-500">
									{{ data.stakeholder_obj?.type || (data.order_type === 'SO' ? 'Customer' : 'Supplier') }}
								</div>
							</div>
						</template>
					</Column>

					<!-- Column 4: Order Date -->
					<Column field="date_added" header="Date" :sortable="true" style="min-width: 110px">
						<template #body="{ data }">
							<div class="text-xs text-slate-600 dark:text-slate-300">
								{{ moment(data.date_added || data.order_date).format('DD MMM YYYY') }}
							</div>
							<div class="text-[10px] text-slate-400">
								{{ moment(data.date_added || data.order_date).format('hh:mm A') }}
							</div>
						</template>
					</Column>

					<!-- Column 5: Financials -->
					<Column field="net_amount" header="Total & Pending" :sortable="true" style="min-width: 150px">
						<template #body="{ data }">
							<div class="text-xs font-bold text-slate-900 dark:text-white">
								{{ formatCurrency(data.net_amount) }}
							</div>
							<div class="text-[11px]">
								<span v-if="(data.pending_amount || 0) > 0" class="text-amber-600 dark:text-amber-400 font-medium">
									Due: {{ formatCurrency(data.pending_amount) }}
								</span>
								<span v-else class="text-emerald-600 dark:text-emerald-400 font-medium">
									Settled
								</span>
							</div>
						</template>
					</Column>

					<!-- Column 6: Workflow Status -->
					<Column field="order_status" header="Status" :sortable="true" style="width: 120px">
						<template #body="{ data }">
							<Tag
								:severity="getOrderStatusSeverity(data.order_status)"
								:value="data.order_status"
								class="!text-[10px] !px-2 !py-0.5"
							/>
						</template>
					</Column>

					<!-- Column 7: Actions -->
					<Column header="Actions" style="width: 110px" bodyStyle="text-align: right">
						<template #body="{ data }">
							<div class="flex items-center justify-end gap-1">
								<router-link :to="{ name: 'orders-id', params: { id: data.id } }">
									<Button
										icon="pi pi-eye"
										text
										rounded
										size="small"
										class="!w-7 !h-7 !text-slate-500 hover:!text-indigo-600 hover:!bg-slate-100 dark:hover:!bg-slate-800"
										v-tooltip.top="'View Order Details'"
									/>
								</router-link>

								<Button
									v-if="data.order_status !== 'Cancelled'"
									icon="pi pi-times-circle"
									severity="danger"
									text
									rounded
									size="small"
									class="!w-7 !h-7 !text-rose-400 hover:!text-rose-600 hover:!bg-rose-50 dark:hover:!bg-rose-950/40"
									v-tooltip.top="'Cancel Order & Reverse Stock'"
									@click="confirmCancelOrder(data)"
								/>
							</div>
						</template>
					</Column>

					<!-- Empty State -->
					<template #empty>
						<div class="py-12 flex flex-col items-center justify-center text-center space-y-3">
							<div class="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center text-xl">
								<i class="pi pi-inbox"></i>
							</div>
							<div class="space-y-1">
								<h3 class="text-sm font-semibold text-slate-800 dark:text-slate-200">No orders found</h3>
								<p class="text-xs text-slate-500 dark:text-slate-400 max-w-sm">
									{{ isFilterActive ? 'Try adjusting your search criteria, stakeholder, or date filter to see matching orders.' : 'Get started by creating your first sales or purchase order.' }}
								</p>
							</div>
							<div class="flex items-center gap-2">
								<Button
									v-if="isFilterActive"
									label="Clear Filters"
									icon="pi pi-filter-slash"
									size="small"
									severity="secondary"
									outlined
									class="!text-xs !py-1.5 !px-3"
									@click="resetFilters"
								/>
								<router-link :to="{ name: 'orders-create' }">
									<Button
										label="Create Order"
										icon="pi pi-plus"
										size="small"
										severity="primary"
										class="!text-xs !py-1.5 !px-3 !bg-indigo-600 !border-indigo-600"
									/>
								</router-link>
							</div>
						</div>
					</template>
				</DataTable>
		</div>

		<!-- Order Cancellation Confirmation Dialog -->
		<Dialog
			v-model:visible="cancelDialogVisible"
			modal
			header="Confirm Order Cancellation"
			:style="{ width: '32rem', maxWidth: '95vw' }"
			class="dark:!bg-slate-900 dark:!text-slate-100"
		>
			<div v-if="orderToCancel" class="space-y-3 pt-2">
				<div class="flex items-start gap-3">
					<div class="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 flex items-center justify-center text-xl shrink-0">
						<i class="pi pi-exclamation-triangle"></i>
					</div>
					<div>
						<h4 class="text-sm font-bold text-slate-900 dark:text-white">
							Cancel {{ getOrderTypeLabel(orderToCancel.order_type) }} #{{ orderToCancel.order_number }}?
						</h4>
						<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
							Cancelling this order will atomically reverse all allocated inventory movements and release or deduct stock in accordance with WMS audit rules:
						</p>
					</div>
				</div>

				<div class="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl text-xs space-y-1 text-slate-600 dark:text-slate-300">
					<div>• <strong>Type:</strong> {{ getOrderTypeLabel(orderToCancel.order_type) }}</div>
					<div>• <strong>Stakeholder:</strong> {{ orderToCancel.stakeholder_obj?.name }}</div>
					<div>• <strong>Order Net Value:</strong> {{ formatCurrency(orderToCancel.net_amount) }}</div>
					<div>• <strong>Inventory Action:</strong>
						<span v-if="orderToCancel.order_type === 'SO'" class="text-emerald-600 dark:text-emerald-400 font-semibold">
							Restores all size stock units back to available inventory.
						</span>
						<span v-else class="text-amber-600 dark:text-amber-400 font-semibold">
							Deducts received units from warehouse inventory.
						</span>
					</div>
				</div>
			</div>

			<template #footer>
				<div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/80">
					<Button
						label="Keep Order"
						severity="secondary"
						text
						size="small"
						class="!text-xs !py-2 !px-3.5"
						@click="cancelDialogVisible = false"
					/>
					<Button
						label="Cancel Order & Reverse Stock"
						icon="pi pi-check"
						severity="danger"
						:loading="isCancelling"
						size="small"
						class="!text-xs !py-2 !px-3.5 !bg-rose-600 hover:!bg-rose-700 !border-rose-600"
						@click="executeCancellation"
					/>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<style scoped></style>