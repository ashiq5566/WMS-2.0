<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import axios from '@/plugins/axios';
import AddStakeHolderModal from "@/components/stakeholders/AddStakeHolderModal.vue";
import Column from "primevue/column";

const stakeholders = ref();
const selectedType = ref();
const selectedStatus = ref();
const searchInput = ref('');
const typeOptions = ref([
	{ label: 'Customer', value: 'Customer' },
	{ label: 'Supplier', value: 'Supplier' }
]);

const statusOptions = ref([
	{ label: 'ACTIVE', value: 'false' },
	{ label: 'INACTIVE', value: 'true' }
]);

const fetchStakeholders = async (search) => {
	try {
		const response = await axios.get('/api/accounts/stakeholders', {
			params: {
				search,
				type: selectedType.value,
				is_deleted: selectedStatus.value
			}
		});
		stakeholders.value = response.data;
	} catch (error) {
		console.error('Error fetching stakeholders:', error);
	}
}

const getSeverity = (status) => {
	switch (status) {
		case true:
			return 'danger';
		case false:
			return 'success';
	}
}

watch(searchInput, (newVal) => {
	fetchStakeholders(newVal);
});

const reloadTable = () => {
	fetchStakeholders();
};

watch(selectedType, () => {
	fetchStakeholders()
})

watch(selectedStatus, () => {
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
				<DataTable :value="stakeholders" tableStyle="min-width: 50rem" sortField="is_deleted" :sortOrder="1">
					<template #header>
						<div class="flex justify-end gap-4">
							<Select v-model="selectedStatus" :options="statusOptions" optionLabel="label"
								option-value="value" placeholder="Select Status" class="mr-4" filter show-clear />
							<Select v-model="selectedType" :options="typeOptions" optionLabel="label"
								option-value="value" placeholder="Select Type" class="mr-4" filter show-clear />
							<IconField>
								<InputIcon>
									<i class="pi pi-search" />
								</InputIcon>
								<InputText v-model="searchInput" placeholder="Keyword Search" />
							</IconField>
							<AddStakeHolderModal @instance-added="reloadTable" />
						</div>
					</template>
					<Column field="stakeholder_id" header="ID">
					</Column>
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
					<Column field="type" header="Type" sortable></Column>
					<Column field="order_status" header="Status">
						<template #body="slotProps">
							<Tag :value="slotProps.data.is_deleted == false ? 'ACTIVE' : 'INACTIVE'"
								:severity="getSeverity(slotProps.data.is_deleted)" />
						</template>
					</Column>
					<template #empty>
						<span class="flex justify-center">No stakeholders found.</span>
					</template>
				</DataTable>
			</template>
		</Card>
	</div>
</template>

<style></style>
