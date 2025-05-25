import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import ModelsConfig from '@/views/ModelsConfig.vue'
import PromptsConfig from '@/views/PromptsConfig.vue'
import CriteriaConfig from '@/views/CriteriaConfig.vue'
import EvaluationRunner from '@/views/EvaluationRunner.vue'
import Results from '@/views/Results.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'results',
      component: Results,
      meta: {
        title: 'Results'
      }
    },
    {
      path: '/config',
      name: 'dashboard',
      component: Dashboard,
      meta: {
        title: 'Configuration Dashboard'
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
      path: '/config/criteria',
      name: 'criteria-config',
      component: CriteriaConfig,
      meta: {
        title: 'Evaluation Criteria'
      }
    },
    {
      path: '/evaluation',
      name: 'evaluation',
      component: EvaluationRunner,
      meta: {
        title: 'Run Evaluation'
      }
    }
  ]
})

// Update page title
router.beforeEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - Storybench` : 'Storybench'
})

export default router
