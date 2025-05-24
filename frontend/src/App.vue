<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <AppHeader @toggle-sidebar="toggleSidebar" />
    
    <!-- Mobile overlay for sidebar -->
    <div 
      v-if="showSidebar && isMobile" 
      class="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
      @click="closeSidebar"
    ></div>
    
    <div class="flex">
      <AppSidebar 
        :show="showSidebar" 
        :is-mobile="isMobile"
        @close="closeSidebar" 
      />
      <main 
        class="flex-1 transition-all duration-300 ease-in-out"
        :class="mainContentClasses"
      >
        <div class="p-4 sm:p-6">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'

export default {
  name: 'App',
  components: {
    AppHeader,
    AppSidebar
  },
  setup() {
    const showSidebar = ref(true)
    const windowWidth = ref(window.innerWidth)
    
    const isMobile = computed(() => windowWidth.value < 1024)
    
    const mainContentClasses = computed(() => ({
      'ml-0': isMobile.value || !showSidebar.value,
      'ml-64': !isMobile.value && showSidebar.value
    }))
    
    const toggleSidebar = () => {
      showSidebar.value = !showSidebar.value
    }
    
    const closeSidebar = () => {
      if (isMobile.value) {
        showSidebar.value = false
      }
    }
    
    const updateWindowWidth = () => {
      windowWidth.value = window.innerWidth
      // Auto-close sidebar on mobile
      if (isMobile.value) {
        showSidebar.value = false
      } else {
        showSidebar.value = true
      }
    }
    
    onMounted(() => {
      window.addEventListener('resize', updateWindowWidth)
      updateWindowWidth() // Set initial state
    })
    
    onUnmounted(() => {
      window.removeEventListener('resize', updateWindowWidth)
    })
    
    return {
      showSidebar,
      isMobile,
      mainContentClasses,
      toggleSidebar,
      closeSidebar
    }
  }
}
</script>
