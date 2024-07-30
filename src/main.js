// Import Tailwind CSS
import './style.css';

// Import PrimeVue theme CSS
import "primevue/resources/themes/aura-dark-green/theme.css"; // theme

// Import PrimeVue core CSS
import "primevue/resources/primevue.min.css"; // core CSS

// Import PrimeIcons CSS
import "primeicons/primeicons.css"; // icons

// Import your custom CSS files
// import './assets/main.css';

import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import router from './router';
import PrimeVue from 'primevue/config';
import Button from 'primevue/button';
import InputText from "primevue/inputtext";
import Card from 'primevue/card';
import Sidebar from 'primevue/sidebar';
import Dialog from 'primevue/dialog';


const app = createApp(App)


app.use(createPinia());
app.use(router);
app.use(PrimeVue);
app.component('Button', Button);
app.component('InputText', InputText);
app.component('Card', Card);
app.component('Sidebar', Sidebar);
app.component('Dialog', Dialog);

app.mount('#app')
