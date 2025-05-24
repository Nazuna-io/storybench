import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useConfigStore = defineStore('config', () => {
  // State
  const modelsConfig = ref(null)
  const apiKeys = ref(null)
  const prompts = ref(null)
  const evaluationCriteria = ref(null)
  const lastValidation = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Actions
  const loadModelsConfig = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/config/models')
      modelsConfig.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load models configuration'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateModelsConfig = async (config) => {
    loading.value = true
    error.value = null
    try {
      await api.put('/config/models', config)
      modelsConfig.value = config
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update models configuration'
      throw err
    } finally {
      loading.value = false
    }
  }

  const loadApiKeys = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/config/api-keys')
      apiKeys.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load API keys'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateApiKeys = async (keys) => {
    loading.value = true
    error.value = null
    try {
      await api.put('/config/api-keys', keys)
      // Reload to get masked versions
      await loadApiKeys()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update API keys'
      throw err
    } finally {
      loading.value = false
    }
  }

  const loadPrompts = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/config/prompts')
      prompts.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load prompts'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updatePrompts = async (promptsData) => {
    loading.value = true
    error.value = null
    try {
      await api.put('/config/prompts', promptsData)
      prompts.value = promptsData
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update prompts'
      throw err
    } finally {
      loading.value = false
    }
  }

  const validateConfiguration = async (options = {}) => {
    loading.value = true
    error.value = null
    try {
      const requestData = {
        test_api_connections: options.testApi ?? true,
        validate_local_models: false,
        lightweight_test: options.lightweight ?? true
      }
      const response = await api.post('/config/validate', requestData)
      lastValidation.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to validate configuration'
      lastValidation.value = { valid: false, error: error.value }
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    modelsConfig,
    apiKeys,
    prompts,
    evaluationCriteria,
    lastValidation,
    loading,
    error,
    
    // Actions
    loadModelsConfig,
    updateModelsConfig,
    loadApiKeys,
    updateApiKeys,
    loadPrompts,
    updatePrompts,
    validateConfiguration,
    clearError
  }
})
