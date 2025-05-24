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
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Global Settings</h2>
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
          </div>
        </div>
      </div>

      <!-- Success Toast -->
      <div v-if="showSuccessToast" class="fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        Configuration saved successfully!
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

// Reactive state
const loading = ref(true)
const saving = ref(false)
const validating = ref(false)
const apiKeysVisible = ref(false)
const showSuccessToast = ref(false)

// Configuration data
const globalSettings = reactive({
  temperature: 0.9,
  max_tokens: 4096,
  num_runs: 3,
  vram_limit_percent: 80
})

// Validation state
const validationErrors = reactive({})
const validationResult = ref(null)

// Methods
const loadConfiguration = async () => {
  try {
    loading.value = true
    
    // Load models configuration
    const modelsConfig = await configStore.getModelsConfig()
    
    if (modelsConfig.global_settings) {
      Object.assign(globalSettings, modelsConfig.global_settings)
    }
    
  } catch (error) {
    console.error('Failed to load configuration:', error)
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
</style>