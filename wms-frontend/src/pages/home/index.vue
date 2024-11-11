<template>
	<div>
		<div class="grid grid-cols-2 gap-4">
			<stockChart class="col-span-1" />
			<sales-payment-chart class="col-span-1" />
		</div>
		<div class="grid grid-cols- gap-4 mt-4">

			<Card>
				<template #title>Accounts Payable(Purchases)</template>
			</Card>
			<Card>
				<template #title>Turn Over</template>
			</Card>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '@/plugins/axios'
import stockChart from '@/components/home/stockChart.vue';
import salesPaymentChart from '@/components/home/salesPaymentChart.vue';

</script>