<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import moment from "moment";
import { debounce } from 'lodash';

const returnTypes = [
	{ label: "PR", value: "PR" },
	{ label: "SR", value: "SR" },
]

const returns = ref();
const selectedType = ref();
const selectedDates = ref();
const stakeholders = ref();
const selectedStakeholder = ref();

const fetchReturns = async () => {
	try {
		const response = await axios.get('/api/inventory/returns', {
			params: {
				return_type: selectedType.value,
				date_added__gte: selectedDates.value ? selectedDates.value[0] : null,
				date_added__lte: selectedDates.value ? selectedDates.value[1] : null,
				original_order__stakeholder: selectedStakeholder.value
			}
		});

		returns.value = response.data;
	} catch (error) {
		console.error('Error fetching returns:', error);
	}
}

const fetchStakeholders = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders/');
		stakeholders.value = response.data.map(item => ({ value: item.id, label: item.name }));
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}
const debouncedFetchReturns = debounce(fetchReturns, 300);

watch(selectedDates, (newVal) => {
	debouncedFetchReturns();
});

watch(selectedType, (newVal) => {
	debouncedFetchReturns();
});

watch(selectedStakeholder, (newVal) => {
	debouncedFetchReturns();
});


onMounted(() => {
	fetchReturns();
	fetchStakeholders();
})


</script>

<template>
	<div class="">
		<Card class="mt-4">
			<template #content>
				<DataTable :value="returns" tableStyle="min-width: 50rem">
					<template #header>
						<div class="flex justify-end gap-4">
							<Select v-model="selectedStakeholder" :options="stakeholders" optionLabel="label" option-value="value"
								placeholder="Select Stakeholder" class="mr-4" filter showClear />
							<Select v-model="selectedType" :options="returnTypes" optionLabel="label" option-value="value"
								placeholder="Select Type" class="mr-4" showClear />
							<DatePicker v-model="selectedDates" selectionMode="range" :manualInput="false" placeholder="Date Range"
								showIcon />
							<router-link :to="{ name: 'returns-create' }">
								<Button label="Create Return" />
							</router-link>
						</div>
					</template>
					<Column field="id" header="ID#">
						<template #body="slotProps">
							<router-link :to="{ name: 'returns-id', params: { id: slotProps.data.id } }">
								<span class="font-bold">
									{{ slotProps.data.id }}
								</span>
							</router-link>
						</template>
					</Column>
					<Column field="company" header="Company">
						<template #body="slotProps">
							{{ slotProps.data.order_obj.stakeholder_obj.name }}
						</template>
					</Column>
					<Column field="return_type" header="Return Date" sortable>
						<template #body="slotProps">
							<span>{{ moment(slotProps.data.date_added).format('DD/MM/YYYY') }}</span>
						</template>
					</Column>
					<Column field="return_type" header="Return Type"></Column>
					<Column field="original_order" header="Order No">
						<template #body="slotProps">
							<span>{{ slotProps.data.order_obj.order_number }}</span>
						</template>
					</Column>
					<template #empty>
						<span class="flex justify-center">No Orders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>