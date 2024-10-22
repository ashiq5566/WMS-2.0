<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from '@/plugins/axios';
import AddStakeHolderModal from "@/components/stakeholders/AddStakeHolderModal.vue";

const stakeholders = ref();

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
					<Column field="name" header="Name">
						<template #body="slotProps">
							<router-link :to="{ name: 'stakeholders-id', params: { id: slotProps.data.id } }">
								<span class="font-bold">
									{{ slotProps.data.name }}
								</span>
							</router-link>
						</template>
					</Column>
					<Column field="address" header="Address"></Column>
					<Column field="mobile" header="Phone"></Column>
					<Column field="email" header="Email"></Column>
					<Column field="type" header="Type"></Column>
					<template #empty>
						<span class="flex justify-center">No stakeholders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>
