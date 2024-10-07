<script setup>
import { useRoute } from 'vue-router'
import axios from '@/plugins/axios'
import { ref, onMounted } from 'vue'

const route = useRoute()
const stakeholder = ref([])

const fetchStakeHolder = async () => {
	const response = await axios.get(`/api/accounts/stakeholders/${route.params.id}`)
	stakeholder.value = response.data
}

onMounted(() => {
	fetchStakeHolder();
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
					<div class="flex flex-col space-y-4">
						<div class="flex items-center">
							<label for="name" class="w-24">Name</label>
							<InputText type="text" id="name" v-model="stakeholder.name" disabled />
						</div>
						<div class="flex items-center">
							<label for="email" class="w-24">Email</label>
							<InputText type="email" id="email" v-model="stakeholder.email" disabled />
						</div>
						<div class="flex items-center">
							<label for="mobile" class="w-24">Phone</label>
							<InputText type="text" id="mobile" v-model="stakeholder.mobile" disabled />
						</div>
						<div class="flex items-center">
							<label for="address" class="w-24">Address</label>
							<InputText type="text" id="address" v-model="stakeholder.address" disabled />
						</div>
						<div class="flex items-center">
							<label for="type" class="w-24">Type</label>
							<InputText type="text" id="type" v-model="stakeholder.type" disabled />
						</div>
					</div>
				</template>
			</Card>
			<Card class="col-span-2 lg:col-span-1">
				<template #title>
					<span>Ongoing Bills</span>
				</template>
			</Card>
			<Card class="col-span-2 lg:col-span-1">
				<template #title>
					<span>Closed Bills</span>
				</template>
			</Card>
		</div>
	</div>
</template>
