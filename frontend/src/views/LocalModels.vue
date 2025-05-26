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
          
          <!-- Hardware Info -->
          <div>
            <h3 class="text-md font-medium text-gray-800 mb-2">Hardware Information</h3>
            <div class="bg-gray-50 p-4 rounded-md">
              <div v-if="hardwareInfo.loading" class="text-center py-2">
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600 mx-auto"></div>
                <p class="text-sm text-gray-600 mt-1">Checking hardware...</p>
              </div>
              <div v-else>
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <p class="text-sm text-gray-500">GPU Available:</p>
                    <p class="text-sm font-medium" :class="hardwareInfo.gpu_available ? 'text-green-600' : 'text-red-600'">
                      {{ hardwareInfo.gpu_available ? 'Yes' : 'No' }}
                    </p>
                  </div>
                  <div v-if="hardwareInfo.gpu_available">
                    <p class="text-sm text-gray-500">VRAM:</p>
                    <p class="text-sm font-medium text-gray-800">
                      {{ hardwareInfo.vram_gb.toFixed(2) }} GB
                    </p>
                  </div>
                  <div>
                    <p class="text-sm text-gray-500">CPU Cores:</p>
                    <p class="text-sm font-medium text-gray-800">
                      {{ hardwareInfo.cpu_cores }}
                    </p>
                  </div>
                  <div>
                    <p class="text-sm text-gray-500">RAM:</p>
                    <p class="text-sm font-medium text-gray-800">
                      {{ hardwareInfo.ram_gb.toFixed(2) }} GB
                    </p>
                  </div>
                </div>
                <div class="mt-2">
                  <p class="text-sm" :class="hardwareInfo.gpu_available ? 'text-green-600' : 'text-amber-600'">
                    {{ hardwareInfo.gpu_available 
                      ? 'GPU acceleration available for faster inference' 
                      : 'Running in CPU-only mode (slower inference)' }}
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="flex justify-end space-x-3 mt-4">
            <button 
              @click="checkHardware" 
              class="btn btn-secondary"
              :disabled="checkingHardware"
            >
              <span v-if="checkingHardware">Checking...</span>
              <span v-else>Check Hardware</span>
            </button>
            <button 
              @click="saveConfiguration" 
              class="btn btn-primary"
              :disabled="saving"
            >
              <span v-if="saving">Saving...</span>
              <span v-else>Save Configuration</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Evaluation Panel -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Run Local Evaluation</h2>
        
        <div class="space-y-4">
          <!-- Sequences Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Sequences to Evaluate
            </label>
            <div class="bg-gray-50 p-4 rounded-md max-h-48 overflow-y-auto">
              <div v-if="loadingSequences" class="text-center py-2">
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600 mx-auto"></div>
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
          
          <!-- Auto-Evaluate Toggle -->
          <div class="flex items-center space-x-2">
            <input 
              v-model="settings.auto_evaluate" 
              type="checkbox" 
              id="auto-evaluate-toggle"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label for="auto-evaluate-toggle" class="text-sm text-gray-700">
              Automatically evaluate responses after generation
            </label>
          </div>
          
          <!-- Start Button -->
          <div class="flex justify-end mt-4">
            <button 
              @click="startEvaluation" 
              class="btn btn-primary"
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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

export default {
  name: 'LocalModels',
  setup() {
    // Model configurations
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
    
    const useLocalEvaluator = ref(false)
    
    // Hardware information
    const hardwareInfo = ref({
      loading: true,
      gpu_available: false,
      gpu_name: '',
      vram_gb: 0,
      cpu_cores: 0,
      ram_gb: 0
    })
    
    const checkingHardware = ref(false)
    
    // Sequences
    const sequences = ref([])
    const selectedSequences = ref([])
    const loadingSequences = ref(true)
    
    // Generation settings
    const settings = ref({
      temperature: 0.8,
      max_tokens: 2048,
      num_runs: 3,
      vram_limit_percent: 80,
      auto_evaluate: true
    })
    
    // Evaluation state
    const isRunning = ref(false)
    const saving = ref(false)
    
    // Console output
    const consoleMessages = ref([])
    const consoleOutput = ref(null)
    
    // SSE connection
    let eventSource = null
    
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
    
    const startSSE = () => {
      if (eventSource) {
        eventSource.close()
      }
      
      eventSource = new EventSource('/api/local-evaluation/events')
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'console') {
            addConsoleMessage(data.console_type || 'output', data.message, data.timestamp)
          } else if (data.type === 'status') {
            // Update status information
            if (data.status === 'completed' || data.status === 'failed' || data.status === 'stopped') {
              isRunning.value = false
              eventSource.close()
              eventSource = null
            }
          }
        } catch (error) {
          console.error('Error parsing SSE message:', error)
        }
      }
      
      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error)
        if (eventSource) {
          eventSource.close()
          eventSource = null
        }
      }
    }
    
    const checkHardware = async () => {
      checkingHardware.value = true
      hardwareInfo.value.loading = true
      
      try {
        const response = await axios.get('/api/hardware-info')
        hardwareInfo.value = {
          ...response.data,
          loading: false
        }
        addConsoleMessage('info', `Hardware check complete: ${hardwareInfo.value.gpu_available ? 'GPU available' : 'CPU only mode'}`)
      } catch (error) {
        console.error('Error checking hardware:', error)
        addConsoleMessage('error', `Failed to check hardware: ${error.message}`)
        hardwareInfo.value.loading = false
      }
      
      checkingHardware.value = false
    }
    
    const loadSequences = async () => {
      loadingSequences.value = true
      
      try {
        const response = await axios.get('/api/prompts/sequences')
        sequences.value = response.data.sequences || []
        
        // Select all sequences by default
        selectedSequences.value = [...sequences.value]
      } catch (error) {
        console.error('Error loading sequences:', error)
        addConsoleMessage('error', `Failed to load sequences: ${error.message}`)
      }
      
      loadingSequences.value = false
    }
    
    const loadConfiguration = async () => {
      try {
        // Load local model configuration
        const response = await axios.get('/api/local-models/config')
        
        if (response.data.generation_model) {
          generationModel.value = response.data.generation_model
        }
        
        if (response.data.evaluation_model) {
          evaluationModel.value = response.data.evaluation_model
          useLocalEvaluator.value = response.data.use_local_evaluator || false
        }
        
        if (response.data.settings) {
          settings.value = {
            ...settings.value,
            ...response.data.settings
          }
        }
        
        addConsoleMessage('info', 'Configuration loaded')
      } catch (error) {
        console.error('Error loading configuration:', error)
        // If 404, it's likely the first time, so just log info
        if (error.response && error.response.status === 404) {
          addConsoleMessage('info', 'No existing configuration found')
        } else {
          addConsoleMessage('error', `Failed to load configuration: ${error.message}`)
        }
      }
    }
    
    const saveConfiguration = async () => {
      saving.value = true
      
      try {
        await axios.post('/api/local-models/config', {
          generation_model: generationModel.value,
          evaluation_model: evaluationModel.value,
          use_local_evaluator: useLocalEvaluator.value,
          settings: settings.value
        })
        
        addConsoleMessage('info', 'Configuration saved successfully')
      } catch (error) {
        console.error('Error saving configuration:', error)
        addConsoleMessage('error', `Failed to save configuration: ${error.message}`)
      }
      
      saving.value = false
    }
    
    const startEvaluation = async () => {
      if (isRunning.value) return
      
      isRunning.value = true
      consoleMessages.value = []
      
      try {
        // Start SSE connection for real-time updates
        startSSE()
        
        // Start evaluation
        await axios.post('/api/local-evaluation/start', {
          generation_model: generationModel.value,
          evaluation_model: useLocalEvaluator.value ? evaluationModel.value : null,
          use_local_evaluator: useLocalEvaluator.value,
          sequences: selectedSequences.value,
          settings: settings.value
        })
        
        addConsoleMessage('info', 'Evaluation started')
      } catch (error) {
        console.error('Error starting evaluation:', error)
        addConsoleMessage('error', `Failed to start evaluation: ${error.message}`)
        isRunning.value = false
        
        if (eventSource) {
          eventSource.close()
          eventSource = null
        }
      }
    }
    
    onMounted(async () => {
      await checkHardware()
      await loadSequences()
      await loadConfiguration()
    })
    
    onUnmounted(() => {
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    })
    
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
      consoleMessages,
      consoleOutput,
      checkHardware,
      saveConfiguration,
      startEvaluation
    }
  }
}
</script>
