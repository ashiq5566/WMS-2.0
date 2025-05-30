<script setup lang="ts">
import { ref } from "vue";
import axios from '@/plugins/axios.js';

const imageInput = ref(null);
const emit = defineEmits(['instance-added']);
const visible = ref(false);

const blankData = {
	name: '',
	unit: ''
};
const formData = ref(JSON.parse(JSON.stringify(blankData)));

const typeOptions = ref([
	{ name: 'Pieces', value: 'Pieces' },
	{ name: 'Kilograms', value: 'Kilograms' },
	{ name: 'Sets', value: 'Sets' }
]);

const handleSubmit = async () => {
	try {
		const data = new FormData();
		data.append('name', formData.value.name);
		data.append('unit', formData.value.unit);
		const imageFile = imageInput.value?.files[0];
		if (imageFile) {
			data.append('image', imageFile);
		}
		const response = await axios.post('/api/inventory/products/', data);
		console.log(response);
		visible.value = false;
		emit('instance-added');
		formData.value = JSON.parse(JSON.stringify(blankData));

	} catch (error) {
		console.error('Creation failed:', error);
	}
};

const cancel = () => {
	visible.value = false
	formData.value = JSON.parse(JSON.stringify(blankData))
}

</script>

<template>
	<div class="">
		<div class="flex justify-end">
			<Button label="Add" @click="visible = true" />
		</div>
		<Dialog v-model:visible="visible" modal header="Add Product" :style="{ width: '40rem' }" :draggable="false">
			<div class="flex items-center gap-4 mb-4">
				<label for="name" class="font-semibold w-32">Name</label>
				<InputText id="name" v-model="formData.name" class="flex-auto" autocomplete="off" />
			</div>

			<div class="flex items-center gap-4 mb-8">
				<label for="type" class="font-semibold w-32">Uint</label>
				<Select v-model="formData.unit" :options="typeOptions" optionLabel="name" optionValue="value"
					placeholder="Select a unit" class="w-[450px]" />
			</div>

			<div class="flex items-center gap-4 mb-8">
				<label for="image" class="font-semibold w-32">Image</label>
				<input type="file" ref="imageInput" />
			</div>

			<div class="flex justify-end gap-2">
				<Button type="button" label="Cancel" severity="secondary" @click="cancel"></Button>
				<Button type="submit" label="Save" @click="handleSubmit()"></Button>
			</div>
		</Dialog>
	</div>
</template>

<style></style>
