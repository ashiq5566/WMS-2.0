<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from '@/plugins/axios';

const router = useRouter();

const username = ref('');
const password = ref('');

const handleSubmit = async () => {
    const formData = new FormData();
    formData.append('username', username.value);
    formData.append('password', password.value);

    try {
        const response = await axios.post('/api/accounts/login/', formData);
        console.log(response);

        router.push('')
    } catch (error) {
        console.error('Login failed:', error);
    }
};
</script>

<template>
    <div class="flex justify-center items-center h-screen">
        <Card class="card">
            <template #content>
                <div class="">
                    <div class="flex flex-col">
                        <label class="w-6rem">Username</label>
                        <InputText v-model="username" id="username" type="text" class="w-12rem" />
                    </div>
                    <div class="flex flex-col">
                        <label class="w-6rem">Password</label>
                        <InputText v-model="password" id="password" type="password" class="w-12rem" />
                    </div>
                    <div class="flex justify-center items-center mt-4">
                        <Button label="Login" icon="pi pi-user" @click="handleSubmit" />
                    </div>
                </div>
            </template>
        </Card>
    </div>
</template>


<style scoped></style>