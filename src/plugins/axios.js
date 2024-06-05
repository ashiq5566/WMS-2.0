// src/axios.js
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();

const axiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:8000', // Replace with your API base URL
  headers: {
    'Content-Type': 'application/json'
  }
});

// Optionally, you can set up interceptors for requests and responses
// axiosInstance.interceptors.request.use(config => {
//   const token = localStorage.getItem('token');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// }, error => {
//   return Promise.reject(error);
// });

// Response interceptor for successful responses
axiosInstance.interceptors.response.use(response => {
  // If the response is from a login request
  if (response.config.url === '/api/accounts/login/') {
    const responseData = response.data;
    if (responseData.message === 'Login successful' && responseData.sessionId) {
      // Store session ID and user information in localStorage
      localStorage.setItem('user_data', JSON.stringify(responseData.data));
    }
  }
  return response;
}, error => {
  return Promise.reject(error);
});


export default axiosInstance;

