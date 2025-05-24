<template>
  <aside class="w-64 bg-white shadow-sm border-r border-gray-200 min-h-[calc(100vh-4rem)]">
    <nav class="p-4">
      <ul class="space-y-2">
        <li>
          <router-link
            to="/"
            class="nav-link"
            :class="{ 'nav-link-active': $route.name === 'dashboard' }"
          >
            <span class="nav-icon">📊</span>
            Dashboard
          </router-link>
        </li>
        
        <li class="pt-4">
          <h3 class="nav-section-title">Configuration</h3>
          <ul class="mt-2 space-y-1">
            <li>
              <router-link
                to="/config/models"
                class="nav-link"
                :class="{ 'nav-link-active': $route.name === 'models-config' }"
              >
                <span class="nav-icon">🤖</span>
                Models & API Keys
              </router-link>
            </li>
            <li>
              <router-link
                to="/config/prompts"
                class="nav-link"
                :class="{ 'nav-link-active': $route.name === 'prompts-config' }"
              >
                <span class="nav-icon">📝</span>
                Prompts
              </router-link>
            </li>
          </ul>
        </li>
        
        <li class="pt-4">
          <h3 class="nav-section-title">Evaluation</h3>
          <ul class="mt-2 space-y-1">
            <li>
              <router-link
                to="/evaluation"
                class="nav-link"
                :class="{ 'nav-link-active': $route.name === 'evaluation' }"
              >
                <span class="nav-icon">▶️</span>
                Run Evaluation
              </router-link>
            </li>
            <li>
              <router-link
                to="/results"
                class="nav-link"
                :class="{ 'nav-link-active': $route.name === 'results' }"
              >
                <span class="nav-icon">📈</span>
                Results
              </router-link>
            </li>
          </ul>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script>
export default {
  name: 'AppSidebar'
}
</script>

<style scoped>
.nav-link {
  @apply flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors duration-200;
}

.nav-link-active {
  @apply bg-primary-50 text-primary-700 border-r-2 border-primary-600;
}

.nav-icon {
  @apply mr-3 text-lg;
}

.nav-section-title {
  @apply text-xs font-semibold text-gray-400 uppercase tracking-wider;
}
</style>
