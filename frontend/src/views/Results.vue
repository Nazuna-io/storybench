<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Results</h1>
      <p class="text-gray-600">View and analyze evaluation results</p>
    </div>

    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Coming Soon</h2>
      <p class="text-gray-600">
        This page will display evaluation results with charts and analysis.
        For now, results are saved in the output directory.
      </p>
      
      <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 class="font-medium text-blue-900">Current Results</h3>
        <p class="text-sm text-blue-700 mt-1">
          Check the <code class="bg-blue-100 px-1 rounded">output/</code> directory for JSON result files.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Results'
}
</script>
