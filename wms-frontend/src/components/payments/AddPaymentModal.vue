<script setup lang="ts">
import { ref, reactive, watch, computed } from "vue";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import {
	formatCurrency,
	validatePaymentPayload,
} from "@/utils/paymentCalculations";

const emit = defineEmits(["instance-added"]);
const toast = useToast();

const visible = ref(false);
const loading = ref(false);
const stakeholders = ref<any[]>([]);
const orders = ref<any[]>([]);
const formErrors = ref<Record<string, string>>({});

const initialData = {
	company: null as number | null,
	order: null as number | null,
	amount: 0,
	payment_method: "CASH",
	payment_type: "INBOUND" as "INBOUND" | "OUTBOUND" | "REFUND",
	payment_date: new Date(),
	reference: "",
	notes: "",
};

const formData = reactive({ ...initialData });

const methods = [
	{ value: "CASH", label: "Cash" },
	{ value: "CARD", label: "Debit / Credit Card" },
	{ value: "BANK", label: "Bank Transfer (NEFT/RTGS/IMPS)" },
	{ value: "OTHER", label: "Other / Cheque" },
];

const paymentTypes = [
	{ label: "Customer Inbound Receipt", value: "INBOUND" },
	{ label: "Supplier Outbound Disbursement", value: "OUTBOUND" },
	{ label: "Customer RMA Refund", value: "REFUND" },
];

// Fetch Stakeholders
const fetchStakeholders = async () => {
	try {
		const response = await axios.get("/api/accounts/stakeholders/");
		stakeholders.value = response.data;
	} catch (error) {
		console.error("Error fetching stakeholders:", error);
	}
};

// Fetch pending orders when company is selected
const fetchOrdersForCompany = async (companyId: number) => {
	try {
		const response = await axios.get("/api/inventory/orders/", {
			params: { stakeholder_id: companyId },
		});
		orders.value = (response.data || []).filter((o: any) => o.pending_amount > 0);
	} catch (error) {
		console.error("Error fetching orders:", error);
	}
};

const selectedCompanyObj = computed(() => {
	return stakeholders.value.find((s) => s.id === formData.company);
});

const selectedOrderObj = computed(() => {
	return orders.value.find((o) => o.id === formData.order);
});

const maxAllowedAmount = computed(() => {
	if (selectedOrderObj.value) {
		return Number(selectedOrderObj.value.pending_amount) || 0;
	}
	if (selectedCompanyObj.value) {
		return Number(selectedCompanyObj.value.total_pending_amount) || 0;
	}
	return undefined;
});

// Auto-fill amount when order is selected
watch(
	() => formData.order,
	(newOrder) => {
		if (newOrder && selectedOrderObj.value) {
			formData.amount = Number(selectedOrderObj.value.pending_amount);
			if (selectedOrderObj.value.order_type === "PO") {
				formData.payment_type = "OUTBOUND";
			} else {
				formData.payment_type = "INBOUND";
			}
		}
	}
);

// Fetch orders on company change
watch(
	() => formData.company,
	(newComp) => {
		formData.order = null;
		orders.value = [];
		if (newComp) {
			fetchOrdersForCompany(newComp);
			if (selectedCompanyObj.value) {
				formData.payment_type = selectedCompanyObj.value.type === "Supplier" ? "OUTBOUND" : "INBOUND";
			}
		}
	}
);

const handleSubmit = async () => {
	formErrors.value = validatePaymentPayload({
		amount: formData.amount,
		payment_date: formData.payment_date,
		payment_method: formData.payment_method,
		company: formData.company,
		order: formData.order,
		pendingAmount: maxAllowedAmount.value,
	});

	if (Object.keys(formErrors.value).length > 0) {
		toast.add({
			severity: "warn",
			summary: "Validation Error",
			detail: "Please correct errors before saving payment.",
			life: 3000,
		});
		return;
	}

	try {
		loading.value = true;
		const payload = {
			company: formData.company,
			order: formData.order || null,
			amount: formData.amount,
			payment_method: formData.payment_method,
			payment_type: formData.payment_type,
			payment_date: new Date(formData.payment_date).toISOString(),
			reference: formData.reference,
			notes: formData.notes,
			status: "Completed",
		};

		const res = await axios.post("/api/inventory/payments/", payload);
		toast.add({
			severity: "success",
			summary: "Payment Recorded",
			detail: `Voucher ${res.data.payment_number || ''} recorded successfully.`,
			life: 3000,
		});

		visible.value = false;
		Object.assign(formData, initialData);
		formErrors.value = {};
		emit("instance-added");
	} catch (error: any) {
		console.error("Payment failed:", error);
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
			summary: "Payment Rejected",
			detail: error.response?.data?.error || "Could not record payment.",
			life: 5000,
		});
	} finally {
		loading.value = false;
	}
};

const cancel = () => {
	visible.value = false;
	Object.assign(formData, initialData);
	formErrors.value = {};
};

const openModal = () => {
	fetchStakeholders();
	visible.value = true;
};
</script>

<template>
	<div>
		<Button
			label="Record Payment"
			icon="pi pi-plus"
			severity="primary"
			size="small"
			class="shadow-sm"
			@click="openModal"
		/>

		<Dialog
			v-model:visible="visible"
			modal
			header="Record Financial Settlement"
			:style="{ width: '38rem' }"
			class="p-fluid"
		>
			<form @submit.prevent="handleSubmit" class="space-y-4 pt-2">
				<!-- Payment Type -->
				<div>
					<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Transaction Classification <span class="text-rose-500">*</span>
					</label>
					<Select
						v-model="formData.payment_type"
						:options="paymentTypes"
						optionLabel="label"
						optionValue="value"
					/>
				</div>

				<!-- Stakeholder / Company -->
				<div>
					<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Stakeholder Partner <span class="text-rose-500">*</span>
					</label>
					<Select
						v-model="formData.company"
						:options="stakeholders"
						optionLabel="name"
						optionValue="id"
						placeholder="Select Customer or Supplier"
						filter
						:class="{ 'p-invalid': formErrors.company }"
					/>
					<small v-if="formErrors.company" class="text-rose-500 text-xs mt-0.5 block">{{ formErrors.company }}</small>
					<div v-if="selectedCompanyObj" class="mt-1 text-[11px] text-slate-500 flex items-center justify-between">
						<span>Pending Debt: <strong class="text-rose-600">{{ formatCurrency(selectedCompanyObj.total_pending_amount) }}</strong></span>
						<span>Opening Balance: {{ formatCurrency(selectedCompanyObj.opening_balance) }}</span>
					</div>
				</div>

				<!-- Linked Order (Optional / Filtered) -->
				<div v-if="formData.company">
					<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Allocate to Specific Order (Optional)
					</label>
					<Select
						v-model="formData.order"
						:options="orders"
						optionLabel="order_number"
						optionValue="id"
						placeholder="Leave empty for FIFO debt allocation"
						showClear
					>
						<template #option="slotProps">
							<div class="flex items-center justify-between w-full text-xs">
								<span>{{ slotProps.option.order_number }}</span>
								<span class="font-semibold text-rose-600">Pending: {{ formatCurrency(slotProps.option.pending_amount) }}</span>
							</div>
						</template>
					</Select>
					<span class="text-[11px] text-slate-400 mt-0.5 block">
						If unselected, payment automatically liquidates opening debt or the oldest active order.
					</span>
				</div>

				<!-- Amount and Method -->
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							Amount (INR) <span class="text-rose-500">*</span>
						</label>
						<InputNumber
							v-model="formData.amount"
							mode="currency"
							currency="INR"
							locale="en-IN"
							:min="1"
							:max="maxAllowedAmount"
							:class="{ 'p-invalid': formErrors.amount }"
						/>
						<small v-if="formErrors.amount" class="text-rose-500 text-xs mt-0.5 block">{{ formErrors.amount }}</small>
					</div>

					<div>
						<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							Payment Method <span class="text-rose-500">*</span>
						</label>
						<Select
							v-model="formData.payment_method"
							:options="methods"
							optionLabel="label"
							optionValue="value"
						/>
					</div>
				</div>

				<!-- Date and Reference / UTR -->
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							Transaction Date <span class="text-rose-500">*</span>
						</label>
						<DatePicker
							v-model="formData.payment_date"
							showIcon
							dateFormat="dd/mm/yy"
							class="w-full"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							Reference / UTR / Cheque #
						</label>
						<InputText
							v-model="formData.reference"
							placeholder="e.g. UTR-9876543210"
							class="font-mono text-xs"
						/>
					</div>
				</div>

				<!-- Notes -->
				<div>
					<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Notes / Remarks
					</label>
					<Textarea
						v-model="formData.notes"
						rows="2"
						placeholder="Add any internal transaction or receipt notes..."
						autoResize
					/>
				</div>

				<div class="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
					<Button type="button" label="Cancel" severity="secondary" outlined @click="cancel" />
					<Button type="submit" label="Record Payment" :loading="loading" />
				</div>
			</form>
		</Dialog>
	</div>
</template>

<style scoped></style>
