import { usuarioLogado } from '@/stores/authStore'

export function configurarGuardsRouter(router) {
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
}
