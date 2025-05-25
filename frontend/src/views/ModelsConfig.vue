<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Model Configuration</h1>
      <p class="text-gray-600">Configure LLM models and API keys</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Loading configuration...</span>
      </div>
    </div>

    <!-- Main Configuration Form -->
    <div v-else class="space-y-6">
      
      <!-- Global Settings Card -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Global Settings</h2>
          <button
            @click="saveGlobalSettings"
            :disabled="saving || hasValidationErrors"
            class="btn btn-primary"
          >
            <span v-if="saving">Saving...</span>
            <span v-else>💾 Save Settings</span>
          </button>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
            <input
              v-model.number="globalSettings.temperature"
              type="number"
              step="0.1"
              min="0"
              max="2"
              class="input-field"
              @input="validateGlobalSettings"
            />
            <p v-if="validationErrors.temperature" class="text-sm text-red-600 mt-1">
              {{ validationErrors.temperature }}
            </p>
            <p class="text-xs text-gray-500 mt-1">Controls randomness (0.0-2.0)</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
            <input
              v-model.number="globalSettings.max_tokens"
              type="number"
              min="1"
              max="32768"
              class="input-field"
              @input="validateGlobalSettings"
            />
            <p v-if="validationErrors.max_tokens" class="text-sm text-red-600 mt-1">
              {{ validationErrors.max_tokens }}
            </p>
            <p class="text-xs text-gray-500 mt-1">Maximum response length</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Number of Runs</label>
            <input
              v-model.number="globalSettings.num_runs"
              type="number"
              min="1"
              max="10"
              class="input-field"
              @input="validateGlobalSettings"
            />
            <p v-if="validationErrors.num_runs" class="text-sm text-red-600 mt-1">
              {{ validationErrors.num_runs }}
            </p>
            <p class="text-xs text-gray-500 mt-1">Evaluation repetitions</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">VRAM Limit (%)</label>
            <input
              v-model.number="globalSettings.vram_limit_percent"
              type="number"
              min="10"
              max="100"
              class="input-field"
              @input="validateGlobalSettings"
            />
            <p v-if="validationErrors.vram_limit_percent" class="text-sm text-red-600 mt-1">
              {{ validationErrors.vram_limit_percent }}
            </p>
            <p class="text-xs text-gray-500 mt-1">Memory usage limit</p>
          </div>
        </div>
      </div>

      <!-- API Keys Management Card -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">API Keys</h2>
          <div class="flex space-x-2">
            <button
              @click="toggleApiKeysVisibility"
              class="btn btn-secondary"
            >
              {{ apiKeysVisible ? '🙈 Hide Keys' : '👁️ Show Keys' }}
            </button>
            <button
              @click="saveApiKeys"
              :disabled="saving"
              class="btn btn-primary"
            >
              <span v-if="saving">Saving...</span>
              <span v-else>💾 Save API Keys</span>
            </button>
          </div>
        </div>
        
        <div class="space-y-4">
          <div v-for="provider in apiProviders" :key="provider.name" class="flex items-center space-x-4">
            <div class="w-24 flex-shrink-0">
              <label class="block text-sm font-medium text-gray-700">{{ provider.label }}</label>
            </div>
            <div class="flex-1">
              <input
                v-model="provider.key"
                :type="apiKeysVisible ? 'text' : 'password'"
                :placeholder="`Enter ${provider.label} API key`"
                class="input-field"
              />
            </div>
            <div class="flex space-x-2">
              <button
                @click="testApiKey(provider)"
                :disabled="!provider.key || provider.testing"
                class="btn btn-sm btn-secondary"
              >
                <span v-if="provider.testing">Testing...</span>
                <span v-else>🧪 Test</span>
              </button>
              <button
                @click="removeProvider(provider.name)"
                v-if="provider.removable"
                class="btn btn-sm btn-danger"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Models Management Card -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Models</h2>
          <button
            @click="addModel"
            class="btn btn-primary"
          >
            ➕ Add Model
          </button>
        </div>
        
        <!-- Models List -->
        <div v-if="models.length > 0" class="space-y-4">
          <div v-for="(model, index) in models" :key="index" class="border border-gray-200 rounded-lg p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <select v-model="model.provider" class="input-field">
                  <option value="">Select Provider</option>
                  <option v-for="provider in apiProviders" :key="provider.name" :value="provider.name">
                    {{ provider.label }}
                  </option>
                </select>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Model ID</label>
                <input
                  v-model="model.model_name"
                  @input="model.name = model.model_name"
                  type="text"
                  placeholder="e.g., gpt-4o, claude-3-5-sonnet-20241022"
                  class="input-field"
                />
                <p class="text-xs text-gray-500 mt-1">Enter the exact model identifier from the API provider</p>
              </div>
              
              <div class="flex items-end space-x-2">
                <button
                  @click="testModel(model, index)"
                  :disabled="!model.model_name || !model.provider || model.testing"
                  class="btn btn-secondary flex-1"
                >
                  <span v-if="model.testing">Testing...</span>
                  <span v-else>🧪 Test Model</span>
                </button>
                <button
                  @click="removeModel(index)"
                  class="btn btn-danger flex-1"
                >
                  🗑️ Remove
                </button>
              </div>
            </div>
            
            <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select v-model="model.type" class="input-field">
                  <option value="api">API</option>
                  <option value="local">Local</option>
                </select>
              </div>
              
              <!-- Local model specific fields -->
              <div v-if="model.type === 'local'">
                <label class="block text-sm font-medium text-gray-700 mb-1">Repository ID</label>
                <input
                  v-model="model.repo_id"
                  type="text"
                  placeholder="e.g., microsoft/DialoGPT-medium"
                  class="input-field"
                />
              </div>
            </div>
            
            <div v-if="model.type === 'local'" class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Filename</label>
                <input
                  v-model="model.filename"
                  type="text"
                  placeholder="e.g., model.gguf"
                  class="input-field"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Subdirectory (optional)</label>
                <input
                  v-model="model.subdirectory"
                  type="text"
                  placeholder="e.g., models"
                  class="input-field"
                />
              </div>
            </div>
          </div>
        </div>
        
        <!-- Empty state -->
        <div v-else class="text-center py-8 text-gray-500">
          <p class="text-lg mb-2">No models configured</p>
          <p class="text-sm">Add your first model to get started with evaluations</p>
        </div>
        
        <!-- Save models button -->
        <div v-if="models.length > 0" class="mt-6 flex justify-end">
          <button
            @click="saveModels"
            :disabled="saving"
            class="btn btn-primary"
          >
            <span v-if="saving">Saving...</span>
            <span v-else">💾 Save Models</span>
          </button>
        </div>
      </div>

      <!-- Success Toast -->
      <div v-if="showSuccessToast" class="fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center z-50">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        {{ successMessage }}
      </div>

      <!-- Error Toast -->
      <div v-if="showErrorToast" class="fixed bottom-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center z-50">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

// Reactive state
const loading = ref(true)
const saving = ref(false)
const apiKeysVisible = ref(false)
const showSuccessToast = ref(false)
const showErrorToast = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Configuration data
const globalSettings = reactive({
  temperature: 1.0,
  max_tokens: 8192,
  num_runs: 3,
  vram_limit_percent: 90
})

const models = ref([])

const apiProviders = ref([
  { name: 'openai', label: 'OpenAI', key: '', testing: false, removable: false },
  { name: 'anthropic', label: 'Anthropic', key: '', testing: false, removable: false },
  { name: 'google', label: 'Google', key: '', testing: false, removable: false },
  { name: 'grok', label: 'Grok', key: '', testing: false, removable: false }
])

// Validation state
const validationErrors = reactive({})

// Computed properties
const hasValidationErrors = computed(() => {
  return Object.values(validationErrors).some(error => error !== null)
})

// Methods
const loadConfiguration = async () => {
  try {
    loading.value = true
    
    // Load global settings and models
    const response = await fetch('http://localhost:8000/api/config/models')
    if (response.ok) {
      const data = await response.json()
      if (data.global_settings) {
        Object.assign(globalSettings, data.global_settings)
      }
      if (data.models) {
        // Ensure name matches model_name for consistency and add testing state
        models.value = data.models.map(model => ({
          ...model,
          name: model.model_name || model.name,
          testing: false
        }))
      }
    }

    // Load API keys
    const keysResponse = await fetch('http://localhost:8000/api/config/api-keys')
    if (keysResponse.ok) {
      const keysData = await keysResponse.json()
      apiProviders.value.forEach(provider => {
        if (keysData[provider.name]) {
          provider.key = keysData[provider.name]
        }
      })
    }
    
  } catch (error) {
    console.error('Failed to load configuration:', error)
    showToast('Failed to load configuration', 'error')
  } finally {
    loading.value = false
  }
}

const validateGlobalSettings = () => {
  validationErrors.temperature = globalSettings.temperature < 0 || globalSettings.temperature > 2 
    ? 'Temperature must be between 0 and 2' : null
  
  validationErrors.max_tokens = globalSettings.max_tokens < 1 || globalSettings.max_tokens > 32768
    ? 'Max tokens must be between 1 and 32,768' : null
    
  validationErrors.num_runs = globalSettings.num_runs < 1 || globalSettings.num_runs > 10
    ? 'Number of runs must be between 1 and 10' : null
    
  validationErrors.vram_limit_percent = globalSettings.vram_limit_percent < 10 || globalSettings.vram_limit_percent > 100
    ? 'VRAM limit must be between 10% and 100%' : null
}

const saveGlobalSettings = async () => {
  validateGlobalSettings()
  if (hasValidationErrors.value) {
    return
  }

  try {
    saving.value = true
    const response = await fetch('http://localhost:8000/api/config/models', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        global_settings: globalSettings,
        models: models.value
      })
    })

    if (response.ok) {
      showToast('Global settings saved successfully!')
    } else {
      throw new Error('Failed to save settings')
    }
  } catch (error) {
    console.error('Failed to save global settings:', error)
    showToast('Failed to save settings', 'error')
  } finally {
    saving.value = false
  }
}

const toggleApiKeysVisibility = () => {
  apiKeysVisible.value = !apiKeysVisible.value
}

const saveApiKeys = async () => {
  try {
    saving.value = true
    const keys = {}
    apiProviders.value.forEach(provider => {
      if (provider.key) {
        keys[provider.name] = provider.key
      }
    })

    const response = await fetch('http://localhost:8000/api/config/api-keys', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(keys)
    })

    if (response.ok) {
      showToast('API keys saved successfully!')
    } else {
      throw new Error('Failed to save API keys')
    }
  } catch (error) {
    console.error('Failed to save API keys:', error)
    showToast('Failed to save API keys', 'error')
  } finally {
    saving.value = false
  }
}

const testApiKey = async (provider) => {
  provider.testing = true
  try {
    const response = await fetch('http://localhost:8000/api/config/test-api-key', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        provider: provider.name,
        api_key: provider.key
      })
    })

    const result = await response.json()
    if (result.success) {
      showToast(`${provider.label} API key is valid!`)
    } else {
      showToast(`${provider.label} API key test failed: ${result.error}`, 'error')
    }
  } catch (error) {
    showToast(`Failed to test ${provider.label} API key`, 'error')
  } finally {
    provider.testing = false
  }
}

const removeProvider = (providerName) => {
  const index = apiProviders.value.findIndex(p => p.name === providerName)
  if (index > -1) {
    apiProviders.value.splice(index, 1)
    showToast('Provider removed successfully!')
  }
}

const addModel = () => {
  models.value.push({
    name: '',
    type: 'api',
    provider: '',
    model_name: '',
    repo_id: '',
    filename: '',
    subdirectory: '',
    testing: false
  })
}

const testModel = async (model, index) => {
  model.testing = true
  try {
    const response = await fetch('http://localhost:8000/api/config/test-model', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        provider: model.provider,
        model_name: model.model_name,
        type: model.type
      })
    })

    const result = await response.json()
    if (result.success) {
      showToast(`Model ${model.model_name} is valid and accessible!`)
    } else {
      showToast(`Model test failed: ${result.error}`, 'error')
    }
  } catch (error) {
    showToast(`Failed to test model: ${error.message}`, 'error')
  } finally {
    model.testing = false
  }
}

const removeModel = (index) => {
  models.value.splice(index, 1)
  showToast('Model removed successfully!')
}

const saveModels = async () => {
  try {
    saving.value = true
    const response = await fetch('http://localhost:8000/api/config/models', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        global_settings: globalSettings,
        models: models.value
      })
    })

    if (response.ok) {
      showToast('Models saved successfully!')
    } else {
      throw new Error('Failed to save models')
    }
  } catch (error) {
    console.error('Failed to save models:', error)
    showToast('Failed to save models', 'error')
  } finally {
    saving.value = false
  }
}

const showToast = (message, type = 'success') => {
  if (type === 'error') {
    errorMessage.value = message
    showErrorToast.value = true
    setTimeout(() => {
      showErrorToast.value = false
    }, 3000)
  } else {
    successMessage.value = message
    showSuccessToast.value = true
    setTimeout(() => {
      showSuccessToast.value = false
    }, 3000)
  }
}

// Lifecycle
onMounted(() => {
  loadConfiguration()
})
</script>

<style scoped>
.input-field {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 
         focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm;
}

.card {
  @apply bg-white shadow rounded-lg border border-gray-200 p-6;
}

.btn {
  @apply inline-flex items-center px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500;
}

.btn-danger {
  @apply bg-red-600 text-white hover:bg-red-700 focus:ring-red-500;
}

.btn-sm {
  @apply px-3 py-1 text-xs;
}
</style>
