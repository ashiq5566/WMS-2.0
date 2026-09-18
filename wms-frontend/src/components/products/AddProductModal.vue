<script setup lang="ts">
import { ref, computed } from "vue";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import Dialog from "primevue/dialog";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Message from "primevue/message";

const visible = ref(false);
const emit = defineEmits(["instance-added"]);
const toast = useToast();

const isSubmitting = ref(false);
const formError = ref("");
const imageInput = ref<HTMLInputElement | null>(null);
const imagePreview = ref<string | null>(null);

interface SizeRow {
	size: number | null;
	price: number | null;
	stock: number | null;
	is_available: boolean;
}

const unitOptions = [
	{ label: "Pieces (Pcs)", value: "Pieces" },
	{ label: "Kilograms (Kg)", value: "Kilograms" },
	{ label: "Sets", value: "Sets" }
];

const statusOptions = [
	{ label: "Active", value: true },
	{ label: "Inactive", value: false }
];

const blankFormData = () => ({
	name: "",
	unit: "Pieces",
	selling_price: null as number | null,
	price_at_time_of_purchase: null as number | null,
	status: true,
	description: "",
	sizes: [] as SizeRow[]
});

const formData = ref(blankFormData());

const sizeRow = (defaultSize: number = 1): SizeRow => ({
	size: defaultSize,
	price: formData.value.price_at_time_of_purchase || 0,
	stock: 0,
	is_available: true
});

const addSize = () => {
	const nextSize = formData.value.sizes.length > 0
		? Math.max(...formData.value.sizes.map(s => Number(s.size) || 0)) + 1
		: 1;
	formData.value.sizes.push(sizeRow(nextSize));
};

const removeSize = (index: number) => {
	formData.value.sizes.splice(index, 1);
};

const onImageChange = (event: Event) => {
	const target = event.target as HTMLInputElement;
	if (target.files && target.files[0]) {
		const file = target.files[0];
		imagePreview.value = URL.createObjectURL(file);
	} else {
		imagePreview.value = null;
	}
};

const removeImage = () => {
	imagePreview.value = null;
	if (imageInput.value) {
		imageInput.value.value = "";
	}
};

// Computed summary statistics for the modal
const totalInitialStock = computed(() => {
	return formData.value.sizes.reduce((sum, s) => sum + (Number(s.stock) || 0), 0);
});

const totalInventoryValuation = computed(() => {
	return formData.value.sizes.reduce((sum, s) => {
		const unitCost = Number(s.price) || Number(formData.value.price_at_time_of_purchase) || 0;
		return sum + (Number(s.stock) || 0) * unitCost;
	}, 0);
});

const resetForm = () => {
	formData.value = blankFormData();
	removeImage();
	formError.value = "";
	isSubmitting.value = false;
};

const validateForm = (): boolean => {
	formError.value = "";

	if (!formData.value.name.trim()) {
		formError.value = "Product Name is required.";
		return false;
	}
	if (!formData.value.unit) {
		formError.value = "Unit of measurement is required.";
		return false;
	}
	if (formData.value.selling_price == null || formData.value.selling_price < 0) {
		formError.value = "A valid Selling Price is required.";
		return false;
	}

	// Validate sizes if provided
	if (formData.value.sizes.length > 0) {
		const seenSizes = new Set<number>();
		for (let i = 0; i < formData.value.sizes.length; i++) {
			const s = formData.value.sizes[i];
			if (s.size == null || isNaN(Number(s.size))) {
				formError.value = `Size in row ${i + 1} must be a valid number.`;
				return false;
			}
			if (seenSizes.has(Number(s.size))) {
				formError.value = `Duplicate size "${s.size}" detected. Each size must be unique per product.`;
				return false;
			}
			seenSizes.add(Number(s.size));

			if (s.price == null || Number(s.price) < 0) {
				formError.value = `Price in size row ${i + 1} must be non-negative.`;
				return false;
			}
			if (s.stock == null || Number(s.stock) < 0) {
				formError.value = `Initial stock in size row ${i + 1} cannot be negative.`;
				return false;
			}
		}
	}

	return true;
};

const handleSubmit = async () => {
	if (!validateForm()) return;

	isSubmitting.value = true;
	try {
		const data = new FormData();
		data.append("name", formData.value.name.trim());
		data.append("unit", formData.value.unit);
		data.append("selling_price", String(formData.value.selling_price));
		if (formData.value.price_at_time_of_purchase != null) {
			data.append("price_at_time_of_purchase", String(formData.value.price_at_time_of_purchase));
		}
		data.append("status", String(formData.value.status));
		if (formData.value.description) {
			data.append("description", formData.value.description.trim());
		}

		// Prepare sanitized sizes JSON
		const formattedSizes = formData.value.sizes.map(s => ({
			size: Number(s.size),
			price: Number(s.price) || 0,
			stock: Number(s.stock) || 0,
			is_available: s.is_available ?? true
		}));
		data.append("sizes", JSON.stringify(formattedSizes));

		if (imageInput.value && imageInput.value.files && imageInput.value.files[0]) {
			data.append("image", imageInput.value.files[0]);
		}

		await axios.post("/api/inventory/products/", data);

		toast.add({
			severity: "success",
			summary: "Product Created",
			detail: `Product "${formData.value.name}" added with ${formattedSizes.length} size variants.`,
			life: 3000
		});

		visible.value = false;
		resetForm();
		emit("instance-added");
	} catch (err: any) {
		console.error("Product creation error:", err);
		const msg = err.response?.data?.name?.[0]
			? `Product with name "${formData.value.name}" already exists.`
			: err.response?.data?.detail || err.response?.data?.message || err.message || "Failed to create product.";
		formError.value = msg;
		toast.add({ severity: "error", summary: "Creation Error", detail: msg, life: 4000 });
	} finally {
		isSubmitting.value = false;
	}
};
</script>

<template>
	<div>
		<Button
			label="Add Product"
			icon="pi pi-plus"
			severity="primary"
			class="!text-xs !py-2 !px-3.5 !rounded-lg !bg-indigo-600 hover:!bg-indigo-700 !border-indigo-600 shadow-sm"
			@click="visible = true"
		/>

		<Dialog
			v-model:visible="visible"
			modal
			:style="{ width: '48rem', maxWidth: '95vw' }"
			class="dark:!bg-slate-900 dark:!text-slate-100"
			@hide="resetForm"
		>
			<template #header>
				<div class="flex items-center gap-3">
					<div class="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
						<i class="pi pi-box text-lg"></i>
					</div>
					<div>
						<h3 class="text-base font-bold text-slate-900 dark:text-white leading-tight">Add New Product</h3>
						<p class="text-xs text-slate-500 dark:text-slate-400">Define product details, catalog pricing, and initial size variants</p>
					</div>
				</div>
			</template>

			<div class="space-y-5 pt-2">
				<!-- Error Message Banner -->
				<Message v-if="formError" severity="error" :closable="true" @close="formError = ''" class="!text-xs">
					{{ formError }}
				</Message>

				<!-- Basic Details Section -->
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					<!-- Product Name -->
					<div class="space-y-1 sm:col-span-2">
						<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Product Name <span class="text-rose-500">*</span>
						</label>
						<InputText
							v-model="formData.name"
							placeholder="e.g. Heavy Duty Storage Pallet"
							class="w-full !text-sm !py-2 dark:!bg-slate-800 dark:!border-slate-700"
						/>
					</div>

					<!-- Unit of Measurement -->
					<div class="space-y-1">
						<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Unit <span class="text-rose-500">*</span>
						</label>
						<Select
							v-model="formData.unit"
							:options="unitOptions"
							optionLabel="label"
							optionValue="value"
							placeholder="Select Unit"
							class="w-full !text-sm dark:!bg-slate-800 dark:!border-slate-700"
						/>
					</div>

					<!-- Catalog Status -->
					<div class="space-y-1">
						<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Status
						</label>
						<Select
							v-model="formData.status"
							:options="statusOptions"
							optionLabel="label"
							optionValue="value"
							class="w-full !text-sm dark:!bg-slate-800 dark:!border-slate-700"
						/>
					</div>

					<!-- Selling Price -->
					<div class="space-y-1">
						<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Selling Price (₹) <span class="text-rose-500">*</span>
						</label>
						<InputNumber
							v-model="formData.selling_price"
							:min="0"
							mode="currency"
							currency="INR"
							locale="en-IN"
							placeholder="₹0.00"
							fluid
							class="w-full !text-sm"
							inputClass="w-full min-w-0 !py-2 dark:!bg-slate-800 dark:!border-slate-700"
						/>
					</div>

					<!-- Purchase / Cost Price -->
					<div class="space-y-1">
						<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Purchase Cost (₹)
						</label>
						<InputNumber
							v-model="formData.price_at_time_of_purchase"
							:min="0"
							mode="currency"
							currency="INR"
							locale="en-IN"
							placeholder="₹0.00"
							fluid
							class="w-full !text-sm"
							inputClass="w-full min-w-0 !py-2 dark:!bg-slate-800 dark:!border-slate-700"
						/>
					</div>

					<!-- Description -->
					<div class="space-y-1 sm:col-span-2">
						<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Description
						</label>
						<InputText
							v-model="formData.description"
							placeholder="Specifications, location, or notes"
							class="w-full !text-sm !py-2 dark:!bg-slate-800 dark:!border-slate-700"
						/>
					</div>

					<!-- Image Attachment -->
					<div class="space-y-1 sm:col-span-2">
						<label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Product Image
						</label>
						<div class="flex items-center gap-4">
							<input
								type="file"
								ref="imageInput"
								accept="image/*"
								class="text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-indigo-950 dark:file:text-indigo-300"
								@change="onImageChange"
							/>
							<div v-if="imagePreview" class="flex items-center gap-2">
								<img :src="imagePreview" alt="Preview" class="w-10 h-10 object-cover rounded border border-slate-200 dark:border-slate-700" />
								<Button icon="pi pi-times" rounded text severity="danger" size="small" @click="removeImage" />
							</div>
						</div>
					</div>
				</div>

				<!-- Sized Inventory Variants Section -->
				<div class="pt-3 border-t border-slate-100 dark:border-slate-800/80">
					<div class="flex items-center justify-between mb-3">
						<div>
							<h4 class="text-sm font-bold text-slate-900 dark:text-white">Size Variants & Opening Stock</h4>
							<p class="text-xs text-slate-500 dark:text-slate-400">Specify size numbers, unit purchase costs, and initial warehouse quantities</p>
						</div>
						<Button
							label="Add Size"
							icon="pi pi-plus"
							size="small"
							severity="secondary"
							outlined
							class="!text-xs !py-1.5 !px-3 !rounded-lg !border-indigo-200 dark:!border-indigo-800 !text-indigo-600 dark:!text-indigo-400 hover:!bg-indigo-50 dark:hover:!bg-indigo-950/40"
							@click="addSize"
						/>
					</div>

					<!-- Empty sizes message -->
					<div v-if="formData.sizes.length === 0" class="p-5 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-slate-400 text-xs bg-slate-50/40 dark:bg-slate-800/20">
						<i class="pi pi-info-circle mr-1.5 text-slate-400"></i>
						No size variants defined. Click "Add Size" if this item has sized inventory, or save directly as a base product.
					</div>

					<!-- Sizes Table Container -->
					<div v-else class="space-y-3">
						<div class="overflow-x-auto border border-slate-200/80 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900/40 shadow-xs max-h-60 overflow-y-auto">
							<table class="w-full min-w-[500px] text-xs">
								<thead class="sticky top-0 z-10 bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold border-b border-slate-200/80 dark:border-slate-800">
									<tr>
										<th class="py-2.5 px-3 text-left w-32">
											Size Number <span class="text-rose-500">*</span>
										</th>
										<th class="py-2.5 px-3 text-left">
											Purchase Cost (₹)
										</th>
										<th class="py-2.5 px-3 text-left w-36">
											Initial Stock (Units)
										</th>
										<th class="py-2.5 px-2 text-center w-14">
											Action
										</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
									<tr
										v-for="(size, index) in formData.sizes"
										:key="index"
										class="hover:bg-slate-50/60 dark:hover:bg-slate-800/30 transition-colors"
									>
										<!-- Size Number -->
										<td class="p-2.5">
											<InputNumber
												v-model="size.size"
												:min="1"
												placeholder="e.g. 8"
												fluid
												class="w-full !text-xs"
												inputClass="w-full min-w-0 !py-1.5 !px-2.5 !text-xs rounded-lg dark:!bg-slate-800 dark:!border-slate-700"
											/>
										</td>

										<!-- Cost Price -->
										<td class="p-2.5">
											<InputNumber
												v-model="size.price"
												:min="0"
												placeholder="₹0.00"
												fluid
												class="w-full !text-xs"
												inputClass="w-full min-w-0 !py-1.5 !px-2.5 !text-xs rounded-lg dark:!bg-slate-800 dark:!border-slate-700"
											/>
										</td>

										<!-- Initial Stock -->
										<td class="p-2.5">
											<InputNumber
												v-model="size.stock"
												:min="0"
												placeholder="0"
												fluid
												class="w-full !text-xs"
												inputClass="w-full min-w-0 !py-1.5 !px-2.5 !text-xs rounded-lg dark:!bg-slate-800 dark:!border-slate-700"
											/>
										</td>

										<!-- Trash Button -->
										<td class="p-2.5 text-center">
											<Button
												icon="pi pi-trash"
												severity="danger"
												text
												rounded
												class="!w-8 !h-8 !p-0 text-rose-500 hover:text-rose-700 hover:!bg-rose-50 dark:hover:!bg-rose-950/40"
												@click="removeSize(index)"
											/>
										</td>
									</tr>
								</tbody>
							</table>
						</div>

						<!-- Size Summary Stats -->
						<div class="p-3 rounded-lg bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30 flex flex-wrap items-center justify-between gap-2 text-xs">
							<span class="text-slate-600 dark:text-slate-400">
								Total Variants: <strong class="text-slate-800 dark:text-slate-200">{{ formData.sizes.length }}</strong>
							</span>
							<span class="text-slate-600 dark:text-slate-400">
								Initial Stock: <strong class="text-emerald-600 dark:text-emerald-400">{{ totalInitialStock }} units</strong>
							</span>
							<span class="text-slate-600 dark:text-slate-400">
								Opening Valuation: <strong class="text-indigo-600 dark:text-indigo-400">₹{{ totalInventoryValuation.toLocaleString('en-IN') }}</strong>
							</span>
						</div>
					</div>
				</div>
			</div>

			<template #footer>
				<div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/80">
					<Button
						label="Cancel"
						severity="secondary"
						text
						class="!text-xs !py-2 !px-4"
						@click="visible = false"
					/>
					<Button
						label="Save Product"
						icon="pi pi-check"
						severity="primary"
						:loading="isSubmitting"
						class="!text-xs !py-2 !px-4 !bg-indigo-600 hover:!bg-indigo-700 !border-indigo-600 shadow-sm"
						@click="handleSubmit"
					/>
				</div>
			</template>
		</Dialog>
	</div>
</template>

