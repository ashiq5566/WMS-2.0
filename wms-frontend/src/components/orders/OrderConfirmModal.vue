<script setup lang="ts">
import { ref, watch, computed } from "vue";
import axios from '@/plugins/axios.js';


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

const emit = defineEmits(['order-confirmed']);
const visible = ref(false);
const discountAmount = ref(0);
const updatedGrossAmount = ref(props.grossAmount);


const handleSubmit = () => {
	emit('order-confirmed', discountAmount.value, updatedGrossAmount.value);
	visible.value = false;
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
