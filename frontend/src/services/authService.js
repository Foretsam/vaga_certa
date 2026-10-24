import { apiRequest } from './api'

export function loginUsuarioApi(email, senha) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, senha })
  })
}

export function cadastrarUsuarioApi(nome, email, senha) {
  return apiRequest('/auth/cadastro', {
    method: 'POST',
    body: JSON.stringify({ nome, email, senha })
  })
}

export function listarUsuariosApi() {
  return apiRequest('/usuarios')
}
