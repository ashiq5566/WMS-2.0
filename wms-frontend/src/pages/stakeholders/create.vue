<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import { validateStakeholder } from "@/utils/stakeholderCalculations";

const router = useRouter();
const toast = useToast();

const loading = ref(false);
const sameAsBilling = ref(false);
const formErrors = ref<Record<string, string>>({});

const form = reactive({
	name: "",
	type: "Customer" as "Customer" | "Supplier",
	company_name: "",
	stakeholder_id: "",
	contact_person: "",
	mobile: "",
	alternate_phone: "",
	email: "",
	website: "",
	address: "",
	shipping_address: "",
	city: "",
	state: "",
	country: "India",
	postal_code: "",
	tax_id: "",
	pan_number: "",
	payment_terms: "Net 30",
	credit_limit: 0,
	opening_balance: 0,
	notes: "",
});

const paymentTermOptions = [
	{ label: "Due on Receipt", value: "Immediate" },
	{ label: "Net 15 Days", value: "Net 15" },
	{ label: "Net 30 Days", value: "Net 30" },
	{ label: "Net 45 Days", value: "Net 45" },
	{ label: "Net 60 Days", value: "Net 60" },
];

const handleSameAsBilling = () => {
	if (sameAsBilling.value) {
		form.shipping_address = form.address;
	}
};

const goBack = () => {
	router.push("/stakeholders");
};

const submitForm = async (redirectAfterSave = true) => {
	// Validate
	formErrors.value = validateStakeholder(form);
	if (Object.keys(formErrors.value).length > 0) {
		toast.add({
			severity: "warn",
			summary: "Validation Error",
			detail: "Please correct highlighted fields before submitting.",
			life: 4000,
		});
		return;
	}

	try {
		loading.value = true;
		const payload = { ...form };
		if (sameAsBilling.value && !payload.shipping_address) {
			payload.shipping_address = payload.address;
		}

		const response = await axios.post("/api/accounts/stakeholders/", payload);
		toast.add({
			severity: "success",
			summary: "Master Record Created",
			detail: `${form.type} "${form.name}" has been registered successfully.`,
			life: 3000,
		});

		if (redirectAfterSave) {
			router.push(`/stakeholders/${response.data.id}`);
		} else {
			// Reset form for next entry
			Object.assign(form, {
				name: "",
				company_name: "",
				stakeholder_id: "",
				contact_person: "",
				mobile: "",
				alternate_phone: "",
				email: "",
				website: "",
				address: "",
				shipping_address: "",
				city: "",
				state: "",
				postal_code: "",
				tax_id: "",
				pan_number: "",
				credit_limit: 0,
				opening_balance: 0,
				notes: "",
			});
			sameAsBilling.value = false;
			formErrors.value = {};
		}
	} catch (error: any) {
		console.error("Creation error:", error);
		const errResponse = error.response?.data;
		if (errResponse && typeof errResponse === "object") {
			const serverErrors: Record<string, string> = {};
			for (const [key, val] of Object.entries(errResponse)) {
				serverErrors[key] = Array.isArray(val) ? val.join(" ") : String(val);
			}
			formErrors.value = serverErrors;
		}
		toast.add({
			severity: "error",
			summary: "Creation Failed",
			detail: error.response?.data?.error || "Unable to create stakeholder master record.",
			life: 5000,
		});
	} finally {
		loading.value = false;
	}
};
</script>

<template>
	<div class="max-w-5xl mx-auto space-y-6 pb-12">
		<!-- Header & Navigation -->
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
			<div>
				<div class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 mb-1">
					<router-link to="/stakeholders" class="hover:text-slate-900 dark:hover:text-white transition-colors">
						Stakeholders
					</router-link>
					<span>/</span>
					<span class="text-slate-900 dark:text-slate-200 font-medium">New Master Record</span>
				</div>
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
					Register Stakeholder
				</h1>
				<p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
					Create an authoritative master profile for a Customer or Supplier.
				</p>
			</div>

			<div class="flex items-center gap-2.5">
				<Button
					label="Cancel"
					icon="pi pi-times"
					severity="secondary"
					outlined
					@click="goBack"
					class="p-button-sm"
				/>
				<Button
					label="Save & Add Another"
					icon="pi pi-plus"
					severity="secondary"
					:loading="loading"
					@click="submitForm(false)"
					class="p-button-sm"
				/>
				<Button
					label="Save Master Record"
					icon="pi pi-check"
					severity="primary"
					:loading="loading"
					@click="submitForm(true)"
					class="p-button-sm shadow-sm"
				/>
			</div>
		</div>

		<form @submit.prevent="submitForm(true)" class="space-y-6">
			<!-- Section 1: Basic Information -->
			<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
				<template #title>
					<div class="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-3">
						<i class="pi pi-id-card text-blue-500"></i>
						<span>1. Basic Profile & Identification</span>
					</div>
				</template>
				<template #content>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
						<!-- Stakeholder Type Selection -->
						<div class="md:col-span-2">
							<label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
								Stakeholder Classification <span class="text-rose-500">*</span>
							</label>
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
								<label
									class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all"
									:class="form.type === 'Customer' ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20' : 'border-slate-200 dark:border-slate-700'"
								>
									<RadioButton v-model="form.type" inputId="typeCustomer" value="Customer" />
									<div>
										<span class="font-semibold text-sm text-slate-900 dark:text-white block">Customer</span>
										<span class="text-xs text-slate-500 dark:text-slate-400">Buyer for outbound Sales Orders</span>
									</div>
								</label>
								<label
									class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all"
									:class="form.type === 'Supplier' ? 'border-amber-500 bg-amber-50/50 dark:bg-amber-900/20' : 'border-slate-200 dark:border-slate-700'"
								>
									<RadioButton v-model="form.type" inputId="typeSupplier" value="Supplier" />
									<div>
										<span class="font-semibold text-sm text-slate-900 dark:text-white block">Supplier</span>
										<span class="text-xs text-slate-500 dark:text-slate-400">Vendor for inbound Purchase Orders</span>
									</div>
								</label>
							</div>
							<small v-if="formErrors.type" class="text-rose-500 text-xs mt-1 block">{{ formErrors.type }}</small>
						</div>

						<!-- Primary Display Name -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Stakeholder Name <span class="text-rose-500">*</span>
							</label>
							<InputText
								v-model="form.name"
								placeholder="e.g. Acme Enterprise"
								class="w-full"
								:class="{ 'p-invalid': formErrors.name }"
							/>
							<small v-if="formErrors.name" class="text-rose-500 text-xs mt-1 block">{{ formErrors.name }}</small>
						</div>

						<!-- Company / Trade Name -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Company / Trade Name
							</label>
							<InputText
								v-model="form.company_name"
								placeholder="Official legal entity name"
								class="w-full"
							/>
						</div>

						<!-- Auto-ID or Custom Code -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Stakeholder Code / ID
							</label>
							<InputText
								v-model="form.stakeholder_id"
								:placeholder="form.type === 'Customer' ? 'Auto-generated (e.g. CUST-0001)' : 'Auto-generated (e.g. SUPP-0001)'"
								class="w-full font-mono text-sm"
							/>
							<span class="text-[11px] text-slate-400 mt-1 block">Leave empty to auto-generate sequentially.</span>
						</div>

						<!-- Primary Contact Person -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Primary Contact Person
							</label>
							<InputText
								v-model="form.contact_person"
								placeholder="Account representative / manager"
								class="w-full"
							/>
						</div>
					</div>
				</template>
			</Card>

			<!-- Section 2: Contact Information -->
			<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
				<template #title>
					<div class="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-3">
						<i class="pi pi-phone text-emerald-500"></i>
						<span>2. Contact Details</span>
					</div>
				</template>
				<template #content>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
						<!-- Mobile / Phone -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Primary Phone / Mobile
							</label>
							<IconField iconPosition="left">
								<InputIcon class="pi pi-phone text-slate-400" />
								<InputText
									v-model="form.mobile"
									placeholder="+91 98765 43210"
									class="w-full"
									:class="{ 'p-invalid': formErrors.mobile }"
								/>
							</IconField>
							<small v-if="formErrors.mobile" class="text-rose-500 text-xs mt-1 block">{{ formErrors.mobile }}</small>
						</div>

						<!-- Alternate Phone -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Alternate / Landline Phone
							</label>
							<IconField iconPosition="left">
								<InputIcon class="pi pi-phone text-slate-400" />
								<InputText
									v-model="form.alternate_phone"
									placeholder="Secondary office line"
									class="w-full"
								/>
							</IconField>
						</div>

						<!-- Email Address -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Email Address
							</label>
							<IconField iconPosition="left">
								<InputIcon class="pi pi-envelope text-slate-400" />
								<InputText
									v-model="form.email"
									type="email"
									placeholder="contact@business.com"
									class="w-full"
									:class="{ 'p-invalid': formErrors.email }"
								/>
							</IconField>
							<small v-if="formErrors.email" class="text-rose-500 text-xs mt-1 block">{{ formErrors.email }}</small>
						</div>

						<!-- Website -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Website URL
							</label>
							<IconField iconPosition="left">
								<InputIcon class="pi pi-globe text-slate-400" />
								<InputText
									v-model="form.website"
									placeholder="https://company.com"
									class="w-full"
								/>
							</IconField>
						</div>
					</div>
				</template>
			</Card>

			<!-- Section 3: Address Information -->
			<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
				<template #title>
					<div class="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-3">
						<i class="pi pi-map-marker text-rose-500"></i>
						<span>3. Address & Logistics Locations</span>
					</div>
				</template>
				<template #content>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
						<!-- Billing Address -->
						<div class="md:col-span-2">
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Billing Address
							</label>
							<Textarea
								v-model="form.address"
								rows="2"
								placeholder="Registered tax & billing office address"
								class="w-full"
								autoResize
								@input="handleSameAsBilling"
							/>
						</div>

						<!-- Checkbox same as billing -->
						<div class="md:col-span-2 flex items-center gap-2">
							<Checkbox
								v-model="sameAsBilling"
								:binary="true"
								inputId="sameAddress"
								@change="handleSameAsBilling"
							/>
							<label for="sameAddress" class="text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer">
								Shipping address is identical to billing address
							</label>
						</div>

						<!-- Shipping Address -->
						<div v-if="!sameAsBilling" class="md:col-span-2">
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Shipping / Warehouse Delivery Address
							</label>
							<Textarea
								v-model="form.shipping_address"
								rows="2"
								placeholder="Receiving dock / site address"
								class="w-full"
								autoResize
							/>
						</div>

						<!-- City -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								City
							</label>
							<InputText v-model="form.city" placeholder="e.g. Mumbai" class="w-full" />
						</div>

						<!-- State -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								State / Province
							</label>
							<InputText v-model="form.state" placeholder="e.g. Maharashtra" class="w-full" />
						</div>

						<!-- Country -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Country
							</label>
							<InputText v-model="form.country" class="w-full" />
						</div>

						<!-- Postal Code -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Postal Code / PIN
							</label>
							<InputText v-model="form.postal_code" placeholder="400001" class="w-full" />
						</div>
					</div>
				</template>
			</Card>

			<!-- Section 4: Tax & Financial Information -->
			<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
				<template #title>
					<div class="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-3">
						<i class="pi pi-credit-card text-indigo-500"></i>
						<span>4. Tax Identification & Financial Ledger Terms</span>
					</div>
				</template>
				<template #content>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
						<!-- GSTIN / Tax ID -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								GSTIN / VAT / Tax ID
							</label>
							<InputText
								v-model="form.tax_id"
								placeholder="27AAAAA0000A1Z5"
								class="w-full font-mono uppercase text-sm"
								:class="{ 'p-invalid': formErrors.tax_id }"
							/>
							<small v-if="formErrors.tax_id" class="text-rose-500 text-xs mt-1 block">{{ formErrors.tax_id }}</small>
						</div>

						<!-- PAN / Business Registration -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								PAN / Business Reg Number
							</label>
							<InputText
								v-model="form.pan_number"
								placeholder="AAAAA0000A"
								class="w-full font-mono uppercase text-sm"
							/>
						</div>

						<!-- Payment Terms -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Standard Payment Terms
							</label>
							<Select
								v-model="form.payment_terms"
								:options="paymentTermOptions"
								optionLabel="label"
								optionValue="value"
								class="w-full"
							/>
						</div>

						<!-- Credit Limit -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Credit Limit (INR)
							</label>
							<InputNumber
								v-model="form.credit_limit"
								mode="currency"
								currency="INR"
								locale="en-IN"
								class="w-full"
								:min="0"
							/>
							<span class="text-[11px] text-slate-400 mt-1 block">Maximum allowed outstanding orders balance.</span>
						</div>

						<!-- Opening Balance -->
						<div>
							<label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
								Opening Balance Debt (INR)
							</label>
							<InputNumber
								v-model="form.opening_balance"
								mode="currency"
								currency="INR"
								locale="en-IN"
								class="w-full"
							/>
							<span class="text-[11px] text-slate-400 mt-1 block">Initial balance carried forward from legacy records.</span>
						</div>
					</div>
				</template>
			</Card>

			<!-- Section 5: Internal Notes -->
			<Card class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl">
				<template #title>
					<div class="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-3">
						<i class="pi pi-file-edit text-slate-500"></i>
						<span>5. Internal Notes & Instructions</span>
					</div>
				</template>
				<template #content>
					<div class="pt-2">
						<Textarea
							v-model="form.notes"
							rows="3"
							placeholder="Add any specific operational notes, delivery preferences, or credit instructions..."
							class="w-full"
							autoResize
						/>
					</div>
				</template>
			</Card>

			<!-- Bottom Actions -->
			<div class="flex items-center justify-end gap-3 pt-2">
				<Button
					label="Cancel"
					severity="secondary"
					outlined
					@click="goBack"
				/>
				<Button
					type="submit"
					label="Save Master Record"
					icon="pi pi-check"
					severity="primary"
					:loading="loading"
					class="shadow-sm"
				/>
			</div>
		</form>
	</div>
</template>

<style scoped></style>
