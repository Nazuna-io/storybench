<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <AppHeader />
    <div class="flex">
      <AppSidebar />
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'

export default {
  name: 'App',
  components: {
    AppHeader,
    AppSidebar
  }
}
</script>
