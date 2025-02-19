// src/axios.js
import axios from 'axios'
import { useRouter } from 'vue-router'
import Cookies from 'js-cookie'

const router = useRouter()

const axiosInstance = axios.create({
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  withCredentials: true // Ensures cookies are sent with requests
})
// Function to update CSRF token dynamically
const updateCsrfToken = () => {
  const csrfToken = Cookies.get('csrftoken')
  if (csrfToken) {
    axiosInstance.defaults.headers.common['X-CSRFToken'] = csrfToken
  }
}

// Call updateCsrfToken initially
updateCsrfToken()

// Response interceptor for successful responses
axiosInstance.interceptors.response.use(
  (response) => {
    //If the response is from a login request
    if (response.config.url === '/api/accounts/login/') {
      const responseData = response.data
      if (responseData.message === 'Login successful' && responseData.sessionId) {
        // Store session ID and user information in localStorage
        localStorage.setItem('user_data', JSON.stringify(responseData.data))

        updateCsrfToken()
      }
    }
    console.log('success')
    return response
  },
  (error) => {
    console.log('error')
    return Promise.reject(error)
  }
)

export default axiosInstance
