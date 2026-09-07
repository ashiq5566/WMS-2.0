<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import moment from "moment";
import axios from "@/plugins/axios";
import { useToast } from "primevue/usetoast";
import {
	formatCurrency,
	getPaymentTypeInfo,
	getPaymentStatusSeverity,
	getPaymentMethodInfo,
	type PaymentRecord,
} from "@/utils/paymentCalculations";
import { setPageTitle } from "@/utils/meta";

const route = useRoute();
const router = useRouter();
const toast = useToast();

const paymentId = route.params.id as string;
const payment = ref<PaymentRecord | null>(null);
const loading = ref(true);

const fetchPayment = async () => {
	try {
		loading.value = true;
		const response = await axios.get(`/api/inventory/payments/${paymentId}/`);
		payment.value = response.data;
		const voucherNum = payment.value?.payment_number || (`#${paymentId}`);
		setPageTitle(`Payment Voucher ${voucherNum}`, `Payment voucher details for ${voucherNum}`);
	} catch (error) {
		console.error("Error fetching payment voucher:", error);
		toast.add({
			severity: "error",
			summary: "Error",
			detail: "Failed to load payment voucher details.",
			life: 4000,
		});
	} finally {
		loading.value = false;
	}
};

const goBack = () => {
	router.push("/payments");
};

const printVoucher = () => {
	window.print();
};

onMounted(() => {
	fetchPayment();
});
</script>

<template>
	<div class="max-w-4xl mx-auto space-y-6 pb-12">
		<!-- Header & Navigation -->
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 print:hidden">
			<div>
				<div class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 mb-1">
					<button @click="goBack" class="hover:text-slate-900 dark:hover:text-white flex items-center gap-1 transition-colors">
						<i class="pi pi-arrow-left text-xs"></i>
						<span>Payments Ledger</span>
					</button>
					<span>/</span>
					<span class="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-700 dark:text-slate-300">
						{{ payment?.payment_number || `VOUCHER-${paymentId}` }}
					</span>
				</div>
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
					Payment Receipt Voucher
				</h1>
			</div>

			<div class="flex items-center gap-2.5">
				<Button
					icon="pi pi-arrow-left"
					label="Back to Payments"
					severity="secondary"
					outlined
					size="small"
					@click="goBack"
				/>
				<Button
					icon="pi pi-print"
					label="Print Voucher"
					severity="primary"
					size="small"
					class="shadow-sm"
					@click="printVoucher"
				/>
			</div>
		</div>

		<!-- Voucher Content Box -->
		<Card v-if="payment" class="shadow-sm border border-slate-200/80 dark:border-slate-800 rounded-xl overflow-hidden print:border-none print:shadow-none">
			<template #content>
				<!-- Printable Header -->
				<div class="border-b border-slate-200 dark:border-slate-800 pb-6 mb-6">
					<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
						<div>
							<span class="text-xs font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400 block mb-1">
								CoreWMS • Financial Settlement
							</span>
							<h2 class="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
								{{ payment.payment_type === 'OUTBOUND' ? 'DISBURSEMENT VOUCHER' : (payment.payment_type === 'REFUND' ? 'REFUND CREDIT NOTE' : 'OFFICIAL PAYMENT RECEIPT') }}
							</h2>
							<p class="text-xs font-mono text-slate-500 mt-1">
								Voucher No: <span class="font-bold text-slate-900 dark:text-white">{{ payment.payment_number || `PAY-${payment.id}` }}</span>
							</p>
						</div>

						<div class="sm:text-right space-y-1">
							<Tag
								:value="getPaymentTypeInfo(payment.payment_type).label"
								:severity="getPaymentTypeInfo(payment.payment_type).severity"
								class="text-xs font-bold uppercase tracking-wider"
							/>
							<div class="text-xs text-slate-500 mt-1">
								<span>Date: </span>
								<span class="font-semibold text-slate-900 dark:text-slate-200">
									{{ payment.payment_date ? moment(payment.payment_date).format('DD MMMM YYYY, hh:mm A') : '—' }}
								</span>
							</div>
							<div class="text-xs text-slate-500">
								<span>Status: </span>
								<Tag
									:value="payment.status || 'Completed'"
									:severity="getPaymentStatusSeverity(payment.status)"
									class="text-[10px]"
								/>
							</div>
						</div>
					</div>
				</div>

				<!-- Partner & Allocation Info Grid -->
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-6 pb-6 border-b border-slate-200 dark:border-slate-800 mb-6">
					<!-- Partner Details -->
					<div class="space-y-2">
						<span class="text-xs font-bold uppercase tracking-wider text-slate-400 block">
							{{ payment.payment_type === 'OUTBOUND' ? 'Beneficiary (Payee)' : 'Received From (Payer)' }}
						</span>
						<div v-if="payment.company_obj">
							<router-link
								:to="`/stakeholders/${payment.company_obj.id}`"
								class="text-base font-bold text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
							>
								{{ payment.company_obj.name }}
							</router-link>
							<p v-if="payment.company_obj.company_name" class="text-xs text-slate-500">
								{{ payment.company_obj.company_name }}
							</p>
							<p v-if="payment.company_obj.address" class="text-xs text-slate-600 dark:text-slate-400 mt-1">
								{{ payment.company_obj.address }}
							</p>
							<div class="text-xs text-slate-500 mt-1 space-y-0.5">
								<p v-if="payment.company_obj.mobile">Phone: {{ payment.company_obj.mobile }}</p>
								<p v-if="payment.company_obj.email">Email: {{ payment.company_obj.email }}</p>
								<p v-if="payment.company_obj.tax_id">GSTIN / Tax ID: <span class="font-mono">{{ payment.company_obj.tax_id }}</span></p>
							</div>
						</div>
						<div v-else class="text-xs text-slate-500 italic">
							General Warehouse Ledger Account
						</div>
					</div>

					<!-- Payment Mechanism Details -->
					<div class="space-y-3 bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
						<span class="text-xs font-bold uppercase tracking-wider text-slate-400 block">
							Settlement Details
						</span>
						<div class="flex items-center justify-between text-xs">
							<span class="text-slate-500">Payment Method:</span>
							<span class="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
								<i :class="getPaymentMethodInfo(payment.payment_method).icon" class="text-slate-400 text-xs"></i>
								{{ getPaymentMethodInfo(payment.payment_method).label }}
							</span>
						</div>
						<div class="flex items-center justify-between text-xs">
							<span class="text-slate-500">Reference / UTR / Cheque:</span>
							<span class="font-mono font-semibold text-slate-900 dark:text-white">
								{{ payment.reference || 'N/A' }}
							</span>
						</div>
						<div class="flex items-center justify-between text-xs">
							<span class="text-slate-500">Transaction ID:</span>
							<span class="font-mono text-slate-600 dark:text-slate-400">#{{ payment.id }}</span>
						</div>
					</div>
				</div>

				<!-- Settlement Amount Spotlight Banner -->
				<div class="bg-blue-50/60 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30 rounded-xl p-5 mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
					<div>
						<span class="text-xs font-bold uppercase tracking-wider text-blue-700 dark:text-blue-300">
							Total Amount Settled
						</span>
						<h3 class="text-3xl font-extrabold text-blue-900 dark:text-blue-100 mt-1">
							{{ formatCurrency(payment.amount) }}
						</h3>
					</div>
					<div class="text-xs text-blue-700/80 dark:text-blue-300/80 max-w-xs">
						Recorded in warehouse accounts journal. Applicable debits/credits updated atomically.
					</div>
				</div>

				<!-- Linked Order Financial Breakdown -->
				<div v-if="payment.order_obj" class="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden mb-6">
					<div class="bg-slate-50 dark:bg-slate-900 px-4 py-2.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
						<span class="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
							Linked Commercial Order: {{ payment.order_obj.order_number }}
						</span>
						<router-link
							:to="`/orders/${payment.order_obj.id}`"
							class="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
						>
							<span>View Order Details</span>
							<i class="pi pi-arrow-up-right text-[10px]"></i>
						</router-link>
					</div>
					<div class="p-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
						<div>
							<span class="text-slate-500 block mb-1">Order Type</span>
							<span class="font-bold text-slate-900 dark:text-white">
								{{ payment.order_obj.order_type === 'PO' ? 'Purchase Order' : 'Sales Order' }}
							</span>
						</div>
						<div>
							<span class="text-slate-500 block mb-1">Total Order Amount</span>
							<span class="font-bold text-slate-900 dark:text-white">
								{{ formatCurrency(payment.order_obj.total_amount) }}
							</span>
						</div>
						<div>
							<span class="text-slate-500 block mb-1">Remaining Balance</span>
							<span
								class="font-bold"
								:class="payment.order_obj.pending_amount > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'"
							>
								{{ formatCurrency(payment.order_obj.pending_amount) }}
							</span>
						</div>
						<div>
							<span class="text-slate-500 block mb-1">Order Status</span>
							<Tag :value="payment.order_obj.order_status" class="text-[10px]" />
						</div>
					</div>
				</div>

				<!-- Notes & Remarks -->
				<div v-if="payment.notes" class="mb-6 p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
					<span class="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
						Internal Operational Notes
					</span>
					<p class="text-xs text-slate-700 dark:text-slate-300">
						{{ payment.notes }}
					</p>
				</div>

				<!-- Signatures / Footer for Print -->
				<div class="pt-8 border-t border-slate-200 dark:border-slate-800 grid grid-cols-2 gap-8 text-center text-xs text-slate-500">
					<div>
						<div class="h-10 border-b border-slate-300 dark:border-slate-700 mb-1"></div>
						<span>Authorized Cashier / Accountant</span>
					</div>
					<div>
						<div class="h-10 border-b border-slate-300 dark:border-slate-700 mb-1"></div>
						<span>Recipient / Stakeholder Signature</span>
					</div>
				</div>
			</template>
		</Card>

		<!-- Skeleton Loader -->
		<Card v-else class="shadow-sm border border-slate-200 dark:border-slate-800 p-8">
			<template #content>
				<div class="py-12 text-center text-slate-400">
					<i class="pi pi-spin pi-spinner text-2xl mb-2 block"></i>
					<span>Loading payment voucher...</span>
				</div>
			</template>
		</Card>
	</div>
</template>

<style scoped>
@media print {
	body {
		background: white !important;
		color: black !important;
	}
}
</style>
