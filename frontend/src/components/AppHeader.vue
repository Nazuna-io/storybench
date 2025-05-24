<template>
  <header class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center">
          <h1 class="text-xl font-bold text-gray-900">
            Storybench
          </h1>
          <span class="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
            LLM Creativity Evaluation
          </span>
        </div>
        
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <div class="status-dot" :class="connectionStatus"></div>
            <span class="text-sm text-gray-600">
              {{ connectionText }}
            </span>
          </div>
          
          <button 
            @click="validateConfiguration"
            :disabled="isValidating"
            class="btn btn-primary"
          >
            <span v-if="isValidating">Validating...</span>
            <span v-else>Validate Config</span>
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
