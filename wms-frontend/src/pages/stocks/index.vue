<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch, computed } from "vue";
import axios from "@/plugins/axios";
import { debounce } from "lodash";
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
import Skeleton from "primevue/skeleton";
import AddProductModal from "@/components/products/AddProductModal.vue";

interface SizeVariant {
	id?: number;
	size: number;
	price: number;
	stock: number;
	is_available: boolean;
}

interface ProductItem {
	id: number;
	product_id: string | null;
	name: string;
	unit: string | null;
	selling_price: number | null;
	price_at_time_of_purchase: number | null;
	status: boolean;
	image: string | null;
	description: string | null;
	sizes: SizeVariant[];
	qty_available: number;
}

const products = ref<ProductItem[]>([]);
const searchInput = ref("");
const editingRows = ref([]);
const isLoading = ref(true);
const isRefreshing = ref(false);
const toast = useToast();

// Filter states
const selectedStockStatus = ref("ALL");
const selectedUnit = ref("ALL");
const selectedActiveStatus = ref("ALL");

// Modals
const selectedProductForSizes = ref<ProductItem | null>(null);
const sizeModalVisible = ref(false);
const previewImage = ref<{ url: string; title: string } | null>(null);

const stockStatusOptions = [
	{ label: "All Stock Levels", value: "ALL" },
	{ label: "In Stock (> 10)", value: "IN_STOCK" },
	{ label: "Low Stock (1 - 10)", value: "LOW_STOCK" },
	{ label: "Out of Stock (0)", value: "OUT_OF_STOCK" },
];

const unitOptions = [
	{ label: "All Units", value: "ALL" },
	{ label: "Pieces (Pcs)", value: "Pieces" },
	{ label: "Kilograms (Kg)", value: "Kilograms" },
	{ label: "Sets", value: "Sets" },
];

const activeStatusOptions = [
	{ label: "All Statuses", value: "ALL" },
	{ label: "Active Only", value: "ACTIVE" },
	{ label: "Inactive Only", value: "INACTIVE" },
];

const statusDropdownOptions = [
	{ label: "Active", value: true },
	{ label: "Inactive", value: false },
];

// Formatting helpers
const formatNumber = (val: number | null | undefined): string => {
	if (val == null || isNaN(val)) return "0";
	return new Intl.NumberFormat("en-IN").format(val);
};

const formatCurrency = (val: number | null | undefined): string => {
	if (val == null || isNaN(val)) return "₹0";
	return new Intl.NumberFormat("en-IN", {
		style: "currency",
		currency: "INR",
		maximumFractionDigits: 0,
	}).format(val);
};

// API calls
const fetchProducts = async (search = searchInput.value) => {
	try {
		const response = await axios.get("/api/inventory/products/", {
			params: {
				search: search.trim() || undefined,
			},
		});
		products.value = response.data || [];
	} catch (error) {
		console.error("Error fetching products:", error);
		toast.add({
			severity: "error",
			summary: "Load Failed",
			detail: "Unable to load warehouse inventory. Please refresh.",
			life: 3500,
		});
	} finally {
		isLoading.value = false;
		isRefreshing.value = false;
	}
};

const reloadTable = () => {
	fetchProducts(searchInput.value);
};

const refreshData = async () => {
	isRefreshing.value = true;
	await fetchProducts(searchInput.value);
	toast.add({
		severity: "info",
		summary: "Refreshed",
		detail: "Inventory data updated.",
		life: 2000,
	});
};

const debouncedFetchProducts = debounce(fetchProducts, 350);

watch(searchInput, (newVal) => {
	debouncedFetchProducts(newVal);
});

onBeforeUnmount(() => {
	debouncedFetchProducts.cancel();
});

onMounted(() => {
	fetchProducts();
});

// Row inline edit save
const onRowEditSave = async (event: any) => {
	const product = event.newData as ProductItem;
	try {
		const payload = {
			name: product.name,
			selling_price: product.selling_price,
			price_at_time_of_purchase: product.price_at_time_of_purchase,
			status: product.status,
			unit: product.unit,
		};
		await axios.put(`/api/inventory/products/${product.id}/`, payload);
		toast.add({
			severity: "success",
			summary: "Product Updated",
			detail: `"${product.name}" saved successfully.`,
			life: 3000,
		});
		fetchProducts();
	} catch (error) {
		console.error("Error updating product:", error);
		toast.add({
			severity: "error",
			summary: "Update Failed",
			detail: "Product edits could not be saved.",
			life: 3500,
		});
		fetchProducts();
	}
};

// Client-side filtering on the fetched dataset
const filteredProducts = computed(() => {
	return products.value.filter((p) => {
		// Stock status filter
		if (selectedStockStatus.value === "IN_STOCK" && p.qty_available <= 10) return false;
		if (selectedStockStatus.value === "LOW_STOCK" && (p.qty_available <= 0 || p.qty_available > 10)) return false;
		if (selectedStockStatus.value === "OUT_OF_STOCK" && p.qty_available > 0) return false;

		// Unit filter
		if (selectedUnit.value !== "ALL" && p.unit !== selectedUnit.value) return false;

		// Active status filter
		if (selectedActiveStatus.value === "ACTIVE" && !p.status) return false;
		if (selectedActiveStatus.value === "INACTIVE" && p.status) return false;

		return true;
	});
});

const isFilterActive = computed(() => {
	return (
		searchInput.value.trim() !== "" ||
		selectedStockStatus.value !== "ALL" ||
		selectedUnit.value !== "ALL" ||
		selectedActiveStatus.value !== "ALL"
	);
});

const resetFilters = () => {
	searchInput.value = "";
	selectedStockStatus.value = "ALL";
	selectedUnit.value = "ALL";
	selectedActiveStatus.value = "ALL";
	fetchProducts("");
};

// Executive KPI Metrics
const totalCatalogCount = computed(() => products.value.length);
const activeCatalogCount = computed(() => products.value.filter((p) => p.status).length);

const totalOnHandUnits = computed(() => {
	return products.value.reduce((acc, p) => acc + (p.qty_available || 0), 0);
});

const totalCostValuation = computed(() => {
	return products.value.reduce((acc, p) => {
		const cost = p.price_at_time_of_purchase || 0;
		return acc + (p.qty_available || 0) * cost;
	}, 0);
});

const totalRetailValuation = computed(() => {
	return products.value.reduce((acc, p) => {
		const price = p.selling_price || 0;
		return acc + (p.qty_available || 0) * price;
	}, 0);
});

const lowStockCount = computed(() => {
	return products.value.filter((p) => p.qty_available > 0 && p.qty_available <= 10).length;
});

const outOfStockCount = computed(() => {
	return products.value.filter((p) => (p.qty_available || 0) <= 0).length;
});

const healthyStockCount = computed(() => {
	return products.value.filter((p) => (p.qty_available || 0) > 10).length;
});

// Modal inspection triggers
const openSizeBreakdown = (product: ProductItem) => {
	selectedProductForSizes.value = product;
	sizeModalVisible.value = true;
};

const openImagePreview = (url: string, title: string) => {
	previewImage.value = { url, title };
};

// Calculate gross margin %
const calculateMargin = (cost: number | null, selling: number | null) => {
	if (!cost || !selling || selling <= 0) return null;
	const margin = ((selling - cost) / selling) * 100;
	return Math.round(margin);
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
						Inventory & Stock Control
					</span>
				</div>
				<h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
					Warehouse Stocks
				</h1>
				<p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
					Real-time SKU catalog, on-hand valuations, size breakdowns, and instant price adjustments
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
				<AddProductModal @instance-added="reloadTable" />
			</div>
		</div>

		<!-- Executive KPI Cards -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- Card 1: Total SKUs -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex items-center justify-between"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Catalog SKUs
					</span>
					<div class="text-2xl font-bold text-slate-900 dark:text-white">
						{{ formatNumber(totalCatalogCount) }}
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400">
						<span class="text-emerald-600 dark:text-emerald-400 font-semibold">{{ activeCatalogCount }}</span> Active items
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xl shadow-inner"
				>
					<i class="pi pi-box"></i>
				</div>
			</div>

			<!-- Card 2: Total On-Hand Stock -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex items-center justify-between"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Total On-Hand Units
					</span>
					<div class="text-2xl font-bold text-slate-900 dark:text-white">
						{{ formatNumber(totalOnHandUnits) }}
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400">
						Across all size variants
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400 flex items-center justify-center text-xl shadow-inner"
				>
					<i class="pi pi-warehouse"></i>
				</div>
			</div>

			<!-- Card 3: Inventory Valuation -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex items-center justify-between"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Cost Valuation
					</span>
					<div class="text-2xl font-bold text-slate-900 dark:text-white">
						{{ formatCurrency(totalCostValuation) }}
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400">
						Retail: <span class="font-medium text-slate-700 dark:text-slate-300">{{ formatCurrency(totalRetailValuation) }}</span>
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xl shadow-inner"
				>
					<i class="pi pi-wallet"></i>
				</div>
			</div>

			<!-- Card 4: Stock Health Status -->
			<div
				class="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm flex items-center justify-between"
			>
				<div class="space-y-1">
					<span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
						Stock Health
					</span>
					<div class="flex items-center gap-2 pt-1">
						<Tag severity="success" :value="`${healthyStockCount} In Stock`" class="!text-[10px] !px-1.5 !py-0.5" />
						<Tag v-if="lowStockCount > 0" severity="warn" :value="`${lowStockCount} Low`" class="!text-[10px] !px-1.5 !py-0.5" />
						<Tag v-if="outOfStockCount > 0" severity="danger" :value="`${outOfStockCount} Out`" class="!text-[10px] !px-1.5 !py-0.5" />
					</div>
					<div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
						{{ lowStockCount + outOfStockCount > 0 ? 'Requires attention / restock' : 'All inventory levels optimal' }}
					</div>
				</div>
				<div
					class="w-12 h-12 rounded-xl flex items-center justify-center text-xl shadow-inner"
					:class="lowStockCount + outOfStockCount > 0 ? 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400' : 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400'"
				>
					<i :class="lowStockCount + outOfStockCount > 0 ? 'pi pi-exclamation-triangle' : 'pi pi-check-circle'"></i>
				</div>
			</div>
		</div>

		<!-- Main Inventory Table Card -->
		<div class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm rounded-2xl p-5 overflow-hidden">
				<!-- Filters and Search Toolbar -->
				<div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-5 border-b border-slate-100 dark:border-slate-800/80">
					<!-- Search Input -->
					<div class="w-full lg:w-80">
						<IconField iconPosition="left" class="w-full">
							<InputIcon class="pi pi-search text-slate-400" />
							<InputText
								v-model="searchInput"
								placeholder="Search product name, ID..."
								class="w-full !text-xs !py-2 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700"
							/>
						</IconField>
					</div>

					<!-- Filter Controls -->
					<div class="flex flex-wrap items-center gap-2.5">
						<!-- Stock Level Filter -->
						<Select
							v-model="selectedStockStatus"
							:options="stockStatusOptions"
							optionLabel="label"
							optionValue="value"
							class="!text-xs !py-0.5 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 min-w-[150px]"
						/>

						<!-- Unit Filter -->
						<Select
							v-model="selectedUnit"
							:options="unitOptions"
							optionLabel="label"
							optionValue="value"
							class="!text-xs !py-0.5 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 min-w-[130px]"
						/>

						<!-- Active Status Filter -->
						<Select
							v-model="selectedActiveStatus"
							:options="activeStatusOptions"
							optionLabel="label"
							optionValue="value"
							class="!text-xs !py-0.5 !rounded-lg dark:!bg-slate-800 dark:!border-slate-700 min-w-[130px]"
						/>

						<!-- Reset Filters -->
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
						<Skeleton width="48px" height="48px" class="rounded-lg dark:!bg-slate-800" />
						<div class="flex-1 space-y-2">
							<Skeleton width="30%" height="16px" class="dark:!bg-slate-800" />
							<Skeleton width="20%" height="12px" class="dark:!bg-slate-800" />
						</div>
						<Skeleton width="80px" height="20px" class="dark:!bg-slate-800" />
						<Skeleton width="80px" height="20px" class="dark:!bg-slate-800" />
						<Skeleton width="60px" height="24px" class="dark:!bg-slate-800" />
					</div>
				</div>

				<!-- Inventory DataTable -->
				<DataTable
					v-else
					v-model:editingRows="editingRows"
					:value="filteredProducts"
					editMode="row"
					dataKey="id"
					:paginator="true"
					:rows="10"
					:rowsPerPageOptions="[10, 20, 50]"
					paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
					currentPageReportTemplate="{first} to {last} of {totalRecords} products"
					responsiveLayout="scroll"
					@row-edit-save="onRowEditSave"
					class="pt-2"
				>
					<!-- Column 1: ID -->
					<Column field="product_id" header="SKU / ID" :sortable="true" style="width: 100px">
						<template #body="{ data }">
							<span class="font-mono text-xs font-semibold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
								{{ data.product_id || `PR-${data.id}` }}
							</span>
						</template>
					</Column>

					<!-- Column 2: Image -->
					<Column header="Image" style="width: 76px">
						<template #body="{ data }">
							<div
								v-if="data.image"
								class="relative w-12 h-12 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 group cursor-pointer shadow-sm"
								@click="openImagePreview(data.image, data.name)"
							>
								<img :src="data.image" :alt="data.name" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-200" />
								<div class="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs">
									<i class="pi pi-search-plus"></i>
								</div>
							</div>
							<div
								v-else
								class="w-12 h-12 rounded-lg bg-slate-100 dark:bg-slate-800 border border-dashed border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-400"
							>
								<i class="pi pi-image text-lg"></i>
							</div>
						</template>
					</Column>

					<!-- Column 3: Name & Specs -->
					<Column field="name" header="Product Details" :sortable="true" style="min-width: 200px">
						<template #body="{ data }">
							<div class="space-y-0.5">
								<div class="font-semibold text-slate-900 dark:text-white text-sm">
									{{ data.name }}
								</div>
								<div class="flex items-center gap-2">
									<span v-if="data.unit" class="text-[11px] font-medium text-slate-500 dark:text-slate-400">
										{{ data.unit }}
									</span>
									<span v-if="data.description" class="text-[11px] text-slate-400 dark:text-slate-500 truncate max-w-[200px]" :title="data.description">
										• {{ data.description }}
									</span>
								</div>
							</div>
						</template>
						<template #editor="{ data, field }">
							<InputText v-model="data[field]" class="!text-xs !py-1.5 w-full" fluid />
						</template>
					</Column>

					<!-- Column 4: Cost Price -->
					<Column field="price_at_time_of_purchase" header="Purchased Price" :sortable="true" style="min-width: 140px">
						<template #body="{ data }">
							<div class="text-xs font-semibold text-slate-700 dark:text-slate-300">
								{{ formatCurrency(data.price_at_time_of_purchase) }}
							</div>
						</template>
						<template #editor="{ data, field }">
							<InputNumber
								v-model="data[field]"
								mode="currency"
								currency="INR"
								locale="en-IN"
								:min="0"
								class="!text-xs !py-0.5 w-full"
								fluid
							/>
						</template>
					</Column>

					<!-- Column 5: Selling Price -->
					<Column field="selling_price" header="Selling Price" :sortable="true" style="min-width: 150px">
						<template #body="{ data }">
							<div class="flex items-center gap-1.5">
								<span class="text-xs font-bold text-slate-900 dark:text-white">
									{{ formatCurrency(data.selling_price) }}
								</span>
								<span
									v-if="calculateMargin(data.price_at_time_of_purchase, data.selling_price) !== null"
									class="text-[10px] font-semibold px-1.5 py-0.2 rounded"
									:class="calculateMargin(data.price_at_time_of_purchase, data.selling_price)! >= 0 ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400'"
								>
									{{ calculateMargin(data.price_at_time_of_purchase, data.selling_price) }}%
								</span>
							</div>
						</template>
						<template #editor="{ data, field }">
							<InputNumber
								v-model="data[field]"
								mode="currency"
								currency="INR"
								locale="en-IN"
								:min="0"
								class="!text-xs !py-0.5 w-full"
								fluid
							/>
						</template>
					</Column>

					<!-- Column 6: Total On-Hand Stock -->
					<Column field="qty_available" header="Total Stock" :sortable="true" style="min-width: 130px">
						<template #body="{ data }">
							<div class="flex items-center gap-2">
								<span class="text-sm font-bold text-slate-900 dark:text-white">
									{{ formatNumber(data.qty_available) }}
								</span>
								<Tag
									v-if="data.qty_available > 10"
									severity="success"
									value="In Stock"
									class="!text-[10px] !px-1.5 !py-0.5"
								/>
								<Tag
									v-else-if="data.qty_available > 0"
									severity="warn"
									value="Low Stock"
									class="!text-[10px] !px-1.5 !py-0.5"
								/>
								<Tag
									v-else
									severity="danger"
									value="Out of Stock"
									class="!text-[10px] !px-1.5 !py-0.5"
								/>
							</div>
						</template>
					</Column>

					<!-- Column 7: Size Variants -->
					<Column header="Size Variants" style="min-width: 170px">
						<template #body="{ data }">
							<div v-if="data.sizes?.length" class="flex flex-wrap items-center gap-1">
								<span
									v-for="s in data.sizes.slice(0, 2)"
									:key="s.id || s.size"
									class="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60"
								>
									Sz {{ s.size }}:
									<strong :class="s.stock > 0 ? 'text-slate-900 dark:text-white' : 'text-rose-500'">{{ s.stock }}</strong>
								</span>
								<Button
									v-if="data.sizes.length > 2"
									:label="`+${data.sizes.length - 2} more`"
									text
									size="small"
									class="!text-[10px] !p-0.5 !text-indigo-600 dark:text-indigo-400 hover:underline"
									@click="openSizeBreakdown(data)"
								/>
								<Button
									v-else
									icon="pi pi-list"
									text
									rounded
									size="small"
									class="!w-6 !h-6 !text-slate-400 hover:!text-indigo-600"
									v-tooltip.top="'View all variant details'"
									@click="openSizeBreakdown(data)"
								/>
							</div>
							<span v-else class="text-xs text-slate-400 italic">No variants</span>
						</template>
					</Column>

					<!-- Column 8: Status -->
					<Column field="status" header="Status" :sortable="true" style="width: 100px">
						<template #body="{ data }">
							<Tag
								:severity="data.status ? 'success' : 'secondary'"
								:value="data.status ? 'Active' : 'Inactive'"
								class="!text-[10px] !px-2 !py-0.5"
							/>
						</template>
						<template #editor="{ data, field }">
							<Select
								v-model="data[field]"
								:options="statusDropdownOptions"
								optionLabel="label"
								optionValue="value"
								class="!text-xs !py-0.5 w-full"
							/>
						</template>
					</Column>

					<!-- Column 9: Row Editor Action -->
					<Column :rowEditor="true" style="width: 100px" bodyStyle="text-align:center" />

					<!-- Empty State -->
					<template #empty>
						<div class="py-12 flex flex-col items-center justify-center text-center space-y-3">
							<div class="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center text-xl">
								<i class="pi pi-inbox"></i>
							</div>
							<div class="space-y-1">
								<h3 class="text-sm font-semibold text-slate-800 dark:text-slate-200">No products found</h3>
								<p class="text-xs text-slate-500 dark:text-slate-400 max-w-sm">
									{{ isFilterActive ? 'Try adjusting your search keywords or filter criteria to see matching inventory.' : 'Get started by creating your first warehouse inventory product.' }}
								</p>
							</div>
							<div v-if="isFilterActive">
								<Button
									label="Clear Filters"
									icon="pi pi-filter-slash"
									size="small"
									severity="secondary"
									outlined
									class="!text-xs !py-1.5 !px-3"
									@click="resetFilters"
								/>
							</div>
						</div>
					</template>
				</DataTable>
		</div>

		<!-- Size Variant Detail Modal -->
		<Dialog
			v-model:visible="sizeModalVisible"
			modal
			header="Size Variant Breakdown"
			class="!w-full !max-w-lg dark:!bg-slate-900 dark:!text-slate-100"
		>
			<template #header>
				<div class="flex items-center gap-3">
					<div class="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
						<i class="pi pi-sitemap text-lg"></i>
					</div>
					<div>
						<h3 class="text-sm font-bold text-slate-900 dark:text-white leading-tight">
							{{ selectedProductForSizes?.name }}
						</h3>
						<p class="text-xs text-slate-500 dark:text-slate-400">
							SKU: {{ selectedProductForSizes?.product_id || `PR-${selectedProductForSizes?.id}` }} • Detailed size stock distribution
						</p>
					</div>
				</div>
			</template>

			<div v-if="selectedProductForSizes" class="space-y-4 pt-2">
				<!-- Quick Product Summary -->
				<div class="grid grid-cols-3 gap-2 p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/80 dark:border-slate-800 text-center">
					<div>
						<div class="text-[10px] uppercase font-semibold text-slate-500">Variants</div>
						<div class="text-sm font-bold text-slate-800 dark:text-slate-200">
							{{ selectedProductForSizes.sizes?.length || 0 }}
						</div>
					</div>
					<div>
						<div class="text-[10px] uppercase font-semibold text-slate-500">Total Units</div>
						<div class="text-sm font-bold text-slate-800 dark:text-slate-200">
							{{ formatNumber(selectedProductForSizes.qty_available) }}
						</div>
					</div>
					<div>
						<div class="text-[10px] uppercase font-semibold text-slate-500">Inventory Cost</div>
						<div class="text-sm font-bold text-emerald-600 dark:text-emerald-400">
							{{ formatCurrency((selectedProductForSizes.qty_available || 0) * (selectedProductForSizes.price_at_time_of_purchase || 0)) }}
						</div>
					</div>
				</div>

				<!-- Sizes Table -->
				<div class="border border-slate-200/80 dark:border-slate-800 rounded-xl overflow-hidden">
					<table class="w-full text-xs text-left">
						<thead class="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 font-semibold border-b border-slate-200/80 dark:border-slate-800">
							<tr>
								<th class="p-2.5">Size</th>
								<th class="p-2.5">Unit Cost</th>
								<th class="p-2.5">On-Hand Stock</th>
								<th class="p-2.5">Total Value</th>
								<th class="p-2.5 text-right">Availability</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
							<tr
								v-for="size in selectedProductForSizes.sizes"
								:key="size.id || size.size"
								class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
							>
								<td class="p-2.5 font-bold text-slate-900 dark:text-white">
									Size {{ size.size }}
								</td>
								<td class="p-2.5 text-slate-600 dark:text-slate-300">
									{{ formatCurrency(size.price || selectedProductForSizes.price_at_time_of_purchase) }}
								</td>
								<td class="p-2.5 font-semibold" :class="size.stock > 0 ? 'text-slate-900 dark:text-white' : 'text-rose-500'">
									{{ size.stock }} units
								</td>
								<td class="p-2.5 text-slate-600 dark:text-slate-300">
									{{ formatCurrency((size.stock || 0) * (size.price || selectedProductForSizes.price_at_time_of_purchase || 0)) }}
								</td>
								<td class="p-2.5 text-right">
									<Tag
										:severity="size.stock > 0 && size.is_available ? 'success' : 'danger'"
										:value="size.stock > 0 && size.is_available ? 'Available' : 'Depleted'"
										class="!text-[10px] !px-1.5 !py-0.2"
									/>
								</td>
							</tr>
							<tr v-if="!selectedProductForSizes.sizes?.length">
								<td colspan="5" class="p-4 text-center text-slate-400 italic">
									No size variants recorded for this product.
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>

			<template #footer>
				<div class="flex justify-end pt-2">
					<Button
						label="Close"
						severity="secondary"
						size="small"
						class="!text-xs !py-1.5 !px-4"
						@click="sizeModalVisible = false"
					/>
				</div>
			</template>
		</Dialog>

		<!-- Image Preview Modal -->
		<Dialog
			v-model:visible="previewImage"
			modal
			:header="previewImage?.title || 'Product Image'"
			class="!w-full !max-w-md dark:!bg-slate-900"
		>
			<div v-if="previewImage" class="flex flex-col items-center justify-center p-2">
				<img :src="previewImage.url" :alt="previewImage.title" class="max-h-96 w-auto rounded-xl object-contain shadow-lg" />
				<span class="text-xs text-slate-500 dark:text-slate-400 mt-3">{{ previewImage.title }}</span>
			</div>
		</Dialog>
	</div>
</template>

<style scoped></style>
