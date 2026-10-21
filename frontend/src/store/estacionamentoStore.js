import { ref } from 'vue'

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
        tipo: 'VAZIO', // 'VAZIO' | 'ESTRADA' | 'VAGA' | 'ENTRADA' | 'SAIDA' | 'ACESSO'
        orientacao: 'NENHUMA',
        vagaId: null,
        identificador: '',
        livre: true,
        macEsp: null
      }
    }
  }
  return celulas
}

// Reconstrói o dicionário `celulas` do Editor 2D a partir das tabelas SQL retornadas pela API
function hidratarEstabelecimentoDoBanco(estBanco) {
  const andaresHidratados = (estBanco.andares || []).map((andar) => {
    const celulas = criarMatrizVazia(andar.grid_x, andar.grid_y)
    const mapaSetores = {}
    ;(andar.setores || []).forEach((s) => {
      mapaSetores[s.id_setor] = s
    })

    // 1. Preenche estradas, entradas, saídas, acessos e fundos de setor
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

    // 2. Preenche as vagas e seus vínculos com ESP32 e Setor
    ;(andar.vagas || []).forEach((v) => {
      const chave = `${v.coord_x},${v.coord_y}`
      const c = celulas[chave]
      if (!c) return

      c.tipo = 'VAGA'
      c.vagaId = v.id_vaga
      c.identificador = v.identificador
      c.livre = Boolean(v.livre)
      c.macEsp = v.mac_esp
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

// =========================================================
// ESTADO GLOBAL REATIVO (AGORA POPULADO PELO MYSQL)
// =========================================================
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
    }
  } catch (err) {
    console.error('Erro ao conectar com a API FastAPI:', err)
  } finally {
    carregandoDados.value = false
  }
}

export async function salvarEstacionamentoNoBanco() {
  // Converte a matriz de cada andar em uma lista enxuta apenas com os quadrados preenchidos
  const payload = {
    nome: formEstabelecimento.value.nome,
    id_usuario: formEstabelecimento.value.id_usuario,
    andares: formEstabelecimento.value.andares.map((andar) => {
      const celulasPreenchidas = []

      Object.values(andar.celulas || {}).forEach((c) => {
        if (c.tipo === 'VAZIO' && !c.setorId) return // Ignora quadrados cinzas vazios!

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