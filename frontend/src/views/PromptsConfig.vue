<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Prompts Management</h1>
      <p class="text-gray-600">Manage creative writing prompts and sequences</p>
    </div>

    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Coming Soon</h2>
      <p class="text-gray-600">
        This page will allow you to manage your creative writing prompts.
        For now, please use the configuration files directly.
      </p>
      
      <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 class="font-medium text-blue-900">Current Configuration</h3>
        <p class="text-sm text-blue-700 mt-1">
          Edit <code class="bg-blue-100 px-1 rounded">config/prompts.json</code> to configure prompts.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PromptsConfig'
}
</script>
