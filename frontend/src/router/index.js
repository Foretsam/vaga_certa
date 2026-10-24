import { createRouter, createWebHistory } from 'vue-router'
import { configurarGuardsRouter } from './guards'

import MotoristaHomeView from '@/views/motorista/MotoristaHomeView.vue'
import MotoristaMapaView from '@/views/motorista/MotoristaMapaView.vue'
import AdminListaView from '@/views/admin/AdminListaView.vue'
import AdminInfoGeraisView from '@/views/admin/AdminInfoGeraisView.vue'
import AdminEditor2DView from '@/views/admin/AdminEditor2DView.vue'
import GerenteView from '@/views/gerente/GerenteView.vue'
import GerenteEstacionamentosView from '@/views/gerente/GerenteEstacionamentosView.vue'
import GerenteRelatoriosView from '@/views/gerente/GerenteRelatoriosView.vue'
import AcessoNegadoView from '@/views/auth/AcessoNegadoView.vue'
import LoginView from '@/views/auth/LoginView.vue'
import CadastroView from '@/views/auth/CadastroView.vue'
import SobreView from '@/views/public/SobreView.vue'

const routes = [
  { path: '/', name: 'motorista-home', component: MotoristaHomeView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/cadastro', name: 'cadastro', component: CadastroView },
  { path: '/sobre', name: 'sobre', component: SobreView },
  { path: '/vagas/:id', name: 'motorista-mapa', component: MotoristaMapaView },
  {
    path: '/gerente',
    name: 'gerente',
    component: GerenteView,
    meta: { rolesPermitidas: ['admin_estabelecimento'] }
  },
  {
    path: '/gerente/estacionamentos',
    name: 'gerente-estacionamentos',
    component: GerenteEstacionamentosView,
    meta: { rolesPermitidas: ['admin_estabelecimento'] }
  },
  {
    path: '/gerente/relatorios',
    name: 'gerente-relatorios',
    component: GerenteRelatoriosView,
    meta: { rolesPermitidas: ['admin_estabelecimento'] }
  },
  {
    path: '/admin',
    name: 'admin-lista',
    component: AdminListaView,
    meta: { rolesPermitidas: ['admin_dev'] }
  },
  {
    path: '/admin/informacoes-gerais',
    name: 'admin-info-gerais',
    component: AdminInfoGeraisView,
    meta: { rolesPermitidas: ['admin_dev'] }
  },
  {
    path: '/admin/editor-2d',
    name: 'admin-editor-2d',
    component: AdminEditor2DView,
    meta: { rolesPermitidas: ['admin_dev'] }
  },
  { path: '/acesso-negado', name: 'acesso-negado', component: AcessoNegadoView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

configurarGuardsRouter(router)

export default router
