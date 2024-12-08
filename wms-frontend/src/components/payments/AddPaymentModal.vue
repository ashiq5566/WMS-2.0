<script setup lang="ts">
import { ref, watch } from "vue";
import axios from '@/plugins/axios.js';
import { onMounted } from "vue";

const emit = defineEmits(['instance-added']);
const visible = ref(false);
const selectedMethod = ref('');
const selectedCompany = ref('');
const stakeholders = ref([]);
const nextBillToClear = ref('');
const formData = ref()

const blankData = {
	company: '',
	amount: '',
	payment_method: '',
	payment_date: '',
};
formData.value = ref(JSON.parse(JSON.stringify(blankData)));
const clearFormData = () => {
	formData.value = JSON.parse(JSON.stringify(blankData));
	selectedMethod.value = '';
	selectedCompany.value = '';
	nextBillToClear.value = '';
}
const methods = [
	{ value: 'CASH', label: 'CASH' },
	{ value: 'CARD', label: 'Card' },
	{ value: 'BANK', label: 'BANK' },
	{ value: 'OTHER', label: 'OTHER' },
]

const fetchStakeholders = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders/');
		stakeholders.value = response.data
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}
const handleSubmit = async () => {
	try {
		formData.value.company = selectedCompany.value;
		formData.value.payment_method = selectedMethod.value;
		formData.value.payment_date = new Date(formData.value.payment_date).toISOString();
		const response = await axios.post('/api/inventory/payments/', formData.value);
		visible.value = false;
		clearFormData();
		emit('instance-added');
	} catch (error) {
		console.error('Creation failed:', error);
	}
};

const cancel = async () => {
	visible.value = false;
	clearFormData();
}

//watch selectedCompany and fetch selected company details ffrom stakeholder.value
watch(selectedCompany, (newVal, oldVal) => {
	if (newVal) {
		const selectedStakeholder = stakeholders.value.find((s) => s.id === newVal);
		nextBillToClear.value = selectedStakeholder.next_bill_to_clear

	}
});

onMounted(() => {
	fetchStakeholders();
})

</script>

<template>
	<div class="">
		<div class="flex justify-end">
			<Button label="Add" @click="visible = true" />
		</div>
		<Dialog v-model:visible="visible" modal header="Add Payments" :style="{ width: '40rem' }">
			<div class="flex items-center gap-4 mb-8">
				<label for="type" class="font-semibold w-32">Company</label>
				<Select v-model="selectedCompany" :options="stakeholders" optionLabel="name" optionValue="id"
					placeholder="Select a Company" class="w-[450px]" />
			</div>
			<div v-if="selectedCompany" class="flex items-center gap-4 mb-4">
				<label for="bill" class="font-semibold w-32">Next Bill To Cle</label>
				<InputText id="bill" v-model="nextBillToClear.order_number" class="flex-auto" disabled />
			</div>
			<div v-if="selectedCompany" class="flex items-center gap-4 mb-4">
				<label for="amount" class="font-semibold w-32">Pending Amount</label>
				<InputText id="amount" v-model="nextBillToClear.pending_amount" class="flex-auto" disabled />
			</div>
			<div class="flex items-center gap-4 mb-8">
				<label for="type" class="font-semibold w-32">Method</label>
				<Select v-model="selectedMethod" :options="methods" optionLabel="label" optionValue="value"
					placeholder="Select a method" class="w-[450px]" />
			</div>
			<div class="flex items-center gap-4 mb-4">
				<label for="amount" class="font-semibold w-32">Amount</label>
				<InputText id="amount" v-model="formData.amount" class="flex-auto" autocomplete="off" />
			</div>
			<div class="flex items-center gap-4 mb-4">
				<label for="date" class="font-semibold w-32">Date</label>
				<DatePicker v-model="formData.payment_date" show-icon />
			</div>
			<div class="flex justify-end gap-2">
				<Button type="button" label="Cancel" severity="secondary" @click="cancel"></Button>
				<Button type="submit" label="Save" @click="handleSubmit()"></Button>
			</div>
		</Dialog>
	</div>
</template>

<style></style>
