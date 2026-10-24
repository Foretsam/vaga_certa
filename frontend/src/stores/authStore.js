import { ref } from 'vue'

export const usuarioLogado = ref(
  JSON.parse(localStorage.getItem('vagacerta_usuario') || 'null')
)

export function salvarSessaoUsuario(dadosUsuario) {
  usuarioLogado.value = dadosUsuario
  localStorage.setItem('vagacerta_usuario', JSON.stringify(dadosUsuario))
}

export function encerrarSessaoUsuario() {
  usuarioLogado.value = null
  localStorage.removeItem('vagacerta_usuario')
}
