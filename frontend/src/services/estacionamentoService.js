import { apiRequest } from './api'

export function listarEstabelecimentosApi() {
  return apiRequest('/estabelecimentos')
}

export function salvarEstabelecimentoApi(payload, idEdicao = null) {
  const endpoint = idEdicao ? `/estabelecimentos/${idEdicao}` : '/estabelecimentos'
  const method = idEdicao ? 'PUT' : 'POST'
  return apiRequest(endpoint, {
    method,
    body: JSON.stringify(payload)
  })
}

export function alternarStatusEstabelecimentoApi(id) {
  return apiRequest(`/estabelecimentos/${id}/status`, {
    method: 'PATCH'
  })
}

export function removerEstabelecimentoApi(id) {
  return apiRequest(`/estabelecimentos/${id}`, {
    method: 'DELETE'
  })
}

export function alterarStatusVagasLoteApi(idsVagas, inativo) {
  return apiRequest('/vagas/status-lote', {
    method: 'PATCH',
    body: JSON.stringify({ ids_vagas: idsVagas, inativo })
  })
}
