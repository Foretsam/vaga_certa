import { ref } from 'vue'

const CHAVE_STORAGE_USUARIO = 'vagacerta_usuario'

// Estado reativo global do usuário autenticado
export const usuarioLogado = ref(
  JSON.parse(localStorage.getItem(CHAVE_STORAGE_USUARIO) || 'null')
)

export function salvarSessaoUsuario(dadosUsuario) {
  usuarioLogado.value = dadosUsuario
  localStorage.setItem(CHAVE_STORAGE_USUARIO, JSON.stringify(dadosUsuario))
}

export function encerrarSessaoUsuario() {
  usuarioLogado.value = null
  localStorage.removeItem(CHAVE_STORAGE_USUARIO)
}