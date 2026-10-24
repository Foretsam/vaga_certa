import { createRouter, createWebHistory } from 'vue-router'
import { usuarioLogado } from '../store/estacionamentoStore'
import MotoristaHomeView from '../views/MotoristaHomeView.vue'
import MotoristaMapaView from '../views/MotoristaMapaView.vue'
import AdminListaView from '../views/AdminListaView.vue'
import AdminInfoGeraisView from '../views/AdminInfoGeraisView.vue'
import AdminEditor2DView from '../views/AdminEditor2DView.vue'
import GerenteView from '../views/GerenteView.vue'
import GerenteEstacionamentosView from '../views/GerenteEstacionamentosView.vue'
import GerenteRelatoriosView from '../views/GerenteRelatoriosView.vue'
import AcessoNegadoView from '../views/AcessoNegadoView.vue'
import LoginView from '../views/LoginView.vue'
import CadastroView from '../views/CadastroView.vue'
import SobreView from '../views/SobreView.vue'

const routes = [
  {
    path: '/',
    name: 'motorista-home',
    component: MotoristaHomeView
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/cadastro',
    name: 'cadastro',
    component: CadastroView
  },
  {
    path: '/sobre',
    name: 'sobre',
    component: SobreView
  },
  {
    path: '/vagas/:id',
    name: 'motorista-mapa',
    component: MotoristaMapaView
  },
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
  {
    path: '/acesso-negado',
    name: 'acesso-negado',
    component: AcessoNegadoView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.path === '/' && to.query.id) {
    return next({ name: 'motorista-mapa', params: { id: to.query.id } })
  }

  if (to.meta.rolesPermitidas) {
    const usuario = usuarioLogado.value
    if (!usuario || !to.meta.rolesPermitidas.includes(usuario.nivel_acesso)) {
      return next({ name: 'acesso-negado' })
    }
  }

  next()
})

export default router