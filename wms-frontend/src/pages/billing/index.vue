<template>
    <div>
        <!-- Product Search -->
        <AutoComplete v-model="selectedProduct" :suggestions="filteredProducts" optionLabel="name"
            placeholder="Search product" @complete="searchProducts" @item-select="onProductSelect" />

        <!-- Quantity Input -->
        <div v-if="selectedProduct" class="mt-3 flex gap-2">
            <InputText type="number" v-model="inputQuantity" :step="isKg ? 0.1 : 1" :min="isKg ? 0.1 : 1"
                :useGrouping="false" placeholder="Enter quantity" />
            <Button label="Add" @click="addToBill()" />
        </div>

        <!-- Bill Table -->
        <DataTable :value="billItems" class="mt-4">
            <Column field="name" header="Item" />
            <Column field="unit" header="Unit" />
            <Column field="price" header="Price" />

            <Column header="Qty">
                <template #body="{ data }">
                    <InputText type="number" v-model="data.quantity" :step="data.unit === 'Kilograms' ? 0.1 : 1"
                        :min="data.unit === 'Kilograms' ? 0.1 : 1" :useGrouping="false"
                        @update:modelValue="updateSubtotal(data)" />
                </template>
            </Column>

            <Column header="Subtotal">
                <template #body="{ data }">
                    ₹ {{ data.subtotal.toFixed(2) }}
                </template>
            </Column>

            <Column>
                <template #body="{ index }">
                    <i class="pi pi-times text-red-500" @click="removeItem(index)" />
                </template>
            </Column>
        </DataTable>

        <!-- Grand Total -->
        <div class="text-right text-2xl font-bold mt-4">
            Grand Total: ₹ {{ grandTotal.toFixed(2) }}
        </div>

        <Button label="Save Bill" icon="pi pi-check" class="mt-4" severity="success" @click="saveInvoice" />

    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from '@/plugins/axios'
import { useToast } from 'primevue/usetoast'

/* ---------------- STATE ---------------- */

const selectedProduct = ref(null)
const inputQuantity = ref(null)
const filteredProducts = ref([])
const billItems = ref([])
const toast = useToast()

/* ---------------- COMPUTED ---------------- */

const isKg = computed(() =>
    selectedProduct.value?.unit === 'Kilograms' ||
    selectedProduct.value?.unit === 'KG'
)

const grandTotal = computed(() =>
    billItems.value.reduce((sum, i) => sum + i.subtotal, 0)
)

/* ---------------- METHODS ---------------- */

const searchProducts = async (event) => {
    try {
        const response = await axios.get('/api/inventory/products/', {
            params: { search: event.query }
        })
        filteredProducts.value = response.data
    } catch (err) {
        console.error(err)
    }
}

const onProductSelect = (event) => {
    selectedProduct.value = event.value
    inputQuantity.value = null
}

const addToBill = () => {
    if (!selectedProduct.value) {
        alert('Select a product first')
        return
    }

    if (!inputQuantity.value || inputQuantity.value <= 0) {
        alert('Enter quantity')
        return
    }

    const product = selectedProduct.value
    const qty = Number(inputQuantity.value)
    const price = product.selling_price ?? product.price_at_time_of_purchase ?? 0

    const existing = billItems.value.find(i => i.product_id === product.id)

    if (existing) {
        existing.quantity += qty
        updateSubtotal(existing)
    } else {
        billItems.value.push({
            product_id: product.id,
            name: product.name,
            unit: product.unit,
            price,
            quantity: qty,
            subtotal: price * qty
        })
    }

    selectedProduct.value = null
    inputQuantity.value = null
}


const updateSubtotal = (item) => {
    item.subtotal = Number(item.price) * Number(item.quantity)
}

const removeItem = (index) => {
    billItems.value.splice(index, 1)
}

const saveInvoice = async () => {
    try {
        // Validation
        if (!billItems.value.length) {
            toast.add({ severity: 'error', summary: 'Error', detail: `Error`, life: 3000 });
            return;
        }

        const payload = {
            invoice_type: 'SALE',   // or 'PURCHASE'
            // customer: selectedCustomerId.value, // if applicable
            subtotal: grandTotal.value,
            total_amount: grandTotal.value,
            items: billItems.value.map(item => ({
                product: item.product_id,
                quantity: item.quantity,
                price: item.price,
                subtotal: item.subtotal
            }))
        };

        console.log('Sending payload:', payload);

        const response = await axios.post('/api/inventory/invoices/', payload);

        console.log('Invoice saved:', response.data);

        // ✅ Reset after success
        billItems.value = [];
        selectedProduct.value = null;
        inputQuantity.value = null;

        toast.add({ severity: 'success', summary: 'Success', detail: `Invoice Added`, life: 3000 });

    } catch (error) {
        console.error('Invoice save failed:', error.response?.data || error.message);
        toast.add({ severity: 'error', summary: 'Error', detail: `Failed`, life: 3000 });
    }
};

</script>
