<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import AddStakeHolderModal from "@/components/stakeholders/AddStakeHolderModal.vue";

const stakeholders = ref();
const selectedType = ref();
const searchInput = ref('');
const typeOptions = ref([
	{ label: 'Customer', value: 'Customer' },
	{ label: 'Supplier', value: 'Supplier' }
]);

const fetchStakeholders = async (search) => {
	try {
		const response = await axios.get('/api/accounts/stakeholders', {
			params: {
				search,
				type: selectedType.value
			}
		});
		stakeholders.value = response.data;
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}

watch(searchInput, (newVal) => {
	fetchStakeholders(newVal);
});

const reloadTable = () => {
	fetchStakeholders();
};

watch(selectedType, (newVal) => {
	fetchStakeholders()
})

onMounted(() => {
	fetchStakeholders();
})


</script>

<template>
	<div class="">
		<Card class="mt-4">
			<template #content>
				<DataTable :value="stakeholders" tableStyle="min-width: 50rem">
					<template #header>
						<div class="flex justify-end gap-4">
							<Select v-model="selectedType" :options="typeOptions" optionLabel="label" option-value="value"
								placeholder="Select Type" class="mr-4" filter show-clear />
							<IconField>
								<InputIcon>
									<i class="pi pi-search" />
								</InputIcon>
								<InputText v-model="searchInput" placeholder="Keyword Search" />
							</IconField>
							<AddStakeHolderModal @instance-added="reloadTable" />
						</div>
					</template>
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
