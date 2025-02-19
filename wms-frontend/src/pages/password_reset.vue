<template>
    <div>
        <h2>Reset Password</h2>
        <form @submit.prevent="resetPassword">
            <InputText v-model="email" type="email" placeholder="Enter your email" required />
            <Button type="submit" class="ml-4">Send Reset Link</Button>
        </form>
        <p v-if="message">{{ message }}</p>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from '@/plugins/axios';

const email = ref('');
const message = ref('');

const resetPassword = async () => {
    try {
        await axios.post('http://localhost:8000/api/accounts/password-reset/', { email: email.value });
        message.value = 'Password reset link sent! Check your email.';
    } catch (error) {
        message.value = 'Error sending password reset email.';
    }
};
</script>
