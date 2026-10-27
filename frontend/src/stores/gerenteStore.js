import { ref, computed } from 'vue'
import { usuarioLogado } from './authStore'
import { estabelecimentos } from './estacionamentoStore'

export const idsSelecionadosGerente = ref([])
export const cidadeSelecionadaGerente = ref('TODAS')
export const simulacao1Ativa = ref(false)

export const estabelecimentosDoGerente = computed(() => {
  if (!usuarioLogado.value) return []
  return estabelecimentos.value.filter(
    e => !e.inativo && Number(e.id_usuario) === Number(usuarioLogado.value.id_usuario)
  )
})

export const cidadesDoGerente = computed(() => {
  const setCidades = new Set(
    estabelecimentosDoGerente.value
      .map(e => (e.cidade || 'Sorocaba').trim())
      .filter(Boolean)
  )
  return Array.from(setCidades).sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

export const estabelecimentosDoGerentePorCidade = computed(() => {
  const todos = estabelecimentosDoGerente.value
  if (!cidadeSelecionadaGerente.value || cidadeSelecionadaGerente.value === 'TODAS') {
    return todos
  }
  return todos.filter(
    e => (e.cidade || 'Sorocaba').toLowerCase() === cidadeSelecionadaGerente.value.toLowerCase()
  )
})

export const estabelecimentosFiltradosGerente = computed(() => {
  const baseCidade = estabelecimentosDoGerentePorCidade.value
  if (idsSelecionadosGerente.value.length === 0) return baseCidade
  const filtrados = baseCidade.filter(e => idsSelecionadosGerente.value.includes(e.id))
  return filtrados.length > 0 ? filtrados : baseCidade
})

export function selecionarCidadeGerente(novaCidade) {
  cidadeSelecionadaGerente.value = novaCidade
  idsSelecionadosGerente.value = []
}

export function alternarSimulacao1Frontend() {
  simulacao1Ativa.value = !simulacao1Ativa.value

  estabelecimentosDoGerente.value.forEach((est) => {
    ;(est.andares || []).forEach((andar) => {
      const vagas = Object.values(andar.celulas || {}).filter(
        c => c.tipo === 'VAGA' && !c.inativa
      )

      if (!simulacao1Ativa.value) {
        vagas.forEach((v) => {
          v.livre = true
          v.usosNoDia = 0
          v.horaChegada = null
          v.duracaoMinutos = 0
        })
        return
      }

      const indices = vagas.map((_, i) => i).sort(() => Math.random() - 0.5)
      const limiteOcupadas = Math.round(vagas.length * 0.6)
      const setOcupadas = new Set(indices.slice(0, limiteOcupadas))

      const agora = new Date()
      vagas.forEach((v, idx) => {
        v.usosNoDia = Math.floor(Math.random() * 10) + 1
        if (setOcupadas.has(idx)) {
          v.livre = false
          const duracao = Math.floor(Math.random() * 195) + 15
          v.duracaoMinutos = duracao
          const chegada = new Date(agora.getTime() - duracao * 60000)
          v.horaChegada = chegada.toTimeString().slice(0, 5)
        } else {
          v.livre = true
          v.duracaoMinutos = 0
          v.horaChegada = null
        }
      })
    })
  })
}