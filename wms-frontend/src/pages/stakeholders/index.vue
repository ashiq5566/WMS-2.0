<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from '@/plugins/axios';
import AddStakeHolderModal from "@/components/stakeholders/AddStakeHolderModal.vue";

const stakeholders = ref();

const columns = [
	{ field: 'name', header: 'Name' },
	{ field: 'address', header: 'Address' },
	{ field: 'mobile', header: 'Phone' },
	{ field: 'email', header: 'Email' },
	{ field: 'type', header: 'Type' }
];

const fetchStakeholders = async () => {
	try {
		const response = await axios.get('/api/accounts/stakeholders');
		console.log("Stakeholders", response);

		stakeholders.value = response.data;
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}
const reloadTable = () => {
	fetchStakeholders();
};

onMounted(() => {
	fetchStakeholders();
})


</script>

<template>
	<div class="">
		<AddStakeHolderModal @instance-added="reloadTable" />
		<Card class="mt-4">
			<template #content>
				<DataTable :value="stakeholders" tableStyle="min-width: 50rem">
					<Column v-for="col of columns" :key="col.field" :field="col.field" :header="col.header"></Column>
					<template #empty>
						<span class="flex justify-center">No stakeholders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>
