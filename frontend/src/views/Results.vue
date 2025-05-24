<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Evaluation Results</h1>
      <p class="text-gray-600">View and analyze LLM creativity evaluation results</p>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="card">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <span class="text-2xl">🎯</span>
          </div>
          <div class="ml-4">
            <h3 class="text-sm font-medium text-gray-500">Total Evaluations</h3>
            <p class="text-2xl font-bold text-gray-900">{{ totalEvaluations }}</p>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <span class="text-2xl">🤖</span>
          </div>
          <div class="ml-4">
            <h3 class="text-sm font-medium text-gray-500">Models Tested</h3>
            <p class="text-2xl font-bold text-gray-900">{{ modelsTested }}</p>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <span class="text-2xl">⭐</span>
          </div>
          <div class="ml-4">
            <h3 class="text-sm font-medium text-gray-500">Avg Score</h3>
            <p class="text-2xl font-bold text-gray-900">{{ averageScore }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Table -->
    <div class="card">
      <div class="mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Recent Results</h2>
      </div>
      
      <div v-if="loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p class="mt-2 text-gray-600">Loading results...</p>
      </div>
      
      <div v-else-if="results.length === 0" class="text-center py-8">
        <span class="text-4xl">📊</span>
        <h3 class="mt-2 text-lg font-medium text-gray-900">No Results Yet</h3>
        <p class="text-gray-600 mb-4">Run your first evaluation to see results here.</p>
        <router-link to="/evaluation" class="btn btn-primary">
          Start Evaluation
        </router-link>
      </div>
      
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Model
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Score
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="result in results" :key="result.id">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ result.model_name }}</div>
                <div class="text-sm text-gray-500">{{ result.config_version }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatDate(result.timestamp) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span 
                  class="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
                  :class="getStatusClass(result.status)"
                >
                  {{ result.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ result.overall_score ? result.overall_score.toFixed(1) : '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button class="text-primary-600 hover:text-primary-900">
                  View Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'Results',
  setup() {
    const loading = ref(false)
    const results = ref([])
    
    // Mock data for now - will be replaced with API calls in Phase 4
    const mockResults = [
      {
        id: 1,
        model_name: 'Claude-4-Sonnet',
        config_version: 'abc123',
        timestamp: '2025-05-24T09:30:00Z',
        status: 'completed',
        overall_score: 8.5
      },
      {
        id: 2,
        model_name: 'Gemini-2.5-Pro',
        config_version: 'abc123',
        timestamp: '2025-05-24T08:15:00Z',
        status: 'completed',
        overall_score: 7.2
      }
    ]
    
    const totalEvaluations = computed(() => results.value.length)
    const modelsTested = computed(() => 
      new Set(results.value.map(r => r.model_name)).size
    )
    const averageScore = computed(() => {
      const scores = results.value.filter(r => r.overall_score).map(r => r.overall_score)
      return scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : '-'
    })
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    const getStatusClass = (status) => {
      switch (status) {
        case 'completed':
          return 'bg-green-100 text-green-800'
        case 'in_progress':
          return 'bg-yellow-100 text-yellow-800'
        case 'failed':
          return 'bg-red-100 text-red-800'
        default:
          return 'bg-gray-100 text-gray-800'
      }
    }
    
    const loadResults = async () => {
      loading.value = true
      try {
        // TODO: Replace with actual API call in Phase 4
        // const response = await api.get('/results')
        // results.value = response.data.results
        
        // For now, use mock data
        await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate loading
        results.value = mockResults
      } catch (error) {
        console.error('Failed to load results:', error)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(() => {
      loadResults()
    })
    
    return {
      loading,
      results,
      totalEvaluations,
      modelsTested,
      averageScore,
      formatDate,
      getStatusClass
    }
  }
}
</script>
