<script setup lang="ts">
import { ref, reactive } from "vue";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import { validateStakeholder } from "@/utils/stakeholderCalculations";

const emit = defineEmits(["instance-added"]);
const toast = useToast();
const visible = ref(false);
const loading = ref(false);
const formErrors = ref<Record<string, string>>({});

const initialData = {
	name: "",
	address: "",
	mobile: "",
	email: "",
	company_name: "",
	type: "Customer" as "Customer" | "Supplier",
	city: "",
	tax_id: "",
	credit_limit: 0,
	opening_balance: 0,
};

const formData = reactive({ ...initialData });

const typeOptions = [
	{ label: "Customer", value: "Customer" },
	{ label: "Supplier", value: "Supplier" },
];

const handleSubmit = async () => {
	formErrors.value = validateStakeholder(formData);
	if (Object.keys(formErrors.value).length > 0) {
		toast.add({
			severity: "warn",
			summary: "Validation Warning",
			detail: "Please fill in required fields correctly.",
			life: 3000,
		});
		return;
	}

	try {
		loading.value = true;
		await axios.post("/api/accounts/stakeholders/", formData);
		toast.add({
			severity: "success",
			summary: "Success",
			detail: `Stakeholder "${formData.name}" added successfully.`,
			life: 3000,
		});
		visible.value = false;
		emit("instance-added");
		Object.assign(formData, initialData);
		formErrors.value = {};
	} catch (error: any) {
		console.error("Creation failed:", error);
		const errResponse = error.response?.data;
		if (errResponse && typeof errResponse === "object") {
			const serverErrors: Record<string, string> = {};
			for (const [k, v] of Object.entries(errResponse)) {
				serverErrors[k] = Array.isArray(v) ? v.join(" ") : String(v);
			}
			formErrors.value = serverErrors;
		}
		toast.add({
			severity: "error",
			summary: "Creation Failed",
			detail: error.response?.data?.error || "Could not register stakeholder.",
			life: 4000,
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
</script>

<template>
	<div>
		<Button
			label="Quick Add"
			icon="pi pi-user-plus"
			severity="secondary"
			outlined
			class="p-button-sm"
			@click="visible = true"
		/>

		<Dialog
			v-model:visible="visible"
			modal
			header="Quick Register Stakeholder"
			:style="{ width: '36rem' }"
			class="p-fluid"
		>
			<div class="space-y-4 pt-2">
				<!-- Name -->
				<div>
					<label for="modal-name" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Stakeholder Name <span class="text-rose-500">*</span>
					</label>
					<InputText
						id="modal-name"
						v-model="formData.name"
						placeholder="Individual or business name"
						:class="{ 'p-invalid': formErrors.name }"
					/>
					<small v-if="formErrors.name" class="text-rose-500 text-xs mt-0.5 block">{{ formErrors.name }}</small>
				</div>

				<!-- Type -->
				<div>
					<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Stakeholder Type <span class="text-rose-500">*</span>
					</label>
					<Select
						v-model="formData.type"
						:options="typeOptions"
						optionLabel="label"
						optionValue="value"
						placeholder="Select Type"
					/>
				</div>

				<!-- Company Name -->
				<div>
					<label for="modal-company" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Company / Trade Name
					</label>
					<InputText id="modal-company" v-model="formData.company_name" placeholder="Legal registered entity" />
				</div>

				<!-- Phone & Email Grid -->
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label for="modal-phone" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							Phone / Mobile
						</label>
						<InputText
							id="modal-phone"
							v-model="formData.mobile"
							placeholder="+91 98765 43210"
							:class="{ 'p-invalid': formErrors.mobile }"
						/>
						<small v-if="formErrors.mobile" class="text-rose-500 text-xs mt-0.5 block">{{ formErrors.mobile }}</small>
					</div>
					<div>
						<label for="modal-email" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							Email
						</label>
						<InputText
							id="modal-email"
							v-model="formData.email"
							type="email"
							placeholder="name@business.com"
							:class="{ 'p-invalid': formErrors.email }"
						/>
						<small v-if="formErrors.email" class="text-rose-500 text-xs mt-0.5 block">{{ formErrors.email }}</small>
					</div>
				</div>

				<!-- Address & City -->
				<div class="grid grid-cols-3 gap-3">
					<div class="col-span-2">
						<label for="modal-address" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							Address
						</label>
						<InputText id="modal-address" v-model="formData.address" placeholder="Street address" />
					</div>
					<div>
						<label for="modal-city" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
							City
						</label>
						<InputText id="modal-city" v-model="formData.city" placeholder="City" />
					</div>
				</div>

				<!-- Opening Balance -->
				<div>
					<label for="modal-balance" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
						Opening Debt Balance (INR)
					</label>
					<InputNumber
						id="modal-balance"
						v-model="formData.opening_balance"
						mode="currency"
						currency="INR"
						locale="en-IN"
					/>
				</div>
			</div>

			<template #footer>
				<div class="flex justify-end gap-2 pt-2">
					<Button type="button" label="Cancel" severity="secondary" outlined @click="cancel" />
					<Button type="submit" label="Save Stakeholder" :loading="loading" @click="handleSubmit" />
				</div>
			</template>
		</Dialog>
	</div>
</template>

<style scoped></style>
