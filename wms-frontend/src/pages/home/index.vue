<template>
	<div>
		<div class="grid grid-cols-2 gap-4">
			<Card>
				<template #title>Product Status</template>
			</Card>
			<Card>
				<template #title>Money Flow</template>
			</Card>
		</div>
		<div class="grid grid-cols-3 gap-4 mt-4">
			<Card>
				<template #title>Accounts Receivable(Sales)</template>
			</Card>
			<Card>
				<template #title>Accounts Payable(Purchases)</template>
			</Card>
			<Card>
				<template #title>Turn Over</template>
			</Card>
		</div>
	</div>
</template>