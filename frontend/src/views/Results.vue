<template>
  <div>
    <div class="mb-4">
      <h1 class="text-2xl font-bold text-gray-900">Evaluation Results</h1>
      <p class="text-gray-600">View and analyze LLM creativity evaluation results</p>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
      <div class="card fade-in-up">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <span class="text-2xl">🎯</span>
          </div>
          <div class="ml-4">
            <h3 class="text-sm font-medium text-gray-500">Total Evaluations</h3>
            <p class="text-xl sm:text-2xl font-bold text-gray-900">{{ totalEvaluations }}</p>
          </div>
        </div>
      </div>
      
      <div class="card fade-in-up">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <span class="text-2xl">🤖</span>
          </div>
          <div class="ml-4">
            <h3 class="text-sm font-medium text-gray-500">Models Tested</h3>
            <p class="text-xl sm:text-2xl font-bold text-gray-900">{{ modelsTested }}</p>
          </div>
        </div>
      </div>
      
      <div class="card fade-in-up sm:col-span-2 lg:col-span-1">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <span class="text-2xl">⭐</span>
          </div>
          <div class="ml-4">
            <h3 class="text-sm font-medium text-gray-500">Avg Score</h3>
            <p class="text-xl sm:text-2xl font-bold text-gray-900">{{ averageScore }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Table -->
    <div class="card fade-in-up">
      <div class="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
        <h2 class="text-lg font-semibold text-gray-900">Recent Results</h2>
        
        <!-- Search, Filter and Refresh Controls -->
        <div class="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
          <!-- Refresh Button -->
          <button
            @click="loadResults"
            :disabled="loading"
            class="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
          >
            <span v-if="loading">🔄</span>
            <span v-else>🔄 Refresh</span>
          </button>
          
          <!-- Search Input -->
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search models..."
              class="w-full sm:w-48 pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            >
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          
          <!-- Status Filter -->
          <select
            v-model="statusFilter"
            class="w-full sm:w-auto px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="prompting">Prompting</option>
            <option value="evaluating">Evaluating</option>
            <option value="stopped">Stopped</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>
      
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
        <p class="text-gray-600 animate-pulse">Loading results...</p>
      </div>
      
      <div v-else-if="results.length === 0" class="text-center py-12">
        <div class="mb-4">
          <span class="text-6xl">📊</span>
        </div>
        <h3 class="text-xl font-medium text-gray-900 mb-2">No Results Yet</h3>
        <p class="text-gray-600 mb-6 max-w-md mx-auto">Run your first evaluation to see results here. Results will show model performance metrics and detailed analysis.</p>
        <router-link to="/evaluation" class="btn btn-primary inline-flex items-center">
          <span class="mr-2">▶️</span>
          Start Evaluation
        </router-link>
      </div>
      
      <div v-else>
        <!-- Desktop Table -->
        <div class="hidden md:block overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('model_name')">
                  <div class="flex items-center space-x-1">
                    <span>Model</span>
                    <span class="text-gray-400">{{ getSortIcon('model_name') }}</span>
                  </div>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('timestamp')">
                  <div class="flex items-center space-x-1">
                    <span>Date</span>
                    <span class="text-gray-400">{{ getSortIcon('timestamp') }}</span>
                  </div>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('status')">
                  <div class="flex items-center space-x-1">
                    <span>Status</span>
                    <span class="text-gray-400">{{ getSortIcon('status') }}</span>
                  </div>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('overall_score')">
                  <div class="flex items-center space-x-1">
                    <span>Overall Score</span>
                    <span class="text-gray-400">{{ getSortIcon('overall_score') }}</span>
                  </div>
                </th>
                <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('creativity')">
                  <div class="flex items-center justify-center space-x-1">
                    <span>Creativity</span>
                    <span class="text-gray-400">{{ getSortIcon('creativity') }}</span>
                  </div>
                </th>
                <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('coherence')">
                  <div class="flex items-center justify-center space-x-1">
                    <span>Coherence</span>
                    <span class="text-gray-400">{{ getSortIcon('coherence') }}</span>
                  </div>
                </th>
                <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('character_depth')">
                  <div class="flex items-center justify-center space-x-1">
                    <span>Character</span>
                    <span class="text-gray-400">{{ getSortIcon('character_depth') }}</span>
                  </div>
                </th>
                <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('dialogue_quality')">
                  <div class="flex items-center justify-center space-x-1">
                    <span>Dialogue</span>
                    <span class="text-gray-400">{{ getSortIcon('dialogue_quality') }}</span>
                  </div>
                </th>
                <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('visual_imagination')">
                  <div class="flex items-center justify-center space-x-1">
                    <span>Visual</span>
                    <span class="text-gray-400">{{ getSortIcon('visual_imagination') }}</span>
                  </div>
                </th>
                <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('conceptual_depth')">
                  <div class="flex items-center justify-center space-x-1">
                    <span>Depth</span>
                    <span class="text-gray-400">{{ getSortIcon('conceptual_depth') }}</span>
                  </div>
                </th>
                <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    @click="sortResults('adaptability')">
                  <div class="flex items-center justify-center space-x-1">
                    <span>Adapt.</span>
                    <span class="text-gray-400">{{ getSortIcon('adaptability') }}</span>
                  </div>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="result in results" :key="result.id" class="hover:bg-gray-50 transition-colors duration-150 table-row">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ result.model_name }}</div>
                  <div class="text-sm text-gray-500">{{ getConfigVersion(result.config_version) }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatDate(result.timestamp) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span 
                    class="inline-flex px-2 py-1 text-xs font-semibold rounded-full transition-colors duration-150"
                    :class="getStatusClass(result.status)"
                  >
                    <span v-if="result.status === 'in_progress'" class="animate-pulse mr-1">🔄</span>
                    {{ getStatusText(result.status) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div class="flex items-center">
                    <span class="font-medium">{{ result.scores?.overall ? result.scores.overall.toFixed(1) : '-' }}</span>
                    <div v-if="result.scores?.overall" class="ml-2 w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        class="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        :style="`width: ${result.scores.overall * 20}%`"
                      ></div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                  {{ getScoreValue(result, 'creativity') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                  {{ getScoreValue(result, 'coherence') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                  {{ getScoreValue(result, 'character_depth') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                  {{ getScoreValue(result, 'dialogue_quality') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                  {{ getScoreValue(result, 'visual_imagination') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                  {{ getScoreValue(result, 'conceptual_depth') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                  {{ getScoreValue(result, 'adaptability') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button 
                    @click="showDetail(result)"
                    class="text-primary-600 hover:text-primary-900 transition-colors duration-150"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- Mobile Card View -->
        <div class="md:hidden space-y-4">
          <div 
            v-for="result in results" 
            :key="result.id"
            class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="text-sm font-medium text-gray-900">{{ result.model_name }}</h3>
                <p class="text-xs text-gray-500">{{ getConfigVersion(result.config_version) }}</p>
              </div>
              <span 
                class="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
                :class="getStatusClass(result.status)"
              >
                <span v-if="result.status === 'in_progress'" class="animate-pulse mr-1">🔄</span>
                {{ getStatusText(result.status) }}
              </span>
            </div>
            
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm text-gray-600">Overall Score:</span>
              <div class="flex items-center">
                <span class="text-sm font-medium text-gray-900 mr-2">
                  {{ result.scores?.overall ? result.scores.overall.toFixed(1) : '-' }}
                </span>
                <div v-if="result.scores?.overall" class="w-12 bg-gray-200 rounded-full h-2">
                  <div 
                    class="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    :style="`width: ${result.scores.overall * 20}%`"
                  ></div>
                </div>
              </div>
            </div>
            
            <div v-if="result.scores?.detailed" class="grid grid-cols-3 gap-2 mb-3 text-xs">
              <div class="text-center">
                <div class="text-gray-500">Creativity</div>
                <div class="font-medium">{{ getScoreValue(result, 'creativity') }}</div>
              </div>
              <div class="text-center">
                <div class="text-gray-500">Coherence</div>
                <div class="font-medium">{{ getScoreValue(result, 'coherence') }}</div>
              </div>
              <div class="text-center">
                <div class="text-gray-500">Character</div>
                <div class="font-medium">{{ getScoreValue(result, 'character_depth') }}</div>
              </div>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">{{ formatDate(result.timestamp) }}</span>
              <button 
                @click="showDetail(result)"
                class="text-primary-600 hover:text-primary-900 text-sm font-medium transition-colors duration-150"
              >
                View Details
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Pagination -->
      <div v-if="filteredAndSortedResults.length > 0" class="mt-6 flex flex-col sm:flex-row items-center justify-between space-y-3 sm:space-y-0">
        <div class="text-sm text-gray-700">
          Showing {{ startIndex + 1 }} to {{ Math.min(startIndex + pageSize, filteredAndSortedResults.length) }} of {{ filteredAndSortedResults.length }} results
        </div>
        
        <div class="flex items-center space-x-2">
          <button
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          <div class="flex space-x-1">
            <button
              v-for="page in visiblePages"
              :key="page"
              @click="currentPage = page"
              :class="[
                'px-3 py-2 text-sm font-medium rounded-md',
                page === currentPage 
                  ? 'bg-primary-600 text-white' 
                  : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
              ]"
            >
              {{ page }}
            </button>
          </div>
          
          <button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
    
    <!-- Detail Modal -->
    <ResultDetailModal
      :show="showDetailModal"
      :result="selectedResult"
      @close="closeDetail"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, onActivated } from 'vue'
import ResultDetailModal from '@/components/ResultDetailModal.vue'

export default {
  name: 'Results',
  components: {
    ResultDetailModal
  },
  setup() {
    const loading = ref(false)
    const results = ref([])
    const availableVersions = ref([])
    const searchQuery = ref('')
    const statusFilter = ref('')
    const currentPage = ref(1)
    const pageSize = ref(10)
    const showDetailModal = ref(false)
    const selectedResult = ref(null)
    const sortBy = ref('overall_score')
    const sortDirection = ref('desc')
    
    let refreshInterval = null
    
    // Computed properties for filtering, sorting and pagination
    const filteredAndSortedResults = computed(() => {
      let filtered = results.value
      
      // Apply search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(result => 
          result.model_name.toLowerCase().includes(query) ||
          getConfigVersion(result.config_version).toLowerCase().includes(query)
        )
      }
      
      // Apply status filter
      if (statusFilter.value) {
        filtered = filtered.filter(result => result.status === statusFilter.value)
      }
      
      // Apply sorting
      filtered.sort((a, b) => {
        const aValue = getSortableValue(a, sortBy.value)
        const bValue = getSortableValue(b, sortBy.value)
        
        let comparison = 0
        if (aValue < bValue) comparison = -1
        if (aValue > bValue) comparison = 1
        
        return sortDirection.value === 'asc' ? comparison : -comparison
      })
      
      return filtered
    })
    
    const totalPages = computed(() => Math.ceil(filteredAndSortedResults.value.length / pageSize.value))
    
    const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)
    
    const paginatedResults = computed(() => {
      const start = startIndex.value
      return filteredAndSortedResults.value.slice(start, start + pageSize.value)
    })
    
    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = currentPage.value
      
      if (total <= 7) {
        for (let i = 1; i <= total; i++) {
          pages.push(i)
        }
      } else {
        if (current <= 4) {
          for (let i = 1; i <= 5; i++) pages.push(i)
          pages.push('...', total)
        } else if (current >= total - 3) {
          pages.push(1, '...')
          for (let i = total - 4; i <= total; i++) pages.push(i)
        } else {
          pages.push(1, '...')
          for (let i = current - 1; i <= current + 1; i++) pages.push(i)
          pages.push('...', total)
        }
      }
      
      return pages.filter(page => page !== '...' || !pages.includes('...'))
    })
    
    // Statistics
    const totalEvaluations = computed(() => results.value.length)
    const modelsTested = computed(() => 
      new Set(results.value.map(r => r.model_name)).size
    )
    const averageScore = computed(() => {
      const scores = results.value.filter(r => r.scores?.overall).map(r => r.scores.overall)
      return scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : '-'
    })
    
    // Reset page when filters or sorting change
    watch([searchQuery, statusFilter, sortBy, sortDirection], () => {
      currentPage.value = 1
    })
    
    const getScoreValue = (result, criterion) => {
      return result.scores?.detailed?.[criterion] ? result.scores.detailed[criterion].toFixed(1) : '-'
    }
    
    const getConfigVersion = (configHash) => {
      // Create version mapping based on API versions (sorted oldest to newest)
      const versionIndex = availableVersions.value.indexOf(configHash)
      return versionIndex >= 0 ? `Config v${versionIndex + 1}` : 'Config v?'
    }
    
    const getSortableValue = (result, column) => {
      switch (column) {
        case 'model_name':
          return result.model_name
        case 'timestamp':
          return new Date(result.timestamp)
        case 'status':
          return result.status
        case 'overall_score':
          return result.scores?.overall || 0
        case 'creativity':
          return result.scores?.detailed?.creativity || 0
        case 'coherence':
          return result.scores?.detailed?.coherence || 0
        case 'character_depth':
          return result.scores?.detailed?.character_depth || 0
        case 'dialogue_quality':
          return result.scores?.detailed?.dialogue_quality || 0
        case 'visual_imagination':
          return result.scores?.detailed?.visual_imagination || 0
        case 'conceptual_depth':
          return result.scores?.detailed?.conceptual_depth || 0
        case 'adaptability':
          return result.scores?.detailed?.adaptability || 0
        default:
          return 0
      }
    }
    
    const sortResults = (column) => {
      if (sortBy.value === column) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortBy.value = column
        sortDirection.value = column === 'overall_score' ? 'desc' : 'asc'
      }
      currentPage.value = 1 // Reset to first page when sorting
    }
    
    const getSortIcon = (column) => {
      if (sortBy.value !== column) {
        return '↕️'
      }
      return sortDirection.value === 'asc' ? '↑' : '↓'
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }
    
    const getStatusClass = (status) => {
      const baseClasses = 'inline-flex px-2 py-1 text-xs font-semibold rounded-full transition-colors duration-150'
      switch (status) {
        case 'completed':
          return `${baseClasses} bg-green-100 text-green-800`
        case 'in_progress':
          return `${baseClasses} bg-blue-100 text-blue-800 status-in-progress`
        case 'failed':
          return `${baseClasses} bg-red-100 text-red-800`
        case 'stopped':
          return `${baseClasses} bg-yellow-100 text-yellow-800`
        default:
          return `${baseClasses} bg-gray-100 text-gray-800`
      }
    }
    
    const getStatusText = (status) => {
      switch (status) {
        case 'in_progress':
          return 'Running'
        case 'completed':
          return 'Completed'
        case 'failed':
          return 'Failed'
        case 'stopped':
          return 'Stopped'
        default:
          return status
      }
    }
    
    const loadResults = async () => {
      loading.value = true
      try {
        const response = await fetch('http://localhost:8000/api/results')
        if (response.ok) {
          const data = await response.json()
          results.value = data.results || []
          // Store available versions for config version mapping (reverse to get oldest first)
          availableVersions.value = (data.versions || []).reverse()
          // Apply default sort by overall score (highest first)
          if (results.value.length > 0 && sortBy.value === 'overall_score') {
            // Force re-sort on initial load
            const currentSort = sortBy.value
            sortBy.value = ''
            sortResults(currentSort)
          }
        } else {
          console.error('Failed to load results:', response.statusText)
          results.value = []
          availableVersions.value = []
        }
      } catch (error) {
        console.error('Failed to load results:', error)
        results.value = []
        availableVersions.value = []
      } finally {
        loading.value = false
      }
    }
    
    const showDetail = (result) => {
      selectedResult.value = result
      showDetailModal.value = true
    }
    
    const closeDetail = () => {
      showDetailModal.value = false
      selectedResult.value = null
    }
    
    onMounted(() => {
      console.log('Results page mounted - loading results')
      loadResults()
      
      // Set up auto-refresh every 15 seconds to catch new evaluations
      refreshInterval = setInterval(() => {
        console.log('Auto-refreshing results...')
        loadResults()
      }, 15000)
    })
    
    // Also refresh when component becomes active (user navigates back)
    onActivated(() => {
      console.log('Results page activated - loading results')
      loadResults()
    })
    
    // Clean up interval
    const cleanup = () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        refreshInterval = null
      }
    }
    
    // Clean up on unmount
    if (typeof onUnmounted !== 'undefined') {
      onUnmounted(cleanup)
    }
    
    return {
      loading,
      results: paginatedResults,
      searchQuery,
      statusFilter,
      currentPage,
      pageSize,
      totalPages,
      startIndex,
      visiblePages,
      filteredAndSortedResults,
      totalEvaluations,
      modelsTested,
      averageScore,
      showDetailModal,
      selectedResult,
      sortBy,
      sortDirection,
      formatDate,
      getStatusClass,
      getStatusText,
      getScoreValue,
      getConfigVersion,
      sortResults,
      getSortIcon,
      showDetail,
      closeDetail
    }
  }
}
</script>
