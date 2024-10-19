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
        type: Array, // Array type
        required: true, // Make it required
    }
});

</script>

<template>
    <div class="">
        <div class="flex justify-end">
            <Button label="Confirm" @click="visible = true" />
        </div>
        <Dialog v-model:visible="visible" modal header="Edit Profile" :style="{ width: '40rem' }">
            <DataTable :value="props.items" tableStyle="min-width: 50rem">
                <Column field="product_name" header="Product"></Column>
                <Column field="quantity" header="Quantity"></Column>
                <Column field="price_at_time_of_order" header="Unit Price"></Column>
                <Column field="total" header="Total"></Column>
                <template #empty>
                    <span class="flex justify-center">No Orders found.</span>
                </template>
            </DataTable>
            <div class="flex justify-end">
                <Button type="submit" label="Confirm" @click="handleSubmit()"></Button>
            </div>
        </Dialog>
    </div>
</template>

<style></style>
