<template>
  <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
    <!-- Background overlay -->
    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" @click="$emit('close')"></div>

      <!-- Modal positioning -->
      <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

      <!-- Modal content -->
      <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full sm:p-6">
        <div class="absolute top-0 right-0 pt-4 pr-4">
          <button
            type="button"
            @click="$emit('close')"
            class="bg-white rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <span class="sr-only">Close</span>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="sm:flex sm:items-start">
          <div class="w-full">
            <!-- Header -->
            <div class="mb-6">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-2xl font-bold text-gray-900" id="modal-title">
                    {{ result?.model_name }}
                  </h3>
                  <p class="text-sm text-gray-500 mt-1">
                    Configuration Version: {{ result?.config_version }}
                  </p>
                </div>
                <div class="flex items-center space-x-3">
                  <span 
                    class="inline-flex px-3 py-1 text-sm font-semibold rounded-full"
                    :class="getStatusClass(result?.status)"
                  >
                    {{ result?.status }}
                  </span>
                  <button
                    @click="exportResult"
                    class="btn btn-secondary text-sm"
                  >
                    Export
                  </button>
                </div>
              </div>
            </div>

            <!-- Summary Stats -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div class="bg-gray-50 rounded-lg p-4">
                <h4 class="text-sm font-medium text-gray-500 mb-1">Overall Score</h4>
                <div class="flex items-center">
                  <span class="text-2xl font-bold text-gray-900">
                    {{ result?.scores?.overall ? result.scores.overall.toFixed(1) : '-' }}
                  </span>
                  <div v-if="result?.scores?.overall" class="ml-3 flex-1">
                    <div class="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        class="progress-bar h-2 rounded-full transition-all duration-500"
                        :style="`width: ${result.scores.overall * 10}%`"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="bg-gray-50 rounded-lg p-4">
                <h4 class="text-sm font-medium text-gray-500 mb-1">Evaluation Date</h4>
                <p class="text-lg font-semibold text-gray-900">
                  {{ formatDate(result?.timestamp) }}
                </p>
              </div>
              
              <div class="bg-gray-50 rounded-lg p-4">
                <h4 class="text-sm font-medium text-gray-500 mb-1">Response Count</h4>
                <p class="text-lg font-semibold text-gray-900">
                  {{ getTotalResponses() }}
                </p>
              </div>
            </div>

            <!-- Detailed Scores -->
            <div v-if="result?.scores" class="mb-6">
              <h4 class="text-lg font-semibold text-gray-900 mb-4">Detailed Scores</h4>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div 
                  v-for="(score, criterion) in result.scores" 
                  :key="criterion"
                  v-show="criterion !== 'overall'"
                  class="bg-white border border-gray-200 rounded-lg p-4"
                >
                  <div class="flex items-center justify-between mb-2">
                    <h5 class="text-sm font-medium text-gray-700 capitalize">{{ criterion }}</h5>
                    <span class="text-sm font-bold text-gray-900">{{ score.toFixed(1) }}</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      class="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      :style="`width: ${score * 10}%`"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Sequence Results -->
            <div v-if="result?.sequences" class="mb-6">
              <h4 class="text-lg font-semibold text-gray-900 mb-4">Sequence Results</h4>
              <div class="space-y-4">
                <div 
                  v-for="(sequenceData, sequenceName) in result.sequences" 
                  :key="sequenceName"
                  class="border border-gray-200 rounded-lg"
                >
                  <button
                    @click="toggleSequence(sequenceName)"
                    class="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 rounded-t-lg"
                  >
                    <div class="flex items-center justify-between">
                      <h5 class="text-sm font-medium text-gray-900">{{ sequenceName }}</h5>
                      <div class="flex items-center space-x-2">
                        <span class="text-xs text-gray-500">
                          {{ Object.keys(sequenceData).length }} runs
                        </span>
                        <svg 
                          class="h-4 w-4 text-gray-400 transform transition-transform duration-200"
                          :class="{ 'rotate-180': expandedSequences.includes(sequenceName) }"
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                  </button>
                  
                  <div 
                    v-show="expandedSequences.includes(sequenceName)"
                    class="px-4 py-3 border-t border-gray-200"
                  >
                    <div class="space-y-3">
                      <div 
                        v-for="(responses, runKey) in sequenceData" 
                        :key="runKey"
                        class="bg-gray-50 rounded-lg p-3"
                      >
                        <h6 class="text-xs font-medium text-gray-700 mb-2 uppercase">{{ runKey }}</h6>
                        <div class="space-y-2">
                          <div 
                            v-for="(response, index) in responses.slice(0, 2)" 
                            :key="index"
                            class="text-sm text-gray-600 bg-white rounded p-2 border"
                          >
                            {{ response.response?.substring(0, 200) }}...
                          </div>
                          <button 
                            v-if="responses.length > 2"
                            class="text-xs text-primary-600 hover:text-primary-800"
                          >
                            Show {{ responses.length - 2 }} more responses
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ResultDetailModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    result: {
      type: Object,
      default: null
    }
  },
  emits: ['close'],
  setup(props) {
    const expandedSequences = ref([])
    
    const toggleSequence = (sequenceName) => {
      const index = expandedSequences.value.indexOf(sequenceName)
      if (index > -1) {
        expandedSequences.value.splice(index, 1)
      } else {
        expandedSequences.value.push(sequenceName)
      }
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
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
    
    const getTotalResponses = () => {
      if (!props.result?.sequences) return 0
      let total = 0
      Object.values(props.result.sequences).forEach(sequenceData => {
        Object.values(sequenceData).forEach(responses => {
          total += responses.length
        })
      })
      return total
    }
    
    const exportResult = () => {
      const dataStr = JSON.stringify(props.result, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${props.result.model_name}_${props.result.config_version}.json`
      link.click()
      URL.revokeObjectURL(url)
    }
    
    return {
      expandedSequences,
      toggleSequence,
      formatDate,
      getStatusClass,
      getTotalResponses,
      exportResult
    }
  }
}
</script>
