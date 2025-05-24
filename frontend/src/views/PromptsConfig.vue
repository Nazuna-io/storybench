<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Prompts Management</h1>
      <p class="text-gray-600">Manage creative writing prompts and sequences</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Loading prompts...</span>
      </div>
    </div>

    <!-- Main Prompts Management -->
    <div v-else class="space-y-6">
      
      <!-- Version Warning Banner -->
      <div v-if="hasChanges" class="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-amber-400 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.732 8.5c-.77.833-.192 2.5 1.306 2.5z"></path>
          </svg>
          <div>
            <h3 class="text-sm font-medium text-amber-800">Configuration Version Update</h3>
            <p class="text-sm text-amber-700 mt-1">
              Saving changes will increment the configuration version.
            </p>
          </div>
        </div>
      </div>

      <!-- Prompt Sequences -->
      <div v-for="(prompts, sequenceName) in promptSequences" :key="sequenceName" class="card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">{{ getSequenceDisplayName(sequenceName) }}</h2>
            <p class="text-sm text-gray-600">{{ getSequenceDescription(sequenceName) }}</p>
          </div>
        </div>

        <div class="space-y-4">
          <div
            v-for="(prompt, promptIndex) in prompts"
            :key="`${sequenceName}-${promptIndex}`"
            class="border border-gray-200 rounded-lg p-4"
          >
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">{{ prompt.name }}</label>
                <p class="text-sm text-gray-600 leading-relaxed">{{ prompt.text }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Success Toast -->
      <div v-if="showSuccessToast" class="fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        Prompts loaded successfully!
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
const showSuccessToast = ref(false)
const hasChanges = ref(false)

// Prompts data
const promptSequences = reactive({})

// Sequence metadata
const sequenceMetadata = {
  FilmNarrative: {
    name: 'Film Narrative',
    description: 'Feature film concepts and screenplay development prompts'
  },
  LiteraryNarrative: {
    name: 'Literary Narrative',
    description: 'Novella and literary fiction writing prompts'
  },
  CommercialConcept: {
    name: 'Commercial Concept',
    description: 'Advertisement and commercial creative concepts'
  },
  RegionalThriller: {
    name: 'Regional Thriller',
    description: 'Location-specific thriller and spy story prompts'
  },
  CrossGenre: {
    name: 'Cross-Genre',
    description: 'Multi-genre fusion and experimental narrative prompts'
  }
}

// Methods
const loadPrompts = async () => {
  try {
    loading.value = true
    const data = await configStore.getPrompts()
    
    // Deep copy the prompts data to avoid reactivity issues
    Object.keys(data).forEach(sequence => {
      promptSequences[sequence] = data[sequence].map(prompt => ({ ...prompt }))
    })
    
    hasChanges.value = false
    showSuccessToast.value = true
    setTimeout(() => {
      showSuccessToast.value = false
    }, 2000)
    
  } catch (error) {
    console.error('Failed to load prompts:', error)
  } finally {
    loading.value = false
  }
}

const getSequenceDisplayName = (sequenceName) => {
  return sequenceMetadata[sequenceName]?.name || sequenceName
}

const getSequenceDescription = (sequenceName) => {
  return sequenceMetadata[sequenceName]?.description || 'Custom prompt sequence'
}

// Lifecycle
onMounted(() => {
  loadPrompts()
})
</script>

<style scoped>
.card {
  @apply bg-white shadow rounded-lg border border-gray-200 p-6;
}
</style>