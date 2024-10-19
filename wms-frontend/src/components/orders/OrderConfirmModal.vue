<script setup lang="ts">
import { ref } from "vue";
import axios from '@/plugins/axios.js';

const emit = defineEmits(['order-confirmed']);
const visible = ref(false);

const handleSubmit = () => {
    emit('order-confirmed');
    visible.value = false;
}
const props = defineProps({
    items: {
        type: Array,
        required: true,
    },
    grossAmount: {
        type: Number,
        required: true,
    }
});

</script>

<template>
    <div class="">
        <div class="flex justify-end">
            <Button label="Confirm" @click="visible = true" />
        </div>
        <Dialog v-model:visible="visible" modal header="Edit Profile" :style="{ width: '40rem' }">
            <DataTable :value="props.items" tableStyle="min-width: 20rem">
                <Column field="product_name" header="Product"></Column>
                <Column field="quantity" header="Quantity"></Column>
                <Column field="price_at_time_of_order" header="Unit Price"></Column>
                <Column field="total" header="Total"></Column>
                <template #empty>
                    <span class="flex justify-center">No Orders found.</span>
                </template>
            </DataTable>
            <div class="flex justify-between mt-4">
                <span>Total Gross Amount: {{ props.grossAmount }}</span>
            </div>
            <div class="flex justify-end mt-4">
                <Button type="submit" label="Confirm" @click="handleSubmit()"></Button>
            </div>
        </Dialog>
    </div>
</template>

<style></style>
