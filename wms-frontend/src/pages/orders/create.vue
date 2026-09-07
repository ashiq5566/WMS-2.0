<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue";
import { useRouter } from "vue-router";
import axios from "@/plugins/axios";
import moment from "moment";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Card from "primevue/card";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Dialog from "primevue/dialog";
import DatePicker from "primevue/datepicker";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import {
	calculateLineTotal,
	calculateGrossAmount,
	calculateNetAmount,
	calculateBalanceDue,
	formatCurrency,
	formatNumber,
} from "@/utils/orderCalculations";

interface SizeVariant {
	id: number;
	size: number;
	price: number;
	stock: number;
	is_available?: boolean;
}

interface ProductItem {
	id: number;
	product_id: string | null;
	name: string;
	unit: string | null;
	selling_price: number | null;
	price_at_time_of_purchase: number | null;
	image: string | null;
	qty_available: number;
	sizes: SizeVariant[];
}

interface Stakeholder {
	id: number;
	name: string;
	type: string;
	pending_amount?: number;
	mobile?: string;
	email?: string;
}

interface OrderLineItem {
	product: number;
	product_name: string;
	product_size: number;
	size: number;
	quantity: number;
	price_at_time_of_order: number;
	total: number;
	unit: string | null;
	stock: number;
}

const router = useRouter();
const toast = useToast();

// Order Header State
const selectedType = ref<"SO" | "PO">("SO");
const selectedStakeholder = ref<number | null>(null);
const orderDate = ref<Date>(new Date());
const orderNumber = ref("");
const orderNotes = ref("");

// Financial State
const discountAmount = ref<number>(0);
const downPayment = ref<number>(0);
const paymentMethod = ref("CASH");

// Items & Catalog State
const itemsData = ref<OrderLineItem[]>([]);
const products = ref<ProductItem[]>([]);
const stakeholders = ref<Stakeholder[]>([]);
const productSearch = ref("");
const isLoadingProducts = ref(true);
const isSubmitting = ref(false);
const formError = ref("");

// Size Variant Selection Dialog
const showSizeModal = ref(false);
const selectedProduct = ref<ProductItem | null>(null);
const selectedSizeVariant = ref<SizeVariant | null>(null);
const variantQuantity = ref(1);
const customVariantPrice = ref<number | null>(null);

// Order Review Dialog
const confirmModalVisible = ref(false);

const orderTypes = [
	{ label: "Sales Order (SO) - Customer Dispatch", value: "SO" },
	{ label: "Purchase Order (PO) - Supplier Inbound", value: "PO" },
];

const paymentMethods = [
	{ label: "Cash", value: "CASH" },
	{ label: "Bank Transfer", value: "BANK" },
	{ label: "Card", value: "CARD" },
	{ label: "Other / Credit", value: "OTHER" },
];

// Data Fetching
const fetchStakeholders = async () => {
	try {
		const targetType = selectedType.value === "SO" ? "Customer" : "Supplier";
		const response = await axios.get("/api/accounts/stakeholders/", {
			params: { type: targetType },
		});
		stakeholders.value = response.data || [];
	} catch (error) {
		console.error("Error loading stakeholders:", error);
	}
};

const fetchProducts = async () => {
	isLoadingProducts.value = true;
	try {
		const response = await axios.get("/api/inventory/products/");
		products.value = response.data || [];
	} catch (error) {
		console.error("Error loading products:", error);
		toast.add({ severity: "error", summary: "Catalog Error", detail: "Could not load products.", life: 3000 });
	} finally {
		isLoadingProducts.value = false;
	}
};

const generateOrderNumber = async () => {
	try {
		const response = await axios.get("/api/inventory/orders/");
		const allOrders = response.data || [];
		const matching = allOrders.filter((o: any) => o.order_type === selectedType.value);
		const count = matching.length + 1;
		const dateCode = moment().format("YYMM");
		orderNumber.value = `${selectedType.value}-${dateCode}-${String(count).padStart(3, "0")}`;
	} catch (error) {
		const randomHex = Math.random().toString(16).substring(2, 6).toUpperCase();
		orderNumber.value = `${selectedType.value}-${randomHex}`;
	}
};

// Filtered products catalog for selection
const filteredCatalog = computed(() => {
	let list = products.value;
	if (selectedType.value === "SO") {
		// For SO, prioritize items with stock
		list = list.filter((p) => (p.sizes && p.sizes.length > 0));
	}
	if (productSearch.value.trim()) {
		const q = productSearch.value.trim().toLowerCase();
		list = list.filter((p) =>
			p.name.toLowerCase().includes(q) ||
			(p.product_id && p.product_id.toLowerCase().includes(q))
		);
	}
	return list;
});

// Selected Stakeholder Object
const currentStakeholder = computed(() => {
	return stakeholders.value.find((s) => s.id === selectedStakeholder.value) || null;
});

// Computed Calculations
const grossAmount = computed(() => {
	return calculateGrossAmount(itemsData.value as any);
});

const netAmount = computed(() => {
	return calculateNetAmount(grossAmount.value, discountAmount.value);
});

const balanceDue = computed(() => {
	return calculateBalanceDue(netAmount.value, downPayment.value);
});

// Watch Order Type Changes
watch(selectedType, () => {
	selectedStakeholder.value = null;
	fetchStakeholders();
	generateOrderNumber();
});

onMounted(() => {
	fetchStakeholders();
	fetchProducts();
	generateOrderNumber();
});

// Size Variant Dialog Triggers
const openSizeSelector = (product: ProductItem) => {
	if (!selectedStakeholder.value) {
		toast.add({
			severity: "warn",
			summary: "Stakeholder Required",
			detail: `Please select a ${selectedType.value === 'SO' ? 'Customer' : 'Supplier'} before adding items.`,
			life: 3000,
		});
		return;
	}
	if (!product.sizes || product.sizes.length === 0) {
		toast.add({
			severity: "error",
			summary: "No Sizes Available",
			detail: `Product "${product.name}" has no registered size variants.`,
			life: 3000,
		});
		return;
	}

	selectedProduct.value = product;
	selectedSizeVariant.value = product.sizes[0] || null;
	variantQuantity.value = 1;
	customVariantPrice.value = selectedType.value === "SO"
		? (product.selling_price || selectedSizeVariant.value?.price || 0)
		: (selectedSizeVariant.value?.price || product.price_at_time_of_purchase || 0);
	showSizeModal.value = true;
};

// When changing size selection in modal, update price default
watch(selectedSizeVariant, (newSize) => {
	if (newSize && selectedProduct.value) {
		customVariantPrice.value = selectedType.value === "SO"
			? (selectedProduct.value.selling_price || newSize.price || 0)
			: (newSize.price || selectedProduct.value.price_at_time_of_purchase || 0);
	}
});

// Add Sized Item to Order
const addVariantToOrder = () => {
	if (!selectedProduct.value || !selectedSizeVariant.value) return;

	const qty = Math.max(1, Number(variantQuantity.value) || 1);
	const unitPrice = Math.max(0, Number(customVariantPrice.value) || 0);

	// Sales Order stock ceiling validation
	if (selectedType.value === "SO") {
		const existingItem = itemsData.value.find(
			(item) => item.product === selectedProduct.value!.id && item.size === selectedSizeVariant.value!.size
		);
		const existingQty = existingItem ? existingItem.quantity : 0;
		const totalRequested = existingQty + qty;

		if (selectedSizeVariant.value.stock < totalRequested) {
			toast.add({
				severity: "error",
				summary: "Insufficient Stock",
				detail: `Available: ${selectedSizeVariant.value.stock} units. You have ${existingQty} in order, requested ${qty} more.`,
				life: 4000,
			});
			return;
		}
	}

	const existingIndex = itemsData.value.findIndex(
		(item) => item.product === selectedProduct.value!.id && item.size === selectedSizeVariant.value!.size
	);

	if (existingIndex >= 0) {
		const item = itemsData.value[existingIndex];
		item.quantity += qty;
		item.price_at_time_of_order = unitPrice;
		item.total = calculateLineTotal(item.quantity, item.price_at_time_of_order);
	} else {
		itemsData.value.push({
			product: selectedProduct.value.id,
			product_name: selectedProduct.value.name,
			product_size: selectedSizeVariant.value.id,
			size: selectedSizeVariant.value.size,
			quantity: qty,
			price_at_time_of_order: unitPrice,
			total: calculateLineTotal(qty, unitPrice),
			unit: selectedProduct.value.unit,
			stock: selectedSizeVariant.value.stock,
		});
	}

	toast.add({
		severity: "success",
		summary: "Item Added",
		detail: `${selectedProduct.value.name} (Size ${selectedSizeVariant.value.size}) added to order.`,
		life: 2500,
	});

	showSizeModal.value = false;
	selectedProduct.value = null;
	selectedSizeVariant.value = null;
};

// Line Item Actions
const updateItemQuantity = (item: OrderLineItem, newQty: number) => {
	const val = Math.max(1, Number(newQty) || 1);
	if (selectedType.value === "SO" && val > item.stock) {
		toast.add({
			severity: "error",
			summary: "Stock Limit Reached",
			detail: `Maximum available stock for Size ${item.size} is ${item.stock} units.`,
			life: 3000,
		});
		item.quantity = item.stock;
	} else {
		item.quantity = val;
	}
	item.total = calculateLineTotal(item.quantity, item.price_at_time_of_order);
};

const updateItemPrice = (item: OrderLineItem, newPrice: number) => {
	item.price_at_time_of_order = Math.max(0, Number(newPrice) || 0);
	item.total = calculateLineTotal(item.quantity, item.price_at_time_of_order);
};

const removeLineItem = (index: number) => {
	const removed = itemsData.value[index];
	itemsData.value.splice(index, 1);
	toast.add({
		severity: "info",
		summary: "Item Removed",
		detail: `${removed.product_name} (Size ${removed.size}) removed.`,
		life: 2500,
	});
};

// Order Submission
const openConfirmationModal = () => {
	formError.value = "";
	if (!selectedStakeholder.value) {
		formError.value = `Please select a ${selectedType.value === 'SO' ? 'Customer' : 'Supplier'}.`;
		return;
	}
	if (itemsData.value.length === 0) {
		formError.value = "Your order must have at least one line item.";
		return;
	}
	if (discountAmount.value > grossAmount.value) {
		formError.value = "Discount cannot exceed the gross order amount.";
		return;
	}
	if (downPayment.value > netAmount.value) {
		formError.value = "Down payment cannot exceed the net order amount.";
		return;
	}
	confirmModalVisible.value = true;
};

const submitOrder = async () => {
	isSubmitting.value = true;
	formError.value = "";

	try {
		const orderPayload = {
			order_number: orderNumber.value.trim() || undefined,
			order_type: selectedType.value,
			stakeholder: selectedStakeholder.value,
			gross_amount: Math.round(grossAmount.value),
			discount: Math.round(discountAmount.value),
			net_amount: Math.round(netAmount.value),
			order_date: moment(orderDate.value).toISOString(),
		};

		const itemsPayload = itemsData.value.map((item) => ({
			product: item.product,
			product_size: item.product_size,
			quantity: item.quantity,
			price_at_time_of_order: item.price_at_time_of_order,
			total: item.total,
		}));

		const response = await axios.post("/api/inventory/orders/", {
			order: orderPayload,
			items: itemsPayload,
		});

		const createdOrder = response.data.order;

		// If initial down payment recorded, post payment settlement
		if (downPayment.value > 0 && createdOrder.id) {
			try {
				await axios.post("/api/inventory/payments/", {
					order: createdOrder.id,
					company: createdOrder.stakeholder,
					amount: Math.round(downPayment.value),
					payment_date: orderPayload.order_date,
					payment_method: paymentMethod.value,
				});
			} catch (payErr) {
				console.error("Down payment registration warning:", payErr);
			}
		}

		toast.add({
			severity: "success",
			summary: "Order Confirmed",
			detail: `${selectedType.value === 'SO' ? 'Sales Order' : 'Purchase Order'} #${createdOrder.order_number || createdOrder.id} created successfully.`,
			life: 3500,
		});

		confirmModalVisible.value = false;
		router.push({ name: "orders" });
	} catch (err: any) {
		console.error("Order creation error:", err);
		const msg = err.response?.data?.error || err.response?.data?.detail || err.message || "Failed to create order.";
		formError.value = msg;
		toast.add({ severity: "error", summary: "Order Failed", detail: msg, life: 4000 });
	} finally {
		isSubmitting.value = false;
	}
};
</script>

<template>
	<div class="space-y-6 pb-16 text-slate-800 dark:text-slate-100">
		<!-- Header & Navigation -->
		<div
			class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm transition-colors"
		>
			<div class="flex items-center gap-3">
				<router-link :to="{ name: 'orders' }">
					<Button
						icon="pi pi-arrow-left"
						severity="secondary"
						text
						rounded
						size="small"
						class="!w-9 !h-9 hover:!bg-slate-100 dark:hover:!bg-slate-800"
					/>
				</router-link>
				<div>
					<div class="flex items-center gap-2 mb-0.5">
						<Tag
							:severity="selectedType === 'SO' ? 'success' : 'info'"
							:value="selectedType === 'SO' ? 'Sales Pipeline' : 'Procurement Intake'"
							class="!text-[10px] !px-2 !py-0.2"
						/>
						<span class="text-xs text-slate-400">• New Commercial Transaction</span>
					</div>
					<h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
						Create {{ selectedType === 'SO' ? 'Sales Order (SO)' : 'Purchase Order (PO)' }}
					</h1>
				</div>
			</div>

			<!-- Order Type Switcher -->
			<div class="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
				<button
					type="button"
					class="text-xs font-bold py-1.5 px-3 rounded-lg transition-all"
					:class="selectedType === 'SO' ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'"
					@click="selectedType = 'SO'"
				>
					<i class="pi pi-arrow-up-right mr-1"></i> Sales Order (SO)
				</button>
				<button
					type="button"
					class="text-xs font-bold py-1.5 px-3 rounded-lg transition-all"
					:class="selectedType === 'PO' ? 'bg-white dark:bg-slate-900 text-purple-600 dark:text-purple-400 shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'"
					@click="selectedType = 'PO'"
				>
					<i class="pi pi-truck mr-1"></i> Purchase Order (PO)
				</button>
			</div>
		</div>

		<!-- Error Banner -->
		<Message v-if="formError" severity="error" :closable="true" @close="formError = ''" class="!text-xs">
			{{ formError }}
		</Message>

		<!-- Order Metadata Form Card -->
		<div class="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm space-y-4">
			<h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
				1. Order Master Details
			</h2>
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
				<!-- Stakeholder -->
				<div class="space-y-1">
					<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
						{{ selectedType === 'SO' ? 'Customer' : 'Supplier' }} <span class="text-rose-500">*</span>
					</label>
					<Select
						v-model="selectedStakeholder"
						:options="stakeholders"
						optionLabel="name"
						optionValue="id"
						:placeholder="`Select ${selectedType === 'SO' ? 'Customer' : 'Supplier'}`"
						filter
						class="w-full !text-xs !py-0.5 dark:!bg-slate-800 dark:!border-slate-700"
					/>
				</div>

				<!-- Order Number -->
				<div class="space-y-1">
					<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
						Order Number
					</label>
					<InputText
						v-model="orderNumber"
						placeholder="Auto-generated"
						class="w-full !text-xs !py-2 font-mono dark:!bg-slate-800 dark:!border-slate-700"
					/>
				</div>

				<!-- Order Date -->
				<div class="space-y-1">
					<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
						Order Date <span class="text-rose-500">*</span>
					</label>
					<DatePicker
						v-model="orderDate"
						showIcon
						dateFormat="dd/mm/yy"
						class="w-full !text-xs dark:!bg-slate-800 dark:!border-slate-700"
					/>
				</div>

				<!-- Stakeholder Info Badge -->
				<div class="space-y-1">
					<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
						Directory Profile
					</label>
					<div class="h-9 px-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-200/80 dark:border-slate-700 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
						<span v-if="currentStakeholder">
							Balance: <strong class="text-amber-600">{{ formatCurrency(currentStakeholder.pending_amount) }}</strong>
						</span>
						<span v-else class="text-slate-400 italic">Select stakeholder above</span>
						<i class="pi pi-user-check text-slate-400"></i>
					</div>
				</div>
			</div>
		</div>

		<!-- Workspace: Catalog & Order Basket Split -->
		<div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
			<!-- Left: Product Catalog (5 cols) -->
			<div class="lg:col-span-5 space-y-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
				<div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
					<h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
						2. Select Items & Size Variants
					</h2>
					<span class="text-xs text-slate-400">{{ filteredCatalog.length }} Products</span>
				</div>

				<!-- Search Input -->
				<IconField iconPosition="left" class="w-full">
					<InputIcon class="pi pi-search text-slate-400" />
					<InputText
						v-model="productSearch"
						placeholder="Search SKU, product name..."
						class="w-full !text-xs !py-2 dark:!bg-slate-800 dark:!border-slate-700"
					/>
				</IconField>

				<!-- Catalog Scrollable List -->
				<div class="max-h-[500px] overflow-y-auto space-y-2.5 pr-1">
					<div v-if="isLoadingProducts" class="space-y-2">
						<div v-for="n in 4" :key="n" class="p-3 border rounded-xl flex gap-3">
							<Skeleton width="48px" height="48px" class="rounded-lg" />
							<div class="flex-1 space-y-2">
								<Skeleton width="60%" height="16px" />
								<Skeleton width="30%" height="12px" />
							</div>
						</div>
					</div>

					<div
						v-for="product in filteredCatalog"
						:key="product.id"
						class="p-3 bg-slate-50/70 dark:bg-slate-800/40 rounded-xl border border-slate-200/60 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-500 transition-all flex items-center justify-between gap-3"
					>
						<!-- Product Info -->
						<div class="flex items-center gap-3 min-w-0">
							<img
								v-if="product.image"
								:src="product.image"
								:alt="product.name"
								class="w-12 h-12 rounded-lg object-cover border border-slate-200 dark:border-slate-700 shrink-0"
							/>
							<div
								v-else
								class="w-12 h-12 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-400 shrink-0"
							>
								<i class="pi pi-box"></i>
							</div>

							<div class="min-w-0">
								<div class="font-bold text-xs text-slate-900 dark:text-white truncate">
									{{ product.name }}
								</div>
								<div class="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
									<span class="font-mono">{{ product.product_id || `PR-${product.id}` }}</span>
									<span>•</span>
									<span :class="product.qty_available > 0 ? 'text-emerald-600 dark:text-emerald-400 font-semibold' : 'text-rose-500 font-semibold'">
										{{ product.qty_available }} in stock
									</span>
								</div>
							</div>
						</div>

						<!-- Action Button -->
						<Button
							label="Add"
							icon="pi pi-plus"
							size="small"
							severity="secondary"
							outlined
							class="!text-xs !py-1.5 !px-3 shrink-0 !rounded-lg !border-indigo-200 dark:!border-indigo-800 !text-indigo-600 dark:!text-indigo-400 hover:!bg-indigo-50 dark:hover:!bg-indigo-950/40"
							@click="openSizeSelector(product)"
						/>
					</div>

					<div v-if="!isLoadingProducts && filteredCatalog.length === 0" class="p-8 text-center text-xs text-slate-400">
						No products found matching criteria.
					</div>
				</div>
			</div>

			<!-- Right: Order Line Items & Financials (7 cols) -->
			<div class="lg:col-span-7 space-y-5 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
				<div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
					<h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
						3. Order Line Items ({{ itemsData.length }})
					</h2>
					<span v-if="itemsData.length > 0" class="text-xs font-semibold text-slate-700 dark:text-slate-300">
						Gross: {{ formatCurrency(grossAmount) }}
					</span>
				</div>

				<!-- Line Items Table -->
				<div v-if="itemsData.length > 0" class="overflow-x-auto border border-slate-200/80 dark:border-slate-800 rounded-xl">
					<table class="w-full text-xs text-left">
						<thead class="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold border-b border-slate-200/80 dark:border-slate-800">
							<tr>
								<th class="p-2.5">Product & Size</th>
								<th class="p-2.5 w-28">Quantity</th>
								<th class="p-2.5 w-28">Rate (₹)</th>
								<th class="p-2.5 text-right w-24">Subtotal</th>
								<th class="p-2.5 text-center w-10"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
							<tr v-for="(item, idx) in itemsData" :key="idx" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
								<td class="p-2.5">
									<div class="font-bold text-slate-900 dark:text-white">{{ item.product_name }}</div>
									<div class="flex items-center gap-1.5 mt-0.5">
										<Tag severity="secondary" :value="`Size ${item.size}`" class="!text-[10px] !px-1.5 !py-0.1" />
										<span v-if="selectedType === 'SO'" class="text-[10px] text-slate-400">
											(Avail: {{ item.stock }})
										</span>
									</div>
								</td>
								<td class="p-2.5">
									<InputNumber
										v-model="item.quantity"
										:min="1"
										:max="selectedType === 'SO' ? item.stock : 99999"
										fluid
										class="!text-xs"
										inputClass="w-full min-w-0 !py-1 !px-2 !text-xs rounded-lg dark:!bg-slate-800"
										@update:modelValue="updateItemQuantity(item, $event)"
									/>
								</td>
								<td class="p-2.5">
									<InputNumber
										v-model="item.price_at_time_of_order"
										:min="0"
										fluid
										class="!text-xs"
										inputClass="w-full min-w-0 !py-1 !px-2 !text-xs rounded-lg dark:!bg-slate-800"
										@update:modelValue="updateItemPrice(item, $event)"
									/>
								</td>
								<td class="p-2.5 text-right font-bold text-slate-900 dark:text-white">
									{{ formatCurrency(item.total) }}
								</td>
								<td class="p-2.5 text-center">
									<Button
										icon="pi pi-trash"
										severity="danger"
										text
										rounded
										size="small"
										class="!w-7 !h-7 !p-0 text-rose-500 hover:!bg-rose-50"
										@click="removeLineItem(idx)"
									/>
								</td>
							</tr>
						</tbody>
					</table>
				</div>

				<div v-else class="p-8 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center space-y-2">
					<div class="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
						<i class="pi pi-shopping-cart"></i>
					</div>
					<p class="text-xs text-slate-500 dark:text-slate-400">
						Order basket is empty. Select products from the left catalog to add sized line items.
					</p>
				</div>

				<!-- Section 4: Settlement & Totals -->
				<div class="pt-4 border-t border-slate-100 dark:border-slate-800/80 space-y-4">
					<h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
						4. Commercial Settlement
					</h2>

					<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
						<!-- Discount Input -->
						<div class="space-y-1">
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300">
								Discount (₹)
							</label>
							<InputNumber
								v-model="discountAmount"
								:min="0"
								:max="grossAmount"
								fluid
								placeholder="0"
								class="!text-xs"
								inputClass="w-full min-w-0 !py-1.5 !px-2.5 !text-xs rounded-lg dark:!bg-slate-800"
							/>
						</div>

						<!-- Initial Down Payment -->
						<div class="space-y-1">
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300">
								Down Payment (₹)
							</label>
							<InputNumber
								v-model="downPayment"
								:min="0"
								:max="netAmount"
								fluid
								placeholder="0"
								class="!text-xs"
								inputClass="w-full min-w-0 !py-1.5 !px-2.5 !text-xs rounded-lg dark:!bg-slate-800"
							/>
						</div>

						<!-- Payment Method -->
						<div class="space-y-1">
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300">
								Payment Mode
							</label>
							<Select
								v-model="paymentMethod"
								:options="paymentMethods"
								optionLabel="label"
								optionValue="value"
								class="w-full !text-xs !py-0.5 dark:!bg-slate-800"
							/>
						</div>
					</div>

					<!-- Financial Summary Bar -->
					<div class="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/80 dark:border-slate-800 space-y-2 text-xs">
						<div class="flex justify-between text-slate-600 dark:text-slate-400">
							<span>Gross Subtotal:</span>
							<span class="font-semibold text-slate-900 dark:text-white">{{ formatCurrency(grossAmount) }}</span>
						</div>
						<div class="flex justify-between text-slate-600 dark:text-slate-400">
							<span>Discount:</span>
							<span class="font-semibold text-rose-500">- {{ formatCurrency(discountAmount) }}</span>
						</div>
						<div class="flex justify-between text-slate-900 dark:text-white font-bold text-sm pt-1 border-t border-slate-200 dark:border-slate-700">
							<span>Net Payable Amount:</span>
							<span class="text-indigo-600 dark:text-indigo-400">{{ formatCurrency(netAmount) }}</span>
						</div>
						<div class="flex justify-between text-slate-600 dark:text-slate-400 pt-1">
							<span>Initial Down Payment:</span>
							<span class="font-semibold text-emerald-600 dark:text-emerald-400">{{ formatCurrency(downPayment) }}</span>
						</div>
						<div class="flex justify-between font-bold text-xs pt-1 border-t border-slate-200/60 dark:border-slate-700/60">
							<span class="text-amber-600 dark:text-amber-400">Remaining Balance Due:</span>
							<span class="text-amber-600 dark:text-amber-400">{{ formatCurrency(balanceDue) }}</span>
						</div>
					</div>

					<!-- Submit Button -->
					<div class="flex items-center justify-end gap-3 pt-2">
						<router-link :to="{ name: 'orders' }">
							<Button label="Cancel" severity="secondary" text class="!text-xs !py-2 !px-4" />
						</router-link>
						<Button
							label="Review & Confirm Order"
							icon="pi pi-check"
							severity="primary"
							:disabled="itemsData.length === 0 || !selectedStakeholder"
							class="!text-xs !py-2 !px-5 !bg-indigo-600 hover:!bg-indigo-700 !border-indigo-600 shadow-sm"
							@click="openConfirmationModal"
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- Modal 1: Select Size Variant Dialog -->
		<Dialog
			v-model:visible="showSizeModal"
			modal
			:header="`Select Variant: ${selectedProduct?.name}`"
			:style="{ width: '36rem', maxWidth: '95vw' }"
			class="dark:!bg-slate-900 dark:!text-slate-100"
		>
			<div v-if="selectedProduct" class="space-y-4 pt-2">
				<div class="space-y-2">
					<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
						Available Sizes
					</label>
					<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
						<div
							v-for="size in selectedProduct.sizes"
							:key="size.id || size.size"
							class="p-2.5 rounded-xl border text-xs cursor-pointer transition-all flex flex-col justify-between"
							:class="selectedSizeVariant?.id === size.id ? 'border-indigo-600 bg-indigo-50/60 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-bold' : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40'"
							@click="selectedSizeVariant = size"
						>
							<div class="flex justify-between items-center">
								<span>Size {{ size.size }}</span>
								<span v-if="selectedSizeVariant?.id === size.id" class="text-indigo-600">✓</span>
							</div>
							<div class="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
								Stock: <strong :class="size.stock > 0 ? 'text-slate-800 dark:text-slate-200' : 'text-rose-500'">{{ size.stock }}</strong>
							</div>
						</div>
					</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<!-- Quantity Input -->
					<div class="space-y-1">
						<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300">
							Quantity <span v-if="selectedType === 'SO'" class="text-slate-400">(Max: {{ selectedSizeVariant?.stock || 0 }})</span>
						</label>
						<InputNumber
							v-model="variantQuantity"
							:min="1"
							:max="selectedType === 'SO' ? (selectedSizeVariant?.stock || 1) : 99999"
							fluid
							class="!text-xs"
							inputClass="w-full min-w-0 !py-2 !px-2.5 !text-xs rounded-lg dark:!bg-slate-800"
						/>
					</div>

					<!-- Unit Rate -->
					<div class="space-y-1">
						<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300">
							Unit Rate (₹)
						</label>
						<InputNumber
							v-model="customVariantPrice"
							:min="0"
							fluid
							class="!text-xs"
							inputClass="w-full min-w-0 !py-2 !px-2.5 !text-xs rounded-lg dark:!bg-slate-800"
						/>
					</div>
				</div>

				<!-- Live Subtotal -->
				<div class="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl text-xs flex justify-between items-center">
					<span class="text-slate-500">Line Subtotal:</span>
					<span class="text-base font-bold text-slate-900 dark:text-white">
						{{ formatCurrency((variantQuantity || 1) * (customVariantPrice || 0)) }}
					</span>
				</div>
			</div>

			<template #footer>
				<div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/80">
					<Button label="Cancel" severity="secondary" text size="small" class="!text-xs !py-2 !px-3" @click="showSizeModal = false" />
					<Button
						label="Add to Order"
						icon="pi pi-check"
						severity="primary"
						size="small"
						:disabled="!selectedSizeVariant || (selectedType === 'SO' && (selectedSizeVariant.stock || 0) <= 0)"
						class="!text-xs !py-2 !px-4 !bg-indigo-600 hover:!bg-indigo-700 !border-indigo-600"
						@click="addVariantToOrder"
					/>
				</div>
			</template>
		</Dialog>

		<!-- Modal 2: Review & Finalize Confirmation Dialog -->
		<Dialog
			v-model:visible="confirmModalVisible"
			modal
			header="Review & Confirm Order"
			:style="{ width: '42rem', maxWidth: '95vw' }"
			class="dark:!bg-slate-900 dark:!text-slate-100"
		>
			<div class="space-y-4 pt-2 text-xs">
				<div class="grid grid-cols-2 gap-3 p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/80 dark:border-slate-800">
					<div>
						<span class="text-slate-400">Order Number:</span>
						<strong class="block font-mono text-slate-900 dark:text-white">{{ orderNumber }}</strong>
					</div>
					<div>
						<span class="text-slate-400">Transaction Type:</span>
						<strong class="block text-slate-900 dark:text-white">{{ selectedType === 'SO' ? 'Sales Order' : 'Purchase Order' }}</strong>
					</div>
					<div>
						<span class="text-slate-400">Stakeholder:</span>
						<strong class="block text-slate-900 dark:text-white">{{ currentStakeholder?.name }}</strong>
					</div>
					<div>
						<span class="text-slate-400">Order Date:</span>
						<strong class="block text-slate-900 dark:text-white">{{ moment(orderDate).format('DD MMM YYYY') }}</strong>
					</div>
				</div>

				<!-- Items Preview Table -->
				<div class="max-h-48 overflow-y-auto border border-slate-200/80 dark:border-slate-800 rounded-xl">
					<table class="w-full text-left">
						<thead class="bg-slate-50 dark:bg-slate-800 font-semibold text-slate-600 dark:text-slate-300">
							<tr>
								<th class="p-2">Item</th>
								<th class="p-2 text-center">Qty</th>
								<th class="p-2 text-right">Rate</th>
								<th class="p-2 text-right">Total</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
							<tr v-for="(it, i) in itemsData" :key="i">
								<td class="p-2">
									{{ it.product_name }} <span class="text-slate-400">(Sz {{ it.size }})</span>
								</td>
								<td class="p-2 text-center">{{ it.quantity }}</td>
								<td class="p-2 text-right">{{ formatCurrency(it.price_at_time_of_order) }}</td>
								<td class="p-2 text-right font-semibold">{{ formatCurrency(it.total) }}</td>
							</tr>
						</tbody>
					</table>
				</div>

				<!-- Settlement Summary -->
				<div class="p-3 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 rounded-xl space-y-1">
					<div class="flex justify-between">
						<span>Net Payable Amount:</span>
						<strong class="text-indigo-600 dark:text-indigo-400">{{ formatCurrency(netAmount) }}</strong>
					</div>
					<div v-if="downPayment > 0" class="flex justify-between">
						<span>Down Payment ({{ paymentMethod }}):</span>
						<strong class="text-emerald-600 dark:text-emerald-400">{{ formatCurrency(downPayment) }}</strong>
					</div>
					<div class="flex justify-between pt-1 border-t border-indigo-100 dark:border-indigo-900/60 font-bold">
						<span>Remaining Pending Due:</span>
						<span class="text-amber-600 dark:text-amber-400">{{ formatCurrency(balanceDue) }}</span>
					</div>
				</div>
			</div>

			<template #footer>
				<div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/80">
					<Button label="Back" severity="secondary" text size="small" class="!text-xs !py-2 !px-3.5" @click="confirmModalVisible = false" />
					<Button
						label="Confirm & Dispatch Order"
						icon="pi pi-check"
						severity="primary"
						:loading="isSubmitting"
						size="small"
						class="!text-xs !py-2 !px-4 !bg-indigo-600 hover:!bg-indigo-700 !border-indigo-600"
						@click="submitOrder"
					/>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<style scoped></style>