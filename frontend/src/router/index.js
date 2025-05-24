import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import ModelsConfig from '@/views/ModelsConfig.vue'
import PromptsConfig from '@/views/PromptsConfig.vue'
import EvaluationRunner from '@/views/EvaluationRunner.vue'
import Results from '@/views/Results.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
      meta: {
        title: 'Dashboard'
      }
    },
    {
      path: '/config/models',
      name: 'models-config',
      component: ModelsConfig,
      meta: {
        title: 'Model Configuration'
      }
    },
    {
      path: '/config/prompts',
      name: 'prompts-config',
      component: PromptsConfig,
      meta: {
        title: 'Prompts Management'
      }
    },
    {
      path: '/evaluation',
      name: 'evaluation',
      component: EvaluationRunner,
      meta: {
        title: 'Run Evaluation'
      }
    },
    {
      path: '/results',
      name: 'results',
      component: Results,
      meta: {
        title: 'Results'
      }
    }
  ]
})

// Update page title
router.beforeEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - Storybench` : 'Storybench'
})

export default router
