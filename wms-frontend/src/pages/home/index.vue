<template>
	<div>
		<div class="grid grid-cols-2 gap-4">
			<stockChart class="col-span-1" />
			<salesPaymentChart class="col-span-1" />
		</div>
		<div class="grid grid-cols-2 gap-4 mt-4">
			<purchasePaymentChart class="col-span-1" />
			<Card>
				<template #title>Turn Over</template>
			</Card>
		</div>
	</div>
</template>

<script setup>
import stockChart from '@/components/home/stockChart.vue';
import salesPaymentChart from '@/components/home/salesPaymentChart.vue';
import purchasePaymentChart from '@/components/home/purchasePaymentChart.vue';

</script>