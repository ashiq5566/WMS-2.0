<script setup lang="ts">
import { ref } from "vue";
import moment from 'moment';
import axios from '@/plugins/axios'
import { useToast } from 'primevue/usetoast';

const emit = defineEmits(['instance-added']);
const selectedMethod = ref('')
const toast = useToast();
const props = defineProps({
	payments: {
		type: Array,
		required: true,
	},
	pendingAmount: {
		type: String,
		required: true,
	},
	orderId: {
		type: String,
		required: true,
	},
	companyId: {
		type: String,
		required: true,
	},
});
const blankData =
{
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
	{ value: 'OTHER', label: 'OTHER' },
]

const addPayment = async () => {

	if (Number(formData.value.amount) > 0 && selectedMethod.value && Number(formData.value.amount) <= Number(props.pendingAmount) && Number(props.pendingAmount) != 0) {

		formData.value.order = props.orderId
		formData.value.company = props.companyId
		formData.value.method = selectedMethod.value

		const response = await axios.post('/api/inventory/payments/', formData.value)
		//set emit when add performed
		toast.add({ severity: 'success', summary: 'Success', detail: `Payment Added`, life: 3000 });
		emit('instance-added');
		formData.value = JSON.parse(JSON.stringify(blankData));
		selectedMethod.value = '';
	} else {
		toast.add({ severity: 'error', summary: 'Error', detail: `Enter a valid method or Amount`, life: 3000 });
	}
}
</script>

<template>
	<div class="">
		<!-- <div class="flex justify-end">
			<InputText class="mr-4 w-1/4" type="text" v-model="props.pendingAmount" disabled />
			<Select v-model="selectedMethod" :options="methods" optionLabel="label" option-value="value"
				placeholder="Select method" class="mr-4" />
			<InputText class="mr-4 w-1/4" type="text" v-model="formData.amount" placeholder="Amount" />
			<Button icon="pi pi-plus" aria-label="Save" @click="addPayment" />
		</div> -->
		<DataTable :value="props.payments" tableStyle="min-width: 30rem" scrollHeight="300px">
			<Column field="id" header="ID#"></Column>
			<Column field="payment_date" header="Date">
				<template #body="slotProps">
					{{ moment(slotProps.data.payment_date).format('DD/MM/YYYY') }}
				</template>
			</Column>
			<Column field="order" header="Order No">
				<template #body="slotProps">
					{{ slotProps.data.order_obj.order_number }}
				</template>
			</Column>
			<Column field="amount" header="Amount"></Column>
			<Column field="payment_method" header="Method">
			</Column>
			<template #empty>
				<span class="flex justify-center">No Payments found.</span>
			</template>
		</DataTable>
	</div>
</template>

<style></style>