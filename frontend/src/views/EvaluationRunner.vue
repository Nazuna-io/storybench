<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Run Evaluation</h1>
      <p class="text-gray-600">Start and monitor LLM creativity evaluations</p>
    </div>

    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Coming Soon</h2>
      <p class="text-gray-600">
        This page will allow you to run evaluations and monitor progress.
        For now, please use the CLI interface.
      </p>
      
      <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 class="font-medium text-blue-900">CLI Usage</h3>
        <p class="text-sm text-blue-700 mt-1">
          Run <code class="bg-blue-100 px-1 rounded">storybench evaluate --config config/models.yaml</code> to start an evaluation.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EvaluationRunner'
}
</script>
