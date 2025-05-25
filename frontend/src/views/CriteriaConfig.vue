<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Evaluation Criteria</h1>
      <p class="text-gray-600">View evaluation criteria used for LLM assessment</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Loading criteria...</span>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else class="space-y-6">
      
      <!-- Criteria Overview Card -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Active Criteria</h2>
          <div class="flex items-center space-x-2 text-sm text-gray-600">
            <span>{{ Object.keys(criteria).length }} criteria defined</span>
          </div>
        </div>
        
        <div v-if="Object.keys(criteria).length === 0" class="text-center py-8">
          <div class="mb-4">
            <span class="text-6xl">📋</span>
          </div>
          <h3 class="text-xl font-medium text-gray-900 mb-2">No Criteria Configured</h3>
          <p class="text-gray-600">No evaluation criteria found in the system</p>
        </div>
        
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="(criterion, key) in criteria"
            :key="key"
            class="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 hover:shadow-md transition-shadow duration-200"
          >
            <div class="flex items-start justify-between mb-3">
              <h3 class="font-semibold text-gray-900 text-lg">{{ criterion.name }}</h3>
              <div class="flex items-center space-x-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                <span>⭐</span>
                <span>Scale: {{ criterion.scale }}</span>
              </div>
            </div>
            
            <p class="text-gray-700 text-sm leading-relaxed mb-4">
              {{ criterion.description }}
            </p>
            
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span class="font-medium">{{ key }}</span>
              <span>{{ criterion.scale }}-point scale</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Configuration Info Card -->
      <div class="card bg-gray-50">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <span class="text-2xl">ℹ️</span>
          </div>
          <div class="ml-4">
            <h3 class="text-lg font-medium text-gray-900 mb-2">About Evaluation Criteria</h3>
            <div class="space-y-2 text-sm text-gray-700">
              <p>These criteria define how LLM responses are automatically evaluated for creativity and quality.</p>
              <p>Each criterion is scored on its defined scale, contributing to the overall evaluation score.</p>
              <p class="text-gray-600 italic">Note: Criteria editing will be available in a future update.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Configuration Metadata -->
      <div v-if="configMetadata" class="card border-l-4 border-blue-500">
        <h3 class="text-sm font-medium text-gray-900 mb-3">Configuration Details</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-gray-500">Version:</span>
            <span class="ml-2 font-medium">{{ configMetadata.version }}</span>
          </div>
          <div>
            <span class="text-gray-500">Config Hash:</span>
            <span class="ml-2 font-mono text-xs">{{ configMetadata.config_hash }}</span>
          </div>
          <div>
            <span class="text-gray-500">Last Updated:</span>
            <span class="ml-2">{{ formatDate(configMetadata.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// Reactive state
const loading = ref(true)
const criteria = ref({})
const configMetadata = ref(null)

// Methods
const loadCriteria = async () => {
  try {
    loading.value = true
    
    const response = await fetch('http://localhost:8000/api/config/evaluation-criteria')
    if (response.ok) {
      const data = await response.json()
      criteria.value = data.criteria || {}
      configMetadata.value = {
        version: data.version,
        config_hash: data.config_hash,
        created_at: data.created_at
      }
    } else {
      console.error('Failed to load criteria:', response.statusText)
      criteria.value = {}
    }
  } catch (error) {
    console.error('Failed to load criteria:', error)
    criteria.value = {}
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadCriteria()
})
</script>

<style scoped>
.card {
  @apply bg-white shadow rounded-lg border border-gray-200 p-6;
}
</style>
