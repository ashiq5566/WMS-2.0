<script setup lang="ts">
import { defineEmits } from 'vue';

const emit = defineEmits(['buttonClicked'])

const handleClick = () => {
    emit('buttonClicked')
}
</script>


<template>
    <Card>
        <template #content>
            <div class="lg:hidden absolute top-0 left-0 m-4">
                <Button icon="pi pi-arrow-right" @click="handleClick" />
            </div>
        </template>
    </Card>
</template>

<style></style>
