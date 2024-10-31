<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from '@/plugins/axios';

const returns = ref();

// const getSeverity = (status) => {
// 	switch (status) {
// 		case 'Issued':
// 			return 'warn';

// 		case 'Delivered':
// 			return 'success';

// 		case 'Recieved':
// 			return 'info';

// 		case 'Cancelled':
// 			return 'warn';

// 		case 'Closed':
// 			return 'danger';
// 	}
// }

const fetchReturns = async () => {
	try {
		const response = await axios.get('/api/inventory/returns');

		returns.value = response.data;
	} catch (error) {
		console.error('Error fetching returns:', error);
	}
}

onMounted(() => {
	fetchReturns();
})


</script>

<template>
	<div class="">
		<div class="flex justify-end">
			<router-link :to="{ name: 'returns-create' }">
				<Button label="Create Return" />
			</router-link>
		</div>
		<Card class="mt-4">
			<template #content>
				<DataTable :value="returns" tableStyle="min-width: 50rem">
					<Column field="id" header="ID#">
						<template #body="slotProps">
							<router-link :to="{ name: 'returns-id', params: { id: slotProps.data.id } }">
								<span class="font-bold">
									{{ slotProps.data.id }}
								</span>
							</router-link>
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