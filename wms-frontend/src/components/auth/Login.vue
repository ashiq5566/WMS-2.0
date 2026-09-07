<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from '@/plugins/axios';
import store from '../../stores/stores.js';
import Password from 'primevue/password';
import Checkbox from 'primevue/checkbox';
import Message from 'primevue/message';

const router = useRouter();

const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const isLoading = ref(false);
const errorMessage = ref('');
const isDarkMode = ref(false);

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark', 'my-app-dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark', 'my-app-dark');
    localStorage.setItem('theme', 'light');
  }
};

onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    isDarkMode.value = true;
    document.documentElement.classList.add('dark', 'my-app-dark');
  } else {
    isDarkMode.value = false;
    document.documentElement.classList.remove('dark', 'my-app-dark');
  }

  const savedUser = localStorage.getItem('saved_username');
  if (savedUser) {
    username.value = savedUser;
    rememberMe.value = true;
  }
});

const handleSubmit = async () => {
  errorMessage.value = '';

  if (!username.value.trim() || !password.value) {
    errorMessage.value = 'Please enter both username and password.';
    return;
  }

  isLoading.value = true;
  const formData = new FormData();
  formData.append('username', username.value.trim());
  formData.append('password', password.value);

  try {
    const response = await axios.post('/api/accounts/login/', formData);

    if (rememberMe.value) {
      localStorage.setItem('saved_username', username.value.trim());
    } else {
      localStorage.removeItem('saved_username');
    }

    store.methods.login(response);
    router.push('/home');
  } catch (error: any) {
    console.error('Login failed:', error);
    errorMessage.value =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      'Invalid username or password. Please verify your credentials and try again.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen w-full flex bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 transition-colors duration-200">
    <!-- Theme Toggle (Fixed Top Right) -->
    <div class="fixed top-4 right-4 z-50">
      <Button
        :icon="isDarkMode ? 'pi pi-sun' : 'pi pi-moon'"
        :aria-label="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        severity="secondary"
        text
        rounded
        class="!w-10 !h-10 !p-0 shadow-sm border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur"
        @click="toggleDarkMode"
      />
    </div>

    <!-- Left Hero/Feature Showcase (Visible on Large Screens) -->
    <div class="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950 text-white overflow-hidden">
      <!-- Background Ambient Glow & Grid -->
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.25),rgba(255,255,255,0))]"></div>
      <div class="absolute -bottom-24 -left-20 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute top-1/4 -right-20 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <!-- Top Brand -->
      <div class="relative z-10 flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <i class="pi pi-box text-white text-xl"></i>
        </div>
        <div>
          <span class="text-xl font-bold tracking-tight">CoreWMS</span>
          <span class="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">Enterprise</span>
        </div>
      </div>

      <!-- Center Feature Highlight -->
      <div class="relative z-10 space-y-6 max-w-lg">
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-400/20 text-indigo-300 text-xs font-medium">
          <i class="pi pi-shield text-xs"></i>
          Next-Gen Warehouse Operations
        </div>
        <h1 class="text-4xl xl:text-5xl font-extrabold tracking-tight leading-tight">
          Precision inventory control at global scale.
        </h1>
        <p class="text-slate-400 text-base leading-relaxed">
          Manage procurement, fulfill customer orders, and orchestrate warehouse logistics in real-time with automated tracking and intelligent reporting.
        </p>

        <!-- Feature Points -->
        <div class="pt-4 space-y-3.5">
          <div class="flex items-center gap-3 text-sm text-slate-300">
            <i class="pi pi-check-circle text-emerald-400 text-base"></i>
            <span>Real-time multi-location inventory synchronization</span>
          </div>
          <div class="flex items-center gap-3 text-sm text-slate-300">
            <i class="pi pi-check-circle text-emerald-400 text-base"></i>
            <span>End-to-end purchase & sales dispatch workflow</span>
          </div>
          <div class="flex items-center gap-3 text-sm text-slate-300">
            <i class="pi pi-check-circle text-emerald-400 text-base"></i>
            <span>Automated stock thresholds & audit-ready analytics</span>
          </div>
        </div>
      </div>

      <!-- Bottom Trust Badge -->
      <div class="relative z-10 pt-6 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <span>© 2026 CoreWMS Platform. All rights reserved.</span>
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          System Operational
        </span>
      </div>
    </div>

    <!-- Right Login Section -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8 md:p-12">
      <div class="w-full max-w-md">
        <!-- Mobile/Tablet Brand Display -->
        <div class="flex flex-col items-center mb-8 lg:hidden">
          <div class="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30 mb-3">
            <i class="pi pi-box text-white text-2xl"></i>
          </div>
          <h2 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">CoreWMS</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Warehouse Management System</p>
        </div>

        <!-- Auth Card -->
        <Card class="!border !border-slate-200/80 dark:!border-slate-800/80 !shadow-xl !shadow-slate-200/50 dark:!shadow-none !bg-white dark:!bg-slate-900 !rounded-2xl overflow-hidden">
          <template #header>
            <div class="px-8 pt-8 pb-4 border-b border-slate-100 dark:border-slate-800/60">
              <!-- Optional Org Logo Header -->
              <div class="flex items-center justify-between mb-4">
                <img
                  src="../../assets/logo_kc.jpeg"
                  alt="Organization Logo"
                  class="h-9 w-auto max-w-[140px] object-contain rounded-md dark:brightness-90"
                  onerror="this.style.display='none'"
                />
                <span class="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  Staff Access
                </span>
              </div>
              <h2 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                Sign in to your account
              </h2>
              <p class="text-sm text-slate-500 dark:text-slate-400 mt-1.5">
                Welcome back! Enter your login details below.
              </p>
            </div>
          </template>

          <template #content>
            <div class="px-2 pt-2">
              <!-- Error Banner -->
              <Message
                v-if="errorMessage"
                severity="error"
                :closable="true"
                class="mb-5 !text-sm"
                @close="errorMessage = ''"
              >
                {{ errorMessage }}
              </Message>

              <form @submit.prevent="handleSubmit" class="space-y-5" novalidate>
                <!-- Username Field -->
                <div class="space-y-1.5">
                  <label
                    for="username"
                    class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
                  >
                    Username
                  </label>
                  <IconField class="w-full">
                    <InputIcon class="pi pi-user text-slate-400" />
                    <InputText
                      id="username"
                      v-model="username"
                      type="text"
                      name="username"
                      autocomplete="username"
                      required
                      placeholder="Enter your username"
                      class="w-full !rounded-lg !py-2.5 !text-sm dark:!bg-slate-800/80 dark:!border-slate-700 focus:!ring-2 focus:!ring-indigo-500"
                      :disabled="isLoading"
                    />
                  </IconField>
                </div>

                <!-- Password Field -->
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between">
                    <label
                      for="password"
                      class="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
                    >
                      Password
                    </label>
                    <span class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer select-none">
                      Forgot password?
                    </span>
                  </div>
                  <Password
                    id="password"
                    v-model="password"
                    name="password"
                    autocomplete="current-password"
                    :feedback="false"
                    :toggleMask="true"
                    fluid
                    placeholder="Enter your password"
                    class="w-full"
                    inputClass="w-full !rounded-lg !py-2.5 !text-sm dark:!bg-slate-800/80 dark:!border-slate-700 focus:!ring-2 focus:!ring-indigo-500"
                    :disabled="isLoading"
                  />
                </div>

                <!-- Remember Me & Help -->
                <div class="flex items-center justify-between pt-1">
                  <div class="flex items-center gap-2">
                    <Checkbox
                      id="rememberMe"
                      v-model="rememberMe"
                      :binary="true"
                      class="!rounded"
                    />
                    <label
                      for="rememberMe"
                      class="text-sm font-medium text-slate-600 dark:text-slate-400 cursor-pointer select-none"
                    >
                      Remember me
                    </label>
                  </div>
                </div>

                <!-- Submit Button -->
                <div class="pt-2">
                  <Button
                    type="submit"
                    label="Sign In"
                    icon="pi pi-sign-in"
                    :loading="isLoading"
                    class="w-full !py-2.5 !text-sm !font-semibold !rounded-lg !bg-indigo-600 hover:!bg-indigo-700 !border-indigo-600 shadow-sm shadow-indigo-500/20"
                  />
                </div>
              </form>
            </div>
          </template>

          <template #footer>
            <div class="px-2 pt-4 pb-2 border-t border-slate-100 dark:border-slate-800/60 text-center">
              <p class="text-xs text-slate-400 dark:text-slate-500 flex items-center justify-center gap-1.5">
                <i class="pi pi-lock text-xs"></i>
                Protected by enterprise-grade access control
              </p>
            </div>
          </template>
        </Card>

        <!-- Sub-footer info -->
        <div class="mt-6 text-center text-xs text-slate-400 dark:text-slate-500">
          Need support? Contact your warehouse system administrator.
        </div>
      </div>
    </div>
  </div>
</template>