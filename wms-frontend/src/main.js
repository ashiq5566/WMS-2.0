// Import Tailwind CSS
import './style.css'

// Import PrimeVue theme CSS
import Aura from '@primevue/themes/aura'

// Import PrimeIcons CSS
import 'primeicons/primeicons.css' // icons

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import PrimeVue from 'primevue/config'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Drawer from 'primevue/drawer'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})
app.component('Button', Button)
app.component('InputText', InputText)
app.component('Card', Card)
app.component('Drawer', Drawer)
app.component('Dialog', Dialog)
app.component('Select', Select)
app.component('DataTable', DataTable)
app.component('Column', Column)

app.mount('#app')
