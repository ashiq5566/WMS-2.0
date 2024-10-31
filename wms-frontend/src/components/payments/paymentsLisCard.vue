<script setup lang="ts">
import { ref } from "vue";
import moment from 'moment';
import axios from '@/plugins/axios'

const emit = defineEmits(['instance-added']);
const selectedMethod = ref('')
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
});
const blankData =
{
	method: '',
	amount: '',
	order: '',
};
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const methods = [
	{ value: 'CASH', label: 'CASH' },
	{ value: 'CARD', label: 'Card' },
	{ value: 'BANK', label: 'BANK' },
	{ value: 'OTHER', label: 'OTHER' },
]

const addPayment = async () => {
	if (formData.value.amount > 0 && selectedMethod.value) {

		formData.value.order = props.orderId
		formData.value.method = selectedMethod.value

		const response = await axios.post('/api/inventory/payments/', formData.value)
		//set emit when add performed
		emit('instance-added');
		formData.value = JSON.parse(JSON.stringify(blankData));
		selectedMethod.value = '';
	} else {
		alert('Please enter valid amount and select payment method.');
	}
}
</script>

<template>
	<div class="">
		<div class="flex justify-end">
			<InputText class="mr-4 w-1/4" type="text" v-model="props.pendingAmount" disabled />
			<Select v-model="selectedMethod" :options="methods" optionLabel="label" option-value="value"
				placeholder="Select method" class="mr-4" />
			<InputText class="mr-4 w-1/4" type="text" v-model="formData.amount" placeholder="Amount" />
			<Button icon="pi pi-plus" aria-label="Save" @click="addPayment" />
		</div>
		<DataTable :value="props.payments" tableStyle="min-width: 50rem">
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