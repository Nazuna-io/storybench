<template>
  <header class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center">
          <!-- Mobile menu button -->
          <button
            @click="$emit('toggle-sidebar')"
            class="mr-4 lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          <h1 class="text-xl font-bold text-gray-900">
            Storybench
          </h1>
          <span class="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full hidden sm:inline-block">
            LLM Creativity Evaluation
          </span>
        </div>
        
        <div class="flex items-center space-x-2 sm:space-x-4">
          <div class="hidden sm:flex items-center space-x-2">
            <div class="status-dot" :class="connectionStatus"></div>
            <span class="text-sm text-gray-600">
              {{ connectionText }}
            </span>
          </div>
          
          <!-- Mobile status indicator -->
          <div class="sm:hidden">
            <div class="status-dot" :class="connectionStatus"></div>
          </div>
          
          <button 
            @click="validateConfiguration"
            :disabled="isValidating"
            class="btn btn-primary text-sm px-3 py-2"
          >
            <span v-if="isValidating" class="hidden sm:inline">Validating...</span>
            <span v-else-if="isValidating" class="sm:hidden">⏳</span>
            <span v-else class="hidden sm:inline">Validate Config</span>
            <span v-else class="sm:hidden">✓</span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'

export default {
  name: 'AppHeader',
  setup() {
    const configStore = useConfigStore()
    const isValidating = ref(false)
    
    const connectionStatus = computed(() => {
      if (configStore.lastValidation?.valid === true) {
        return 'status-connected'
      } else if (configStore.lastValidation?.valid === false) {
        return 'status-disconnected'
      }
      return 'status-unknown'
    })
    
    const connectionText = computed(() => {
      if (configStore.lastValidation?.valid === true) {
        return 'Configuration Valid'
      } else if (configStore.lastValidation?.valid === false) {
        return 'Configuration Issues'
      }
      return 'Not Validated'
    })
    
    const validateConfiguration = async () => {
      isValidating.value = true
      try {
        await configStore.validateConfiguration()
      } finally {
        isValidating.value = false
      }
    }
    
    onMounted(() => {
      // Auto-validate on app load
      validateConfiguration()
    })
    
    return {
      isValidating,
      connectionStatus,
      connectionText,
      validateConfiguration
    }
  }
}
</script>
