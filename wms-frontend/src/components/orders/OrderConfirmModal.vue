<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useRouter } from 'vue-router';


const props = defineProps({
	items: {
		type: Array,
		required: true,
	},
	grossAmount: {
		type: Number,
		required: true,
	}
});

const router = useRouter();

const emit = defineEmits(['order-confirmed']);
const visible = ref(false);
const discountAmount = ref(0);
const downPayment = ref(0);
const paymentType = ref('');

const updatedGrossAmount = ref(props.grossAmount);
const methods = [
	{ value: 'CASH', label: 'CASH' },
	{ value: 'CARD', label: 'Card' },
	{ value: 'BANK', label: 'BANK' },
	{ value: 'OTHER', label: 'OTHER' },
]

const handleSubmit = () => {
	emit('order-confirmed', discountAmount.value, updatedGrossAmount.value, downPayment.value, paymentType.value);
	visible.value = false;
	router.push('/orders');
}

watch(() => props.grossAmount, (newValue) => {
	updatedGrossAmount.value = newValue;
}, { immediate: true });

watch(discountAmount, (newValue) => {
	console.log("Discount Amount Updated:", newValue);
	updatedGrossAmount.value = props.grossAmount - newValue;
}, { immediate: true });


</script>

<template>
	<div class="">
		<div class="flex justify-end">
			<Button label="Confirm" @click="visible = true" />
		</div>
		<Dialog v-model:visible="visible" modal header="Edit Profile" :style="{ width: '40rem' }">
			<DataTable :value="items" tableStyle="min-width: 20rem">
				<Column field="product_name" header="Product"></Column>
				<Column field="quantity" header="Quantity"></Column>
				<Column field="price_at_time_of_order" header="Unit Price"></Column>
				<Column field="total" header="Total"></Column>
				<template #empty>
					<span class="flex justify-center">No Orders found.</span>
				</template>
			</DataTable>
			<div class="flex justify-end">
				<InputText class="my-4" type="text" v-model="discountAmount" placeholder="Discount" />
			</div>
			<div class="flex justify-end">
				<InputText class="my-4" type="text" v-model="downPayment" placeholder="Down Payment" />
			</div>
			<div class="flex justify-end">
				<Select class="my-4" v-model="paymentType" :options="methods" optionLabel="label" option-value="value"
					placeholder="Payment Type" />
			</div>
			<div class="flex justify-end mt-4">
				<span class="font-bold">Total Gross Amount: {{ updatedGrossAmount }}</span>
			</div>
			<div class="flex justify-end mt-4">
				<Button type="submit" label="Confirm" @click="handleSubmit()"></Button>
			</div>
		</Dialog>
	</div>
</template>

<style></style>
