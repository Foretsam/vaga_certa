import { ref, computed } from 'vue'

const API_URL = 'http://127.0.0.1:8000'

export const paletaSetores = [
  { nome: 'Ciano Vivo', hex: '#00b4d8', vagaHex: '#005066' },
  { nome: 'Azul Royal', hex: '#3b82f6', vagaHex: '#1d3b8b' },
  { nome: 'Coral Vibrante', hex: '#fb7185', vagaHex: '#881337' },
  { nome: 'Turquesa Intenso', hex: '#14b8a6', vagaHex: '#115e59' },
  { nome: 'Âmbar Dourado', hex: '#f59e0b', vagaHex: '#78350f' },
  { nome: 'Índigo Vivo', hex: '#6366f1', vagaHex: '#312e81' }
]

export function escurecerCorHex(hex) {
  if (!hex) return '#334155'
  const encontrada = paletaSetores.find(p => p.hex.toLowerCase() === hex.toLowerCase())
  if (encontrada) return encontrada.vagaHex

  const limpo = hex.replace('#', '')
  const num = parseInt(limpo, 16)
  const fator = 0.45
  const r = Math.max(0, Math.floor(((num >> 16) & 255) * fator))
  const g = Math.max(0, Math.floor(((num >> 8) & 255) * fator))
  const b = Math.max(0, Math.floor((num & 255) * fator))
  return `rgb(${r}, ${g}, ${b})`
}

export function criarMatrizVazia(largura, altura) {
  const celulas = {}
  for (let y = 1; y <= altura; y++) {
    for (let x = 1; x <= largura; x++) {
      celulas[`${x},${y}`] = {
        x,
        y,
        setorId: null,
        corSetor: null,
        nomeSetor: null,
        prefixoSetor: null,
        tipo: 'VAZIO',
        orientacao: 'NENHUMA',
        vagaId: null,
        identificador: '',
        livre: true,
        inativa: false,
        semEsp: false,
        usosNoDia: 0,
        horaChegada: null,
        duracaoMinutos: 0,
        macEsp: null
      }
    }
  }
  return celulas
}

function hidratarEstabelecimentoDoBanco(estBanco) {
  const andaresHidratados = (estBanco.andares || []).map((andar) => {
    const celulas = criarMatrizVazia(andar.grid_x, andar.grid_y)
    const mapaSetores = {}
    ;(andar.setores || []).forEach((s) => {
      mapaSetores[s.id_setor] = s
    })

    ;(andar.elementos_mapa || []).forEach((el) => {
      const chave = `${el.coord_x},${el.coord_y}`
      const c = celulas[chave]
      if (!c) return

      if (el.id_setor && mapaSetores[el.id_setor]) {
        const s = mapaSetores[el.id_setor]
        c.setorId = s.id_setor
        c.nomeSetor = s.nome_setor
        c.prefixoSetor = s.prefixo
        c.corSetor = s.cor_hex
      }

      if (el.tipo !== 'FUNDO_SETOR') {
        c.tipo = el.tipo
        c.orientacao = el.orientacao || 'NENHUMA'
      }
    })

    ;(andar.vagas || []).forEach((v) => {
      const chave = `${v.coord_x},${v.coord_y}`
      const c = celulas[chave]
      if (!c) return

      c.tipo = 'VAGA'
      c.vagaId = v.id_vaga
      c.identificador = v.identificador
      c.livre = Boolean(v.livre)
      c.inativa = Boolean(v.inativo)
      c.macEsp = v.mac_esp
      c.semEsp = !v.mac_esp
      c.setorId = v.id_setor
      c.nomeSetor = v.nome_setor
      c.prefixoSetor = v.prefixo
      c.corSetor = v.cor_hex
    })

    return {
      id_andar: andar.id_andar,
      nome_andar: andar.nome_andar,
      grid_x: andar.grid_x,
      grid_y: andar.grid_y,
      setores: andar.setores || [],
      equipamentos: [],
      celulas
    }
  })

  return {
    id: estBanco.id,
    nome: estBanco.nome,
    id_usuario: estBanco.id_usuario,
    inativo: Boolean(estBanco.inativo),
    andares: andaresHidratados
  }
}

export const usuariosCadastrados = ref([])
export const estabelecimentos = ref([])
export const carregandoDados = ref(false)
export const usuarioLogado = ref(
  JSON.parse(localStorage.getItem('vagacerta_usuario') || 'null')
)

export const modoEdicaoId = ref(null)
export const formEstabelecimento = ref({
  nome: '',
  id_usuario: 1,
  andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
})

// =========================================================
// ESTADO DO GERENTE: FILTRO MULTI-ESTACIONAMENTOS E SIMULAÇÃO 1
// =========================================================
// Lista vazia significa "Dashboard completo" (todos os estacionamentos do gerente)
export const idsSelecionadosGerente = ref([])
export const simulacao1Ativa = ref(false)

export const estabelecimentosDoGerente = computed(() => {
  if (!usuarioLogado.value) return []
  return estabelecimentos.value.filter(
    e => !e.inativo && Number(e.id_usuario) === Number(usuarioLogado.value.id_usuario)
  )
})

export const estabelecimentosFiltradosGerente = computed(() => {
  const todos = estabelecimentosDoGerente.value
  if (idsSelecionadosGerente.value.length === 0) return todos
  const filtrados = todos.filter(e => idsSelecionadosGerente.value.includes(e.id))
  return filtrados.length > 0 ? filtrados : todos
})

// Retorna o andar que possui ENTRADA e SAÍDA (ou o 1º andar caso estejam em andares separados)
export function obterAndarEntradaSaida(est) {
  if (!est?.andares || est.andares.length === 0) return null
  const andarAmbos = est.andares.find((a) => {
    const cels = Object.values(a.celulas || {})
    return cels.some(c => c.tipo === 'ENTRADA') && cels.some(c => c.tipo === 'SAIDA')
  })
  if (andarAmbos) return andarAmbos

  const andarEntrada = est.andares.find((a) =>
    Object.values(a.celulas || {}).some(c => c.tipo === 'ENTRADA' || c.tipo === 'SAIDA')
  )
  return andarEntrada || est.andares[0]
}

export function contarVagasEstabelecimento(est) {
  let total = 0
  let ocupadas = 0
  let livres = 0
  let inativas = 0
  let somaDuracao = 0
  let qtdComDuracao = 0
  let somaUsosDia = 0

  ;(est.andares || []).forEach((andar) => {
    Object.values(andar.celulas || {}).forEach((c) => {
      if (c.tipo === 'VAGA') {
        total++
        somaUsosDia += c.usosNoDia || 0
        if (c.inativa) {
          inativas++
        } else if (c.livre) {
          livres++
        } else {
          ocupadas++
          if (c.duracaoMinutos > 0) {
            somaDuracao += c.duracaoMinutos
            qtdComDuracao++
          }
        }
      }
    })
  })

  const ativas = Math.max(1, total - inativas)
  const taxaOcupacao = total > 0 ? Math.round((ocupadas / ativas) * 100) : 0
  const tempoMedioMin = qtdComDuracao > 0 ? Math.round(somaDuracao / qtdComDuracao) : (ocupadas > 0 ? 78 : 0)

  return {
    total,
    ocupadas,
    livres,
    inativas,
    taxaOcupacao,
    tempoMedioMin,
    somaUsosDia
  }
}

// Aplica a "Simulação 1" apenas no frontend (60% ocupadas + 1 a 10 usos por vaga)
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

      // Embaralha índices para escolher exatamente 60% das vagas como ocupadas
      const indices = vagas.map((_, i) => i).sort(() => Math.random() - 0.5)
      const limiteOcupadas = Math.round(vagas.length * 0.6)
      const setOcupadas = new Set(indices.slice(0, limiteOcupadas))

      const agora = new Date()
      vagas.forEach((v, idx) => {
        v.usosNoDia = Math.floor(Math.random() * 10) + 1 // 1 a 10 usos
        if (setOcupadas.has(idx)) {
          v.livre = false
          const duracao = Math.floor(Math.random() * 195) + 15 // 15 a 210 min
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

export async function carregarDadosDoBanco() {
  carregandoDados.value = true
  try {
    const [resUsuarios, resEst] = await Promise.all([
      fetch(`${API_URL}/usuarios`),
      fetch(`${API_URL}/estabelecimentos`)
    ])

    if (resUsuarios.ok) {
      usuariosCadastrados.value = await resUsuarios.json()
    }
    if (resEst.ok) {
      const listaCrua = await resEst.json()
      estabelecimentos.value = listaCrua.map(hidratarEstabelecimentoDoBanco)
      if (simulacao1Ativa.value) {
        simulacao1Ativa.value = false
        alternarSimulacao1Frontend()
      }
    }
  } catch (err) {
    console.error('Erro ao conectar com a API FastAPI:', err)
  } finally {
    carregandoDados.value = false
  }
}

export async function salvarEstacionamentoNoBanco() {
  const payload = {
    nome: formEstabelecimento.value.nome,
    id_usuario: formEstabelecimento.value.id_usuario,
    andares: formEstabelecimento.value.andares.map((andar) => {
      const celulasPreenchidas = []

      Object.values(andar.celulas || {}).forEach((c) => {
        if (c.tipo === 'VAZIO' && !c.setorId) return
        celulasPreenchidas.push({
          x: c.x,
          y: c.y,
          tipo: c.tipo === 'VAZIO' && c.setorId ? 'FUNDO_SETOR' : c.tipo,
          orientacao: c.orientacao || 'NENHUMA',
          setor_id_temp: c.setorId || null,
          identificador: c.identificador || null,
          livre: c.livre !== false,
          mac_esp: c.macEsp || null
        })
      })

      return {
        nome_andar: andar.nome_andar,
        grid_x: andar.grid_x,
        grid_y: andar.grid_y,
        setores: (andar.setores || []).map(s => ({
          id_temp: s.id_setor,
          nome_setor: s.nome_setor,
          prefixo: s.prefixo,
          cor_hex: s.cor_hex
        })),
        celulas_preenchidas: celulasPreenchidas
      }
    })
  }

  const editando = Boolean(modoEdicaoId.value)
  const url = editando
    ? `${API_URL}/estabelecimentos/${modoEdicaoId.value}`
    : `${API_URL}/estabelecimentos`
  const metodo = editando ? 'PUT' : 'POST'

  const resposta = await fetch(url, {
    method: metodo,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!resposta.ok) {
    const erroJson = await resposta.json().catch(() => ({}))
    throw new Error(erroJson.detail || 'Falha ao salvar estacionamento no servidor.')
  }

  await carregarDadosDoBanco()
}

export async function alternarInativoNoBanco(est) {
  const resposta = await fetch(`${API_URL}/estabelecimentos/${est.id}/status`, {
    method: 'PATCH'
  })
  if (!resposta.ok) {
    throw new Error('Não foi possível alterar o status do estabelecimento.')
  }
  await carregarDadosDoBanco()
}

export async function removerEstabelecimentoNoBanco(est) {
  const resposta = await fetch(`${API_URL}/estabelecimentos/${est.id}`, {
    method: 'DELETE'
  })
  if (!resposta.ok) {
    throw new Error('Não foi possível remover o estabelecimento do banco.')
  }
  await carregarDadosDoBanco()
}

export function iniciarNovoFormulario() {
  modoEdicaoId.value = null
  const idPadrao = usuariosCadastrados.value[0]?.id_usuario || 1
  formEstabelecimento.value = {
    nome: '',
    id_usuario: idPadrao,
    andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
  }
}

export function carregarFormularioEdicao(est) {
  modoEdicaoId.value = est.id
  formEstabelecimento.value = JSON.parse(JSON.stringify(est))
}