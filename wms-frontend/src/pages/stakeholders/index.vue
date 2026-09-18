<script setup lang="ts">
import { onMounted, ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import AddStakeHolderModal from "@/components/stakeholders/AddStakeHolderModal.vue";
import {
	formatCurrency,
	formatNumber,
	getStakeholderStatusSeverity,
	getStakeholderStatusLabel,
	getStakeholderTypeSeverity,
	type StakeholderRecord
} from "@/utils/stakeholderCalculations";

const router = useRouter();
const toast = useToast();
const confirm = useConfirm();

// State
const stakeholders = ref<StakeholderRecord[]>([]);
const loading = ref(false);
const statsLoading = ref(false);
const searchInput = ref("");
const selectedType = ref<string | null>(null);
const selectedStatus = ref<string | null>(null);
const selectedCity = ref("");

// Master KPI Stats
const stats = ref({
	total_stakeholders: 0,
	active_customers: 0,
	active_suppliers: 0,
	inactive_records: 0,
	new_this_month: 0,
	total_receivable: 0,
	total_payable: 0,
});

const typeOptions = [
	{ label: "All Types", value: null },
	{ label: "Customers", value: "Customer" },
	{ label: "Suppliers", value: "Supplier" },
];

const statusOptions = [
	{ label: "All Statuses", value: null },
	{ label: "Active Only", value: "false" },
	{ label: "Inactive Only", value: "true" },
];

// Fetch KPI statistics
const fetchStats = async () => {
	try {
		statsLoading.value = true;
		const response = await axios.get("/api/accounts/stakeholders/stats/");
		stats.value = response.data;
	} catch (error) {
		console.error("Error fetching stakeholder stats:", error);
	} finally {
		statsLoading.value = false;
	}
};

// Fetch stakeholders list
const fetchStakeholders = async () => {
	try {
		loading.value = true;
		const params: Record<string, any> = {};
		if (searchInput.value.trim()) params.search = searchInput.value.trim();
		if (selectedType.value) params.type = selectedType.value;
		if (selectedStatus.value != null) params.is_deleted = selectedStatus.value;
		if (selectedCity.value.trim()) params.city = selectedCity.value.trim();

		const response = await axios.get("/api/accounts/stakeholders/", { params });
		stakeholders.value = response.data;
	} catch (error) {
		console.error("Error fetching stakeholders:", error);
		toast.add({
			severity: "error",
			summary: "Fetch Failed",
			detail: "Could not load stakeholder records.",
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
		fetchStakeholders();
	}, 350);
});

watch([selectedType, selectedStatus], () => {
	fetchStakeholders();
});

const reloadTable = () => {
	fetchStakeholders();
	fetchStats();
};

const navigateToCreate = () => {
	router.push("/stakeholders/create");
};

const navigateToDetail = (id: number) => {
	router.push(`/stakeholders/${id}`);
};

// Toggle active/inactive status
const toggleStatus = async (stakeholder: StakeholderRecord) => {
	const actionText = stakeholder.is_deleted ? "activate" : "deactivate";
	confirm.require({
		message: `Are you sure you want to ${actionText} stakeholder "${stakeholder.name}"?`,
		header: `Confirm ${actionText.toUpperCase()}`,
		icon: "pi pi-exclamation-triangle",
		acceptClass: stakeholder.is_deleted ? "p-button-success" : "p-button-warn",
		accept: async () => {
			try {
				const response = await axios.post(`/api/accounts/stakeholders/${stakeholder.id}/toggle_status/`);
				toast.add({
					severity: "success",
					summary: "Status Updated",
					detail: response.data.message || `Stakeholder ${actionText}d successfully.`,
					life: 3000,
				});
				reloadTable();
			} catch (error: any) {
				toast.add({
					severity: "error",
					summary: "Update Failed",
					detail: error.response?.data?.error || "Could not change status.",
					life: 4000,
				});
			}
		},
	});
};

// Delete stakeholder with referential integrity error handling
const deleteStakeholder = async (stakeholder: StakeholderRecord) => {
	confirm.require({
		message: `Are you sure you want to delete "${stakeholder.name}"? This action cannot be undone if no transactions are linked.`,
		header: "Delete Stakeholder",
		icon: "pi pi-trash",
		acceptClass: "p-button-danger",
		accept: async () => {
			try {
				await axios.delete(`/api/accounts/stakeholders/${stakeholder.id}/`);
				toast.add({
					severity: "success",
					summary: "Deleted",
					detail: `Stakeholder "${stakeholder.name}" deleted successfully.`,
					life: 3000,
				});
				reloadTable();
			} catch (error: any) {
				const errorMsg = error.response?.data?.error || error.response?.data?.suggestion || "Failed to delete stakeholder.";
				toast.add({
					severity: "error",
					summary: "Deletion Blocked",
					detail: errorMsg,
					life: 6000,
				});
			}
		},
	});
};

// Export to CSV
const exportCSV = () => {
	if (!stakeholders.value.length) return;
	const headers = ["ID", "Code", "Name", "Company", "Type", "Phone", "Email", "City", "Pending Balance", "Status"];
	const rows = stakeholders.value.map((s) => [
		s.id,
		s.stakeholder_id || "",
		`"${s.name.replace(/"/g, '""')}"`,
		`"${(s.company_name || "").replace(/"/g, '""')}"`,
		s.type,
		s.mobile || "",
		s.email || "",
		`"${(s.city || "").replace(/"/g, '""')}"`,
		s.total_pending_amount || 0,
		s.is_deleted ? "INACTIVE" : "ACTIVE",
	]);
	const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
	const encodedUri = encodeURI(csvContent);
	const link = document.createElement("a");
	link.setAttribute("href", encodedUri);
	link.setAttribute("download", `wms_stakeholders_${new Date().toISOString().slice(0, 10)}.csv`);
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
};

// Export to JSON
const exportJSON = () => {
	if (!stakeholders.value.length) return;
	const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(stakeholders.value, null, 2));
	const link = document.createElement("a");
	link.setAttribute("href", dataStr);
	link.setAttribute("download", `wms_stakeholders_${new Date().toISOString().slice(0, 10)}.json`);
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
};

onMounted(() => {
	fetchStats();
	fetchStakeholders();
});
</script>

<template>
	<div class="space-y-6">
		<!-- Page Header & Action Bar -->
		<div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
			<div>
				<div class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 mb-1">
					<i class="pi pi-users text-xs"></i>
					<span>Master Data Management</span>
					<span>/</span>
					<span class="text-slate-900 dark:text-slate-200 font-medium">Stakeholders</span>
				</div>
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
					Customer & Supplier Directory
				</h1>
				<p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
					Manage business partners, contact profiles, credit limits, and financial ledgers.
				</p>
			</div>

			<div class="flex items-center gap-2.5">
				<Button
					icon="pi pi-download"
					label="Export"
					severity="secondary"
					outlined
					@click="exportCSV"
					class="p-button-sm"
				/>
				<AddStakeHolderModal @instance-added="reloadTable" />
				<Button
					icon="pi pi-plus"
					label="Create Master Record"
					severity="primary"
					@click="navigateToCreate"
					class="p-button-sm shadow-sm"
				/>
			</div>
		</div>

		<!-- KPI Metric Cards Banner -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
			<!-- Total Stakeholders -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center justify-between">
				<div>
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Records</p>
					<h3 class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
						{{ formatNumber(stats.total_stakeholders) }}
					</h3>
					<span class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 block">Registered entities</span>
				</div>
				<div class="w-11 h-11 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center">
					<i class="pi pi-building text-lg"></i>
				</div>
			</div>

			<!-- Active Customers -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center justify-between">
				<div>
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Customers</p>
					<h3 class="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
						{{ formatNumber(stats.active_customers) }}
					</h3>
					<span class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 block">Outbound buyers</span>
				</div>
				<div class="w-11 h-11 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
					<i class="pi pi-user-plus text-lg"></i>
				</div>
			</div>

			<!-- Active Suppliers -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center justify-between">
				<div>
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Suppliers</p>
					<h3 class="text-2xl font-extrabold text-amber-600 dark:text-amber-400 mt-1">
						{{ formatNumber(stats.active_suppliers) }}
					</h3>
					<span class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 block">Inbound vendors</span>
				</div>
				<div class="w-11 h-11 rounded-lg bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 flex items-center justify-center">
					<i class="pi pi-truck text-lg"></i>
				</div>
			</div>

			<!-- Inactive Records -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center justify-between">
				<div>
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Inactive Records</p>
					<h3 class="text-2xl font-extrabold text-slate-600 dark:text-slate-400 mt-1">
						{{ formatNumber(stats.inactive_records) }}
					</h3>
					<span class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 block">Soft-deactivated</span>
				</div>
				<div class="w-11 h-11 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center">
					<i class="pi pi-ban text-lg"></i>
				</div>
			</div>

			<!-- Ledger Exposure -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center justify-between">
				<div>
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Receivables</p>
					<h3 class="text-xl font-extrabold text-indigo-600 dark:text-indigo-400 mt-1">
						{{ formatCurrency(stats.total_receivable) }}
					</h3>
					<span class="text-xs text-amber-600 dark:text-amber-400 mt-0.5 block">
						Payables: {{ formatCurrency(stats.total_payable) }}
					</span>
				</div>
				<div class="w-11 h-11 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
					<i class="pi pi-wallet text-lg"></i>
				</div>
			</div>
		</div>

		<!-- Master Table Card with Filter Toolbar -->
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
							:class="selectedType === null ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'"
						>
							All Types
						</button>
						<button
							type="button"
							@click="selectedType = 'Customer'"
							class="px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5"
							:class="selectedType === 'Customer' ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'"
						>
							<i class="pi pi-user text-xs"></i>
							Customers
						</button>
						<button
							type="button"
							@click="selectedType = 'Supplier'"
							class="px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5"
							:class="selectedType === 'Supplier' ? 'bg-white dark:bg-slate-700 text-amber-600 dark:text-amber-400 shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'"
						>
							<i class="pi pi-truck text-xs"></i>
							Suppliers
						</button>
					</div>

					<!-- Dropdown & Search Filters -->
					<div class="flex flex-wrap items-center gap-3">
						<!-- Status Filter -->
						<Select
							v-model="selectedStatus"
							:options="statusOptions"
							optionLabel="label"
							optionValue="value"
							placeholder="Status"
							class="w-40 p-inputtext-sm"
							showClear
						/>

						<!-- Keyword Search -->
						<IconField iconPosition="left" class="w-full sm:w-64">
							<InputIcon class="pi pi-search text-slate-400" />
							<InputText
								v-model="searchInput"
								placeholder="Search name, code, phone..."
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
							@click="reloadTable"
							title="Refresh records"
						/>
					</div>
				</div>

				<!-- DataTable -->
				<DataTable
					:value="stakeholders"
					:loading="loading"
					paginator
					:rows="10"
					:rowsPerPageOptions="[10, 20, 50]"
					tableStyle="min-width: 65rem"
					responsiveLayout="scroll"
					dataKey="id"
					class="p-datatable-sm"
				>
					<!-- Code / ID Column -->
					<Column field="stakeholder_id" header="Code / ID" sortable style="width: 130px">
						<template #body="slotProps">
							<span class="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
								{{ slotProps.data.stakeholder_id || `STK-${slotProps.data.id}` }}
							</span>
						</template>
					</Column>

					<!-- Name & Company Column -->
					<Column field="name" header="Stakeholder / Company" sortable>
						<template #body="slotProps">
							<div class="flex items-center gap-2.5">
								<div class="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300">
									{{ (slotProps.data.name || 'S').slice(0, 2).toUpperCase() }}
								</div>
								<div>
									<router-link
										:to="`/stakeholders/${slotProps.data.id}`"
										class="font-semibold text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
									>
										{{ slotProps.data.name }}
									</router-link>
									<p v-if="slotProps.data.company_name" class="text-xs text-slate-500 dark:text-slate-400">
										{{ slotProps.data.company_name }}
									</p>
								</div>
							</div>
						</template>
					</Column>

					<!-- Type Column -->
					<Column field="type" header="Type" sortable style="width: 120px">
						<template #body="slotProps">
							<Tag
								:value="slotProps.data.type"
								:severity="getStakeholderTypeSeverity(slotProps.data.type)"
								class="text-xs font-medium"
							/>
						</template>
					</Column>

					<!-- Contact Details Column -->
					<Column header="Contact">
						<template #body="slotProps">
							<div class="space-y-0.5 text-xs text-slate-600 dark:text-slate-300">
								<div v-if="slotProps.data.mobile" class="flex items-center gap-1.5">
									<i class="pi pi-phone text-[10px] text-slate-400"></i>
									<span>{{ slotProps.data.mobile }}</span>
								</div>
								<div v-if="slotProps.data.email" class="flex items-center gap-1.5 text-slate-500">
									<i class="pi pi-envelope text-[10px] text-slate-400"></i>
									<span class="truncate max-w-[160px]">{{ slotProps.data.email }}</span>
								</div>
								<span v-if="!slotProps.data.mobile && !slotProps.data.email" class="text-slate-400 italic">No contact</span>
							</div>
						</template>
					</Column>

					<!-- City / Location Column -->
					<Column field="city" header="City / Location" sortable style="width: 140px">
						<template #body="slotProps">
							<span class="text-xs text-slate-700 dark:text-slate-300">
								{{ slotProps.data.city || (slotProps.data.address ? slotProps.data.address.split(',')[0] : '—') }}
							</span>
						</template>
					</Column>

					<!-- Outstanding Balance Column -->
					<Column field="total_pending_amount" header="Pending Balance" sortable style="width: 150px">
						<template #body="slotProps">
							<div class="text-right">
								<span
									class="text-sm font-bold block"
									:class="(slotProps.data.total_pending_amount || 0) > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-700 dark:text-slate-300'"
								>
									{{ formatCurrency(slotProps.data.total_pending_amount) }}
								</span>
								<span v-if="slotProps.data.credit_limit > 0" class="text-[10px] text-slate-400 block">
									Limit: {{ formatCurrency(slotProps.data.credit_limit) }}
								</span>
							</div>
						</template>
					</Column>

					<!-- Status Column -->
					<Column field="is_deleted" header="Status" sortable style="width: 110px">
						<template #body="slotProps">
							<Tag
								:value="getStakeholderStatusLabel(slotProps.data.is_deleted, slotProps.data.is_active)"
								:severity="getStakeholderStatusSeverity(slotProps.data.is_deleted, slotProps.data.is_active)"
								class="text-xs font-semibold"
							/>
						</template>
					</Column>

					<!-- Actions Column -->
					<Column header="Actions" style="width: 140px">
						<template #body="slotProps">
							<div class="flex items-center gap-1 justify-end">
								<!-- View / Edit -->
								<Button
									icon="pi pi-arrow-up-right"
									severity="secondary"
									text
									rounded
									size="small"
									@click="navigateToDetail(slotProps.data.id)"
									title="View Master Profile"
								/>

								<!-- Deactivate / Activate Toggle -->
								<Button
									:icon="slotProps.data.is_deleted ? 'pi pi-check' : 'pi pi-ban'"
									:severity="slotProps.data.is_deleted ? 'success' : 'warn'"
									text
									rounded
									size="small"
									@click="toggleStatus(slotProps.data)"
									:title="slotProps.data.is_deleted ? 'Reactivate Stakeholder' : 'Deactivate Stakeholder'"
								/>

								<!-- Delete Guarded -->
								<Button
									icon="pi pi-trash"
									severity="danger"
									text
									rounded
									size="small"
									@click="deleteStakeholder(slotProps.data)"
									title="Delete Stakeholder"
								/>
							</div>
						</template>
					</Column>

					<!-- Empty State -->
					<template #empty>
						<div class="py-12 text-center">
							<div class="w-14 h-14 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
								<i class="pi pi-users text-2xl"></i>
							</div>
							<h4 class="text-base font-semibold text-slate-800 dark:text-slate-200">No stakeholders found</h4>
							<p class="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
								Try adjusting your filters or search query, or register a new customer or supplier.
							</p>
							<Button
								label="Create Stakeholder"
								icon="pi pi-plus"
								severity="primary"
								size="small"
								class="mt-4"
								@click="navigateToCreate"
							/>
						</div>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style scoped></style>

