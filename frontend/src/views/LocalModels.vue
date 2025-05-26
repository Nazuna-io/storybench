<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Local Models</h1>
      <p class="text-gray-600">Configure and run evaluations using local GGUF models</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Model Configuration Panel -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Model Configuration</h2>
        
        <div class="space-y-4">
          <!-- Generation Model -->
          <div>
            <h3 class="text-md font-medium text-gray-800 mb-2">Generation Model</h3>
            <div class="space-y-3 bg-gray-50 p-4 rounded-md">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Hugging Face Repository ID
                </label>
                <input 
                  v-model="generationModel.repo_id" 
                  type="text" 
                  placeholder="e.g., TheBloke/Llama-2-7B-GGUF"
                  class="input-field w-full"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Model Filename
                </label>
                <input 
                  v-model="generationModel.filename" 
                  type="text" 
                  placeholder="e.g., llama-2-7b.Q4_K_M.gguf"
                  class="input-field w-full"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Subdirectory (Optional)
                </label>
                <input 
                  v-model="generationModel.subdirectory" 
                  type="text" 
                  placeholder="e.g., quantized"
                  class="input-field w-full"
                />
              </div>
            </div>
          </div>
          
          <!-- Evaluation Model -->
          <div>
            <h3 class="text-md font-medium text-gray-800 mb-2">Evaluation Model</h3>
            
            <div class="mb-3">
              <div class="flex items-center space-x-2">
                <input 
                  v-model="useLocalEvaluator" 
                  type="checkbox" 
                  id="local-evaluator-toggle"
                  class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <label for="local-evaluator-toggle" class="text-sm text-gray-700">
                  Use local model for evaluation (instead of API)
                </label>
              </div>
            </div>
            
            <div v-if="useLocalEvaluator" class="space-y-3 bg-gray-50 p-4 rounded-md">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Hugging Face Repository ID
                </label>
                <input 
                  v-model="evaluationModel.repo_id" 
                  type="text" 
                  placeholder="e.g., TheBloke/Llama-2-13B-GGUF"
                  class="input-field w-full"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Model Filename
                </label>
                <input 
                  v-model="evaluationModel.filename" 
                  type="text" 
                  placeholder="e.g., llama-2-13b.Q4_K_M.gguf"
                  class="input-field w-full"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Subdirectory (Optional)
                </label>
                <input 
                  v-model="evaluationModel.subdirectory" 
                  type="text" 
                  placeholder="e.g., quantized"
                  class="input-field w-full"
                />
              </div>
            </div>
            
            <div v-else class="bg-gray-50 p-4 rounded-md">
              <p class="text-sm text-gray-600">
                Using API evaluator model as configured in Models & API Keys page.
              </p>
            </div>
          </div>
          
          <!-- Generation Settings -->
          <div>
            <h3 class="text-md font-medium text-gray-800 mb-2">Generation Settings</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input 
                  v-model.number="settings.temperature" 
                  type="number" 
                  min="0.1" 
                  max="2.0" 
                  step="0.1"
                  class="input-field w-full"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input 
                  v-model.number="settings.max_tokens" 
                  type="number" 
                  min="100" 
                  max="8192" 
                  step="100"
                  class="input-field w-full"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Number of Runs
                </label>
                <input 
                  v-model.number="settings.num_runs" 
                  type="number" 
                  min="1" 
                  max="5" 
                  step="1"
                  class="input-field w-full"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  VRAM Limit (%)
                </label>
                <input 
                  v-model.number="settings.vram_limit_percent" 
                  type="number" 
                  min="10" 
                  max="100" 
                  step="5"
                  class="input-field w-full"
                />
              </div>
            </div>
          </div>
          
          <!-- Buttons -->
          <div class="flex space-x-3 mt-6">
            <button 
              @click="saveConfiguration" 
              class="btn-primary"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : 'Save Configuration' }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- Hardware Info and Sequences Panel -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Hardware & Sequences</h2>
        <div class="space-y-6">
          <!-- Hardware Info -->
          <div>
            <h3 class="text-md font-medium text-gray-800 mb-2">Hardware Information</h3>
            <div v-if="checkingHardware" class="text-center py-4">
              <div class="spinner"></div>
              <p class="mt-4 text-gray-600">Checking hardware capabilities...</p>
            </div>
            <div v-else class="bg-gray-50 p-4 rounded-md">
              <div class="grid grid-cols-2 gap-2">
                <div class="text-sm text-gray-600">CPU:</div>
                <div class="text-sm font-medium">{{ hardwareInfo.cpu_info || 'Unknown' }}</div>
                
                <div class="text-sm text-gray-600">RAM:</div>
                <div class="text-sm font-medium">{{ hardwareInfo.ram_gb ? `${hardwareInfo.ram_gb.toFixed(1)} GB` : 'Unknown' }}</div>
                
                <div class="text-sm text-gray-600">GPU Available:</div>
                <div class="text-sm font-medium">{{ hardwareInfo.gpu_available ? 'Yes' : 'No' }}</div>
                
                <template v-if="hardwareInfo.gpu_available">
                  <div class="text-sm text-gray-600">GPU:</div>
                  <div class="text-sm font-medium">{{ hardwareInfo.gpu_name || 'Unknown' }}</div>
                  
                  <div class="text-sm text-gray-600">VRAM:</div>
                  <div class="text-sm font-medium">{{ hardwareInfo.vram_gb ? `${hardwareInfo.vram_gb.toFixed(1)} GB` : 'Unknown' }}</div>
                </template>
              </div>
              <div class="mt-3">
                <button @click="checkHardware" class="btn-secondary text-sm">
                  Refresh Hardware Info
                </button>
              </div>
            </div>
          </div>
          
          <!-- Sequences Selection -->
          <div>
            <h3 class="text-md font-medium text-gray-800 mb-2">Sequences to Evaluate</h3>
            <div class="bg-gray-50 p-4 rounded-md max-h-48 overflow-y-auto">
              <div v-if="loadingSequences" class="text-center py-2">
                <div class="spinner"></div>
                <p class="text-sm text-gray-600 mt-1">Loading sequences...</p>
              </div>
              <div v-else-if="sequences.length === 0" class="text-center py-2">
                <p class="text-sm text-gray-600">No sequences available</p>
              </div>
              <div v-else class="space-y-2">
                <div v-for="sequence in sequences" :key="sequence" class="flex items-center">
                  <input 
                    :id="`sequence-${sequence}`"
                    v-model="selectedSequences"
                    :value="sequence"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <label :for="`sequence-${sequence}`" class="ml-2 text-sm text-gray-700">
                    {{ sequence }}
                  </label>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Download Progress -->
          <div v-if="downloadProgress.isDownloading" class="mt-4 bg-blue-50 p-4 rounded-md">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-blue-700">Downloading Model</span>
              <span class="text-sm text-blue-700">{{ Math.round(downloadProgress.percent) }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                class="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
                :style="{ width: `${downloadProgress.percent}%` }"
              ></div>
            </div>
            <p class="text-sm text-blue-600 mt-2">{{ downloadProgress.message }}</p>
          </div>
          
          <!-- Start Button -->
          <div class="flex justify-end mt-4">
            <button 
              @click="startEvaluation" 
              class="btn-primary"
              :disabled="isRunning || selectedSequences.length === 0"
            >
              <span v-if="isRunning">Running...</span>
              <span v-else>Start Local Evaluation</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Console Output -->
    <div class="card mt-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Console Output</h2>
      
      <div 
        ref="consoleOutput"
        class="bg-gray-900 text-gray-200 p-4 rounded-md h-64 overflow-y-auto font-mono text-sm"
      >
        <div v-if="consoleMessages.length === 0" class="text-gray-500">
          Console output will appear here...
        </div>
        <div 
          v-for="(message, index) in consoleMessages" 
          :key="index"
          :class="{
            'text-green-400': message.type === 'output',
            'text-yellow-400': message.type === 'status',
            'text-red-400': message.type === 'error',
            'text-cyan-400': message.type === 'info'
          }"
        >
          <span class="text-gray-500">[{{ message.timestamp }}]</span> {{ message.text }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

export default {
  setup() {
    // Hardware info
    const hardwareInfo = ref({})
    const checkingHardware = ref(true)
    
    // Model configuration
    const generationModel = ref({
      repo_id: '',
      filename: '',
      subdirectory: ''
    })
    
    const evaluationModel = ref({
      repo_id: '',
      filename: '',
      subdirectory: ''
    })
    
    const useLocalEvaluator = ref(true)
    
    // Sequences
    const sequences = ref([])
    const selectedSequences = ref([])
    const loadingSequences = ref(true)
    
    // Generation settings
    const settings = ref({
      temperature: 1,
      max_tokens: 8192,
      num_runs: 3,
      vram_limit_percent: 80,
      auto_evaluate: true
    })
    
    // Evaluation state
    const isRunning = ref(false)
    const saving = ref(false)
    const downloadProgress = ref({
      isDownloading: false,
      percent: 0,
      message: ''
    })
    const consoleMessages = ref([])
    const consoleOutput = ref(null)
    
    // SSE connection
    let eventSource = null
    
    // Load configuration on mount
    onMounted(async () => {
      await loadConfiguration()
      await checkHardware()
      await loadSequences()
    })
    
    // Cleanup on unmount
    onUnmounted(() => {
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    })
    
    // Console output helpers
    const scrollToBottom = async () => {
      await nextTick()
      if (consoleOutput.value) {
        consoleOutput.value.scrollTop = consoleOutput.value.scrollHeight
      }
    }
    
    const addConsoleMessage = (type, message, timestamp = new Date().toISOString()) => {
      consoleMessages.value.push({ type, text: message, timestamp })
      scrollToBottom()
    }
    
    // Load configuration from backend
    const loadConfiguration = async () => {
      try {
        const response = await axios.get('/api/local-models/config')
        
        if (response.data) {
          // Load generation model
          generationModel.value = response.data.generation_model || {
            repo_id: '',
            filename: '',
            subdirectory: ''
          }
          
          // Load evaluation model
          evaluationModel.value = response.data.evaluation_model || {
            repo_id: '',
            filename: '',
            subdirectory: ''
          }
          
          // Load local evaluator setting
          useLocalEvaluator.value = response.data.use_local_evaluator !== undefined 
            ? response.data.use_local_evaluator 
            : true
          
          // Load other settings
          if (response.data.settings) {
            settings.value = {
              ...settings.value,
              ...response.data.settings
            }
          }
        }
        
        addConsoleMessage('info', 'Configuration loaded')
      } catch (error) {
        console.error('Error loading configuration:', error)
        addConsoleMessage('error', `Error loading configuration: ${error.message}`)
      }
    }
    
    // Save configuration to backend
    const saveConfiguration = async () => {
      saving.value = true
      
      try {
        const config = {
          generation_model: generationModel.value,
          evaluation_model: evaluationModel.value,
          use_local_evaluator: useLocalEvaluator.value,
          settings: settings.value
        }
        
        await axios.post('/api/local-models/config', config)
        addConsoleMessage('info', 'Configuration saved successfully')
      } catch (error) {
        console.error('Error saving configuration:', error)
        addConsoleMessage('error', `Error saving configuration: ${error.message}`)
      } finally {
        saving.value = false
      }
    }
    
    // Check hardware capabilities
    const checkHardware = async () => {
      checkingHardware.value = true
      
      try {
        const response = await axios.get('/api/local-models/hardware-info')
        hardwareInfo.value = response.data
        addConsoleMessage('info', `Hardware check: ${hardwareInfo.value.gpu_available ? 'GPU available' : 'CPU only mode'}`)
      } catch (error) {
        console.error('Error checking hardware:', error)
        addConsoleMessage('error', `Error checking hardware: ${error.message}`)
      } finally {
        checkingHardware.value = false
      }
    }
    
    // Load available sequences
    const loadSequences = async () => {
      loadingSequences.value = true
      
      try {
        // First try to load from the new endpoint
        const response = await axios.get('/api/prompts/sequences')
        sequences.value = response.data || []
        
        // Select all sequences by default
        selectedSequences.value = [...sequences.value]
        addConsoleMessage('info', `Loaded ${sequences.value.length} sequences`)
      } catch (error) {
        console.error('Error loading sequences:', error)
        
        try {
          // Fallback to the old endpoint
          const fallbackResponse = await axios.get('/api/config/sequences')
          sequences.value = fallbackResponse.data.sequences || []
          selectedSequences.value = [...sequences.value]
          addConsoleMessage('info', `Loaded ${sequences.value.length} sequences (fallback)`)
        } catch (fallbackError) {
          console.error('Error loading sequences (fallback):', fallbackError)
          addConsoleMessage('error', `Error loading sequences: ${error.message}`)
          
          // Use sample sequences as last resort
          sequences.value = ['FilmNarrative', 'LiteraryNarrative']
          selectedSequences.value = [...sequences.value]
          addConsoleMessage('info', 'Using sample sequences as fallback')
        }
      } finally {
        loadingSequences.value = false
      }
    }
    
    // Start SSE connection for real-time updates
    const startSSE = () => {
      if (eventSource) {
        eventSource.close()
      }
      
      eventSource = new EventSource('/api/local-models/events')
      
      // Generic message handler
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          addConsoleMessage('info', JSON.stringify(data))
        } catch (error) {
          console.error('Error parsing SSE message:', error)
        }
      }
      
      // Event-specific handlers
      eventSource.addEventListener('console', (event) => {
        try {
          const data = JSON.parse(event.data)
          addConsoleMessage(data.console_type || 'output', data.message, data.timestamp)
        } catch (error) {
          console.error('Error parsing console event:', error)
        }
      })
      
      eventSource.addEventListener('progress', (event) => {
        try {
          const data = JSON.parse(event.data)
          downloadProgress.value.isDownloading = true
          downloadProgress.value.percent = data.progress
          downloadProgress.value.message = data.message || 'Downloading model...'
          
          if (data.progress >= 100) {
            setTimeout(() => {
              downloadProgress.value.isDownloading = false
            }, 2000)
          }
        } catch (error) {
          console.error('Error parsing progress event:', error)
        }
      })
      
      eventSource.addEventListener('status', (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.status === 'completed' || data.status === 'failed' || data.status === 'stopped') {
            isRunning.value = false
            addConsoleMessage('status', `Evaluation ${data.status}`)
            
            if (eventSource) {
              eventSource.close()
              eventSource = null
            }
          }
        } catch (error) {
          console.error('Error parsing status event:', error)
        }
      })
      
      // Error handler
      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error)
        addConsoleMessage('error', 'SSE connection error')
        
        if (eventSource) {
          eventSource.close()
          eventSource = null
        }
      }
    }
    
    // Start local evaluation
    const startEvaluation = async () => {
      if (isRunning.value || selectedSequences.value.length === 0) return
      
      isRunning.value = true
      consoleMessages.value = []
      addConsoleMessage('info', 'Starting local evaluation...')
      
      try {
        // Start SSE connection for real-time updates
        startSSE()
        
        // Start evaluation
        await axios.post('/api/local-models/start', {
          generation_model: generationModel.value,
          evaluation_model: useLocalEvaluator.value ? evaluationModel.value : null,
          use_local_evaluator: useLocalEvaluator.value,
          sequences: selectedSequences.value,
          settings: settings.value
        })
        
        addConsoleMessage('info', 'Evaluation started')
      } catch (error) {
        console.error('Error starting evaluation:', error)
        addConsoleMessage('error', `Error starting evaluation: ${error.message}`)
        isRunning.value = false
        
        if (eventSource) {
          eventSource.close()
          eventSource = null
        }
      }
    }
    
    return {
      generationModel,
      evaluationModel,
      useLocalEvaluator,
      hardwareInfo,
      checkingHardware,
      sequences,
      selectedSequences,
      loadingSequences,
      settings,
      isRunning,
      saving,
      downloadProgress,
      consoleMessages,
      consoleOutput,
      saveConfiguration,
      checkHardware,
      startEvaluation
    }
  }
}
</script>

<style>
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border-left-color: #3b82f6;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>
