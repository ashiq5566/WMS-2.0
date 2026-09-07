<script setup lang="ts">
import { ref } from "vue";
import moment from 'moment';
import axios from '@/plugins/axios';
import { useToast } from 'primevue/usetoast';
import { useRouter } from 'vue-router';
import { formatCurrency, getMethodBadgeClass } from '@/utils/paymentCalculations';

const router = useRouter();
const emit = defineEmits(['instance-added']);
const selectedMethod = ref('');
const toast = useToast();
const props = defineProps({
	payments: {
		type: Array,
		required: true,
	},
	pendingAmount: {
		type: [String, Number],
		required: true,
	},
	orderId: {
		type: [String, Number],
		required: true,
	},
	companyId: {
		type: [String, Number],
		required: true,
	},
});
const blankData = {
	method: '',
	amount: '',
	order: '',
	company: '',
};
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const methods = [
	{ value: 'CASH', label: 'CASH' },
	{ value: 'CARD', label: 'Card' },
	{ value: 'BANK', label: 'BANK' },
	{ value: 'UPI', label: 'UPI' },
	{ value: 'OTHER', label: 'OTHER' },
];

const addPayment = async () => {
	if (Number(formData.value.amount) > 0 && selectedMethod.value && Number(formData.value.amount) <= Number(props.pendingAmount) && Number(props.pendingAmount) != 0) {
		formData.value.order = props.orderId;
		formData.value.company = props.companyId;
		formData.value.payment_method = selectedMethod.value;

		try {
			await axios.post('/api/inventory/payments/', formData.value);
			toast.add({ severity: 'success', summary: 'Success', detail: 'Payment Added Successfully', life: 3000 });
			emit('instance-added');
			formData.value = JSON.parse(JSON.stringify(blankData));
			selectedMethod.value = '';
		} catch (error: any) {
			const errMsg = error.response?.data?.amount || error.response?.data?.detail || 'Failed to record payment';
			toast.add({ severity: 'error', summary: 'Payment Failed', detail: String(errMsg), life: 4000 });
		}
	} else {
		toast.add({ severity: 'error', summary: 'Invalid Input', detail: 'Enter a valid method and amount within pending balance', life: 3000 });
	}
};
</script>

<template>
	<div class="space-y-4">
		<DataTable :value="props.payments" tableStyle="min-width: 28rem" scrollHeight="320px" class="p-datatable-sm">
			<Column field="payment_number" header="Payment #">
				<template #body="slotProps">
					<button
						type="button"
						class="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
						@click="router.push(`/payments/${slotProps.data.id}`)"
					>
						{{ slotProps.data.payment_number || ('#' + slotProps.data.id) }}
					</button>
				</template>
			</Column>
			<Column field="payment_date" header="Date">
				<template #body="slotProps">
					<span class="text-xs text-slate-600 dark:text-slate-400">
						{{ slotProps.data.payment_date ? moment(slotProps.data.payment_date).format('DD/MM/YYYY') : '-' }}
					</span>
				</template>
			</Column>
			<Column field="amount" header="Amount">
				<template #body="slotProps">
					<span class="font-semibold text-emerald-600 dark:text-emerald-400 text-xs">
						{{ formatCurrency(slotProps.data.amount) }}
					</span>
				</template>
			</Column>
			<Column field="payment_method" header="Method">
				<template #body="slotProps">
					<span :class="getMethodBadgeClass(slotProps.data.payment_method)">
						{{ slotProps.data.payment_method || 'CASH' }}
					</span>
				</template>
			</Column>
			<template #empty>
				<div class="py-6 text-center text-xs text-slate-500 dark:text-slate-400">
					<i class="pi pi-credit-card text-2xl mb-1 text-slate-300 dark:text-slate-600 block"></i>
					No payments recorded for this order yet.
				</div>
			</template>
		</DataTable>
	</div>
</template>

<style scoped></style>