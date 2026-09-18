<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue";
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
import DatePicker from "primevue/datepicker";
import Skeleton from "primevue/skeleton";
import {
	formatCurrency,
	formatNumber,
	getReturnTypeLabel,
	getReturnTypeSeverity,
	getReturnStatusSeverity,
} from "@/utils/returnCalculations";

interface StakeholderObj {
	id: number;
	name: string;
	type?: string;
}

interface ReturnItemRecord {
	id: number;
	product: number;
	product_obj?: {
		id: number;
		name: string;
	};
	product_size?: number;
	product_size_obj?: {
		id: number;
		size: number;
	};
	quantity: number;
	price_at_return: number;
	total: number;
	condition?: string;
}

interface ReturnRecord {
	id: number;
	return_type: "SR" | "PR";
	return_status?: string;
	original_order: number;
	order_obj?: {
		id: number;
		order_number: string;
		order_type: "SO" | "PO";
		order_status: string;
		stakeholder_obj?: StakeholderObj;
	};
	date: string;
	date_added?: string;
	total_amount: number;
	reason?: string;
	items?: ReturnItemRecord[];
}

const returns = ref<ReturnRecord[]>([]);
const stakeholders = ref<StakeholderObj[]>([]);
const searchInput = ref("");
const filterDates = ref<Date[] | null>(null);
const selectedType = ref("ALL");
const selectedStatus = ref("ALL");
const selectedStakeholder = ref<number | string>("ALL");

const isLoading = ref(true);
const isRefreshing = ref(false);
const isApproving = ref<number | null>(null);
const toast = useToast();

const typeOptions = [
	{ label: "All Return Types", value: "ALL" },
	{ label: "Sales Returns (SR - Inbound)", value: "SR" },
	{ label: "Purchase Returns (PR - Outbound)", value: "PR" },
];

const statusOptions = [
	{ label: "All Statuses", value: "ALL" },
	{ label: "Completed", value: "Completed" },
	{ label: "Approved", value: "Approved" },
	{ label: "Pending Approval", value: "Pending Approval" },
	{ label: "Draft", value: "Draft" },
	{ label: "Rejected", value: "Rejected" },
];

const fetchStakeholders = async () => {
	try {
		const response = await axios.get("/api/accounts/stakeholders/");
		stakeholders.value = response.data || [];
	} catch (error) {
		console.error("Error fetching stakeholders:", error);
	}
};

const fetchReturns = async (search = searchInput.value) => {
	try {
		const params: Record<string, any> = {};

		if (selectedType.value !== "ALL") {
			params.return_type = selectedType.value;
		}

		if (selectedStatus.value !== "ALL") {
			params.return_status = selectedStatus.value;
		}

		if (selectedStakeholder.value !== "ALL") {
			params.original_order__stakeholder = selectedStakeholder.value;
		}

		if (filterDates.value && filterDates.value[0]) {
			params.date_added__gte = moment(filterDates.value[0]).startOf("day").toISOString();
		}
		if (filterDates.value && filterDates.value[1]) {
			params.date_added__lte = moment(filterDates.value[1]).endOf("day").toISOString();
		}

		if (search && search.trim()) {
			params.search = search.trim();
		}

		const response = await axios.get("/api/inventory/returns/", { params });
		returns.value = response.data || [];
	} catch (error) {
		console.error("Error fetching returns:", error);
		toast.add({
			severity: "error",
			summary: "Error",
			detail: "Failed to load returns list.",
			life: 3000,
		});
	} finally {
		isLoading.value = false;
		isRefreshing.value = false;
	}
};

const debouncedFetchReturns = debounce((val: string) => {
	fetchReturns(val);
}, 300);

const handleSearch = () => {
	isLoading.value = true;
	debouncedFetchReturns(searchInput.value);
};

const refreshData = async () => {
	isRefreshing.value = true;
	await fetchReturns(searchInput.value);
	toast.add({
		severity: "success",
		summary: "Refreshed",
		detail: "Returns synchronized with server.",
		life: 2000,
	});
};

const approveReturn = async (id: number) => {
	try {
		isApproving.value = id;
		await axios.post(`/api/inventory/returns/${id}/approve/`);
		toast.add({
			severity: "success",
			summary: "Return Approved",
			detail: `RMA-${String(id).padStart(4, "0")} approved and stock updated.`,
			life: 3000,
		});
		await fetchReturns(searchInput.value);
	} catch (error: any) {
		const msg = error.response?.data?.error || "Failed to approve return.";
		toast.add({ severity: "error", summary: "Approval Failed", detail: msg, life: 4000 });
	} finally {
		isApproving.value = null;
	}
};

const clearFilters = () => {
	searchInput.value = "";
	selectedType.value = "ALL";
	selectedStatus.value = "ALL";
	selectedStakeholder.value = "ALL";
	filterDates.value = null;
	isLoading.value = true;
	fetchReturns("");
};

const hasActiveFilters = computed(() => {
	return (
		searchInput.value !== "" ||
		selectedType.value !== "ALL" ||
		selectedStatus.value !== "ALL" ||
		selectedStakeholder.value !== "ALL" ||
		filterDates.value !== null
	);
});

// KPIs
const totalReturnsCount = computed(() => returns.value.length);

const totalSalesReturnValue = computed(() => {
	return returns.value
		.filter((r) => r.return_type === "SR")
		.reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0);
});

const totalPurchaseReturnValue = computed(() => {
	return returns.value
		.filter((r) => r.return_type === "PR")
		.reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0);
});

const totalItemsReturned = computed(() => {
	return returns.value.reduce((sum, r) => {
		const itemsQty = r.items?.reduce((itemSum, item) => itemSum + (Number(item.quantity) || 0), 0) || 0;
		return sum + itemsQty;
	}, 0);
});

watch([selectedType, selectedStatus, selectedStakeholder, filterDates], () => {
	isLoading.value = true;
	fetchReturns(searchInput.value);
});

onMounted(async () => {
	await Promise.all([fetchStakeholders(), fetchReturns()]);
});
</script>

<template>
	<div class="space-y-6">
		<!-- Page Header -->
		<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
			<div>
				<h1 class="text-2xl font-bold tracking-tight text-surface-900 dark:text-surface-0">
					Returns Management (RMA)
				</h1>
				<p class="text-sm text-surface-500 dark:text-surface-400 mt-1">
					Process customer returns (SR) and supplier returns (PR) with status workflows, condition classification, and live inventory reconciliations.
				</p>
			</div>
			<div class="flex items-center gap-3">
				<Button
					icon="pi pi-refresh"
					severity="secondary"
					outlined
					:loading="isRefreshing"
					@click="refreshData"
					v-tooltip.bottom="'Refresh data'"
				/>
				<router-link :to="{ name: 'returns-create' }">
					<Button label="Create Return" icon="pi pi-plus" class="shadow-sm" />
				</router-link>
			</div>
		</div>

		<!-- KPI Metric Cards -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- Total Returns -->
			<div class="p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-0 dark:bg-surface-900 shadow-sm">
				<div class="flex items-center justify-between">
					<span class="text-xs font-medium uppercase tracking-wider text-surface-500 dark:text-surface-400">Total Returns</span>
					<div class="w-8 h-8 rounded-lg bg-primary-50 dark:bg-primary-950/50 flex items-center justify-center text-primary-600 dark:text-primary-400">
						<i class="pi pi-replay text-sm"></i>
					</div>
				</div>
				<div class="mt-2 text-2xl font-bold text-surface-900 dark:text-surface-0">
					{{ formatNumber(totalReturnsCount) }}
				</div>
				<span class="text-xs text-surface-500 dark:text-surface-400">Processed RMAs</span>
			</div>

			<!-- Sales Returns (SR) Value -->
			<div class="p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-0 dark:bg-surface-900 shadow-sm">
				<div class="flex items-center justify-between">
					<span class="text-xs font-medium uppercase tracking-wider text-surface-500 dark:text-surface-400">Customer Returns (SR)</span>
					<div class="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400">
						<i class="pi pi-arrow-down-left text-sm"></i>
					</div>
				</div>
				<div class="mt-2 text-2xl font-bold text-blue-600 dark:text-blue-400">
					{{ formatCurrency(totalSalesReturnValue) }}
				</div>
				<span class="text-xs text-surface-500 dark:text-surface-400">Restored into inventory</span>
			</div>

			<!-- Purchase Returns (PR) Value -->
			<div class="p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-0 dark:bg-surface-900 shadow-sm">
				<div class="flex items-center justify-between">
					<span class="text-xs font-medium uppercase tracking-wider text-surface-500 dark:text-surface-400">Supplier Returns (PR)</span>
					<div class="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
						<i class="pi pi-arrow-up-right text-sm"></i>
					</div>
				</div>
				<div class="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">
					{{ formatCurrency(totalPurchaseReturnValue) }}
				</div>
				<span class="text-xs text-surface-500 dark:text-surface-400">Deducted from warehouse</span>
			</div>

			<!-- Total Units Returned -->
			<div class="p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-0 dark:bg-surface-900 shadow-sm">
				<div class="flex items-center justify-between">
					<span class="text-xs font-medium uppercase tracking-wider text-surface-500 dark:text-surface-400">Units Returned</span>
					<div class="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
						<i class="pi pi-box text-sm"></i>
					</div>
				</div>
				<div class="mt-2 text-2xl font-bold text-surface-900 dark:text-surface-0">
					{{ formatNumber(totalItemsReturned) }}
				</div>
				<span class="text-xs text-surface-500 dark:text-surface-400">Total physical units</span>
			</div>
		</div>

		<!-- Filters & Search Toolbar -->
		<Card class="border border-surface-200 dark:border-surface-800 shadow-sm">
			<template #content>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-center text-xs">
					<!-- Search -->
					<div>
						<IconField iconPosition="left" class="w-full">
							<InputIcon class="pi pi-search" />
							<InputText
								v-model="searchInput"
								placeholder="Search RMA, Order #, Party..."
								class="w-full text-xs"
								@input="handleSearch"
							/>
						</IconField>
					</div>

					<!-- Return Type Filter -->
					<div>
						<Select
							v-model="selectedType"
							:options="typeOptions"
							optionLabel="label"
							optionValue="value"
							placeholder="Filter by Type"
							class="w-full text-xs"
						/>
					</div>

					<!-- Return Status Filter -->
					<div>
						<Select
							v-model="selectedStatus"
							:options="statusOptions"
							optionLabel="label"
							optionValue="value"
							placeholder="Filter by Status"
							class="w-full text-xs"
						/>
					</div>

					<!-- Stakeholder Filter -->
					<div>
						<Select
							v-model="selectedStakeholder"
							:options="[{ id: 'ALL', name: 'All Parties' }, ...stakeholders]"
							optionLabel="name"
							optionValue="id"
							placeholder="Filter by Party"
							filter
							class="w-full text-xs"
						/>
					</div>

					<!-- Date Range Filter & Reset -->
					<div class="flex items-center gap-2">
						<DatePicker
							v-model="filterDates"
							selectionMode="range"
							:manualInput="false"
							placeholder="Date Range"
							showIcon
							class="w-full text-xs"
						/>
						<Button
							v-if="hasActiveFilters"
							icon="pi pi-filter-slash"
							severity="secondary"
							text
							rounded
							@click="clearFilters"
							v-tooltip.top="'Clear all filters'"
						/>
					</div>
				</div>
			</template>
		</Card>

		<!-- Data Table Card -->
		<Card class="border border-surface-200 dark:border-surface-800 shadow-sm overflow-hidden">
			<template #content>
				<div v-if="isLoading" class="p-6 space-y-4">
					<Skeleton height="3rem" class="w-full" />
					<Skeleton height="3rem" class="w-full" />
					<Skeleton height="3rem" class="w-full" />
					<Skeleton height="3rem" class="w-full" />
				</div>

				<DataTable
					v-else
					:value="returns"
					tableStyle="min-width: 60rem"
					paginator
					:rows="10"
					:rowsPerPageOptions="[10, 20, 50]"
					class="p-datatable-sm"
					responsiveLayout="scroll"
				>
					<!-- RMA / ID Column -->
					<Column field="id" header="RMA #" sortable style="width: 12%">
						<template #body="{ data }">
							<router-link
								:to="{ name: 'returns-id', params: { id: data.id } }"
								class="font-semibold text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1.5"
							>
								<i class="pi pi-receipt text-xs"></i>
								<span>RMA-{{ String(data.id).padStart(4, '0') }}</span>
							</router-link>
						</template>
					</Column>

					<!-- Return Type -->
					<Column field="return_type" header="Type" sortable style="width: 14%">
						<template #body="{ data }">
							<Tag
								:severity="getReturnTypeSeverity(data.return_type)"
								:value="data.return_type === 'SR' ? 'Sales Return' : 'Purchase Return'"
								class="text-[10px] font-semibold px-2 py-0.5"
							/>
						</template>
					</Column>

					<!-- Return Status -->
					<Column field="return_status" header="Status" sortable style="width: 14%">
						<template #body="{ data }">
							<Tag
								:severity="getReturnStatusSeverity(data.return_status || 'Completed')"
								:value="data.return_status || 'Completed'"
								class="text-[10px] font-semibold px-2 py-0.5"
							/>
						</template>
					</Column>

					<!-- Original Order Number -->
					<Column field="order_obj.order_number" header="Original Order" sortable style="width: 15%">
						<template #body="{ data }">
							<router-link
								v-if="data.order_obj?.id"
								:to="{ name: 'orders-id', params: { id: data.order_obj.id } }"
								class="font-medium text-surface-700 dark:text-surface-300 hover:text-primary-600 dark:hover:text-primary-400 hover:underline flex items-center gap-1"
							>
								<i class="pi pi-external-link text-xs"></i>
								<span>{{ data.order_obj.order_number }}</span>
							</router-link>
							<span v-else class="text-surface-400 italic">N/A</span>
						</template>
					</Column>

					<!-- Stakeholder / Party -->
					<Column header="Customer / Supplier" style="width: 18%">
						<template #body="{ data }">
							<div class="flex flex-col">
								<span class="font-medium text-surface-900 dark:text-surface-100">
									{{ data.order_obj?.stakeholder_obj?.name || "Unknown Party" }}
								</span>
								<span class="text-xs text-surface-500 dark:text-surface-400">
									{{ data.order_obj?.order_type === "SO" ? "Customer" : "Supplier" }}
								</span>
							</div>
						</template>
					</Column>

					<!-- Date -->
					<Column field="date" header="Date" sortable style="width: 12%">
						<template #body="{ data }">
							<span class="text-sm text-surface-600 dark:text-surface-400">
								{{ moment(data.date_added || data.date).format("DD MMM YYYY") }}
							</span>
						</template>
					</Column>

					<!-- Return Total Amount -->
					<Column field="total_amount" header="Return Amount" sortable style="width: 12%">
						<template #body="{ data }">
							<span class="font-semibold text-surface-900 dark:text-surface-100">
								{{ formatCurrency(data.total_amount) }}
							</span>
						</template>
					</Column>

					<!-- Actions -->
					<Column header="Action" style="width: 12%; text-align: right">
						<template #body="{ data }">
							<div class="flex items-center justify-end gap-1">
								<Button
									v-if="data.return_status === 'Pending Approval' || data.return_status === 'Draft'"
									icon="pi pi-check"
									label="Approve"
									size="small"
									severity="success"
									text
									:loading="isApproving === data.id"
									@click="approveReturn(data.id)"
									v-tooltip.top="'Approve & Restock'"
								/>
								<router-link :to="{ name: 'returns-id', params: { id: data.id } }">
									<Button
										icon="pi pi-chevron-right"
										severity="secondary"
										text
										rounded
										size="small"
										v-tooltip.left="'View Return Details'"
									/>
								</router-link>
							</div>
						</template>
					</Column>

					<!-- Empty State -->
					<template #empty>
						<div class="text-center py-12">
							<div class="w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-800 flex items-center justify-center mx-auto mb-4 text-surface-400">
								<i class="pi pi-replay text-2xl"></i>
							</div>
							<h3 class="text-base font-semibold text-surface-900 dark:text-surface-100">
								No returns found
							</h3>
							<p class="text-sm text-surface-500 dark:text-surface-400 mt-1 max-w-sm mx-auto">
								{{ hasActiveFilters ? 'Try adjusting your search criteria or date filters.' : 'No return orders have been processed yet.' }}
							</p>
							<div class="mt-4 flex justify-center gap-2">
								<Button
									v-if="hasActiveFilters"
									label="Clear Filters"
									icon="pi pi-filter-slash"
									severity="secondary"
									outlined
									size="small"
									@click="clearFilters"
								/>
								<router-link :to="{ name: 'returns-create' }">
									<Button label="Create New Return" icon="pi pi-plus" size="small" />
								</router-link>
							</div>
						</div>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>