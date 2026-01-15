<template>
    <!-- div show a text -->
    <div>
        <AutoComplete v-model="selectedProduct" :suggestions="filteredProducts" optionLabel="name"
            placeholder="Search product" @complete="searchProducts" @item-select="addProductToBill" />

        <DataTable :value="billItems">
            <Column field="name" header="Item" />
            <Column field="unit" header="Unit" />
            <Column field="price" header="Price" />

            <Column header="Qty">
                <template #body="{ data }">
                    <InputNumber v-model="data.quantity" :min="0" :step="data.unit === 'KG' ? 0.1 : 1"
                        :useGrouping="false" @update:modelValue="updateSubtotal(data)" />
                </template>
            </Column>

            <Column header="Subtotal">
                <template #body="{ data }">
                    ₹ {{ data.subtotal.toFixed(2) }}
                </template>
            </Column>

            <Column>
                <template #body="{ index }">
                    <Button icon="pi pi-trash" severity="danger" @click="removeItem(index)" />
                </template>
            </Column>
        </DataTable>
        <div class="text-right text-2xl font-bold mt-4">
            Grand Total: ₹ {{ grandTotal.toFixed(2) }}
        </div>

    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from '@/plugins/axios';

const billItems = ref([])

function addProductToBill(event) {
    const product = event.value   // THIS is the real selected product

    const existing = billItems.value.find(i => i.product_id === product.id)
    if (existing) {
        existing.quantity += product.unit === 'Kilograms' ? 0.1 : 1
        updateSubtotal(existing)
        return
    }

    const qty = product.unit === 'Kilograms' ? 0.5 : 1

    billItems.value.push({
        product_id: product.id,
        name: product.name,
        unit: product.unit,
        price: product.selling_price || 0,
        quantity: qty,
        subtotal: (product.selling_price || 0) * qty
    })
}


function updateSubtotal(item) {
    item.subtotal = Number(item.price) * Number(item.quantity)
}

function removeItem(index) {
    billItems.value.splice(index, 1)
}

const grandTotal = computed(() =>
    billItems.value.reduce((sum, i) => sum + i.subtotal, 0)
)

const selectedProduct = ref(null)
const filteredProducts = ref([])

const searchProducts = async (event) => {
    try {
        const response = await axios.get('/api/inventory/products/', {
            params: { search: event.query }
        })
        filteredProducts.value = response.data

        console.log("sdsdfs", filteredProducts.value)
    } catch (err) {
        console.error(err)
    }
}
</script>
