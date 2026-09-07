<script setup lang="ts">
import { ref } from "vue";
import axios from "@/plugins/axios";

const visible = ref(false);
const emit = defineEmits(["instance-added"]);

const imageInput = ref<HTMLInputElement | null>(null);

interface SizeRow {
	size: string;
	price: string;
	stock: string;
	selling_price: string;
}

const formData = ref<{
	name: string;
	unit: string;
	selling_price: string;
	sizes: SizeRow[];
}>({
	name: "",
	unit: "",
	selling_price: "",
	sizes: []
});

const sizeRow = (): SizeRow => ({
	size: "",
	price: "",
	stock: "",
	selling_price: "",
});

const addSize = () => {
	formData.value.sizes.push(sizeRow());
};

const removeSize = (index: number) => {
	formData.value.sizes.splice(index, 1);
};

const handleSubmit = async () => {
	try {
		const data = new FormData();
		data.append("name", formData.value.name);
		data.append("unit", formData.value.unit);
		data.append("selling_price", formData.value.selling_price);

		// Append sizes
		data.append("sizes", JSON.stringify(formData.value.sizes))

		if (imageInput.value && imageInput.value.files && imageInput.value.files[0]) {
			data.append("image", imageInput.value.files[0]);
		}

		await axios.post("/api/inventory/products/", data);

		visible.value = false;
		emit("instance-added");

		formData.value = {
			name: "",
			unit: "",
			selling_price: "",
			sizes: []
		};

	} catch (err) {
		console.error(err);
	}
};
</script>


<template>
	<div class="">
		<div class="flex justify-end">
			<Button label="Add" @click="visible = true" />
		</div>
		<Dialog :visible="visible" @update:visible="visible = $event" modal header="Add Product" style="width: 45rem">

			<div class="space-y-4">

				<div>
					<label>Name</label>
					<InputText v-model="formData.name" class="w-full" />
				</div>

				<div>
					<label>Unit</label>
					<Select v-model="formData.unit" :options="['Pieces', 'Kilograms', 'Sets']" class="w-full" />
				</div>

				<div>
					<label>Price</label>
					<InputText v-model="formData.selling_price" class="w-full" />
				</div>

				<div>
					<label>Image</label>
					<input type="file" ref="imageInput" />
				</div>

				<!-- Sizes -->
				<div>
					<h3 class="font-semibold mb-2">Sizes</h3>

					<div v-for="(size, index) in formData.sizes" :key="index" class="grid grid-cols-5 gap-3 mb-2">
						<InputText v-model="size.size" placeholder="Size" />
						<InputText v-model="size.price" placeholder="Price" />
						<InputText v-model="size.stock" placeholder="Stock" />
						<InputText v-model="size.selling_price" placeholder="Selling Price" />

						<Button icon="pi pi-trash" severity="danger" @click="removeSize(index)" />
					</div>

					<Button label="Add Size" @click="addSize" />
				</div>

				<div class="flex justify-end gap-2">
					<Button label="Cancel" severity="secondary" @click="visible = false" />
					<Button label="Save" @click="handleSubmit" />
				</div>

			</div>
		</Dialog>

	</div>
</template>

<style></style>
