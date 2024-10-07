<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from '@/plugins/axios';

const orders = ref();


const fetchOrders = async () => {
    try {
        const response = await axios.get('/api/inventory/orders');

        orders.value = response.data;
    } catch (error) {
        console.error('Error fetching orders:', error);
    }
}
// const reloadTable = () => {
//     fetchStakeholders();
// };

onMounted(() => {
    fetchOrders();
})


</script>

<template>
    <div class="">
        <!-- <AddStakeHolderModal @instance-added="reloadTable" /> -->
        <Card class="mt-4">
            <template #content>
                <DataTable :value="orders" tableStyle="min-width: 50rem">
                    <Column field="id" header="ID#">
                        <template #body="slotProps">
                            <router-link :to="{ name: 'orders-id', params: { id: slotProps.data.id } }">
                                <span class="font-bold">
                                    {{ slotProps.data.id }}
                                </span>
                            </router-link>
                        </template>
                    </Column>
                    <Column field="order_type" header="Order Type"></Column>
                    <Column field="order_number" header="Order Number"></Column>
                    <Column field="stakeholder" header="Stakeholder"></Column>
                    <Column field="net_amount" header="Net Amount"></Column>
                    <Column field="status" header="Status"></Column>
                    <template #empty>
                        <span class="flex justify-center">No Orders found.</span>
                    </template>
                </DataTable>
            </template>
        </Card>
    </div>
</template>

<style></style>
