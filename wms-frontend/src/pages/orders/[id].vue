<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import moment from "moment";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Card from "primevue/card";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Tag from "primevue/tag";
import Dialog from "primevue/dialog";
import paymentsLisCard from "@/components/payments/paymentsLisCard.vue";
import {
	formatCurrency,
	getOrderStatusSeverity,
	getOrderTypeLabel,
} from "@/utils/orderCalculations";
import {
	getReturnTypeLabel,
	getReturnTypeSeverity,
	getReturnStatusSeverity,
} from "@/utils/returnCalculations";
import { setPageTitle } from "@/utils/meta";

const route = useRoute();
const router = useRouter();
const toast = useToast();

const order = ref<any>({});
const orderItems = ref<any[]>([]);
const returnOrders = ref<any[]>([]);
const payments = ref<any[]>([]);
const isLoading = ref(true);

// Cancellation modal state
const cancelDialogVisible = ref(false);
const isCancelling = ref(false);

const fetchOrder = async () => {
	try {
		const response = await axios.get(`/api/inventory/orders/${route.params.id}`);
		order.value = response.data || {};
		const orderNum = order.value.order_number || (`#${route.params.id}`);
		setPageTitle(`Order ${orderNum}`, `Order ${orderNum} details and payment ledger`);
	} catch (error) {
		console.error("Error loading order:", error);
		toast.add({ severity: "error", summary: "Load Failed", detail: "Could not retrieve order details.", life: 3000 });
	}
};

const fetchOrderItems = async () => {
	try {
		const response = await axios.get("/api/inventory/order-items/", {
			params: { order_id: route.params.id },
		});
		orderItems.value = response.data || [];
	} catch (error) {
		console.error("Error loading items:", error);
	}
};

const fetchReturns = async () => {
	try {
		const response = await axios.get("/api/inventory/returns/", {
			params: { original_order: route.params.id },
		});
		returnOrders.value = response.data || [];
	} catch (error) {
		console.error("Error loading returns:", error);
	}
};

const fetchPayments = async () => {
	try {
		const response = await axios.get("/api/inventory/payments", {
			params: { order_id: route.params.id },
		});
		payments.value = response.data || [];
	} catch (error) {
		console.error("Error loading payments:", error);
	}
};

const handlePayment = async () => {
	await fetchOrder();
	await fetchPayments();
};

const returnedMap = computed(() => {
	const map: Record<number, number> = {};
	for (const ret of returnOrders.value) {
		if (['Approved', 'Processed', 'Completed'].includes(ret.return_status || 'Completed')) {
			if (ret.items) {
				for (const item of ret.items) {
					const psId = item.product_size || item.product_size_obj?.id;
					if (psId) {
						map[psId] = (map[psId] || 0) + (Number(item.quantity) || 0);
					}
				}
			}
		}
	}
	return map;
});

const totalReturnableUnits = computed(() => {
	return orderItems.value.reduce((sum, item) => {
		const psId = item.product_size || item.product_size_obj?.id;
		const returned = returnedMap.value[psId] || 0;
		const remaining = Math.max(0, (Number(item.quantity) || 0) - returned);
		return sum + remaining;
	}, 0);
});

const canCreateReturn = computed(() => {
	if (!order.value?.id) return false;
	if (order.value.order_status === 'Cancelled') return false;
	if (!['Issued', 'Delivered', 'Recieved', 'Closed'].includes(order.value.order_status)) return false;
	return totalReturnableUnits.value > 0;
});

const navigateToCreateReturn = () => {
	router.push({
		name: 'returns-create',
		query: { order_id: order.value.id },
	});
};

const executeCancellation = async () => {
	isCancelling.value = true;
	try {
		await axios.post(`/api/inventory/orders/${route.params.id}/cancel/`);
		toast.add({
			severity: "success",
			summary: "Order Cancelled",
			detail: "Order was cancelled and stock was reversed in warehouse inventory.",
			life: 3500,
		});
		cancelDialogVisible.value = false;
		await fetchOrder();
		await fetchOrderItems();
	} catch (error: any) {
		console.error("Cancellation error:", error);
		const msg = error.response?.data?.error || "Failed to cancel order.";
		toast.add({ severity: "error", summary: "Cancellation Failed", detail: msg, life: 4000 });
	} finally {
		isCancelling.value = false;
	}
};

onMounted(async () => {
	isLoading.value = true;
	await Promise.all([fetchOrder(), fetchOrderItems(), fetchPayments(), fetchReturns()]);
	isLoading.value = false;
});
</script>

<template>
	<div class="space-y-6 pb-16 text-slate-800 dark:text-slate-100">
		<!-- Header -->
		<div
			class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm transition-colors"
		>
			<div class="flex items-center gap-3">
				<Button
					icon="pi pi-arrow-left"
					severity="secondary"
					text
					rounded
					size="small"
					class="!w-9 !h-9 hover:!bg-slate-100 dark:hover:!bg-slate-800"
					@click="$router.back()"
				/>
				<div>
					<div class="flex items-center gap-2 mb-0.5">
						<Tag
							:severity="order.order_type === 'SO' ? 'success' : 'info'"
							:value="order.order_type === 'SO' ? 'Sales Order' : 'Purchase Order'"
							class="!text-[10px] !px-2 !py-0.2"
						/>
						<Tag
							:severity="getOrderStatusSeverity(order.order_status)"
							:value="order.order_status"
							class="!text-[10px] !px-2 !py-0.2"
						/>
					</div>
					<h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white font-mono">
						Order #{{ order.order_number || `ORD-${order.id}` }}
					</h1>
				</div>
			</div>

			<div class="flex items-center gap-2.5">
				<Button
					v-if="canCreateReturn"
					label="Create Return (RMA)"
					icon="pi pi-replay"
					severity="warn"
					size="small"
					class="!text-xs !py-2 !px-3.5"
					@click="navigateToCreateReturn"
				/>
				<Button
					v-else-if="order.order_status !== 'Cancelled' && totalReturnableUnits === 0 && orderItems.length > 0"
					label="Fully Returned"
					icon="pi pi-check-circle"
					severity="secondary"
					disabled
					size="small"
					class="!text-xs !py-2 !px-3.5"
				/>
				<Button
					v-if="order.order_status !== 'Cancelled'"
					label="Cancel Order & Reverse Stock"
					icon="pi pi-times-circle"
					severity="danger"
					outlined
					size="small"
					class="!text-xs !py-2 !px-3.5"
					@click="cancelDialogVisible = true"
				/>
			</div>
		</div>

		<!-- Top Row: Details & Line Items -->
		<div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
			<!-- Order Details Card (5 cols) -->
			<Card class="lg:col-span-5 !bg-white dark:!bg-slate-900 !border !border-slate-200/80 dark:!border-slate-800/80 !shadow-sm !rounded-2xl">
				<template #title>
					<div class="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
						<i class="pi pi-file-edit text-indigo-600"></i>
						<span>Order Header & Financials</span>
					</div>
				</template>
				<template #content>
					<div class="space-y-4 pt-2 text-xs">
						<div class="grid grid-cols-2 gap-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
							<div>
								<span class="text-slate-400 block mb-0.5">Stakeholder:</span>
								<strong class="text-slate-900 dark:text-white">{{ order.stakeholder_obj?.name }}</strong>
								<span class="text-[10px] text-slate-400 block">{{ order.stakeholder_obj?.type }}</span>
							</div>
							<div>
								<span class="text-slate-400 block mb-0.5">Order Date:</span>
								<strong class="text-slate-900 dark:text-white">
									{{ moment(order.date_added || order.created_at).format('DD MMM YYYY') }}
								</strong>
								<span class="text-[10px] text-slate-400 block">
									{{ moment(order.date_added || order.created_at).format('hh:mm A') }}
								</span>
							</div>
						</div>

						<!-- Financial Breakdown -->
						<div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
							<div class="flex justify-between text-slate-600 dark:text-slate-400">
								<span>Gross Subtotal:</span>
								<span class="font-semibold text-slate-900 dark:text-white">{{ formatCurrency(order.gross_amount) }}</span>
							</div>
							<div class="flex justify-between text-slate-600 dark:text-slate-400">
								<span>Discount Applied:</span>
								<span class="font-semibold text-rose-500">- {{ formatCurrency(order.discount) }}</span>
							</div>
							<div class="flex justify-between text-slate-900 dark:text-white font-bold text-sm pt-1 border-t border-slate-100 dark:border-slate-800">
								<span>Net Payable:</span>
								<span class="text-indigo-600 dark:text-indigo-400">{{ formatCurrency(order.net_amount) }}</span>
							</div>
							<div v-if="order.total_amount !== order.net_amount" class="flex justify-between text-slate-500 pt-1">
								<span>Post-Return Value:</span>
								<span class="font-semibold">{{ formatCurrency(order.total_amount) }}</span>
							</div>
							<div class="flex justify-between font-bold pt-2 border-t border-slate-100 dark:border-slate-800">
								<span class="text-amber-600 dark:text-amber-400">Outstanding Balance:</span>
								<span class="text-amber-600 dark:text-amber-400">{{ formatCurrency(order.pending_amount) }}</span>
							</div>
						</div>
					</div>
				</template>
			</Card>

			<!-- Line Items Card (7 cols) -->
			<Card class="lg:col-span-7 !bg-white dark:!bg-slate-900 !border !border-slate-200/80 dark:!border-slate-800/80 !shadow-sm !rounded-2xl">
				<template #title>
					<div class="flex items-center justify-between text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
						<div class="flex items-center gap-2">
							<i class="pi pi-list text-indigo-600"></i>
							<span>Order Items ({{ orderItems.length }})</span>
						</div>
						<Tag
							v-if="canCreateReturn"
							severity="success"
							:value="`${totalReturnableUnits} units returnable`"
							class="!text-[10px]"
						/>
					</div>
				</template>
				<template #content>
					<div class="overflow-x-auto border border-slate-200/80 dark:border-slate-800 rounded-xl mt-2">
						<table class="w-full text-xs text-left">
							<thead class="bg-slate-50 dark:bg-slate-800 font-semibold text-slate-600 dark:text-slate-300 border-b border-slate-200/80 dark:border-slate-800">
								<tr>
									<th class="p-2.5">Product & Size</th>
									<th class="p-2.5 text-center w-16">Ordered</th>
									<th class="p-2.5 text-center w-16">Returned</th>
									<th class="p-2.5 text-center w-20">Returnable</th>
									<th class="p-2.5 text-right w-20">Rate</th>
									<th class="p-2.5 text-right w-24">Line Total</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
								<tr v-for="item in orderItems" :key="item.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
									<td class="p-2.5">
										<div class="font-semibold text-slate-900 dark:text-white">
											{{ item.product_obj?.name }}
										</div>
										<div class="text-[11px] text-slate-400">
											<span v-if="item.product_size_obj">Size {{ item.product_size_obj.size }}</span>
											<span v-else>Standard Item</span>
										</div>
									</td>
									<td class="p-2.5 text-center font-medium text-slate-800 dark:text-slate-200">
										{{ item.quantity }}
									</td>
									<td class="p-2.5 text-center">
										<span :class="(returnedMap[item.product_size || item.product_size_obj?.id] || 0) > 0 ? 'text-rose-500 font-bold' : 'text-slate-400'">
											{{ returnedMap[item.product_size || item.product_size_obj?.id] || 0 }}
										</span>
									</td>
									<td class="p-2.5 text-center">
										<span
											class="px-1.5 py-0.5 rounded text-[11px] font-semibold"
											:class="Math.max(0, item.quantity - (returnedMap[item.product_size || item.product_size_obj?.id] || 0)) > 0 ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400' : 'bg-slate-100 text-slate-400 dark:bg-slate-800'"
										>
											{{ Math.max(0, item.quantity - (returnedMap[item.product_size || item.product_size_obj?.id] || 0)) }}
										</span>
									</td>
									<td class="p-2.5 text-right text-slate-600 dark:text-slate-300">
										{{ formatCurrency(item.price_at_time_of_order) }}
									</td>
									<td class="p-2.5 text-right font-bold text-slate-900 dark:text-white">
										{{ formatCurrency(item.total) }}
									</td>
								</tr>
								<tr v-if="orderItems.length === 0">
									<td colspan="6" class="p-6 text-center text-slate-400 italic">No line items attached.</td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>
			</Card>
		</div>

		<!-- Bottom Row: Payments & Returns -->
		<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
			<!-- Payment History (7 cols) -->
			<div class="lg:col-span-7">
				<paymentsLisCard
					:payments="payments"
					:pendingAmount="order.pending_amount"
					:orderId="route.params.id"
					:companyId="order.stakeholder"
					@instance-added="handlePayment"
				/>
			</div>

			<!-- Returns (5 cols) -->
			<Card class="lg:col-span-5 !bg-white dark:!bg-slate-900 !border !border-slate-200/80 dark:!border-slate-800/80 !shadow-sm !rounded-2xl">
				<template #title>
					<div class="flex items-center justify-between text-sm font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
						<div class="flex items-center gap-2">
							<i class="pi pi-undo text-rose-500"></i>
							<span>Return Logistics (RMA)</span>
						</div>
						<Button
							v-if="canCreateReturn"
							label="Create Return"
							icon="pi pi-plus"
							size="small"
							text
							class="!text-xs !py-1 !px-2"
							@click="navigateToCreateReturn"
						/>
					</div>
				</template>
				<template #content>
					<div v-if="returnOrders.length > 0" class="space-y-3 pt-2 text-xs">
						<div
							v-for="ret in returnOrders"
							:key="ret.id"
							class="p-3 bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 rounded-xl space-y-2"
						>
							<div class="flex items-center justify-between">
								<router-link
									:to="{ name: 'returns-id', params: { id: ret.id } }"
									class="font-mono font-bold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
								>
									<span>RMA-{{ String(ret.id).padStart(4, '0') }}</span>
									<i class="pi pi-external-link text-[10px]"></i>
								</router-link>
								<div class="flex items-center gap-1.5">
									<Tag
										:severity="getReturnTypeSeverity(ret.return_type)"
										:value="ret.return_type === 'SR' ? 'Sales Return' : 'Purchase Return'"
										class="!text-[10px]"
									/>
									<Tag
										:severity="getReturnStatusSeverity(ret.return_status || 'Completed')"
										:value="ret.return_status || 'Completed'"
										class="!text-[10px]"
									/>
								</div>
							</div>
							<div class="flex items-center justify-between text-slate-500 dark:text-slate-400 pt-1">
								<span>{{ moment(ret.date_added || ret.date).format('DD MMM YYYY') }}</span>
								<span class="font-bold text-slate-900 dark:text-white text-sm">
									{{ formatCurrency(ret.total_amount) }}
								</span>
							</div>
						</div>
					</div>
					<div v-else class="p-8 text-center text-xs text-slate-400">
						No returns processed against this order.
					</div>
				</template>
			</Card>
		</div>

		<!-- Cancellation Dialog -->
		<Dialog
			v-model:visible="cancelDialogVisible"
			modal
			header="Confirm Order Cancellation"
			:style="{ width: '32rem', maxWidth: '95vw' }"
			class="dark:!bg-slate-900 dark:!text-slate-100"
		>
			<div class="space-y-3 pt-2 text-xs">
				<p class="text-slate-600 dark:text-slate-300">
					Are you sure you want to cancel Order <strong>{{ order.order_number }}</strong>?
				</p>
				<p class="text-slate-500 dark:text-slate-400">
					This action will atomically reverse all inventory allocations for this order and mark any remaining balance as void.
				</p>
			</div>
			<template #footer>
				<div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/80">
					<Button label="Back" severity="secondary" text size="small" class="!text-xs !py-2 !px-3" @click="cancelDialogVisible = false" />
					<Button
						label="Cancel Order & Restore Stock"
						severity="danger"
						:loading="isCancelling"
						size="small"
						class="!text-xs !py-2 !px-4 !bg-rose-600 !border-rose-600"
						@click="executeCancellation"
					/>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<style scoped></style>