<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  paletaSetores,
  escurecerCorHex,
  criarMatrizVazia,
  estabelecimentos,
  modoEdicaoId,
  formEstabelecimento
} from '../store/estacionamentoStore'

const router = useRouter()

if (!formEstabelecimento.value.andares || !formEstabelecimento.value.andares[0]?.celulas) {
  router.replace({ name: 'admin-info-gerais' })
}

const andarEditorIndex = ref(0)
const andarEditorAtual = computed(() => formEstabelecimento.value.andares[andarEditorIndex.value])

// Menus flutuantes (Mobile/Tablet <= 1024px)
const menuTopoMobileAberto = ref(false)
const menuAdicionarMobileAberto = ref(false)
const mostrarPainelAvisos = ref(false)

function alternarMenuEngrenagem() {
  menuTopoMobileAberto.value = !menuTopoMobileAberto.value
  if (menuTopoMobileAberto.value) {
    menuAdicionarMobileAberto.value = false
    mostrarPainelAvisos.value = false
  }
}

function alternarMenuAdicionar() {
  menuAdicionarMobileAberto.value = !menuAdicionarMobileAberto.value
  if (menuAdicionarMobileAberto.value) {
    menuTopoMobileAberto.value = false
    mostrarPainelAvisos.value = false
  }
}

function alternarPainelAvisos() {
  mostrarPainelAvisos.value = !mostrarPainelAvisos.value
  if (mostrarPainelAvisos.value) {
    menuTopoMobileAberto.value = false
    menuAdicionarMobileAberto.value = false
  }
}

// =========================================================
// TOUCH PAN (ARRASTAR DEDO) E PINCH-TO-ZOOM (MOVIMENTO PINÇA)
// =========================================================
const panX = ref(0)
const panY = ref(0)
const zoomEscala = ref(1)

let toqueUnico = null
let pinchInicial = null

function distanciaEntreToques(t1, t2) {
  return Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY)
}

function pontoMedioToques(t1, t2) {
  return {
    x: (t1.clientX + t2.clientX) / 2,
    y: (t1.clientY + t2.clientY) / 2
  }
}

function aoIniciarToqueGrid(e) {
  if (e.touches.length === 2) {
    toqueUnico = null
    const dist = distanciaEntreToques(e.touches[0], e.touches[1])
    const meio = pontoMedioToques(e.touches[0], e.touches[1])
    pinchInicial = {
      dist,
      escala: zoomEscala.value,
      panX: panX.value,
      panY: panY.value,
      meioX: meio.x,
      meioY: meio.y
    }
  } else if (e.touches.length === 1) {
    pinchInicial = null
    const t = e.touches[0]
    toqueUnico = {
      startX: t.clientX,
      startY: t.clientY,
      lastX: t.clientX,
      lastY: t.clientY,
      panXInicial: panX.value,
      panYInicial: panY.value,
      moveu: false
    }
  }
}

function aoMoverToqueGrid(e) {
  if (e.touches.length === 2 && pinchInicial) {
    const novaDist = distanciaEntreToques(e.touches[0], e.touches[1])
    const novoMeio = pontoMedioToques(e.touches[0], e.touches[1])
    const fator = novaDist / pinchInicial.dist
    zoomEscala.value = Math.min(2.5, Math.max(0.45, pinchInicial.escala * fator))
    panX.value = pinchInicial.panX + (novoMeio.x - pinchInicial.meioX)
    panY.value = pinchInicial.panY + (novoMeio.y - pinchInicial.meioY)
  } else if (e.touches.length === 1 && toqueUnico) {
    const t = e.touches[0]
    toqueUnico.lastX = t.clientX
    toqueUnico.lastY = t.clientY
    const dx = t.clientX - toqueUnico.startX
    const dy = t.clientY - toqueUnico.startY

    if (Math.hypot(dx, dy) > 7) {
      toqueUnico.moveu = true
      panX.value = toqueUnico.panXInicial + dx
      panY.value = toqueUnico.panYInicial + dy
    }
  }
}

function aoFinalizarToqueGrid(e) {
  if (e.touches.length < 2) {
    pinchInicial = null
  }
  if (e.touches.length === 0 && toqueUnico) {
    // Se foi um toque curto (Tap) sem arrastar a tela, seleciona o quadrado ou aplica o carimbo
    if (!toqueUnico.moveu) {
      const el = document.elementFromPoint(toqueUnico.lastX, toqueUnico.lastY)
      const celulaEl = el?.closest('[data-coord]')
      if (celulaEl) {
        const [cx, cy] = celulaEl.getAttribute('data-coord').split(',').map(Number)
        if (ferramentaCarimbo.value) {
          aplicarCarimboNoGrid(cx, cy)
        } else {
          const chave = `${cx},${cy}`
          const nova = new Set(selecionados.value)
          if (nova.has(chave)) {
            nova.delete(chave)
          } else {
            nova.add(chave)
          }
          selecionados.value = nova
          mostrarMenuFlutuante.value = nova.size > 0
        }
      }
    }
    toqueUnico = null
  }
}

function resetarCameraGrid() {
  panX.value = 0
  panY.value = 0
  zoomEscala.value = 1
}

// =========================================================
// PILHAS DE DESFAZER / REFAZER
// =========================================================
const historicoUndo = ref([])
const historicoRedo = ref([])

function salvarSnapshot() {
  if (!andarEditorAtual.value) return
  historicoUndo.value.push(JSON.stringify({
    grid_x: andarEditorAtual.value.grid_x,
    grid_y: andarEditorAtual.value.grid_y,
    setores: andarEditorAtual.value.setores,
    equipamentos: andarEditorAtual.value.equipamentos,
    celulas: andarEditorAtual.value.celulas
  }))
  if (historicoUndo.value.length > 30) historicoUndo.value.shift()
  historicoRedo.value = []
}

function desfazer() {
  if (historicoUndo.value.length === 0) return
  historicoRedo.value.push(JSON.stringify({
    grid_x: andarEditorAtual.value.grid_x,
    grid_y: andarEditorAtual.value.grid_y,
    setores: andarEditorAtual.value.setores,
    equipamentos: andarEditorAtual.value.equipamentos,
    celulas: andarEditorAtual.value.celulas
  }))
  const estadoAnterior = JSON.parse(historicoUndo.value.pop())
  Object.assign(andarEditorAtual.value, estadoAnterior)
  selecionados.value.clear()
}

function refazer() {
  if (historicoRedo.value.length === 0) return
  historicoUndo.value.push(JSON.stringify({
    grid_x: andarEditorAtual.value.grid_x,
    grid_y: andarEditorAtual.value.grid_y,
    setores: andarEditorAtual.value.setores,
    equipamentos: andarEditorAtual.value.equipamentos,
    celulas: andarEditorAtual.value.celulas
  }))
  const estadoFuturo = JSON.parse(historicoRedo.value.pop())
  Object.assign(andarEditorAtual.value, estadoFuturo)
  selecionados.value.clear()
}

function limparSetoresOrfaosNoAndar(andar) {
  if (!andar || !andar.celulas || !andar.setores) return
  const idsPresentesNoGrid = new Set(
    Object.values(andar.celulas)
      .map(c => c.setorId)
      .filter(Boolean)
  )
  andar.setores = andar.setores.filter(s => idsPresentesNoGrid.has(s.id_setor))
}

// =========================================================
// SISTEMA DE VALIDAÇÃO EM TEMPO REAL
// =========================================================
const listaAvisosValidacao = computed(() => {
  const avisos = []
  if (!formEstabelecimento.value?.andares) return avisos

  let temEntradaGlobal = false
  let temSaidaGlobal = false

  formEstabelecimento.value.andares.forEach((andar) => {
    const celulas = Object.values(andar.celulas || {})

    const vagasAndar = celulas.filter(c => c.tipo === 'VAGA')
    const semEquip = vagasAndar.some(c => !c.macEsp)
    const semSetor = vagasAndar.some(c => !c.setorId)
    const temEntrada = celulas.some(c => c.tipo === 'ENTRADA')
    const temSaida = celulas.some(c => c.tipo === 'SAIDA')
    const temAcesso = celulas.some(c => c.tipo === 'ACESSO')

    if (temEntrada) temEntradaGlobal = true
    if (temSaida) temSaidaGlobal = true

    if (vagasAndar.length === 0) {
      avisos.push(`[${andar.nome_andar}] Precisa ter ao menos 1 vaga cadastrada.`)
    }
    if (semEquip) {
      avisos.push(`[${andar.nome_andar}] Há vagas amarelas sem equipamento.`)
    }
    if (semSetor) {
      avisos.push(`[${andar.nome_andar}] Há vagas fora de um setor.`)
    }
    if (!temEntrada && !temSaida && !temAcesso) {
      avisos.push(`[${andar.nome_andar}] Precisa ter Entrada, Saída ou Acesso.`)
    }

    ;(andar.setores || []).forEach((setor) => {
      const vagasNoSetor = vagasAndar.filter(v => v.setorId === setor.id_setor).length
      if (vagasNoSetor === 0) {
        avisos.push(`[${andar.nome_andar}] Setor "${setor.nome_setor}" (${setor.prefixo}) precisa de 1 vaga.`)
      }
    })
  })

  if (!temEntradaGlobal) {
    avisos.push('[Geral] Obrigatório ter 1 ENTRADA em algum andar.')
  }
  if (!temSaidaGlobal) {
    avisos.push('[Geral] Obrigatório ter 1 SAÍDA em algum andar.')
  }

  return avisos
})

const podeSalvarEstacionamento = computed(() => listaAvisosValidacao.value.length === 0)

// =========================================================
// HOVER DO SETOR E SELEÇÃO POR RATO (DESKTOP)
// =========================================================
const hoverCoord = ref(null)

function contarVagasDoSetorNoAndar(setorId) {
  if (!andarEditorAtual.value?.celulas || !setorId) return 0
  return Object.values(andarEditorAtual.value.celulas).filter(
    c => c.setorId === setorId && c.tipo === 'VAGA'
  ).length
}

const infoSetorHover = computed(() => {
  if (!hoverCoord.value || !andarEditorAtual.value?.celulas) return null
  const celula = andarEditorAtual.value.celulas[`${hoverCoord.value.x},${hoverCoord.value.y}`]
  if (!celula || !celula.setorId) return null

  return {
    nome: celula.nomeSetor,
    prefixo: celula.prefixoSetor,
    cor: celula.corSetor,
    qtdVagas: contarVagasDoSetorNoAndar(celula.setorId)
  }
})

function obterTituloCelula(x, y) {
  const c = andarEditorAtual.value?.celulas[`${x},${y}`]
  if (!c) return `(${x}, ${y})`
  let base = `(${x}, ${y}) ${c.identificador || c.tipo}`
  if (c.setorId) {
    const totalVagasSetor = contarVagasDoSetorNoAndar(c.setorId)
    base += ` | Setor: ${c.nomeSetor} (${totalVagasSetor} vaga${totalVagasSetor === 1 ? '' : 's'})`
  }
  return base
}

const selecionados = ref(new Set())
const arrastando = ref(false)
const pontoInicialArrasto = ref(null)
const baseSelecionadosCtrl = ref(new Set())
const mostrarMenuFlutuante = ref(false)

function iniciarSelecaoCelula(x, y, event) {
  if (ferramentaCarimbo.value) {
    aplicarCarimboNoGrid(x, y)
    return
  }

  arrastando.value = true
  mostrarMenuFlutuante.value = false
  pontoInicialArrasto.value = { x, y }
  const chave = `${x},${y}`

  if (event.ctrlKey || event.metaKey) {
    baseSelecionadosCtrl.value = new Set(selecionados.value)
    if (baseSelecionadosCtrl.value.has(chave)) {
      baseSelecionadosCtrl.value.delete(chave)
    } else {
      baseSelecionadosCtrl.value.add(chave)
    }
    selecionados.value = new Set(baseSelecionadosCtrl.value)
  } else {
    baseSelecionadosCtrl.value = new Set()
    selecionados.value = new Set([chave])
  }
}

function moverMouseCelula(x, y) {
  hoverCoord.value = { x, y }
  if (!arrastando.value || !pontoInicialArrasto.value) return

  const xMin = Math.min(pontoInicialArrasto.value.x, x)
  const xMax = Math.max(pontoInicialArrasto.value.x, x)
  const yMin = Math.min(pontoInicialArrasto.value.y, y)
  const yMax = Math.max(pontoInicialArrasto.value.y, y)

  const novaSelecao = new Set(baseSelecionadosCtrl.value)
  for (let cy = yMin; cy <= yMax; cy++) {
    for (let cx = xMin; cx <= xMax; cx++) {
      novaSelecao.add(`${cx},${cy}`)
    }
  }
  selecionados.value = novaSelecao
}

function finalizarSelecaoMouse() {
  if (arrastando.value) {
    arrastando.value = false
    if (selecionados.value.size > 0) {
      mostrarMenuFlutuante.value = true
    }
  }
}

// =========================================================
// AÇÕES DE SETOR, ESTRADAS, VAGAS E LIXEIRA 🗑️
// =========================================================
function obterProximoNumeroSetor(celulas, setorId, prefixo) {
  let maior = 0
  const regex = new RegExp(`^${prefixo}(\\d+)$`, 'i')
  Object.values(celulas).forEach((c) => {
    if (c.setorId === setorId && c.tipo === 'VAGA' && c.identificador) {
      const match = c.identificador.match(regex)
      if (match) {
        const num = parseInt(match[1], 10)
        if (num > maior) maior = num
      }
    }
  })
  return maior + 1
}

function numerarVagasDoSetor(celulas, setorId, prefixo) {
  const vagasDoSetor = Object.values(celulas)
    .filter(c => c.setorId === setorId && c.tipo === 'VAGA')
    .sort((a, b) => (a.y - b.y) || (a.x - b.x))

  vagasDoSetor.forEach((vaga, idx) => {
    vaga.identificador = `${prefixo}${idx + 1}`
  })
}

function aplicarTipoSelecao(novoTipo) {
  const celulas = andarEditorAtual.value.celulas
  const chaves = Array.from(selecionados.value)

  const temConflito = chaves.some((k) => {
    const atual = celulas[k]?.tipo
    return (novoTipo === 'ESTRADA' && atual === 'VAGA') || (novoTipo === 'VAGA' && atual === 'ESTRADA')
  })

  if (temConflito) {
    const msg = novoTipo === 'ESTRADA'
      ? 'Existem VAGAS na seleção. Deseja substituí-las por ESTRADAS?'
      : 'Existem ESTRADAS na seleção. Deseja substituí-las por VAGAS?'
    if (!confirm(msg)) return
  }

  salvarSnapshot()

  const chavesOrdenadas = chaves.sort((a, b) => {
    const [ax, ay] = a.split(',').map(Number)
    const [bx, by] = b.split(',').map(Number)
    return (ay - by) || (ax - bx)
  })

  chavesOrdenadas.forEach((k) => {
    const c = celulas[k]
    if (!c) return
    const jaEraVaga = c.tipo === 'VAGA'
    c.tipo = novoTipo
    c.orientacao = 'NENHUMA'

    if (novoTipo === 'VAGA') {
      c.macEsp = null
      c.livre = true
      if (c.setorId && c.prefixoSetor) {
        if (!jaEraVaga || !c.identificador) {
          const prox = obterProximoNumeroSetor(celulas, c.setorId, c.prefixoSetor)
          c.identificador = `${c.prefixoSetor}${prox}`
        }
      } else {
        c.identificador = ''
      }
    } else {
      c.macEsp = null
      c.identificador = ''
    }
  })

  mostrarMenuFlutuante.value = false
  selecionados.value.clear()
}

function removerTipoSelecao(tipoAlvo) {
  salvarSnapshot()
  const celulas = andarEditorAtual.value.celulas
  selecionados.value.forEach((k) => {
    const c = celulas[k]
    if (!c) return
    if (tipoAlvo === 'SETOR') {
      c.setorId = null
      c.corSetor = null
      c.nomeSetor = null
      c.prefixoSetor = null
      if (c.tipo === 'VAGA') c.identificador = ''
    } else if (c.tipo === tipoAlvo) {
      c.tipo = 'VAZIO'
      c.macEsp = null
      c.identificador = ''
    }
  })
  limparSetoresOrfaosNoAndar(andarEditorAtual.value)
  mostrarMenuFlutuante.value = false
  selecionados.value.clear()
}

function limparTudoNaSelecao() {
  salvarSnapshot()
  const celulas = andarEditorAtual.value.celulas
  selecionados.value.forEach((k) => {
    const c = celulas[k]
    if (!c) return
    c.tipo = 'VAZIO'
    c.orientacao = 'NENHUMA'
    c.setorId = null
    c.corSetor = null
    c.nomeSetor = null
    c.prefixoSetor = null
    c.vagaId = null
    c.identificador = ''
    c.livre = true
    c.macEsp = null
  })
  limparSetoresOrfaosNoAndar(andarEditorAtual.value)
  mostrarMenuFlutuante.value = false
  selecionados.value.clear()
}

// =========================================================
// MODAIS COMPACTOS (SETOR, TAMANHO DO GRID, ACESSOS E MAC)
// =========================================================
const modalSetorAberto = ref(false)
const novoSetorNome = ref('')
const novoSetorPrefixo = ref('A')
const novoSetorCor = ref(paletaSetores[0].hex)

function abrirModalSetor() {
  novoSetorNome.value = ''
  novoSetorPrefixo.value = 'A'
  novoSetorCor.value = paletaSetores[0].hex
  modalSetorAberto.value = true
}

function sanitizarPrefixoSetor() {
  novoSetorPrefixo.value = novoSetorPrefixo.value.replace(/[^a-zA-Z]/g, '').slice(0, 3).toUpperCase()
}

function confirmarSetorSelecao() {
  const nomeLimpo = novoSetorNome.value.trim()
  const prefixoFinal = novoSetorPrefixo.value.trim().slice(0, 3).toUpperCase()

  if (!nomeLimpo) {
    alert('Digite um nome para o setor!')
    return
  }
  if (!prefixoFinal) {
    alert('Digite um prefixo (1 a 3 letras) para o setor!')
    return
  }

  for (const andar of formEstabelecimento.value.andares) {
    limparSetoresOrfaosNoAndar(andar)
    for (const s of andar.setores || []) {
      if (s.nome_setor.toLowerCase() === nomeLimpo.toLowerCase()) {
        alert(`O nome de setor "${nomeLimpo}" já está em uso no andar "${andar.nome_andar}".`)
        return
      }
      if ((s.prefixo || '').toUpperCase() === prefixoFinal) {
        alert(`O prefixo "${prefixoFinal}" já está em uso pelo setor "${s.nome_setor}".`)
        return
      }
    }
  }

  salvarSnapshot()
  const idSetor = Date.now()
  andarEditorAtual.value.setores.push({
    id_setor: idSetor,
    nome_setor: nomeLimpo,
    prefixo: prefixoFinal,
    cor_hex: novoSetorCor.value,
    inativo_offline: false
  })

  const celulas = andarEditorAtual.value.celulas
  selecionados.value.forEach((k) => {
    const c = celulas[k]
    if (c) {
      c.setorId = idSetor
      c.nomeSetor = nomeLimpo
      c.prefixoSetor = prefixoFinal
      c.corSetor = novoSetorCor.value
    }
  })

  limparSetoresOrfaosNoAndar(andarEditorAtual.value)
  numerarVagasDoSetor(celulas, idSetor, prefixoFinal)

  modalSetorAberto.value = false
  mostrarMenuFlutuante.value = false
  selecionados.value.clear()
}

const modalGridAberto = ref(false)
const inputGridX = ref(30)
const inputGridY = ref(20)

function clonarLimiteGridX() {
  const v = parseInt(inputGridX.value, 10)
  if (!isNaN(v)) {
    if (v > 100) inputGridX.value = 100
    if (v < 5) inputGridX.value = 5
  }
}

function clonarLimiteGridY() {
  const v = parseInt(inputGridY.value, 10)
  if (!isNaN(v)) {
    if (v > 100) inputGridY.value = 100
    if (v < 5) inputGridY.value = 5
  }
}

function abrirModalTamanhoGrid() {
  inputGridX.value = andarEditorAtual.value.grid_x
  inputGridY.value = andarEditorAtual.value.grid_y
  menuTopoMobileAberto.value = false
  modalGridAberto.value = true
}

function confirmarTamanhoGrid() {
  const nx = Math.min(100, Math.max(5, parseInt(inputGridX.value, 10) || 30))
  const ny = Math.min(100, Math.max(5, parseInt(inputGridY.value, 10) || 20))
  inputGridX.value = nx
  inputGridY.value = ny
  salvarSnapshot()

  const novasCelulas = criarMatrizVazia(nx, ny)
  Object.values(andarEditorAtual.value.celulas).forEach((antiga) => {
    if (antiga.x <= nx && antiga.y <= ny) {
      novasCelulas[`${antiga.x},${antiga.y}`] = antiga
    }
  })

  andarEditorAtual.value.grid_x = nx
  andarEditorAtual.value.grid_y = ny
  andarEditorAtual.value.celulas = novasCelulas
  limparSetoresOrfaosNoAndar(andarEditorAtual.value)
  modalGridAberto.value = false
}

const ferramentaCarimbo = ref(null)
const modalAcessoAberto = ref(false)
const configAcessoTemp = ref({ tipo: 'ENTRADA', orientacao: 'H', tamanho: 2 })

function prepararAcesso(tipo, orientacao) {
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
  menuAdicionarMobileAberto.value = false
  configAcessoTemp.value = { tipo, orientacao, tamanho: 2 }
  modalAcessoAberto.value = true
}

function ajustarLimiteAcesso() {
  const val = parseInt(configAcessoTemp.value.tamanho, 10)
  if (isNaN(val)) return
  if (val > 20) configAcessoTemp.value.tamanho = 20
  if (val < 1) configAcessoTemp.value.tamanho = 1
}

function ativarCarimboAcesso() {
  const tam = Math.max(1, Math.min(20, parseInt(configAcessoTemp.value.tamanho, 10) || 1))
  configAcessoTemp.value.tamanho = tam
  ferramentaCarimbo.value = {
    categoria: 'ACESSO',
    tipo: configAcessoTemp.value.tipo,
    orientacao: configAcessoTemp.value.orientacao,
    w: configAcessoTemp.value.orientacao === 'H' ? tam : 1,
    h: configAcessoTemp.value.orientacao === 'V' ? tam : 1
  }
  modalAcessoAberto.value = false
}

const linhasEquipamentos = [
  [{ w: 1, h: 2 }, { w: 1, h: 3 }, { w: 1, h: 4 }],
  [{ w: 2, h: 3 }, { w: 2, h: 4 }],
  [{ w: 1, h: 1 }, { w: 2, h: 2 }],
  [{ w: 2, h: 1 }, { w: 3, h: 1 }, { w: 4, h: 1 }],
  [{ w: 3, h: 2 }, { w: 4, h: 2 }]
]

function ativarCarimboEquipamento(w, h) {
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
  menuAdicionarMobileAberto.value = false
  ferramentaCarimbo.value = { categoria: 'EQUIPAMENTO', tipo: 'ESP32', w, h }
}

function estaNaSombraCarimbo(x, y) {
  if (!ferramentaCarimbo.value || !hoverCoord.value) return false
  const { w, h } = ferramentaCarimbo.value
  return (
    x >= hoverCoord.value.x &&
    x < hoverCoord.value.x + w &&
    y >= hoverCoord.value.y &&
    y < hoverCoord.value.y + h
  )
}

const modalMacAberto = ref(false)
const inputMacEsp = ref('AA:BB:CC:DD:EE:01')
const coordenadasCarimboPendente = ref([])

function aplicarCarimboNoGrid(startX, startY) {
  const carimbo = ferramentaCarimbo.value
  if (!carimbo) return

  const coordsAfetadas = []
  for (let cy = startY; cy < startY + carimbo.h; cy++) {
    for (let cx = startX; cx < startX + carimbo.w; cx++) {
      if (cx <= andarEditorAtual.value.grid_x && cy <= andarEditorAtual.value.grid_y) {
        coordsAfetadas.push(`${cx},${cy}`)
      }
    }
  }

  const celulas = andarEditorAtual.value.celulas

  if (carimbo.categoria === 'ACESSO') {
    const temVagaOuEstrada = coordsAfetadas.some(
      k => celulas[k].tipo === 'VAGA' || celulas[k].tipo === 'ESTRADA'
    )
    if (temVagaOuEstrada) {
      if (!confirm('Ao clicar em Ok, as vagas e as estradas da seleção serão removidas')) {
        return
      }
    }
    salvarSnapshot()
    coordsAfetadas.forEach((k) => {
      celulas[k].tipo = carimbo.tipo
      celulas[k].orientacao = carimbo.orientacao
      celulas[k].macEsp = null
      celulas[k].identificador = ''
    })
    ferramentaCarimbo.value = null
    return
  }

  if (carimbo.categoria === 'EQUIPAMENTO') {
    const vagasDebaixo = coordsAfetadas.filter(k => celulas[k].tipo === 'VAGA')
    if (vagasDebaixo.length === 0) {
      alert('Nenhuma VAGA encontrada sob este carimbo de equipamento! Crie as vagas primeiro.')
      return
    }
    coordenadasCarimboPendente.value = vagasDebaixo
    modalMacAberto.value = true
  }
}

function confirmarVinculoEquipamento() {
  if (!inputMacEsp.value.trim()) {
    alert('Informe o código MAC ou identificador do ESP32.')
    return
  }
  salvarSnapshot()
  const celulas = andarEditorAtual.value.celulas

  coordenadasCarimboPendente.value.forEach((k) => {
    const c = celulas[k]
    c.macEsp = inputMacEsp.value.trim().toUpperCase()
    if (c.setorId && c.prefixoSetor && !c.identificador) {
      const prox = obterProximoNumeroSetor(celulas, c.setorId, c.prefixoSetor)
      c.identificador = `${c.prefixoSetor}${prox}`
    }
  })

  modalMacAberto.value = false
  ferramentaCarimbo.value = null
}

function finalizarSalvarEstacionamento() {
  if (!podeSalvarEstacionamento.value) {
    mostrarPainelAvisos.value = true
    return
  }

  if (modoEdicaoId.value) {
    const idx = estabelecimentos.value.findIndex(e => e.id === modoEdicaoId.value)
    if (idx !== -1) {
      estabelecimentos.value[idx] = JSON.parse(JSON.stringify(formEstabelecimento.value))
    }
  } else {
    const novoId = estabelecimentos.value.length > 0
      ? Math.max(...estabelecimentos.value.map(e => e.id)) + 1
      : 1
    estabelecimentos.value.push({
      ...JSON.parse(JSON.stringify(formEstabelecimento.value)),
      id: novoId,
      inativo: false
    })
  }

  alert('✅ Estacionamento salvo com sucesso!')
  router.push({ name: 'admin-lista' })
}

function tratarTeclaGlobal(event) {
  if (event.key === 'Escape') {
    if (ferramentaCarimbo.value) ferramentaCarimbo.value = null
    if (mostrarMenuFlutuante.value) {
      mostrarMenuFlutuante.value = false
      selecionados.value.clear()
    }
    mostrarPainelAvisos.value = false
    menuTopoMobileAberto.value = false
    menuAdicionarMobileAberto.value = false
  }
}

onMounted(() => {
  window.addEventListener('mouseup', finalizarSelecaoMouse)
  window.addEventListener('keydown', tratarTeclaGlobal)
})

onUnmounted(() => {
  window.removeEventListener('mouseup', finalizarSelecaoMouse)
  window.removeEventListener('keydown', tratarTeclaGlobal)
})
</script>

<template>
  <div v-if="andarEditorAtual" class="editor-layout">
    <!-- =======================================================
         HUD FLUTUANTE MOBILE/TABLET MENOR (<= 1024px)
         Esquerda: ☰ (no App.vue) e ⚠️ abaixo dele
         Direita: 💾 no topo, ⚙️ abaixo, ➕ abaixo
         ======================================================= -->
    <button
      class="hud-btn-flutuante hud-esquerda-alertas"
      :class="{ 'caution-ok': podeSalvarEstacionamento, 'caution-pendente': !podeSalvarEstacionamento }"
      title="Avisos de validação"
      @click="alternarPainelAvisos"
    >
      ⚠️
      <span class="hud-mini-badge">{{ listaAvisosValidacao.length }}</span>
    </button>

    <div class="hud-coluna-direita-mobile">
      <button
        class="hud-btn-flutuante hud-btn-salvar"
        :disabled="!podeSalvarEstacionamento"
        title="Finalizar e Salvar"
        @click="finalizarSalvarEstacionamento"
      >
        💾
      </button>

      <!-- Apenas o ícone de engrenagem sem texto -->
      <button
        class="hud-btn-flutuante"
        :class="{ 'hud-ativo': menuTopoMobileAberto }"
        title="Opções do Editor"
        @click="alternarMenuEngrenagem"
      >
        ⚙️
      </button>

      <!-- Menu de Adicionar (Grupo 1 e Grupo 2) embaixo da engrenagem -->
      <button
        class="hud-btn-flutuante hud-btn-add"
        :class="{ 'hud-ativo': menuAdicionarMobileAberto }"
        title="Adicionar Acessos e Equipamentos"
        @click="alternarMenuAdicionar"
      >
        ➕
      </button>
    </div>

    <!-- BARRA SUPERIOR DO EDITOR (Visível no Desktop; Popover quando ⚙️ é clicado no Mobile) -->
    <header
      class="editor-topbar"
      :class="{ 'topbar-mobile-aberta': menuTopoMobileAberto }"
    >
      <div class="topbar-esquerda">
        <button class="btn-secundario btn-duas-linhas" @click="router.push({ name: 'admin-info-gerais' })">
          ⬅️ Editar estacionamento<br /><span>Informações Gerais</span>
        </button>

        <div class="seletor-andar-box">
          <span>Andar:</span>
          <select
            v-if="formEstabelecimento.andares.length > 1"
            v-model="andarEditorIndex"
            class="select-andar-editor"
            @change="selecionados.clear(); historicoUndo = []; historicoRedo = []; resetarCameraGrid(); menuTopoMobileAberto = false"
          >
            <option
              v-for="(a, idx) in formEstabelecimento.andares"
              :key="a.id_andar"
              :value="idx"
            >
              {{ a.nome_andar }} ({{ a.grid_x }}x{{ a.grid_y }})
            </option>
          </select>
          <strong v-else>{{ andarEditorAtual.nome_andar }}</strong>
        </div>

        <button class="btn-secundario btn-duas-linhas" @click="abrirModalTamanhoGrid">
          📐 Tamanho do Grid<br /><span>({{ andarEditorAtual.grid_x }}x{{ andarEditorAtual.grid_y }})</span>
        </button>

        <button class="btn-secundario" :disabled="historicoUndo.length === 0" @click="desfazer">
          ↩️ Desfazer
        </button>
        <button class="btn-secundario" :disabled="historicoRedo.length === 0" @click="refazer">
          ↪️ Refazer
        </button>
        <button
          v-if="panX !== 0 || panY !== 0 || zoomEscala !== 1"
          class="btn-secundario"
          title="Centralizar Zoom"
          @click="resetarCameraGrid"
        >
          🔍 {{ Math.round(zoomEscala * 100) }}%
        </button>
      </div>

      <div class="topbar-direita">
        <button
          class="btn-caution-avisos"
          :class="{ 'caution-ok': podeSalvarEstacionamento, 'caution-pendente': !podeSalvarEstacionamento }"
          title="Clique para mostrar/ocultar avisos de validação"
          @click="alternarPainelAvisos"
        >
          ⚠️
          <span class="caution-badge">{{ listaAvisosValidacao.length }}</span>
        </button>

        <button
          class="btn-salvar-final btn-duas-linhas"
          :disabled="!podeSalvarEstacionamento"
          @click="finalizarSalvarEstacionamento"
        >
          💾 Finalizar e<br /><span>Salvar no Banco</span>
        </button>
      </div>
    </header>

    <!-- WORKSPACE PRINCIPAL -->
    <div class="editor-workspace">
      <div class="area-grid-container">
        <!-- 1. OVERLAY DE AVISOS -->
        <Transition name="fade-pop">
          <div v-if="mostrarPainelAvisos" class="overlay-flutuante painel-avisos-overlay">
            <div class="overlay-header">
              <strong>⚠️ Validação ({{ listaAvisosValidacao.length }})</strong>
              <button class="btn-fechar-mini" @click="mostrarPainelAvisos = false">✖</button>
            </div>
            <ul v-if="listaAvisosValidacao.length > 0" class="lista-avisos-ul">
              <li v-for="(aviso, i) in listaAvisosValidacao" :key="i">{{ aviso }}</li>
            </ul>
            <p v-else class="aviso-tudo-ok">
              ✅ Tudo certo! Todos os andares, setores, vagas e acessos estão validados.
            </p>
          </div>
        </Transition>

        <!-- 2. OVERLAY DE CARIMBO ATIVO -->
        <Transition name="fade-pop">
          <div v-if="ferramentaCarimbo" class="overlay-flutuante banner-carimbo-overlay">
            <span>
              🎯 <strong>{{ ferramentaCarimbo.tipo }} ({{ ferramentaCarimbo.w }}x{{ ferramentaCarimbo.h }})</strong> — Toque no Grid
            </span>
            <button class="btn-cancelar-carimbo" @click="ferramentaCarimbo = null">✖</button>
          </div>
        </Transition>

        <!-- 3. OVERLAY DE SELEÇÃO DE QUADRADOS (COM LIXEIRA 🗑️) -->
        <Transition name="fade-pop">
          <div v-if="mostrarMenuFlutuante && selecionados.size > 0" class="overlay-flutuante menu-selecao-overlay">
            <span class="contagem-sel">{{ selecionados.size }} sel.:</span>

            <div class="grupo-acao-item">
              <span>🛣️</span>
              <button class="btn-mini add" title="Adicionar Estrada" @click="aplicarTipoSelecao('ESTRADA')">➕</button>
              <button class="btn-mini rem" title="Remover Estrada" @click="removerTipoSelecao('ESTRADA')">➖</button>
            </div>

            <div class="grupo-acao-item">
              <span>🎨</span>
              <button class="btn-mini add" title="Definir Setor" @click="abrirModalSetor">➕</button>
              <button class="btn-mini rem" title="Remover Setor" @click="removerTipoSelecao('SETOR')">➖</button>
            </div>

            <div class="grupo-acao-item">
              <span>🅿️</span>
              <button class="btn-mini add" title="Adicionar Vagas" @click="aplicarTipoSelecao('VAGA')">➕</button>
              <button class="btn-mini rem" title="Remover Vagas" @click="removerTipoSelecao('VAGA')">➖</button>
            </div>

            <button
              class="btn-mini lixeira-tudo"
              title="Remover TUDO na seleção"
              @click="limparTudoNaSelecao"
            >
              🗑️
            </button>

            <button
              class="btn-mini limpar"
              title="Desselecionar"
              @click="selecionados.clear(); mostrarMenuFlutuante = false"
            >
              ✖
            </button>
          </div>
        </Transition>

        <!-- 4. OVERLAY DE HOVER DO SETOR -->
        <Transition name="fade-pop">
          <div v-if="infoSetorHover" class="overlay-flutuante badge-hover-setor">
            <span class="bolinha-cor-setor" :style="{ backgroundColor: infoSetorHover.cor }"></span>
            <strong>{{ infoSetorHover.nome }} ({{ infoSetorHover.prefixo }})</strong>
            <span>— {{ infoSetorHover.qtdVagas }} vaga(s)</span>
          </div>
        </Transition>

        <!-- TABULEIRO 2D COM SUPORTE A PAN E PINCH-TO-ZOOM -->
        <div
          class="area-grid-principal"
          @mouseleave="hoverCoord = null"
          @touchstart.passive="aoIniciarToqueGrid"
          @touchmove.prevent="aoMoverToqueGrid"
          @touchend="aoFinalizarToqueGrid"
        >
          <div
            class="viewport-touch-canvas"
            :style="{
              transform: `translate(${panX}px, ${panY}px) scale(${zoomEscala})`,
              transformOrigin: '0 0'
            }"
          >
            <div class="matriz-com-coordenadas">
              <div
                class="linha-coordenadas-x"
                :style="{ gridTemplateColumns: `36px repeat(${andarEditorAtual.grid_x}, 36px)` }"
              >
                <div class="canto-xy">Y\X</div>
                <div v-for="x in andarEditorAtual.grid_x" :key="`coord-x-${x}`" class="rotulo-coord">
                  {{ x }}
                </div>
              </div>

              <div
                v-for="y in andarEditorAtual.grid_y"
                :key="`row-${y}`"
                class="linha-grid-y"
                :style="{ gridTemplateColumns: `36px repeat(${andarEditorAtual.grid_x}, 36px)` }"
              >
                <div class="rotulo-coord">{{ y }}</div>

                <div
                  v-for="x in andarEditorAtual.grid_x"
                  :key="`cell-${x}-${y}`"
                  :data-coord="`${x},${y}`"
                  class="celula-editor-fundo"
                  :style="{
                    backgroundColor: andarEditorAtual.celulas[`${x},${y}`]?.corSetor || 'transparent'
                  }"
                  @mousedown.prevent="iniciarSelecaoCelula(x, y, $event)"
                  @mouseenter="moverMouseCelula(x, y)"
                >
                  <div
                    class="quadrado-editor"
                    :class="{
                      'qe-vazio': andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'VAZIO',
                      'qe-estrada': andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'ESTRADA',
                      'qe-vaga-amarela': andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarEditorAtual.celulas[`${x},${y}`]?.macEsp,
                      'qe-entrada': andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'ENTRADA',
                      'qe-saida': andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'SAIDA',
                      'qe-acesso': andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'ACESSO',
                      'qe-selecionado-roxo': selecionados.has(`${x},${y}`),
                      'qe-sombra-verde': estaNaSombraCarimbo(x, y)
                    }"
                    :style="
                      andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' &&
                      andarEditorAtual.celulas[`${x},${y}`]?.macEsp &&
                      !selecionados.has(`${x},${y}`)
                        ? { backgroundColor: escurecerCorHex(andarEditorAtual.celulas[`${x},${y}`]?.corSetor) }
                        : {}
                    "
                    :title="obterTituloCelula(x, y)"
                  >
                    <span v-if="andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'VAGA'">
                      {{ andarEditorAtual.celulas[`${x},${y}`]?.identificador || 'V' }}
                    </span>
                    <span v-else-if="andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'ENTRADA'">E</span>
                    <span v-else-if="andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'SAIDA'">S</span>
                    <span v-else-if="andarEditorAtual.celulas[`${x},${y}`]?.tipo === 'ACESSO'">A</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SIDEBAR DIREITA (Fixa em Desktop; Abre no botão ➕ em Mobile/Tablet <= 1024px) -->
      <aside
        class="sidebar-direita-editor"
        :class="{ 'sidebar-mobile-aberta': menuAdicionarMobileAberto }"
      >
        <div class="painel-ferramentas">
          <h4>🚪 Entradas / Saídas / Acessos</h4>
          <p class="dica-painel">Clique para definir o tamanho e posicionar</p>

          <div class="linha-botoes-dupla">
            <button class="btn-ferramenta cor-entrada" @click="prepararAcesso('ENTRADA', 'H')">
              ➡️ Entrada (H)
            </button>
            <button class="btn-ferramenta cor-entrada" @click="prepararAcesso('ENTRADA', 'V')">
              ⬇️ Entrada (V)
            </button>
          </div>

          <div class="linha-botoes-dupla">
            <button class="btn-ferramenta cor-saida" @click="prepararAcesso('SAIDA', 'H')">
              ➡️ Saída (H)
            </button>
            <button class="btn-ferramenta cor-saida" @click="prepararAcesso('SAIDA', 'V')">
              ⬇️ Saída (V)
            </button>
          </div>

          <div class="linha-botoes-dupla">
            <button class="btn-ferramenta cor-acesso" @click="prepararAcesso('ACESSO', 'H')">
              🚶 Acesso (H)
            </button>
            <button class="btn-ferramenta cor-acesso" @click="prepararAcesso('ACESSO', 'V')">
              🚶 Acesso (V)
            </button>
          </div>
        </div>

        <div class="painel-ferramentas">
          <h4>📡 Equipamentos (ESP32)</h4>
          <p class="dica-painel">Escolha o formato (X por Y) e clique nas vagas</p>

          <div
            v-for="(linha, rIdx) in linhasEquipamentos"
            :key="`eq-row-${rIdx}`"
            class="linha-equipamentos"
          >
            <button
              v-for="item in linha"
              :key="`${item.w}x${item.h}`"
              class="btn-equipamento"
              @click="ativarCarimboEquipamento(item.w, item.h)"
            >
              🔌 {{ item.w }}x{{ item.h }}
            </button>
          </div>
        </div>

        <div class="painel-ferramentas legenda-editor">
          <h4>📌 Cores do Editor</h4>
          <div><span class="amostra" style="background:#cbd5e1"></span> Cinza Claro: Vazio</div>
          <div><span class="amostra amostra-asfalto"></span> Asfalto Escuro: Estrada</div>
          <div><span class="amostra" style="background:#eab308"></span> Amarelo: Vaga sem ESP32</div>
          <div><span class="amostra" style="background:#005066"></span> Cor Escura: Vaga Vinculada</div>
        </div>
      </aside>
    </div>

    <!-- =======================================================
         MODAIS POP-UP MAIS COMPACTOS E PROPORCIONAIS
         ======================================================= -->
    <Transition name="fade-pop">
      <div v-if="modalSetorAberto" class="modal-backdrop">
        <div class="modal-box">
          <h3>🎨 Definir Setor</h3>
          <div class="campo-grupo" style="margin-top:10px">
            <label>Nome do Setor (único)</label>
            <input v-model="novoSetorNome" type="text" maxlength="25" placeholder="Ex: Setor A" />
          </div>
          <div class="campo-grupo">
            <label>Prefixo das Vagas (máx. 3 letras)</label>
            <input
              v-model="novoSetorPrefixo"
              type="text"
              maxlength="3"
              class="input-curto-prefixo"
              placeholder="A"
              @input="sanitizarPrefixoSetor"
            />
          </div>
          <div class="campo-grupo">
            <label>Cor viva do setor:</label>
            <div class="grade-cores-setor">
              <button
                v-for="cor in paletaSetores"
                :key="cor.hex"
                class="botao-cor-setor"
                :class="{ 'cor-selecionada': novoSetorCor === cor.hex }"
                :style="{ backgroundColor: cor.hex }"
                @click="novoSetorCor = cor.hex"
              >
                {{ cor.nome }}
              </button>
            </div>
          </div>
          <div class="modal-acoes">
            <button class="btn-secundario" @click="modalSetorAberto = false">Cancelar</button>
            <button class="btn-primario" @click="confirmarSetorSelecao">OK</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade-pop">
      <div v-if="modalGridAberto" class="modal-backdrop">
        <div class="modal-box modal-compacto">
          <h3>📐 Tamanho do Grid</h3>
          <p class="subtitulo">Mín. 5 | Máx. 100</p>
          <div class="linha-inputs-compactos">
            <div class="campo-compacto">
              <label>Largura (X)</label>
              <input
                v-model="inputGridX"
                type="number"
                min="5"
                max="100"
                class="input-numero-compacto"
                @input="clonarLimiteGridX"
                @change="clonarLimiteGridX"
              />
            </div>
            <span class="separador-x">×</span>
            <div class="campo-compacto">
              <label>Altura (Y)</label>
              <input
                v-model="inputGridY"
                type="number"
                min="5"
                max="100"
                class="input-numero-compacto"
                @input="clonarLimiteGridY"
                @change="clonarLimiteGridY"
              />
            </div>
          </div>
          <div class="modal-acoes">
            <button class="btn-secundario" @click="modalGridAberto = false">Cancelar</button>
            <button class="btn-primario" @click="confirmarTamanhoGrid">Aplicar</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade-pop">
      <div v-if="modalAcessoAberto" class="modal-backdrop">
        <div class="modal-box modal-compacto">
          <h3>
            🚪 {{ configAcessoTemp.tipo }}
            ({{ configAcessoTemp.orientacao === 'H' ? 'Horiz.' : 'Vert.' }})
          </h3>
          <div class="campo-compacto" style="margin-top:10px">
            <label v-if="configAcessoTemp.orientacao === 'H'">Largura X (1 a 20):</label>
            <label v-else>Altura Y (1 a 20):</label>
            <input
              v-model="configAcessoTemp.tamanho"
              type="number"
              min="1"
              max="20"
              class="input-numero-compacto"
              @input="ajustarLimiteAcesso"
              @change="ajustarLimiteAcesso"
            />
          </div>
          <div class="modal-acoes">
            <button class="btn-secundario" @click="modalAcessoAberto = false">Cancelar</button>
            <button class="btn-primario" @click="ativarCarimboAcesso">OK</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade-pop">
      <div v-if="modalMacAberto" class="modal-backdrop">
        <div class="modal-box modal-compacto">
          <h3>📡 Vincular ESP32</h3>
          <p class="subtitulo">
            {{ coordenadasCarimboPendente.length }} vaga(s) selecionada(s)
          </p>
          <div class="campo-grupo" style="margin-top:10px">
            <label>Código MAC do ESP32</label>
            <input v-model="inputMacEsp" type="text" maxlength="17" placeholder="AA:BB:CC:DD:EE:FF" />
          </div>
          <div class="modal-acoes">
            <button class="btn-secundario" @click="modalMacAberto = false">Cancelar</button>
            <button class="btn-primario" @click="confirmarVinculoEquipamento">Vincular</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>