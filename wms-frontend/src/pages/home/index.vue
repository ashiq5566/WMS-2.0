<template>
	<div>
		<div class="grid grid-cols-3 gap-4 mb-4">
			<div class="flex col-span-2 gap-2">
				<Card class="w-1/2">
					<template #title>
						Sales Overview
					</template>
					<template #content>
						<div class="flex flex-col gap-4">
							<div class="border border-gray-300 rounded-lg p-4 flex">
								<div class="bg-[#FFF5EB] w-[50px] h-[50px] mr-4"></div>
								<div>
									<h3 class="text-2xl">5000</h3>
									<span>Total Revenue</span>
								</div>
							</div>
							<div class="border border-gray-300 rounded-lg p-4 flex">
								<div class="bg-[#FFF5EB] w-[50px] h-[50px] mr-4"></div>
								<div>
									<h3 class="text-2xl">5000</h3>
									<span>Total Revenue</span>
								</div>
							</div>
							<div class="border border-gray-300 rounded-lg p-4 flex">
								<div class="bg-[#FFF5EB] w-[50px] h-[50px] mr-4"></div>
								<div>
									<h3 class="text-2xl">5000</h3>
									<span>Total Revenue</span>
								</div>
							</div>
						</div>
					</template>
				</Card>
				<Card class="w-1/2">
					<template #title>
						Purchase Overview
					</template>
				</Card>
			</div>
			<div class="col-span-1">
				<turnOverChart class="col-span-1" />
			</div>
		</div>
		<div class="grid grid-cols-3 gap-4 mb-4">
			<div class="col-span-2 flex gap-2">
				<Card class="w-1/2">
					<template #title>
						Payements Overview (Sales)
					</template>
				</Card>
				<Card class="w-1/2">
					<template #title>
						Payements Overview (Purchase)
					</template>
				</Card>
			</div>
			<div class="col-span-1">
				<salesPaymentChart />
				<purchasePaymentChart />
			</div>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<stockChart class="col-span-1" />
		</div>
	</div>
</template>

<script setup>
import stockChart from '@/components/home/stockChart.vue';
import salesPaymentChart from '@/components/home/salesPaymentChart.vue';
import purchasePaymentChart from '@/components/home/purchasePaymentChart.vue';
import turnOverChart from '@/components/home/turnOverChart.vue';

</script>