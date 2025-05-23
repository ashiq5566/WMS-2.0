<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import moment from 'moment';
import axios from '@/plugins/axios'
import { useToast } from 'primevue/usetoast';

const toast = useToast();
const route = useRoute()
const stakeholder = ref([])
const ongoingBills = ref([])
const closedBills = ref([])
const transactions = ref([])

const fetchStakeHolder = async () => {
	const response = await axios.get(`/api/accounts/stakeholders/${route.params.id}`)
	stakeholder.value = response.data
}

const fetchBills = async () => {
	try {
		const response = await axios.get('/api/inventory/orders', {
			params: {
				stakeholder_id: stakeholder.value.id
			},
		});

		ongoingBills.value = response.data.filter(bill => bill.order_status === 'Issued');
		closedBills.value = response.data.filter(bill => bill.order_status === 'Closed');
		const net_amount = response.data.reduce((sum, bill) => sum + bill.net_amount, 0);

	} catch (error) {
		console.error('Error fetching return Bills:', error);
	}
}

const fetchTransactions = async () => {
	try {
		const response = await axios.get('/api/inventory/payments', {
			params: {
				company__id: stakeholder.value.id
			},
		});
		transactions.value = response.data;
	} catch (error) {
		console.error('Error fetching return Bills:', error);
	}
}

// Calculate the progress percentage
const progressPercentage = computed(() =>
	stakeholder.value.total_pending_amount > 0
		? (stakeholder.value.total_setteled_amount / stakeholder.value.total_pending_amount) * 100
		: 0
);

const onUpdate = async () => {
	try {
		const response = await axios.put(`/api/accounts/stakeholders/${route.params.id}/`, stakeholder.value);
		toast.add({ severity: 'success', summary: 'Success', detail: `Profile Updated SuccessFully`, life: 3000 });
	} catch (error) {
		toast.add({ severity: 'error', summary: 'Error', detail: `${error.message}`, life: 3000 });
	}
}

const changeStatus = async () => {
	try {
		// if (stakeholder.value.is_deleted == false) { 

		// }
		const response = await axios.patch(`/api/accounts/stakeholders/${route.params.id}/`, {
			is_deleted: !stakeholder.value.is_deleted,
		});
		fetchStakeHolder()
		toast.add({ severity: 'success', summary: 'Success', detail: `Status Updated SuccessFully`, life: 3000 });
	} catch (error) {
		toast.add({ severity: 'error', summary: 'Error', detail: `${error.message}`, life: 3000 });
	}
}

onMounted(async () => {
	await fetchStakeHolder();
	await fetchBills();
	await fetchTransactions();
})
</script>

<template>
	<div>
		<div class="grid grid-cols-2 gap-4">
			<Card class="col-span-2 lg:col-span-1">
				<template #title>
					<h4 class="font-bold">Contact Details</h4>
				</template>
				<template #content>
					<div class="grid grid-cols-2 gap-4">
						<div class="flex items-center">
							<label for="name" class="w-20">Name</label>
							<InputText type="text" id="name" v-model="stakeholder.name" />
						</div>
						<div class="flex items-center">
							<label for="email" class="w-20">Email</label>
							<InputText type="email" id="email" v-model="stakeholder.email" />
						</div>
						<div class="flex items-center">
							<label for="mobile" class="w-20">Phone</label>
							<InputText type="text" id="mobile" v-model="stakeholder.mobile" />
						</div>
						<div class="flex items-center">
							<label for="address" class="w-20">Address</label>
							<InputText type="text" id="address" v-model="stakeholder.address" />
						</div>
						<div class="flex items-center">
							<label for="type" class="w-20">Type</label>
							<InputText type="text" id="type" v-model="stakeholder.type" disabled />
						</div>
						<div class="flex items-center">
							<label for="type" class="w-20">Pending</label>
							<InputText type="text" id="type" v-model="stakeholder.total_pending_amount" disabled />
						</div>
						<div class="flex col-span-2 justify-end gap-2">
							<Button label="Update" @click="onUpdate" />
							<Button :label="stakeholder.is_deleted == false ? 'Deactivate' : 'Activate'"
								:severity="stakeholder.is_deleted == false ? 'warn' : 'success'" @click="changeStatus" />
						</div>
					</div>
				</template>
			</Card>
			<Card class="col-span-2 lg:col-span-1">
				<template #title>
					<span>Ongoing Bills</span>
				</template>
				<template #content>
					<DataTable :value="ongoingBills" tableStyle="min-width: 30rem" scrollHeight="300px">
						<Column field="id" header="ID#">
							<template #body="slotProps">
								<router-link :to="{ name: 'orders-id', params: { id: slotProps.data.id } }">
									<span class="font-bold">
										{{ slotProps.data.id }}
									</span>
								</router-link>
							</template>
						</Column>
						<Column field="order_number" header="Order Number"></Column>
						<Column field="net_amount" header="Net Amount"></Column>
						<Column field="pending_amount" header="Pending Amount"></Column>
						<template #empty>
							<span class="flex justify-center">No Orders found.</span>
						</template>
					</DataTable>
				</template>
			</Card>
			<Card class="col-span-2 lg:col-span-1">
				<template #title>
					<span>Closed Bills</span>
				</template>
				<template #content>
					<DataTable :value="closedBills" tableStyle="min-width: 30rem" scrollHeight="300px">
						<Column field="id" header="ID#">
							<template #body="slotProps">
								<router-link :to="{ name: 'orders-id', params: { id: slotProps.data.id } }">
									<span class="font-bold">
										{{ slotProps.data.id }}
									</span>
								</router-link>
							</template>
						</Column>
						<Column field="order_number" header="Order Number"></Column>
						<Column field="net_amount" header="Net Amount"></Column>
						<template #empty>
							<span class="flex justify-center">No Orders found.</span>
						</template>
					</DataTable>
				</template>
			</Card>
			<Card class="col-span-2 lg:col-span-1">
				<template #title>
					<span>Transactions</span>
				</template>
				<template #content>
					<DataTable :value="transactions" tableStyle="min-width: 30rem;" scrollHeight="300px">
						<Column field="id" header="ID#"></Column>
						<Column field="payment_date" header="Date" sortable>
							<template #body="slotProps">
								{{ moment(slotProps.data.payment_date).format('DD/MM/YYYY') }}
							</template>
						</Column>
						<Column field="order" header="Order No">
							<template #body="slotProps">
								{{ slotProps.data.order_obj?.order_number }}
							</template>
						</Column>
						<Column field="amount" header="Amount"></Column>
						<Column field="payment_method" header="Method">
						</Column>
						<template #footer>
							<div class="flex justify-end items-center">
								<label for="total">Total Paid:</label>
								<span class="text-red-500 font-bold ml-2 text-xl">{{ stakeholder.total_setteled_amount }}/-</span>
							</div>
						</template>
						<template #empty>
							<span class="flex justify-center">No Payments found.</span>
						</template>
					</DataTable>
				</template>
			</Card>
		</div>
	</div>
</template>
