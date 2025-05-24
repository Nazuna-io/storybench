<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Run Evaluation</h1>
      <p class="text-gray-600">Start and monitor LLM creativity evaluations</p>
    </div>

    <!-- Resume Status -->
    <div v-if="resumeInfo.can_resume" class="card mb-6 border-yellow-200 bg-yellow-50">
      <div class="flex items-start">
        <div class="flex-shrink-0">
          <span class="text-2xl">⏰</span>
        </div>
        <div class="ml-4 flex-1">
          <h3 class="text-lg font-medium text-yellow-800">Resume Available</h3>
          <p class="text-yellow-700 mb-3">You can resume a previous evaluation</p>
          
          <div class="text-sm text-yellow-700 mb-4">
            <div v-if="resumeInfo.models_completed.length > 0">
              ✅ Completed: {{ resumeInfo.models_completed.join(', ') }}
            </div>
            <div v-if="resumeInfo.models_in_progress.length > 0">
              🔄 In Progress: {{ resumeInfo.models_in_progress.join(', ') }}
            </div>
            <div v-if="resumeInfo.models_pending.length > 0">
              ⏳ Pending: {{ resumeInfo.models_pending.join(', ') }}
            </div>
          </div>
          
          <div class="flex space-x-3">
            <button 
              @click="startEvaluation(true)" 
              :disabled="isRunning"
              class="btn btn-primary"
            >
              Resume Evaluation
            </button>
            <button 
              @click="startEvaluation(false)" 
              :disabled="isRunning"
              class="btn btn-secondary"
            >
              Start Fresh
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- Control Panel -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Evaluation Control</h2>
      
      <div v-if="!isRunning" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Resume from previous run
          </label>
          <div class="flex items-center space-x-2">
            <input 
              v-model="resumeEnabled" 
              type="checkbox" 
              id="resume-checkbox"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            >
            <label for="resume-checkbox" class="text-sm text-gray-600">
              Continue from where previous evaluation left off
            </label>
          </div>
        </div>
        
        <button 
          @click="startEvaluation(resumeEnabled)" 
          class="btn btn-primary"
          :disabled="startingEvaluation"
        >
          <span v-if="startingEvaluation">Starting...</span>
          <span v-else">🚀 Start Evaluation</span>
        </button>
      </div>
      
      <div v-else class="space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
            <span class="text-gray-900 font-medium">Evaluation Running</span>
          </div>
          <button 
            @click="stopEvaluation" 
            class="btn btn-danger"
            :disabled="stoppingEvaluation"
          >
            <span v-if="stoppingEvaluation">Stopping...</span>
            <span v-else>🛑 Stop</span>
          </button>
        </div>
      </div>
    </div>            <div><strong>Current Model:</strong> {{ progress.current_model }}</div>
            <div v-if="progress.current_sequence"><strong>Sequence:</strong> {{ progress.current_sequence }}</div>
            <div v-if="progress.current_run"><strong>Run:</strong> {{ progress.current_run }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Console Output -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Console Output</h2>
      
      <div 
        ref="consoleOutput"
        class="bg-gray-900 text-green-400 p-4 rounded-lg h-96 overflow-y-auto font-mono text-sm"
      >
        <div v-for="(message, index) in consoleMessages" :key="index" class="mb-1">
          <span class="text-gray-500">[{{ formatTimestamp(message.timestamp) }}]</span>
          <span :class="getMessageClass(message.type)">{{ message.message }}</span>
        </div>
        <div v-if="consoleMessages.length === 0" class="text-gray-500">
          Waiting for evaluation to start...
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

export default {
  name: 'EvaluationRunner',
  setup() {
    const isRunning = ref(false)
    const startingEvaluation = ref(false)
    const stoppingEvaluation = ref(false)
    const resumeEnabled = ref(true)
    const resumeInfo = ref({
      can_resume: false,
      models_completed: [],
      models_in_progress: [],
      models_pending: []
    })
    const progress = ref({
      total_tasks: 0,
      completed_tasks: 0,
      current_model: null,
      current_sequence: null,
      current_run: null
    })
    const consoleMessages = ref([])
    const consoleOutput = ref(null)
    
    let eventSource = null
    
    const progressPercentage = computed(() => {
      if (progress.value.total_tasks === 0) return 0
      return Math.round((progress.value.completed_tasks / progress.value.total_tasks) * 100)
    })    
    const formatTimestamp = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString()
    }
    
    const getMessageClass = (type) => {
      switch (type) {
        case 'error': return 'text-red-400'
        case 'progress': return 'text-blue-400'
        case 'output': return 'text-green-400'
        default: return 'text-gray-300'
      }
    }
    
    const scrollToBottom = async () => {
      await nextTick()
      if (consoleOutput.value) {
        consoleOutput.value.scrollTop = consoleOutput.value.scrollHeight
      }
    }
    
    const addConsoleMessage = (type, message, timestamp = new Date().toISOString()) => {
      consoleMessages.value.push({ type, message, timestamp })
      scrollToBottom()
    }
    
    const startSSE = () => {
      if (eventSource) {
        eventSource.close()
      }
      
      eventSource = new EventSource('http://localhost:8000/api/sse/events')
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          switch (data.type) {
            case 'progress':
              progress.value = { ...progress.value, ...data.data }
              break
            case 'output':
              addConsoleMessage('output', data.message, data.timestamp)
              break
            case 'error':
              addConsoleMessage('error', data.message, data.timestamp)
              break
            case 'heartbeat':
              // Keep connection alive
              break
          }
        } catch (error) {
          console.error('Error parsing SSE data:', error)
        }
      }
      
      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error)
        addConsoleMessage('error', 'Connection to server lost. Attempting to reconnect...')
      }
    }    
    const startEvaluation = async (resume = false) => {
      startingEvaluation.value = true
      
      try {
        const response = await fetch('http://localhost:8000/api/evaluations/start', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ resume })
        })
        
        if (response.ok) {
          isRunning.value = true
          addConsoleMessage('output', `🚀 Evaluation ${resume ? 'resumed' : 'started'} successfully`)
          startSSE()
        } else {
          const error = await response.json()
          addConsoleMessage('error', `Failed to start evaluation: ${error.detail}`)
        }
      } catch (error) {
        addConsoleMessage('error', `Failed to start evaluation: ${error.message}`)
      } finally {
        startingEvaluation.value = false
      }
    }
    
    const stopEvaluation = async () => {
      stoppingEvaluation.value = true
      
      try {
        const response = await fetch('http://localhost:8000/api/evaluations/stop', {
          method: 'POST'
        })
        
        if (response.ok) {
          isRunning.value = false
          addConsoleMessage('output', '🛑 Evaluation stopped')
          if (eventSource) {
            eventSource.close()
            eventSource = null
          }
        } else {
          const error = await response.json()
          addConsoleMessage('error', `Failed to stop evaluation: ${error.detail}`)
        }
      } catch (error) {
        addConsoleMessage('error', `Failed to stop evaluation: ${error.message}`)
      } finally {
        stoppingEvaluation.value = false
      }
    }    
    const loadStatus = async () => {
      try {
        // Check current evaluation status
        const statusResponse = await fetch('http://localhost:8000/api/evaluations/status')
        if (statusResponse.ok) {
          const status = await statusResponse.json()
          isRunning.value = status.running
          if (status.progress) {
            progress.value = status.progress
          }
          if (isRunning.value) {
            startSSE()
          }
        }
        
        // Check resume status
        const resumeResponse = await fetch('http://localhost:8000/api/evaluations/resume-status')
        if (resumeResponse.ok) {
          const resumeData = await resumeResponse.json()
          resumeInfo.value = resumeData.resume_info
        }
      } catch (error) {
        console.error('Failed to load status:', error)
      }
    }
    
    onMounted(() => {
      loadStatus()
    })
    
    onUnmounted(() => {
      if (eventSource) {
        eventSource.close()
      }
    })
    
    return {
      isRunning,
      startingEvaluation,
      stoppingEvaluation,
      resumeEnabled,
      resumeInfo,
      progress,
      progressPercentage,
      consoleMessages,
      consoleOutput,
      formatTimestamp,
      getMessageClass,
      startEvaluation,
      stopEvaluation
    }
  }
}
</script>