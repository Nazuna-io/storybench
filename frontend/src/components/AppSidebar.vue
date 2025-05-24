<template>
  <aside 
    class="fixed inset-y-16 left-0 z-50 w-64 bg-white shadow-lg border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 lg:z-auto lg:shadow-sm"
    :class="{
      'translate-x-0': show,
      '-translate-x-full': !show && isMobile
    }"
  >
    <!-- Mobile close button -->
    <div v-if="isMobile" class="lg:hidden flex justify-end p-4 border-b border-gray-200">
      <button
        @click="$emit('close')"
        class="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
      >
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <nav class="p-4">
      <ul class="space-y-2">
        <li>
          <router-link
            to="/"
            class="nav-link"
            :class="{ 'nav-link-active': $route.name === 'results' }"
            @click="handleNavClick"
          >
            <span class="nav-icon">📈</span>
            Results
          </router-link>
        </li>
        
        <li>
          <router-link
            to="/evaluation"
            class="nav-link"
            :class="{ 'nav-link-active': $route.name === 'evaluation' }"
            @click="handleNavClick"
          >
            <span class="nav-icon">▶️</span>
            Run Evaluation
          </router-link>
        </li>
        
        <li class="pt-4">
          <h3 class="nav-section-title">Configuration</h3>
          <ul class="mt-2 space-y-1">
            <li>
              <router-link
                to="/config"
                class="nav-link"
                :class="{ 'nav-link-active': $route.name === 'dashboard' }"
                @click="handleNavClick"
              >
                <span class="nav-icon">📊</span>
                Dashboard
              </router-link>
            </li>
            <li>
              <router-link
                to="/config/models"
                class="nav-link"
                :class="{ 'nav-link-active': $route.name === 'models-config' }"
                @click="handleNavClick"
              >
                <span class="nav-icon">🤖</span>
                <span class="hidden sm:inline">Models & API Keys</span>
                <span class="sm:hidden">Models</span>
              </router-link>
            </li>
            <li>
              <router-link
                to="/config/prompts"
                class="nav-link"
                :class="{ 'nav-link-active': $route.name === 'prompts-config' }"
                @click="handleNavClick"
              >
                <span class="nav-icon">📝</span>
                Prompts
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
  name: 'AppSidebar',
  props: {
    show: {
      type: Boolean,
      default: true
    },
    isMobile: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const handleNavClick = () => {
      if (props.isMobile) {
        emit('close')
      }
    }
    
    return {
      handleNavClick
    }
  }
}

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
