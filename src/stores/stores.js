// src/store.js
import { reactive } from 'vue';

const state = reactive({
  isAuthenticated: !!localStorage.getItem('user_data')
});

const methods = {
  login(user_data) {
    localStorage.setItem('user_data', user_data);
    state.isAuthenticated = true;
  },
  logout() {
    localStorage.removeItem('user_data');
    state.isAuthenticated = false;
  }
};

if (localStorage.getItem('user_data')) {
  state.isAuthenticated = true;
}

export default {
  state,
  methods
};
