<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import moment from 'moment';
import { debounce } from 'lodash';


const payments = ref();
const filterDates = ref();


const fetchPayments = async () => {
	try {
		const response = await axios.get('/api/inventory/payments', {
			params: {
				payment_date__gte: filterDates.value ? filterDates.value[0] : null,
				payment_date__lte: filterDates.value ? filterDates.value[1] : null,
			}
		});

		payments.value = response.data;
	} catch (error) {
		console.error('Error fetching payments:', error);
	}
}
const debouncedFetchOrders = debounce(fetchPayments, 300);

watch(filterDates, (newVal) => {
	debouncedFetchOrders();
});

onMounted(() => {
	fetchPayments();
})


</script>

<template>
	<div class="">
		<div class="flex justify-end">
		</div>
		<Card class="mt-4">
			<template #content>
				<DataTable :value="payments" tableStyle="min-width: 50rem">
					<template #header>
						<div class="flex justify-end">
							<DatePicker v-model="filterDates" selectionMode="range" :manualInput="false" class="mr-4"
								placeholder="Date Range" showIcon />
						</div>
					</template>
					<Column field="id" header="ID#"></Column>
					<Column field="payment_date" header="Date" sortable>
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
			</template>
		</Card>
	</div>
</template>

<style></style>