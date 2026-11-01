export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/**
 * Cliente HTTP padronizado para comunicação com a API FastAPI.
 */
export async function apiRequest(endpoint, options = {}) {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  }

  const resposta = await fetch(`${API_URL}${endpoint}`, config)
  const dados = await resposta.json().catch(() => ({}))

  if (!resposta.ok) {
    throw new Error(dados.detail || 'Erro na comunicação com o servidor.')
  }

  return dados
}