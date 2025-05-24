import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 404) {
      console.error('API endpoint not found:', error.config.url)
    } else if (error.response?.status >= 500) {
      console.error('Server error:', error.response.data)
    } else if (error.code === 'ECONNABORTED') {
      console.error('Request timeout')
      error.message = 'Request timed out. Please try again.'
    }
    
    return Promise.reject(error)
  }
)

export default api
