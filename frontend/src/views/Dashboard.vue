<template>
  <div class="dashboard">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="text-gray-600">Overview of your Storybench configuration and status</p>
    </div>

    <!-- Status Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <StatusCard
        title="Configuration"
        :status="configStatus"
        :value="configValue"
        icon="⚙️"
      />
      <StatusCard
        title="API Connections"
        :status="apiStatus"
        :value="apiValue"
        icon="🔗"
      />
      <StatusCard
        title="Models"
        :status="modelsStatus"
        :value="modelsValue"
        icon="🤖"
      />
      <StatusCard
        title="Prompts"
        :status="promptsStatus"
        :value="promptsValue"
        icon="📝"
      />
    </div>

    <!-- API Validation Results -->
    <div v-if="configStore.lastValidation" class="card mb-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">API Connection Status</h3>
      <div v-if="configStore.lastValidation.api_validation" class="space-y-3">
        <div
          v-for="(result, provider) in configStore.lastValidation.api_validation"
          :key="provider"
          class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
        >
          <div class="flex items-center space-x-3">
            <div
              class="status-dot"
              :class="result.connected ? 'status-connected' : 'status-disconnected'"
            ></div>
            <span class="font-medium capitalize">{{ provider }}</span>
          </div>
          <div class="text-right">
            <div v-if="result.connected" class="text-sm text-green-600">
              Connected ({{ result.latency_ms?.toFixed(1) }}ms)
            </div>
            <div v-else class="text-sm text-red-600">
              {{ result.error }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'
import StatusCard from '@/components/StatusCard.vue'

export default {
  name: 'Dashboard',
  components: {
    StatusCard
  },
  setup() {
    const configStore = useConfigStore()

    const configStatus = computed(() => {
      return configStore.lastValidation?.valid ? 'success' : 'error'
    })

    const configValue = computed(() => {
      return configStore.lastValidation?.valid ? 'Valid' : 'Issues Found'
    })

    const apiStatus = computed(() => {
      if (!configStore.lastValidation?.api_validation) return 'unknown'
      const connected = Object.values(configStore.lastValidation.api_validation)
        .filter(r => r.connected).length
      const total = Object.keys(configStore.lastValidation.api_validation).length
      return connected === total ? 'success' : connected > 0 ? 'warning' : 'error'
    })

    const apiValue = computed(() => {
      if (!configStore.lastValidation?.api_validation) return 'Unknown'
      const connected = Object.values(configStore.lastValidation.api_validation)
        .filter(r => r.connected).length
      const total = Object.keys(configStore.lastValidation.api_validation).length
      return `${connected}/${total} Connected`
    })

    const modelsStatus = computed(() => {
      if (!configStore.modelsConfig?.models) return 'unknown'
      return configStore.modelsConfig.models.length > 0 ? 'success' : 'warning'
    })

    const modelsValue = computed(() => {
      const count = configStore.modelsConfig?.models?.length || 0
      return `${count} Configured`
    })

    const promptsStatus = computed(() => {
      if (!configStore.prompts?.prompts) return 'unknown'
      const totalPrompts = Object.values(configStore.prompts.prompts)
        .reduce((sum, prompts) => sum + prompts.length, 0)
      return totalPrompts > 0 ? 'success' : 'warning'
    })

    const promptsValue = computed(() => {
      if (!configStore.prompts?.prompts) return 'Loading...'
      const sequences = Object.keys(configStore.prompts.prompts).length
      return `${sequences} Sequences`
    })

    onMounted(async () => {
      // Load initial data
      try {
        await Promise.all([
          configStore.loadModelsConfig(),
          configStore.loadPrompts()
        ])
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      }
    })

    return {
      configStore,
      configStatus,
      configValue,
      apiStatus,
      apiValue,
      modelsStatus,
      modelsValue,
      promptsStatus,
      promptsValue
    }
  }
}
</script>
