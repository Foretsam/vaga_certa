import { createRouter, createWebHistory } from 'vue-router'
import MotoristaHomeView from '../views/MotoristaHomeView.vue'
import MotoristaMapaView from '../views/MotoristaMapaView.vue'
import AdminListaView from '../views/AdminListaView.vue'
import AdminInfoGeraisView from '../views/AdminInfoGeraisView.vue'
import AdminEditor2DView from '../views/AdminEditor2DView.vue'

const routes = [
  {
    path: '/',
    name: 'motorista-home',
    component: MotoristaHomeView
  },
  {
    path: '/vagas/:id',
    name: 'motorista-mapa',
    component: MotoristaMapaView
  },
  {
    path: '/admin',
    name: 'admin-lista',
    component: AdminListaView
  },
  {
    path: '/admin/informacoes-gerais',
    name: 'admin-info-gerais',
    component: AdminInfoGeraisView
  },
  {
    path: '/admin/editor-2d',
    name: 'admin-editor-2d',
    component: AdminEditor2DView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Se alguém ler um QR Code externo no formato antigo "/?id=1", redireciona direto para "/vagas/1"
router.beforeEach((to, from, next) => {
  if (to.path === '/' && to.query.id) {
    next({ name: 'motorista-mapa', params: { id: to.query.id } })
  } else {
    next()
  }
})

export default router