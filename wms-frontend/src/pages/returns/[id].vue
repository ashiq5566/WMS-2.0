<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "@/plugins/axios";
import moment from "moment";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Card from "primevue/card";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Tag from "primevue/tag";
import Skeleton from "primevue/skeleton";
import {
	formatCurrency,
	formatNumber,
	getItemConditionSeverity,
	getReturnTypeLabel,
	getReturnTypeSeverity,
	getReturnStatusSeverity,
	calculateInventoryImpact,
	type ReturnCondition,
} from "@/utils/returnCalculations";
import { setPageTitle } from "@/utils/meta";

const route = useRoute();
const router = useRouter();
const toast = useToast();

interface StakeholderObj {
	id: number;
	name: string;
	type?: string;
	phone?: string;
}

interface ProductObj {
	id: number;
	name: string;
	unit?: string;
}

interface ProductSizeObj {
	id: number;
	size: number;
}

interface ReturnItemRecord {
	id: number;
	product: number;
	product_obj?: ProductObj;
	product_size?: number;
	product_size_obj?: ProductSizeObj;
	quantity: number;
	price_at_return: number;
	total: number;
	condition?: ReturnCondition;
	reason?: string;
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
		total_amount: number;
		pending_amount: number;
		stakeholder_obj?: StakeholderObj;
	};
	date: string;
	date_added?: string;
	total_amount: number;
	reason?: string;
	stock_adjusted?: boolean;
	items?: ReturnItemRecord[];
}

const returnRecord = ref<ReturnRecord | null>(null);
const returnItems = ref<ReturnItemRecord[]>([]);
const isLoading = ref(true);
const isApproving = ref(false);

const fetchReturnDetails = async () => {
	try {
		isLoading.value = true;
		const returnId = route.params.id;

		const [retRes, itemsRes] = await Promise.all([
			axios.get(`/api/inventory/returns/${returnId}/`),
			axios.get("/api/inventory/return-items/", { params: { return_order: returnId } }),
		]);

		returnRecord.value = retRes.data;
		returnItems.value = itemsRes.data?.length ? itemsRes.data : retRes.data?.items || [];
		const rmaNum = `RMA-${String(returnRecord.value?.id || returnId).padStart(4, "0")}`;
		setPageTitle(`Return ${rmaNum}`, `Return authorization ${rmaNum} inspection details`);
	} catch (error) {
		console.error("Error fetching return details:", error);
		toast.add({
			severity: "error",
			summary: "Error",
			detail: "Failed to load return details.",
			life: 3000,
		});
	} finally {
		isLoading.value = false;
	}
};

const approveReturn = async () => {
	if (!returnRecord.value?.id) return;
	try {
		isApproving.value = true;
		const res = await axios.post(`/api/inventory/returns/${returnRecord.value.id}/approve/`);
		toast.add({
			severity: "success",
			summary: "Return Approved",
			detail: `RMA-${String(returnRecord.value.id).padStart(4, "0")} approved and inventory updated.`,
			life: 3500,
		});
		returnRecord.value = res.data;
		await fetchReturnDetails();
	} catch (error: any) {
		console.error("Approval error:", error);
		const msg = error.response?.data?.error || "Failed to approve return.";
		toast.add({ severity: "error", summary: "Approval Failed", detail: msg, life: 4000 });
	} finally {
		isApproving.value = false;
	}
};

const totalUnits = computed(() => {
	return returnItems.value.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0);
});

const calculatedTotalAmount = computed(() => {
	if (returnRecord.value?.total_amount != null) {
		return Number(returnRecord.value.total_amount);
	}
	return returnItems.value.reduce((sum, item) => sum + (Number(item.total) || 0), 0);
});

const inventoryImpact = computed(() => {
	if (!returnRecord.value) return { sellableUnits: 0, quarantinedUnits: 0, deductionUnits: 0, totalUnits: 0 };
	return calculateInventoryImpact(
		returnRecord.value.return_type,
		returnItems.value.map((i) => ({ quantity: i.quantity, condition: i.condition || "Good" }))
	);
});

const printReturn = () => {
	window.print();
};

onMounted(() => {
	fetchReturnDetails();
});
</script>

<template>
	<div class="space-y-6">
		<!-- Loading State -->
		<div v-if="isLoading" class="p-6 space-y-4">
			<Skeleton height="3rem" class="w-full" />
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<Skeleton height="8rem" />
				<Skeleton height="8rem" />
				<Skeleton height="8rem" />
			</div>
			<Skeleton height="15rem" class="w-full" />
		</div>

		<!-- Main Return View -->
		<div v-else-if="returnRecord" class="space-y-6">
			<!-- Header -->
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
				<div class="flex items-center gap-3">
					<router-link to="/returns">
						<Button icon="pi pi-arrow-left" severity="secondary" text rounded size="small" />
					</router-link>
					<div>
						<div class="flex items-center gap-2.5">
							<h1 class="text-2xl font-bold tracking-tight text-surface-900 dark:text-surface-0">
								RMA-{{ String(returnRecord.id).padStart(4, '0') }}
							</h1>
							<Tag
								:severity="getReturnTypeSeverity(returnRecord.return_type)"
								:value="getReturnTypeLabel(returnRecord.return_type)"
								class="text-xs font-semibold px-2.5 py-0.5"
							/>
							<Tag
								:severity="getReturnStatusSeverity(returnRecord.return_status || 'Completed')"
								:value="returnRecord.return_status || 'Completed'"
								class="text-xs font-semibold px-2.5 py-0.5"
							/>
						</div>
						<p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
							Authorized on {{ moment(returnRecord.date_added || returnRecord.date).format("MMMM Do, YYYY") }}
						</p>
					</div>
				</div>

				<div class="flex items-center gap-2">
					<Button
						v-if="returnRecord.return_status === 'Pending Approval' || returnRecord.return_status === 'Draft'"
						label="Approve & Restock"
						icon="pi pi-check"
						severity="success"
						size="small"
						:loading="isApproving"
						@click="approveReturn"
					/>
					<Button
						icon="pi pi-print"
						label="Print RMA"
						severity="secondary"
						outlined
						size="small"
						@click="printReturn"
					/>
					<router-link :to="{ name: 'returns-create' }">
						<Button icon="pi pi-plus" label="New Return" size="small" />
					</router-link>
				</div>
			</div>

			<!-- Metadata Information Cards -->
			<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
				<!-- Original Order Card -->
				<Card class="border border-surface-200 dark:border-surface-800 shadow-sm">
					<template #content>
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold uppercase tracking-wider text-surface-500 dark:text-surface-400">
								Reference Order
							</span>
							<div class="w-7 h-7 rounded bg-primary-50 dark:bg-primary-950/50 flex items-center justify-center text-primary-600 dark:text-primary-400">
								<i class="pi pi-file text-xs"></i>
							</div>
						</div>
						<div class="space-y-1">
							<router-link
								v-if="returnRecord.order_obj?.id"
								:to="{ name: 'orders-id', params: { id: returnRecord.order_obj.id } }"
								class="text-base font-bold text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1.5"
							>
								<span>{{ returnRecord.order_obj.order_number }}</span>
								<i class="pi pi-external-link text-xs"></i>
							</router-link>
							<div class="flex items-center justify-between text-xs text-surface-500 dark:text-surface-400 pt-0.5">
								<span>Status:</span>
								<span class="font-medium text-surface-800 dark:text-surface-200">
									{{ returnRecord.order_obj?.order_status || "N/A" }}
								</span>
							</div>
						</div>
					</template>
				</Card>

				<!-- Stakeholder / Party Card -->
				<Card class="border border-surface-200 dark:border-surface-800 shadow-sm">
					<template #content>
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold uppercase tracking-wider text-surface-500 dark:text-surface-400">
								Party / Stakeholder
							</span>
							<div class="w-7 h-7 rounded bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400">
								<i class="pi pi-user text-xs"></i>
							</div>
						</div>
						<div class="space-y-1">
							<div class="text-base font-bold text-surface-900 dark:text-surface-0 truncate">
								{{ returnRecord.order_obj?.stakeholder_obj?.name || "Unknown Party" }}
							</div>
							<div class="flex items-center justify-between text-xs text-surface-500 dark:text-surface-400 pt-0.5">
								<span>Role:</span>
								<span class="font-medium text-surface-800 dark:text-surface-200">
									{{ returnRecord.return_type === "SR" ? "Customer" : "Supplier" }}
								</span>
							</div>
						</div>
					</template>
				</Card>

				<!-- Receiving Warehouse Card -->
				<Card class="border border-surface-200 dark:border-surface-800 shadow-sm">
					<template #content>
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold uppercase tracking-wider text-surface-500 dark:text-surface-400">
								Warehouse Facility
							</span>
							<div class="w-7 h-7 rounded bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
								<i class="pi pi-building text-xs"></i>
							</div>
						</div>
						<div class="space-y-1">
							<div class="text-base font-bold text-surface-900 dark:text-surface-0 truncate">
								Main Central (WH-01)
							</div>
							<div class="flex items-center justify-between text-xs text-surface-500 dark:text-surface-400 pt-0.5">
								<span>Reason:</span>
								<span class="font-medium text-surface-800 dark:text-surface-200 truncate max-w-[120px]">
									{{ returnRecord.reason || "Standard Return" }}
								</span>
							</div>
						</div>
					</template>
				</Card>

				<!-- Financial Reconciliation Card -->
				<Card class="border border-surface-200 dark:border-surface-800 shadow-sm">
					<template #content>
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold uppercase tracking-wider text-surface-500 dark:text-surface-400">
								Return Settlement Credit
							</span>
							<div class="w-7 h-7 rounded bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
								<i class="pi pi-wallet text-xs"></i>
							</div>
						</div>
						<div class="space-y-1">
							<div class="text-xl font-bold text-primary-600 dark:text-primary-400">
								{{ formatCurrency(calculatedTotalAmount) }}
							</div>
							<div class="flex items-center justify-between text-xs text-surface-500 dark:text-surface-400 pt-0.5">
								<span>Physical Units:</span>
								<span class="font-semibold text-surface-900 dark:text-surface-100">
									{{ formatNumber(totalUnits) }} units
								</span>
							</div>
						</div>
					</template>
				</Card>
			</div>

			<!-- Itemized Return Items Manifest -->
			<Card class="border border-surface-200 dark:border-surface-800 shadow-sm">
				<template #title>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2 text-base font-semibold text-surface-900 dark:text-surface-100">
							<i class="pi pi-list text-primary-600 dark:text-primary-400"></i>
							<span>Returned Line Items</span>
						</div>
						<Tag
							severity="secondary"
							:value="`${returnItems.length} lines`"
							class="text-xs"
						/>
					</div>
				</template>
				<template #content>
					<DataTable
						:value="returnItems"
						tableStyle="min-width: 45rem"
						class="p-datatable-sm"
						responsiveLayout="scroll"
					>
						<Column header="#" style="width: 5%">
							<template #body="{ index }">
								<span class="text-xs text-surface-400">{{ index + 1 }}</span>
							</template>
						</Column>

						<Column header="Product Name" style="width: 28%">
							<template #body="{ data }">
								<div class="flex flex-col">
									<span class="font-semibold text-surface-900 dark:text-surface-100">
										{{ data.product_obj?.name || `Product #${data.product}` }}
									</span>
									<span class="text-xs text-surface-500 dark:text-surface-400">
										Code: PR{{ data.product }}
									</span>
								</div>
							</template>
						</Column>

						<Column header="Size Variant" style="width: 14%">
							<template #body="{ data }">
								<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-surface-100 dark:bg-surface-800 text-surface-800 dark:text-surface-200">
									Size {{ data.product_size_obj?.size || data.product_size || "N/A" }}
								</span>
							</template>
						</Column>

						<Column header="Quantity" style="width: 12%">
							<template #body="{ data }">
								<span class="font-bold text-surface-900 dark:text-surface-100">
									{{ formatNumber(data.quantity) }}
								</span>
							</template>
						</Column>

						<Column header="Unit Price" style="width: 14%">
							<template #body="{ data }">
								<span>{{ formatCurrency(data.price_at_return) }}</span>
							</template>
						</Column>

						<Column header="Subtotal" style="width: 14%">
							<template #body="{ data }">
								<span class="font-semibold text-surface-900 dark:text-surface-100">
									{{ formatCurrency(data.total) }}
								</span>
							</template>
						</Column>

						<Column header="Condition & Notes" style="width: 20%">
							<template #body="{ data }">
								<div class="flex flex-col gap-1">
									<Tag
										v-if="data.condition"
										:severity="getItemConditionSeverity(data.condition)"
										:value="data.condition"
										class="text-[10px] font-semibold w-fit"
									/>
									<span v-if="data.reason" class="text-xs text-surface-500 dark:text-surface-400 italic truncate max-w-xs">
										{{ data.reason }}
									</span>
								</div>
							</template>
						</Column>

						<template #empty>
							<div class="text-center py-6 text-surface-500 dark:text-surface-400">
								No line items recorded for this return.
							</div>
						</template>
					</DataTable>

					<!-- Ledger & Inventory Impact Explanation -->
					<div class="mt-6 p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs text-surface-600 dark:text-surface-400">
						<div class="flex items-center gap-2.5">
							<i class="pi pi-box text-primary-600 dark:text-primary-400 text-lg"></i>
							<div>
								<span class="font-semibold text-surface-900 dark:text-surface-100 block">
									Inventory & Financial Settlement Impact:
								</span>
								<span v-if="returnRecord.return_type === 'SR'">
									<strong>{{ inventoryImpact.sellableUnits }} units</strong> restocked to active warehouse inventory.
									<span v-if="inventoryImpact.quarantinedUnits > 0" class="text-amber-600 font-semibold">
										({{ inventoryImpact.quarantinedUnits }} units quarantined due to damage/defects).
									</span>
								</span>
								<span v-else>
									<strong>{{ inventoryImpact.deductionUnits }} units</strong> deducted from warehouse stock (returned to vendor).
								</span>
							</div>
						</div>
						<div class="flex items-center gap-4 border-t sm:border-t-0 sm:border-l border-surface-200 dark:border-surface-800 pt-2 sm:pt-0 sm:pl-4">
							<div>
								<span class="block text-surface-400 text-[11px]">Total Refund Credit:</span>
								<span class="text-base font-bold text-surface-900 dark:text-surface-0">
									{{ formatCurrency(calculatedTotalAmount) }}
								</span>
							</div>
						</div>
					</div>
				</template>
			</Card>
		</div>

		<!-- Not Found State -->
		<div v-else class="text-center py-16">
			<i class="pi pi-exclamation-circle text-4xl text-surface-400 mb-3"></i>
			<h2 class="text-xl font-bold text-surface-900 dark:text-surface-100">Return Not Found</h2>
			<p class="text-sm text-surface-500 dark:text-surface-400 mt-1 mb-4">
				The requested return record could not be found or has been removed.
			</p>
			<router-link to="/returns">
				<Button label="Back to Returns" icon="pi pi-arrow-left" size="small" />
			</router-link>
		</div>
	</div>
</template>