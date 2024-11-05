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
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import Tag from 'primevue/tag'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})
app.use(ToastService)
app.component('Button', Button)
app.component('InputText', InputText)
app.component('Card', Card)
app.component('Drawer', Drawer)
app.component('Dialog', Dialog)
app.component('Select', Select)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Toast', Toast)
app.component('Tag', Tag)
app.component('IconField', IconField)
app.component('InputIcon', InputIcon)

app.mount('#app')
