<template>
  <div class="card">
    <div class="flex items-center">
      <div class="flex-shrink-0">
        <span class="text-2xl">{{ icon }}</span>
      </div>
      <div class="ml-4">
        <h3 class="text-sm font-medium text-gray-500">{{ title }}</h3>
        <div class="flex items-center mt-1">
          <div
            class="status-dot mr-2"
            :class="{
              'status-connected': status === 'success',
              'status-disconnected': status === 'error',
              'bg-yellow-500': status === 'warning',
              'status-unknown': status === 'unknown'
            }"
          ></div>
          <p class="text-lg font-semibold text-gray-900">{{ value }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatusCard',
  props: {
    title: {
      type: String,
      required: true
    },
    status: {
      type: String,
      default: 'unknown'
    },
    value: {
      type: String,
      required: true
    },
    icon: {
      type: String,
      required: true
    }
  }
}
</script>
