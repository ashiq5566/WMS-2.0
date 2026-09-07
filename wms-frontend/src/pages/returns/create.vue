<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import axios from "@/plugins/axios";
import moment from "moment";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Card from "primevue/card";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Dialog from "primevue/dialog";
import Skeleton from "primevue/skeleton";
import Message from "primevue/message";
import DatePicker from "primevue/datepicker";
import {
	calculateRemainingReturnable,
	calculateReturnLineTotal,
	calculateTotalReturnAmount,
	calculateInventoryImpact,
	formatCurrency,
	formatNumber,
	getItemConditionSeverity,
	getReturnTypeLabel,
	getReturnTypeSeverity,
	getReturnStatusSeverity,
	type ReturnCondition,
	type ReturnStatus,
	type ReturnItemDraft,
} from "@/utils/returnCalculations";

const router = useRouter();
const route = useRoute();
const toast = useToast();

interface StakeholderObj {
	id: number;
	name: string;
	type?: string;
	phone?: string;
	address?: string;
}

interface OrderRecord {
	id: number;
	order_number: string;
	order_type: "SO" | "PO";
	order_status: string;
	stakeholder: number;
	stakeholder_obj?: StakeholderObj;
	net_amount: number;
	total_amount: number;
	pending_amount: number;
	created_at: string;
	date_added?: string;
}

interface OrderItemRecord {
	id: number;
	order: number;
	product: number;
	product_obj: {
		id: number;
		name: string;
		unit?: string;
	};
	product_size: number;
	product_size_obj?: {
		id: number;
		size: number;
		stock?: number;
	};
	quantity: number;
	price_at_time_of_order: number;
	total: number;
	already_returned: number;
	remaining_returnable: number;
}

const orders = ref<OrderRecord[]>([]);
const selectedOrder = ref<OrderRecord | null>(null);
const orderItems = ref<OrderItemRecord[]>([]);
const returnItemsDraft = ref<ReturnItemDraft[]>([]);

// Header form state
const returnDate = ref<Date>(new Date());
const selectedWarehouse = ref("Main Central Warehouse (WH-01)");
const returnReason = ref("");
const returnStatus = ref<ReturnStatus>("Completed");

const warehouseOptions = [
	{ label: "Main Central Warehouse (WH-01)", value: "Main Central Warehouse (WH-01)" },
	{ label: "Transit & Quarantine Depot (WH-02)", value: "Transit & Quarantine Depot (WH-02)" },
];

const statusOptions = [
	{ label: "Completed (Process & Reconcile Now)", value: "Completed" },
	{ label: "Approved (Authorized for Restocking)", value: "Approved" },
	{ label: "Pending Approval (Under Inspection)", value: "Pending Approval" },
	{ label: "Draft (Hold Record)", value: "Draft" },
];

const reasonOptions = [
	{ label: "Customer Sizing / Fit Issue", value: "Customer Sizing / Fit Issue" },
	{ label: "Defective / Faulty Manufacturing", value: "Defective / Faulty Manufacturing" },
	{ label: "Damaged in Transit / Shipping", value: "Damaged in Transit / Shipping" },
	{ label: "Incorrect Item Delivered", value: "Incorrect Item Delivered" },
	{ label: "Supplier Return / Rejection", value: "Supplier Return / Rejection" },
	{ label: "Other / Discretionary Return", value: "Other / Discretionary Return" },
];

const conditionOptions: { label: string; value: ReturnCondition }[] = [
	{ label: "Good (Restockable)", value: "Good" },
	{ label: "Wrong Item (Restockable)", value: "Wrong Item" },
	{ label: "Damaged (Quarantine/Write-off)", value: "Damaged" },
	{ label: "Defective (Quarantine/Manufacturer)", value: "Defective" },
	{ label: "Expired (Dispose)", value: "Expired" },
];

const isLoadingOrders = ref(true);
const isLoadingOrderItems = ref(false);
const isSubmitting = ref(false);
const showConfirmModal = ref(false);

const fetchOrders = async () => {
	try {
		isLoadingOrders.value = true;
		const response = await axios.get("/api/inventory/orders/", {
			params: {
				order_status_array: ["Issued", "Delivered", "Recieved", "Closed"],
			},
		});
		orders.value = response.data || [];

		// Handle pre-population from route query parameter (from Order Details page)
		const queryOrderId = route.query.order_id;
		if (queryOrderId) {
			const target = orders.value.find((o) => String(o.id) === String(queryOrderId));
			if (target) {
				selectedOrder.value = target;
			}
		}
	} catch (error) {
		console.error("Error fetching orders:", error);
		toast.add({
			severity: "error",
			summary: "Error",
			detail: "Failed to load eligible orders.",
			life: 3000,
		});
	} finally {
		isLoadingOrders.value = false;
	}
};

const fetchOrderDetails = async (orderId: number) => {
	try {
		isLoadingOrderItems.value = true;
		returnItemsDraft.value = [];

		// Fetch items for the order and previous returns
		const [itemsRes, returnsRes] = await Promise.all([
			axios.get("/api/inventory/order-items/", { params: { order_id: orderId } }),
			axios.get("/api/inventory/returns/", { params: { original_order: orderId } }),
		]);

		const rawItems: any[] = itemsRes.data || [];
		const existingReturns: any[] = returnsRes.data || [];

		// Calculate cumulative returns per product_size (only approved/processed/completed ones count)
		const returnedMap: Record<number, number> = {};
		for (const ret of existingReturns) {
			if (['Approved', 'Processed', 'Completed'].includes(ret.return_status || 'Completed')) {
				if (ret.items) {
					for (const ri of ret.items) {
						const psId = ri.product_size || ri.product_size_obj?.id;
						if (psId) {
							returnedMap[psId] = (returnedMap[psId] || 0) + (Number(ri.quantity) || 0);
						}
					}
				}
			}
		}

		orderItems.value = rawItems.map((item) => {
			const psId = item.product_size || item.product_size_obj?.id;
			const ordered = Number(item.quantity) || 0;
			const returned = returnedMap[psId] || 0;
			const remaining = calculateRemainingReturnable(ordered, returned);

			return {
				...item,
				already_returned: returned,
				remaining_returnable: remaining,
			};
		});

		// If user came from an order details page, inform them if there are eligible items
		const totalAvailable = orderItems.value.reduce((sum, it) => sum + it.remaining_returnable, 0);
		if (totalAvailable === 0 && orderItems.value.length > 0) {
			toast.add({
				severity: "info",
				summary: "Fully Returned",
				detail: "All items from this order have already been returned.",
				life: 4000,
			});
		}
	} catch (error) {
		console.error("Error loading order items:", error);
		toast.add({
			severity: "error",
			summary: "Error",
			detail: "Failed to load order items and return history.",
			life: 3000,
		});
	} finally {
		isLoadingOrderItems.value = false;
	}
};

const isItemInReturnList = (orderItemId: number) => {
	return returnItemsDraft.value.some((draft) => draft.order_item_id === orderItemId);
};

const addItemToReturn = (item: OrderItemRecord) => {
	if (item.remaining_returnable <= 0) {
		toast.add({
			severity: "warn",
			summary: "Limit Reached",
			detail: "This item has already been completely returned.",
			life: 3000,
		});
		return;
	}

	if (isItemInReturnList(item.id)) {
		toast.add({
			severity: "info",
			summary: "Already Added",
			detail: "This item variant is already in the return list.",
			life: 2000,
		});
		return;
	}

	const unitPrice = Number(item.price_at_time_of_order) || 0;
	const initialQty = Math.min(1, item.remaining_returnable);

	returnItemsDraft.value.push({
		order_item_id: item.id,
		product: item.product || item.product_obj?.id,
		product_name: item.product_obj?.name || "Product",
		product_size: item.product_size || item.product_size_obj?.id,
		size: item.product_size_obj?.size || 0,
		quantity: initialQty,
		price_at_return: unitPrice,
		total: calculateReturnLineTotal(initialQty, unitPrice),
		condition: "Good",
		reason: returnReason.value || "",
		max_returnable: item.remaining_returnable,
	});
};

const removeItemFromReturn = (index: number) => {
	returnItemsDraft.value.splice(index, 1);
};

const updateItemQuantity = (item: ReturnItemDraft, val: number | null) => {
	const cleanVal = Math.max(1, Math.min(Number(val) || 1, item.max_returnable));
	item.quantity = cleanVal;
	item.total = calculateReturnLineTotal(cleanVal, item.price_at_return);
};

// Summary metrics & calculations
const totalReturnAmount = computed(() => calculateTotalReturnAmount(returnItemsDraft.value));

const returnType = computed(() => {
	if (!selectedOrder.value) return "SR";
	return selectedOrder.value.order_type === "SO" ? "SR" : "PR";
});

const inventoryImpact = computed(() => {
	return calculateInventoryImpact(returnType.value, returnItemsDraft.value);
});

// Tax impact: in this WMS, prices are net inclusive (0% extra tax or GST inclusive ledger)
const taxImpact = computed(() => {
	return 0; // Tax is integrated in net settlement
});

const canSubmit = computed(() => {
	return (
		selectedOrder.value !== null &&
		selectedOrder.value.order_status !== "Cancelled" &&
		returnItemsDraft.value.length > 0 &&
		returnItemsDraft.value.every((item) => item.quantity > 0 && item.quantity <= item.max_returnable)
	);
});

const openConfirmModal = () => {
	if (!canSubmit.value) return;
	showConfirmModal.value = true;
};

const submitReturn = async () => {
	if (!selectedOrder.value || returnItemsDraft.value.length === 0) return;

	try {
		isSubmitting.value = true;

		const payload = {
			return: {
				original_order: selectedOrder.value.id,
				return_type: returnType.value,
				return_status: returnStatus.value,
				total_amount: totalReturnAmount.value,
				reason: returnReason.value,
			},
			items: returnItemsDraft.value.map((item) => ({
				product: item.product,
				product_size: item.product_size,
				quantity: item.quantity,
				price_at_return: item.price_at_return,
				total: item.total,
				condition: item.condition,
				reason: item.reason || returnReason.value || (item.condition === "Good" ? "Customer Return" : item.condition),
			})),
		};

		const response = await axios.post("/api/inventory/returns/", payload);
		const createdRmaId = response.data.return.id;

		toast.add({
			severity: "success",
			summary: "Return Created",
			detail: `RMA-${String(createdRmaId).padStart(4, "0")} (${returnStatus.value}) processed successfully.`,
			life: 3000,
		});

		showConfirmModal.value = false;
		router.push({ name: "returns-id", params: { id: createdRmaId } });
	} catch (error: any) {
		console.error("Error creating return:", error);
		const errorMsg =
			error.response?.data?.error ||
			error.response?.data?.detail ||
			"Failed to process return. Please verify quantities and stock.";
		toast.add({
			severity: "error",
			summary: "Return Authorization Failed",
			detail: errorMsg,
			life: 5000,
		});
	} finally {
		isSubmitting.value = false;
	}
};

watch(selectedOrder, (newOrder) => {
	if (newOrder) {
		fetchOrderDetails(newOrder.id);
	} else {
		orderItems.value = [];
		returnItemsDraft.value = [];
	}
});

onMounted(() => {
	fetchOrders();
});
</script>

<template>
	<div class="space-y-6">
		<!-- Page Header -->
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
			<div>
				<div class="flex items-center gap-2">
					<router-link to="/returns">
						<Button icon="pi pi-arrow-left" severity="secondary" text rounded size="small" />
					</router-link>
					<h1 class="text-2xl font-bold tracking-tight text-surface-900 dark:text-surface-0">
						Create Return Authorization (RMA)
					</h1>
					<Tag
						value="New RMA"
						severity="info"
						class="text-xs font-mono font-bold uppercase ml-2"
					/>
				</div>
				<p class="text-sm text-surface-500 dark:text-surface-400 mt-1 ml-9">
					Authorize reverse logistics, inspect delivered order lines, apply condition classifications, and reconcile warehouse stock.
				</p>
			</div>
			<div class="flex items-center gap-2">
				<router-link to="/returns">
					<Button label="Cancel" severity="secondary" outlined size="small" />
				</router-link>
				<Button
					label="Submit Return"
					icon="pi pi-check"
					size="small"
					:disabled="!canSubmit"
					@click="openConfirmModal"
				/>
			</div>
		</div>

		<!-- Section 1: Return Information -->
		<Card class="border border-surface-200 dark:border-surface-800 shadow-sm">
			<template #title>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2 text-base font-semibold text-surface-900 dark:text-surface-100">
						<span class="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/40 text-primary-600 dark:text-primary-400 text-xs font-bold flex items-center justify-center">1</span>
						<span>Return Header & Reference</span>
					</div>
					<Tag
						v-if="selectedOrder"
						:severity="getReturnTypeSeverity(returnType)"
						:value="getReturnTypeLabel(returnType)"
						class="text-xs font-bold"
					/>
				</div>
			</template>
			<template #content>
				<div class="grid grid-cols-1 md:grid-cols-3 gap-5 items-start mt-2 text-xs">
					<!-- Reference Order Selection -->
					<div class="space-y-1">
						<label class="block font-semibold uppercase tracking-wider text-surface-600 dark:text-surface-400">
							Reference Order *
						</label>
						<Select
							v-model="selectedOrder"
							:options="orders"
							optionLabel="order_number"
							placeholder="Select source order..."
							filter
							:loading="isLoadingOrders"
							class="w-full"
						>
							<template #option="{ option }">
								<div class="flex items-center justify-between w-full py-1 text-xs">
									<div class="flex flex-col">
										<span class="font-medium text-surface-900 dark:text-surface-100">{{ option.order_number }}</span>
										<span class="text-[11px] text-surface-500">{{ option.stakeholder_obj?.name }}</span>
									</div>
									<div class="flex items-center gap-2">
										<Tag
											:severity="option.order_type === 'SO' ? 'info' : 'warn'"
											:value="option.order_type === 'SO' ? 'SO' : 'PO'"
											class="text-[10px]"
										/>
										<span class="font-semibold">{{ formatCurrency(option.total_amount) }}</span>
									</div>
								</div>
							</template>
						</Select>
					</div>

					<!-- Warehouse Assignment -->
					<div class="space-y-1">
						<label class="block font-semibold uppercase tracking-wider text-surface-600 dark:text-surface-400">
							Receiving / Shipping Warehouse *
						</label>
						<Select
							v-model="selectedWarehouse"
							:options="warehouseOptions"
							optionLabel="label"
							optionValue="value"
							class="w-full"
						/>
					</div>

					<!-- Return Workflow Status -->
					<div class="space-y-1">
						<label class="block font-semibold uppercase tracking-wider text-surface-600 dark:text-surface-400">
							Initial Return Status *
						</label>
						<Select
							v-model="returnStatus"
							:options="statusOptions"
							optionLabel="label"
							optionValue="value"
							class="w-full"
						/>
					</div>

					<!-- Return Date -->
					<div class="space-y-1">
						<label class="block font-semibold uppercase tracking-wider text-surface-600 dark:text-surface-400">
							Return Date *
						</label>
						<DatePicker
							v-model="returnDate"
							:manualInput="false"
							showIcon
							class="w-full"
						/>
					</div>

					<!-- Primary Return Reason -->
					<div class="space-y-1 md:col-span-2">
						<label class="block font-semibold uppercase tracking-wider text-surface-600 dark:text-surface-400">
							Primary Return Reason
						</label>
						<Select
							v-model="returnReason"
							:options="reasonOptions"
							optionLabel="label"
							optionValue="value"
							editable
							placeholder="Select or enter primary reason..."
							class="w-full"
						/>
					</div>
				</div>

				<!-- Stakeholder & Source Order Context Banner -->
				<div
					v-if="selectedOrder"
					class="mt-5 p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900/50 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs"
				>
					<div>
						<span class="text-surface-400 block mb-0.5">Party Name:</span>
						<strong class="text-surface-900 dark:text-surface-100 text-sm">
							{{ selectedOrder.stakeholder_obj?.name }}
						</strong>
						<span class="text-[11px] text-surface-500 block">{{ selectedOrder.order_type === 'SO' ? 'Customer' : 'Supplier' }}</span>
					</div>
					<div>
						<span class="text-surface-400 block mb-0.5">Order Status:</span>
						<Tag
							severity="secondary"
							:value="selectedOrder.order_status"
							class="text-[10px] font-semibold"
						/>
					</div>
					<div>
						<span class="text-surface-400 block mb-0.5">Original Order Total:</span>
						<span class="font-bold text-surface-900 dark:text-surface-100 text-sm">
							{{ formatCurrency(selectedOrder.total_amount) }}
						</span>
					</div>
					<div>
						<span class="text-surface-400 block mb-0.5">Outstanding Pending:</span>
						<span class="font-bold text-amber-600 dark:text-amber-400 text-sm">
							{{ formatCurrency(selectedOrder.pending_amount) }}
						</span>
					</div>
				</div>
			</template>
		</Card>

		<!-- Section 2: Order Lines Inspection (Source Order) -->
		<Card v-if="selectedOrder" class="border border-surface-200 dark:border-surface-800 shadow-sm">
			<template #title>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2 text-base font-semibold text-surface-900 dark:text-surface-100">
						<span class="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/40 text-primary-600 dark:text-primary-400 text-xs font-bold flex items-center justify-center">2</span>
						<span>Source Order Line Items & Available Return Quantities</span>
					</div>
					<span class="text-xs text-surface-500 dark:text-surface-400">
						Click "+ Add to Return" to configure line items
					</span>
				</div>
			</template>
			<template #content>
				<div v-if="isLoadingOrderItems" class="space-y-3 p-4">
					<Skeleton height="2.5rem" class="w-full" />
					<Skeleton height="2.5rem" class="w-full" />
					<Skeleton height="2.5rem" class="w-full" />
				</div>

				<DataTable
					v-else
					:value="orderItems"
					class="p-datatable-sm"
					responsiveLayout="scroll"
				>
					<Column header="Product & Size Variant" style="width: 28%">
						<template #body="{ data }">
							<div class="flex flex-col">
								<span class="font-semibold text-surface-900 dark:text-surface-100">
									{{ data.product_obj?.name }}
								</span>
								<span class="text-xs text-surface-500 dark:text-surface-400">
									Size: <strong class="text-surface-700 dark:text-surface-300">{{ data.product_size_obj?.size || data.product_size || "N/A" }}</strong>
								</span>
							</div>
						</template>
					</Column>

					<Column header="Unit Price" style="width: 14%">
						<template #body="{ data }">
							<span>{{ formatCurrency(data.price_at_time_of_order) }}</span>
						</template>
					</Column>

					<Column header="Delivered / Ordered" style="width: 14%; text-align: center">
						<template #body="{ data }">
							<span class="font-medium">{{ formatNumber(data.quantity) }}</span>
						</template>
					</Column>

					<Column header="Already Returned" style="width: 14%; text-align: center">
						<template #body="{ data }">
							<span :class="data.already_returned > 0 ? 'text-amber-600 dark:text-amber-400 font-bold' : 'text-surface-400'">
								{{ formatNumber(data.already_returned) }}
							</span>
						</template>
					</Column>

					<Column header="Available to Return" style="width: 16%; text-align: center">
						<template #body="{ data }">
							<Tag
								:severity="data.remaining_returnable > 0 ? 'success' : 'secondary'"
								:value="data.remaining_returnable > 0 ? `${formatNumber(data.remaining_returnable)} units` : 'Fully Returned'"
								class="text-xs font-semibold"
							/>
						</template>
					</Column>

					<Column header="Action" style="width: 14%; text-align: right">
						<template #body="{ data }">
							<Button
								v-if="!isItemInReturnList(data.id) && data.remaining_returnable > 0"
								icon="pi pi-plus"
								label="Add to Return"
								size="small"
								outlined
								class="text-xs"
								@click="addItemToReturn(data)"
							/>
							<Tag
								v-else-if="isItemInReturnList(data.id)"
								severity="info"
								value="Selected"
								class="text-xs"
							/>
							<span v-else class="text-xs text-surface-400 italic">None</span>
						</template>
					</Column>

					<template #empty>
						<div class="text-center py-6 text-surface-500 dark:text-surface-400">
							No items found for this order.
						</div>
					</template>
				</DataTable>
			</template>
		</Card>

		<!-- Section 3: Return Items Manifest (To be processed) -->
		<Card v-if="selectedOrder" class="border border-surface-200 dark:border-surface-800 shadow-sm">
			<template #title>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2 text-base font-semibold text-surface-900 dark:text-surface-100">
						<span class="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/40 text-primary-600 dark:text-primary-400 text-xs font-bold flex items-center justify-center">3</span>
						<span>Return Items Manifest & Condition Grading</span>
					</div>
					<Tag
						v-if="returnItemsDraft.length"
						severity="primary"
						:value="`${returnItemsDraft.length} items configured`"
						class="text-xs"
					/>
				</div>
			</template>
			<template #content>
				<div v-if="returnItemsDraft.length === 0" class="text-center py-10 border border-dashed border-surface-200 dark:border-surface-800 rounded-xl">
					<i class="pi pi-inbox text-3xl text-surface-400 mb-2"></i>
					<p class="text-sm font-medium text-surface-700 dark:text-surface-300">No items selected for return yet</p>
					<p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
						Click "+ Add to Return" on any available order line in Step 2 above.
					</p>
				</div>

				<div v-else class="space-y-5">
					<DataTable :value="returnItemsDraft" class="p-datatable-sm" responsiveLayout="scroll">
						<Column header="Product & Size" style="width: 22%">
							<template #body="{ data }">
								<div class="flex flex-col">
									<span class="font-semibold text-surface-900 dark:text-surface-100">{{ data.product_name }}</span>
									<span class="text-xs text-surface-500 dark:text-surface-400">Size: {{ data.size }}</span>
								</div>
							</template>
						</Column>

						<Column header="Return Qty *" style="width: 18%">
							<template #body="{ data }">
								<div class="flex flex-col gap-1">
									<InputNumber
										v-model="data.quantity"
										:min="1"
										:max="data.max_returnable"
										showButtons
										buttonLayout="horizontal"
										inputClass="w-16 text-center text-sm font-semibold"
										incrementButtonIcon="pi pi-plus"
										decrementButtonIcon="pi pi-minus"
										@update:modelValue="(val) => updateItemQuantity(data, val)"
									/>
									<span
										class="text-[10px]"
										:class="data.quantity > data.max_returnable ? 'text-rose-500 font-bold' : 'text-surface-500 dark:text-surface-400'"
									>
										Max eligible: {{ data.max_returnable }}
									</span>
								</div>
							</template>
						</Column>

						<Column header="Unit Rate" style="width: 12%">
							<template #body="{ data }">
								<span>{{ formatCurrency(data.price_at_return) }}</span>
							</template>
						</Column>

						<Column header="Condition *" style="width: 18%">
							<template #body="{ data }">
								<Select
									v-model="data.condition"
									:options="conditionOptions"
									optionLabel="label"
									optionValue="value"
									class="w-full text-xs"
								/>
							</template>
						</Column>

						<Column header="Line Notes / Reason" style="width: 17%">
							<template #body="{ data }">
								<InputText
									v-model="data.reason"
									placeholder="Item condition or fault notes..."
									class="w-full text-xs"
								/>
							</template>
						</Column>

						<Column header="Line Subtotal" style="width: 11%">
							<template #body="{ data }">
								<span class="font-bold text-surface-900 dark:text-surface-100">
									{{ formatCurrency(data.total) }}
								</span>
							</template>
						</Column>

						<Column header="" style="width: 4%; text-align: right">
							<template #body="{ index }">
								<Button
									icon="pi pi-trash"
									severity="danger"
									text
									rounded
									size="small"
									@click="removeItemFromReturn(index)"
									v-tooltip.top="'Remove line'"
								/>
							</template>
						</Column>
					</DataTable>

					<!-- Section 4: Comprehensive Summary Panel -->
					<div class="p-5 rounded-2xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900/40 space-y-4">
						<div class="flex items-center gap-2 pb-3 border-b border-surface-200 dark:border-surface-800 text-sm font-bold text-surface-900 dark:text-surface-100">
							<i class="pi pi-chart-pie text-primary-600"></i>
							<span>Return Impact & Financial Summary</span>
						</div>

						<div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
							<div class="p-3 rounded-xl bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-800">
								<span class="text-surface-400 block mb-1">Return Lines</span>
								<span class="text-lg font-bold text-surface-900 dark:text-surface-0">
									{{ returnItemsDraft.length }} distinct items
								</span>
							</div>
							<div class="p-3 rounded-xl bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-800">
								<span class="text-surface-400 block mb-1">Total Return Quantity</span>
								<span class="text-lg font-bold text-surface-900 dark:text-surface-0">
									{{ inventoryImpact.totalUnits }} units
								</span>
							</div>
							<div class="p-3 rounded-xl bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-800">
								<span class="text-surface-400 block mb-1">Tax Adjustments</span>
								<span class="text-lg font-bold text-surface-600 dark:text-surface-400">
									{{ formatCurrency(taxImpact) }} (0% / Exempt)
								</span>
							</div>
							<div class="p-3 rounded-xl bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-800">
								<span class="text-surface-400 block mb-1">Total Return Value</span>
								<span class="text-xl font-bold text-primary-600 dark:text-primary-400">
									{{ formatCurrency(totalReturnAmount) }}
								</span>
							</div>
						</div>

						<!-- Inventory Impact Breakdown -->
						<div class="p-3 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-0 dark:bg-surface-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
							<div class="flex items-center gap-2">
								<i class="pi pi-box text-emerald-600 dark:text-emerald-400 text-base"></i>
								<div>
									<span class="font-semibold text-surface-900 dark:text-surface-100 block">Inventory Physical Flow:</span>
									<span v-if="returnType === 'SR'">
										Restocking <strong>{{ inventoryImpact.sellableUnits }} units</strong> into sellable warehouse stock
										<span v-if="inventoryImpact.quarantinedUnits > 0" class="text-amber-600 font-semibold">
											({{ inventoryImpact.quarantinedUnits }} units quarantined due to damage/defect)
										</span>.
									</span>
									<span v-else>
										Deducting <strong>{{ inventoryImpact.deductionUnits }} units</strong> from warehouse stock (returning to supplier).
									</span>
								</div>
							</div>
							<div class="text-right sm:border-l sm:pl-4 border-surface-200 dark:border-surface-800">
								<span class="text-surface-400 block text-[11px]">Workflow Execution:</span>
								<Tag
									:severity="getReturnStatusSeverity(returnStatus)"
									:value="returnStatus"
									class="text-[10px] font-semibold"
								/>
							</div>
						</div>
					</div>

					<!-- Bottom Action Buttons -->
					<div class="flex items-center justify-between pt-3 border-t border-surface-200 dark:border-surface-800">
						<router-link to="/returns">
							<Button label="Back to Returns" severity="secondary" outlined size="small" />
						</router-link>
						<Button
							label="Authorize & Submit Return"
							icon="pi pi-check"
							:disabled="!canSubmit"
							@click="openConfirmModal"
						/>
					</div>
				</div>
			</template>
		</Card>

		<!-- Pre-flight Confirmation Dialog -->
		<Dialog
			v-model:visible="showConfirmModal"
			modal
			header="Authorize Return (RMA Submission)"
			:style="{ width: '38rem' }"
			class="p-fluid"
		>
			<div class="space-y-4 pt-2 text-xs">
				<p class="text-surface-600 dark:text-surface-300">
					Review the reverse logistics and financial settlement details before finalizing.
				</p>

				<div class="p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-900/50 space-y-2">
					<div class="flex justify-between">
						<span class="text-surface-500">Return Type:</span>
						<span class="font-semibold">{{ getReturnTypeLabel(returnType) }}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-surface-500">Source Order:</span>
						<span class="font-semibold">{{ selectedOrder?.order_number }}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-surface-500">Warehouse:</span>
						<span class="font-semibold">{{ selectedWarehouse }}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-surface-500">Party / Stakeholder:</span>
						<span class="font-semibold">{{ selectedOrder?.stakeholder_obj?.name }}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-surface-500">Execution Status:</span>
						<Tag :severity="getReturnStatusSeverity(returnStatus)" :value="returnStatus" class="text-[10px]" />
					</div>
					<div class="flex justify-between">
						<span class="text-surface-500">Units Restored / Deducted:</span>
						<span class="font-bold">{{ inventoryImpact.totalUnits }} units</span>
					</div>
					<div class="flex justify-between border-t border-surface-200 dark:border-surface-800 pt-2 text-sm font-bold">
						<span class="text-surface-900 dark:text-surface-100">Total Return Credit:</span>
						<span class="text-primary-600 dark:text-primary-400">{{ formatCurrency(totalReturnAmount) }}</span>
					</div>
				</div>

				<div class="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 p-3 rounded-lg flex items-start gap-2 text-amber-800 dark:text-amber-200">
					<i class="pi pi-exclamation-triangle text-amber-600 dark:text-amber-400 mt-0.5"></i>
					<span>
						<strong v-if="returnStatus === 'Completed' || returnStatus === 'Approved'">Immediate Execution:</strong>
						<strong v-else>Draft Mode:</strong>
						{{ returnStatus === 'Completed' || returnStatus === 'Approved'
							? 'This will immediately update inventory stock and order financial ledgers.'
							: 'Stock and order balances will remain untouched until the return is approved.' }}
					</span>
				</div>
			</div>

			<template #footer>
				<div class="flex justify-end gap-2">
					<Button
						label="Review Again"
						severity="secondary"
						outlined
						@click="showConfirmModal = false"
						:disabled="isSubmitting"
					/>
					<Button
						label="Confirm & Submit RMA"
						icon="pi pi-check"
						:loading="isSubmitting"
						@click="submitReturn"
					/>
				</div>
			</template>
		</Dialog>
	</div>
</template>