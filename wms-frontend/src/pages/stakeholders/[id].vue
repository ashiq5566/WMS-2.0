<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import moment from "moment";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import {
	formatCurrency,
	formatNumber,
	getStakeholderStatusSeverity,
	getStakeholderStatusLabel,
	getStakeholderTypeSeverity,
	calculateCreditUtilization,
	calculateSettlementProgress,
	validateStakeholder,
	type StakeholderRecord,
} from "@/utils/stakeholderCalculations";
import { setPageTitle } from "@/utils/meta";

const route = useRoute();
const router = useRouter();
const toast = useToast();
const confirm = useConfirm();

const stakeholderId = route.params.id as string;

// Master state
const stakeholder = ref<StakeholderRecord>({} as StakeholderRecord);
const loading = ref(true);
const updating = ref(false);
const activeTab = ref(0);
const formErrors = ref<Record<string, string>>({});

// Related records
const orders = ref<any[]>([]);
const returns = ref<any[]>([]);
const transactions = ref<any[]>([]);
const ordersLoading = ref(false);
const returnsLoading = ref(false);
const transactionsLoading = ref(false);

const paymentTermOptions = [
	{ label: "Due on Receipt", value: "Immediate" },
	{ label: "Net 15 Days", value: "Net 15" },
	{ label: "Net 30 Days", value: "Net 30" },
	{ label: "Net 45 Days", value: "Net 45" },
	{ label: "Net 60 Days", value: "Net 60" },
];

// Fetch master record
const fetchStakeholder = async () => {
	try {
		loading.value = true;
		const response = await axios.get(`/api/accounts/stakeholders/${stakeholderId}/`);
		stakeholder.value = response.data;
		const partnerName = stakeholder.value.name || 'Stakeholder';
		const partnerCode = stakeholder.value.code ? ` (${stakeholder.value.code})` : '';
		setPageTitle(`${partnerName}${partnerCode}`, `Master profile, orders, returns, and financial ledger for ${partnerName}`);
	} catch (error) {
		console.error("Error fetching stakeholder profile:", error);
		toast.add({
			severity: "error",
			summary: "Load Failed",
			detail: "Could not fetch stakeholder profile.",
			life: 4000,
		});
	} finally {
		loading.value = false;
	}
};

// Fetch linked orders
const fetchOrders = async () => {
	try {
		ordersLoading.value = true;
		const response = await axios.get("/api/inventory/orders/", {
			params: { stakeholder_id: stakeholderId },
		});
		orders.value = Array.isArray(response.data) ? response.data : [];
	} catch (error) {
		console.error("Error fetching orders:", error);
	} finally {
		ordersLoading.value = false;
	}
};

// Fetch linked returns
const fetchReturns = async () => {
	try {
		returnsLoading.value = true;
		const response = await axios.get("/api/inventory/returns/", {
			params: { search: stakeholder.value.name || "" },
		});
		const list = Array.isArray(response.data) ? response.data : [];
		returns.value = list.filter(
			(r: any) =>
				r.original_order?.stakeholder === Number(stakeholderId) ||
				r.original_order?.stakeholder_obj?.id === Number(stakeholderId) ||
				r.original_order?.stakeholder_obj?.name === stakeholder.value.name
		);
	} catch (error) {
		console.error("Error fetching returns:", error);
	} finally {
		returnsLoading.value = false;
	}
};

// Fetch linked payments / ledger transactions
const fetchTransactions = async () => {
	try {
		transactionsLoading.value = true;
		const response = await axios.get("/api/inventory/payments/", {
			params: { company__id: stakeholderId },
		});
		transactions.value = Array.isArray(response.data) ? response.data : [];
	} catch (error) {
		console.error("Error fetching transactions:", error);
	} finally {
		transactionsLoading.value = false;
	}
};

// Computed Financial Metrics
const totalInvoiced = computed(() => {
	return orders.value.reduce((sum, o) => sum + (Number(o.total_amount) || 0), 0);
});

const progressPercentage = computed(() => {
	return calculateSettlementProgress(
		stakeholder.value.total_setteled_amount || 0,
		stakeholder.value.total_pending_amount || 0
	);
});

const creditStats = computed(() => {
	return calculateCreditUtilization(
		stakeholder.value.total_pending_amount || 0,
		stakeholder.value.credit_limit || 0
	);
});

// Update Profile
const onUpdate = async () => {
	formErrors.value = validateStakeholder(stakeholder.value);
	if (Object.keys(formErrors.value).length > 0) {
		toast.add({
			severity: "warn",
			summary: "Validation Error",
			detail: "Please correct highlighted fields before updating.",
			life: 4000,
		});
		return;
	}

	try {
		updating.value = true;
		const response = await axios.put(`/api/accounts/stakeholders/${stakeholderId}/`, stakeholder.value);
		stakeholder.value = response.data;
		toast.add({
			severity: "success",
			summary: "Master Profile Updated",
			detail: `Stakeholder "${stakeholder.value.name}" updated successfully.`,
			life: 3000,
		});
	} catch (error: any) {
		console.error("Update failed:", error);
		const errData = error.response?.data;
		if (errData && typeof errData === "object") {
			const serverErrors: Record<string, string> = {};
			for (const [k, v] of Object.entries(errData)) {
				serverErrors[k] = Array.isArray(v) ? v.join(" ") : String(v);
			}
			formErrors.value = serverErrors;
		}
		toast.add({
			severity: "error",
			summary: "Update Failed",
			detail: error.response?.data?.error || "Unable to save profile changes.",
			life: 4000,
		});
	} finally {
		updating.value = false;
	}
};

// Toggle Deactivation / Activation
const toggleStatus = async () => {
	const actionText = stakeholder.value.is_deleted ? "activate" : "deactivate";
	confirm.require({
		message: `Are you sure you want to ${actionText} stakeholder "${stakeholder.value.name}"?`,
		header: `Confirm ${actionText.toUpperCase()}`,
		icon: "pi pi-exclamation-triangle",
		acceptClass: stakeholder.value.is_deleted ? "p-button-success" : "p-button-warn",
		accept: async () => {
			try {
				const response = await axios.post(`/api/accounts/stakeholders/${stakeholderId}/toggle_status/`);
				toast.add({
					severity: "success",
					summary: "Status Updated",
					detail: response.data.message || `Stakeholder ${actionText}d successfully.`,
					life: 3000,
				});
				await fetchStakeholder();
			} catch (error: any) {
				toast.add({
					severity: "error",
					summary: "Failed",
					detail: error.response?.data?.error || "Could not change status.",
					life: 4000,
				});
			}
		},
	});
};

// Delete stakeholder with referential check
const deleteStakeholder = () => {
	confirm.require({
		message: `Are you sure you want to permanently delete "${stakeholder.value.name}"? If active orders, returns, or payments exist, deletion will be safely rejected.`,
		header: "Delete Stakeholder Master",
		icon: "pi pi-trash",
		acceptClass: "p-button-danger",
		accept: async () => {
			try {
				await axios.delete(`/api/accounts/stakeholders/${stakeholderId}/`);
				toast.add({
					severity: "success",
					summary: "Deleted",
					detail: "Stakeholder master record removed.",
					life: 3000,
				});
				router.push("/stakeholders");
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

const goBack = () => {
	router.push("/stakeholders");
};

const createOrderForStakeholder = () => {
	router.push({
		path: "/orders/create",
		query: { stakeholder_id: stakeholderId, type: stakeholder.value.type === "Supplier" ? "PO" : "SO" },
	});
};

onMounted(async () => {
	await fetchStakeholder();
	await Promise.all([fetchOrders(), fetchReturns(), fetchTransactions()]);
});
</script>

<template>
	<div class="space-y-6 pb-12">
		<!-- Navigation & Action Header -->
		<div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
			<div>
				<div class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 mb-1">
					<button @click="goBack" class="hover:text-slate-900 dark:hover:text-white flex items-center gap-1 transition-colors">
						<i class="pi pi-arrow-left text-xs"></i>
						<span>Stakeholders</span>
					</button>
					<span>/</span>
					<span class="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-700 dark:text-slate-300">
						{{ stakeholder.stakeholder_id || `STK-${stakeholder.id}` }}
					</span>
				</div>
				<div class="flex flex-wrap items-center gap-3 mt-1">
					<h1 class="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
						{{ stakeholder.name || 'Loading Stakeholder...' }}
					</h1>
					<Tag
						v-if="stakeholder.type"
						:value="stakeholder.type"
						:severity="getStakeholderTypeSeverity(stakeholder.type)"
						class="text-xs font-semibold"
					/>
					<Tag
						v-if="stakeholder.is_deleted !== undefined"
						:value="getStakeholderStatusLabel(stakeholder.is_deleted, stakeholder.is_active)"
						:severity="getStakeholderStatusSeverity(stakeholder.is_deleted, stakeholder.is_active)"
						class="text-xs font-semibold"
					/>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="flex flex-wrap items-center gap-2.5">
				<Button
					icon="pi pi-shopping-cart"
					:label="stakeholder.type === 'Supplier' ? 'New Purchase Order' : 'New Sales Order'"
					severity="secondary"
					outlined
					size="small"
					@click="createOrderForStakeholder"
				/>
				<Button
					:icon="stakeholder.is_deleted ? 'pi pi-check' : 'pi pi-ban'"
					:label="stakeholder.is_deleted ? 'Reactivate' : 'Deactivate'"
					:severity="stakeholder.is_deleted ? 'success' : 'warn'"
					size="small"
					@click="toggleStatus"
				/>
				<Button
					icon="pi pi-trash"
					severity="danger"
					text
					rounded
					size="small"
					@click="deleteStakeholder"
					title="Delete Stakeholder"
				/>
				<Button
					icon="pi pi-check"
					label="Save Changes"
					severity="primary"
					size="small"
					:loading="updating"
					@click="onUpdate"
					class="shadow-sm"
				/>
			</div>
		</div>

		<!-- Financial & Operational KPI Overview Strip -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- Outstanding Balance -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
				<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Outstanding Balance</p>
				<h3
					class="text-2xl font-extrabold mt-1"
					:class="(stakeholder.total_pending_amount || 0) > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-900 dark:text-white'"
				>
					{{ formatCurrency(stakeholder.total_pending_amount) }}
				</h3>
				<span class="text-xs text-slate-500 dark:text-slate-400 mt-1 block">
					Opening: {{ formatCurrency(stakeholder.opening_balance) }}
				</span>
			</div>

			<!-- Total Settled Amount -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
				<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Settled</p>
				<h3 class="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
					{{ formatCurrency(stakeholder.total_setteled_amount) }}
				</h3>
				<div class="flex items-center gap-2 mt-1.5">
					<div class="flex-1 bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
						<div
							class="bg-emerald-500 h-full rounded-full transition-all duration-500"
							:style="{ width: `${progressPercentage}%` }"
						></div>
					</div>
					<span class="text-[11px] font-bold text-slate-600 dark:text-slate-300">{{ progressPercentage }}%</span>
				</div>
			</div>

			<!-- Lifetime Order Value -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
				<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Lifetime Invoiced</p>
				<h3 class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
					{{ formatCurrency(totalInvoiced) }}
				</h3>
				<span class="text-xs text-slate-500 dark:text-slate-400 mt-1 block">
					Across {{ formatNumber(orders.length) }} orders
				</span>
			</div>

			<!-- Credit Limit Utilization -->
			<div class="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
				<div class="flex items-center justify-between">
					<p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Credit Limit</p>
					<span v-if="creditStats.isExceeded" class="text-[10px] bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300 font-bold px-1.5 py-0.5 rounded">
						EXCEEDED
					</span>
				</div>
				<h3 class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
					{{ (stakeholder.credit_limit || 0) > 0 ? formatCurrency(stakeholder.credit_limit) : 'No Limit' }}
				</h3>
				<div v-if="(stakeholder.credit_limit || 0) > 0" class="mt-1.5">
					<div class="flex items-center justify-between text-[11px] text-slate-500 mb-1">
						<span>Used: {{ creditStats.percentage }}%</span>
						<span>Avail: {{ formatCurrency(creditStats.remaining) }}</span>
					</div>
					<div class="bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
						<div
							class="h-full rounded-full transition-all duration-500"
							:class="creditStats.severity === 'danger' ? 'bg-rose-500' : creditStats.severity === 'warn' ? 'bg-amber-500' : 'bg-blue-500'"
							:style="{ width: `${creditStats.percentage}%` }"
						></div>
					</div>
				</div>
				<span v-else class="text-xs text-slate-400 mt-1 block">Unlimited credit line</span>
			</div>
		</div>

		<!-- Tabbed Workspace -->
		<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl overflow-hidden">
			<template #content>
				<!-- Custom Navigation Tab Strip -->
				<div class="flex flex-wrap items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3 mb-6">
					<button
						type="button"
						@click="activeTab = 0"
						class="px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2"
						:class="activeTab === 0 ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
					>
						<i class="pi pi-id-card text-xs"></i>
						Master Profile
					</button>

					<button
						type="button"
						@click="activeTab = 1"
						class="px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2"
						:class="activeTab === 1 ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
					>
						<i class="pi pi-shopping-bag text-xs"></i>
						<span>Orders</span>
						<span class="text-xs px-1.5 py-0.2 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
							{{ orders.length }}
						</span>
					</button>

					<button
						type="button"
						@click="activeTab = 2"
						class="px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2"
						:class="activeTab === 2 ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
					>
						<i class="pi pi-replay text-xs"></i>
						<span>RMA Returns</span>
						<span class="text-xs px-1.5 py-0.2 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
							{{ returns.length }}
						</span>
					</button>

					<button
						type="button"
						@click="activeTab = 3"
						class="px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2"
						:class="activeTab === 3 ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
					>
						<i class="pi pi-wallet text-xs"></i>
						<span>Financial Ledger</span>
						<span class="text-xs px-1.5 py-0.2 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
							{{ transactions.length }}
						</span>
					</button>

					<button
						type="button"
						@click="activeTab = 4"
						class="px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2"
						:class="activeTab === 4 ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
					>
						<i class="pi pi-history text-xs"></i>
						<span>Audit & Log</span>
					</button>
				</div>

				<!-- TAB 0: Master Profile (View / Edit Form) -->
				<div v-show="activeTab === 0" class="space-y-6">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<!-- Basic Details Box -->
						<div class="space-y-4 p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
							<h4 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
								<i class="pi pi-user text-blue-500"></i>
								Basic Information
							</h4>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Stakeholder Name <span class="text-rose-500">*</span>
								</label>
								<InputText v-model="stakeholder.name" class="w-full" :class="{ 'p-invalid': formErrors.name }" />
								<small v-if="formErrors.name" class="text-rose-500 text-xs mt-1 block">{{ formErrors.name }}</small>
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Company / Legal Trade Name
								</label>
								<InputText v-model="stakeholder.company_name" class="w-full" />
							</div>

							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										Classification Type
									</label>
									<InputText :value="stakeholder.type" disabled class="w-full bg-slate-100 dark:bg-slate-800" />
								</div>
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										Master Code / ID
									</label>
									<InputText v-model="stakeholder.stakeholder_id" class="w-full font-mono text-sm" />
								</div>
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Primary Contact Person
								</label>
								<InputText v-model="stakeholder.contact_person" class="w-full" />
							</div>
						</div>

						<!-- Contact Details Box -->
						<div class="space-y-4 p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
							<h4 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
								<i class="pi pi-phone text-emerald-500"></i>
								Communication Channels
							</h4>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Mobile / Phone
								</label>
								<IconField iconPosition="left">
									<InputIcon class="pi pi-phone text-slate-400" />
									<InputText v-model="stakeholder.mobile" class="w-full" :class="{ 'p-invalid': formErrors.mobile }" />
								</IconField>
								<small v-if="formErrors.mobile" class="text-rose-500 text-xs mt-1 block">{{ formErrors.mobile }}</small>
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Alternate Phone
								</label>
								<IconField iconPosition="left">
									<InputIcon class="pi pi-phone text-slate-400" />
									<InputText v-model="stakeholder.alternate_phone" class="w-full" />
								</IconField>
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Email Address
								</label>
								<IconField iconPosition="left">
									<InputIcon class="pi pi-envelope text-slate-400" />
									<InputText v-model="stakeholder.email" type="email" class="w-full" :class="{ 'p-invalid': formErrors.email }" />
								</IconField>
								<small v-if="formErrors.email" class="text-rose-500 text-xs mt-1 block">{{ formErrors.email }}</small>
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Website URL
								</label>
								<IconField iconPosition="left">
									<InputIcon class="pi pi-globe text-slate-400" />
									<InputText v-model="stakeholder.website" class="w-full" />
								</IconField>
							</div>
						</div>

						<!-- Address Information Box -->
						<div class="space-y-4 p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
							<h4 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
								<i class="pi pi-map-marker text-rose-500"></i>
								Addresses & Logistics
							</h4>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Billing Address
								</label>
								<Textarea v-model="stakeholder.address" rows="2" class="w-full" autoResize />
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Shipping / Warehouse Address
								</label>
								<Textarea v-model="stakeholder.shipping_address" rows="2" class="w-full" autoResize />
							</div>

							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										City
									</label>
									<InputText v-model="stakeholder.city" class="w-full" />
								</div>
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										State
									</label>
									<InputText v-model="stakeholder.state" class="w-full" />
								</div>
							</div>

							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										Country
									</label>
									<InputText v-model="stakeholder.country" class="w-full" />
								</div>
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										Postal Code
									</label>
									<InputText v-model="stakeholder.postal_code" class="w-full" />
								</div>
							</div>
						</div>

						<!-- Tax & Terms Box -->
						<div class="space-y-4 p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
							<h4 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
								<i class="pi pi-credit-card text-indigo-500"></i>
								Tax & Financial Configuration
							</h4>

							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										GSTIN / Tax ID
									</label>
									<InputText v-model="stakeholder.tax_id" class="w-full font-mono uppercase text-sm" />
								</div>
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										PAN Number
									</label>
									<InputText v-model="stakeholder.pan_number" class="w-full font-mono uppercase text-sm" />
								</div>
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Payment Terms
								</label>
								<Select
									v-model="stakeholder.payment_terms"
									:options="paymentTermOptions"
									optionLabel="label"
									optionValue="value"
									class="w-full"
								/>
							</div>

							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										Credit Limit (INR)
									</label>
									<InputNumber
										v-model="stakeholder.credit_limit"
										mode="currency"
										currency="INR"
										locale="en-IN"
										class="w-full"
									/>
								</div>
								<div>
									<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
										Opening Debt (INR)
									</label>
									<InputNumber
										v-model="stakeholder.opening_balance"
										mode="currency"
										currency="INR"
										locale="en-IN"
										class="w-full"
									/>
								</div>
							</div>

							<div>
								<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
									Internal Notes
								</label>
								<Textarea v-model="stakeholder.notes" rows="2" class="w-full" autoResize />
							</div>
						</div>
					</div>

					<div class="flex justify-end pt-2">
						<Button
							label="Save Changes"
							icon="pi pi-check"
							severity="primary"
							:loading="updating"
							@click="onUpdate"
							class="shadow-sm"
						/>
					</div>
				</div>

				<!-- TAB 1: Orders View -->
				<div v-show="activeTab === 1">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-base font-bold text-slate-900 dark:text-white">
							Linked {{ stakeholder.type === 'Supplier' ? 'Purchase Orders' : 'Sales Orders' }}
						</h3>
						<Button
							icon="pi pi-plus"
							label="Create Order"
							size="small"
							@click="createOrderForStakeholder"
						/>
					</div>

					<DataTable
						:value="orders"
						:loading="ordersLoading"
						paginator
						:rows="10"
						tableStyle="min-width: 50rem"
						class="p-datatable-sm"
					>
						<Column field="id" header="Order ID" sortable style="width: 110px">
							<template #body="slotProps">
								<router-link
									:to="`/orders/${slotProps.data.id}`"
									class="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline"
								>
									#{{ slotProps.data.id }}
								</router-link>
							</template>
						</Column>
						<Column field="order_number" header="Order Reference" sortable></Column>
						<Column field="date" header="Date" sortable>
							<template #body="slotProps">
								<span class="text-xs text-slate-600 dark:text-slate-300">
									{{ slotProps.data.date ? moment(slotProps.data.date).format('DD MMM YYYY') : '—' }}
								</span>
							</template>
						</Column>
						<Column field="order_status" header="Status" sortable style="width: 120px">
							<template #body="slotProps">
								<Tag :value="slotProps.data.order_status" class="text-xs font-semibold" />
							</template>
						</Column>
						<Column field="total_amount" header="Total" sortable style="width: 140px">
							<template #body="slotProps">
								<span class="font-semibold text-slate-900 dark:text-white">
									{{ formatCurrency(slotProps.data.total_amount) }}
								</span>
							</template>
						</Column>
						<Column field="pending_amount" header="Pending" sortable style="width: 140px">
							<template #body="slotProps">
								<span
									class="font-bold"
									:class="slotProps.data.pending_amount > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-600 dark:text-slate-400'"
								>
									{{ formatCurrency(slotProps.data.pending_amount) }}
								</span>
							</template>
						</Column>
						<Column header="Action" style="width: 90px">
							<template #body="slotProps">
								<router-link :to="`/orders/${slotProps.data.id}`">
									<Button icon="pi pi-arrow-up-right" text rounded size="small" />
								</router-link>
							</template>
						</Column>
						<template #empty>
							<div class="py-8 text-center text-slate-500">
								No orders found for this stakeholder.
							</div>
						</template>
					</DataTable>
				</div>

				<!-- TAB 2: Returns View -->
				<div v-show="activeTab === 2">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-base font-bold text-slate-900 dark:text-white">
							RMA Return Authorizations
						</h3>
						<router-link to="/returns/create">
							<Button icon="pi pi-plus" label="Initiate RMA Return" size="small" />
						</router-link>
					</div>

					<DataTable
						:value="returns"
						:loading="returnsLoading"
						paginator
						:rows="10"
						tableStyle="min-width: 50rem"
						class="p-datatable-sm"
					>
						<Column field="id" header="RMA #" sortable style="width: 110px">
							<template #body="slotProps">
								<span class="font-mono text-xs font-bold text-slate-700 dark:text-slate-300">
									RMA-{{ slotProps.data.id }}
								</span>
							</template>
						</Column>
						<Column field="date" header="Return Date" sortable>
							<template #body="slotProps">
								<span class="text-xs text-slate-600 dark:text-slate-300">
									{{ moment(slotProps.data.date).format('DD MMM YYYY') }}
								</span>
							</template>
						</Column>
						<Column field="return_type" header="Type" style="width: 130px">
							<template #body="slotProps">
								<Tag
									:value="slotProps.data.return_type === 'SR' ? 'Sales Return' : 'Purchase Return'"
									:severity="slotProps.data.return_type === 'SR' ? 'info' : 'warn'"
									class="text-xs"
								/>
							</template>
						</Column>
						<Column field="return_status" header="Status" style="width: 120px">
							<template #body="slotProps">
								<Tag :value="slotProps.data.return_status" class="text-xs font-semibold" />
							</template>
						</Column>
						<Column field="total_amount" header="Credit / Refund" sortable style="width: 140px">
							<template #body="slotProps">
								<span class="font-bold text-rose-600 dark:text-rose-400">
									{{ formatCurrency(slotProps.data.total_amount) }}
								</span>
							</template>
						</Column>
						<Column header="Action" style="width: 90px">
							<template #body="slotProps">
								<router-link to="/returns">
									<Button icon="pi pi-arrow-up-right" text rounded size="small" />
								</router-link>
							</template>
						</Column>
						<template #empty>
							<div class="py-8 text-center text-slate-500">
								No RMA returns recorded for this stakeholder.
							</div>
						</template>
					</DataTable>
				</div>

				<!-- TAB 3: Financial Ledger -->
				<div v-show="activeTab === 3">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-base font-bold text-slate-900 dark:text-white">
							Payment Transactions & Settlement Journal
						</h3>
					</div>

					<DataTable
						:value="transactions"
						:loading="transactionsLoading"
						paginator
						:rows="10"
						tableStyle="min-width: 50rem"
						class="p-datatable-sm"
					>
						<Column field="id" header="Txn ID" sortable style="width: 110px">
							<template #body="slotProps">
								<span class="font-mono text-xs font-bold text-slate-700 dark:text-slate-300">
									TXN-{{ slotProps.data.id }}
								</span>
							</template>
						</Column>
						<Column field="payment_date" header="Date" sortable>
							<template #body="slotProps">
								<span class="text-xs text-slate-600 dark:text-slate-300">
									{{ moment(slotProps.data.payment_date).format('DD MMM YYYY') }}
								</span>
							</template>
						</Column>
						<Column field="order" header="Linked Order">
							<template #body="slotProps">
								<span class="text-xs font-mono text-slate-600 dark:text-slate-300">
									{{ slotProps.data.order_obj?.order_number || (slotProps.data.order ? `#${slotProps.data.order}` : 'General Ledger') }}
								</span>
							</template>
						</Column>
						<Column field="payment_method" header="Method" style="width: 140px">
							<template #body="slotProps">
								<Tag :value="slotProps.data.payment_method || 'Cash'" severity="secondary" class="text-xs" />
							</template>
						</Column>
						<Column field="amount" header="Settled Amount" sortable style="width: 150px">
							<template #body="slotProps">
								<span class="font-bold text-emerald-600 dark:text-emerald-400">
									{{ formatCurrency(slotProps.data.amount) }}
								</span>
							</template>
						</Column>
						<template #footer>
							<div class="flex items-center justify-between text-sm py-2">
								<span class="text-slate-500">Total Settled Receipts:</span>
								<span class="font-extrabold text-emerald-600 dark:text-emerald-400 text-lg">
									{{ formatCurrency(stakeholder.total_setteled_amount) }}
								</span>
							</div>
						</template>
						<template #empty>
							<div class="py-8 text-center text-slate-500">
								No payment transactions recorded for this stakeholder.
							</div>
						</template>
					</DataTable>
				</div>

				<!-- TAB 4: Audit & Log -->
				<div v-show="activeTab === 4">
					<h3 class="text-base font-bold text-slate-900 dark:text-white mb-4">
						Record Audit Trail & Metadata
					</h3>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl">
						<div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
							<p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Registered Timestamp</p>
							<p class="text-sm font-semibold text-slate-900 dark:text-white mt-1">
								{{ stakeholder.date_added ? moment(stakeholder.date_added).format('DD MMMM YYYY, hh:mm A') : '—' }}
							</p>
						</div>

						<div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
							<p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Last Updated</p>
							<p class="text-sm font-semibold text-slate-900 dark:text-white mt-1">
								{{ stakeholder.date_updated ? moment(stakeholder.date_updated).format('DD MMMM YYYY, hh:mm A') : '—' }}
							</p>
						</div>

						<div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
							<p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Database Primary Key</p>
							<p class="text-sm font-mono font-semibold text-slate-900 dark:text-white mt-1">
								#{{ stakeholder.id }}
							</p>
						</div>

						<div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
							<p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Deactivation State</p>
							<p class="text-sm font-semibold text-slate-900 dark:text-white mt-1">
								{{ stakeholder.is_deleted ? 'Soft Deleted / Inactive' : 'Active System Record' }}
							</p>
						</div>
					</div>
				</div>
			</template>
		</Card>
	</div>
</template>

<style scoped></style>
