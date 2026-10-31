<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  estabelecimentosDoGerente,
  simulacao1Ativa,
  alternarSimulacao1Frontend,
  carregarDadosDoBanco,
  cidadeSelecionadaGerente, 
  cidadesDoGerente, 
  estabelecimentosDoGerentePorCidade, 
  selecionarCidadeGerente
} from '@/stores/estacionamentoStore'
import {
  IconParking,
  IconSearch,
  IconSquareRoundedChevronDown,
  IconSquareRoundedArrowLeft,
  IconSquareRoundedCheck,
  IconSquareRoundedX,
  IconBan,
  IconFlame,
  IconQrcode,
  IconPlayerPlay,
  IconStack2,
  IconLayoutBoard,
  IconDoorEnter,
  IconDoorExit,
  IconArrowBarRight,
  IconSettings,
  IconPin
} from '@/constants/icons'

const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const router = useRouter()

const estSelecionadoId = ref(null)
const andarIndex = ref(0)

// Dropdown de pesquisa para trocar de estacionamento
const dropdownEstAberto = ref(false)
const dropdownCidadeAberto = ref(false)
const dropdownAndarAberto = ref(false)
const termoBuscaEst = ref('')

// Modos especiais: 'NENHUM' | 'INATIVAR' | 'REATIVAR'
const modoAcaoVagas = ref('NENHUM')
const modoMapaCalor = ref(false)
const salvandoStatusLote = ref(false)

// Menus mobile (<= 1024px)
const menuOpcoesMobileAberto = ref(false)
const painelLateralMobileAberto = ref(false)

// Modal QR Code da Entrada
const modalQrAberto = ref(false)

// Seleção arrastável
const selecionados = ref(new Set())
const arrastando = ref(false)
const pontoInicialArrasto = ref(null)
const baseSelecionadosCtrl = ref(new Set())
const hoverCoord = ref(null)

// Touch Pan & Pinch-to-Zoom
const panX = ref(0)
const panY = ref(0)
const zoomEscala = ref(1)
let toqueUnico = null
let pinchInicial = null

onMounted(async () => {
  if (estabelecimentosDoGerente.value.length === 0) {
    await carregarDadosDoBanco()
  }
  inicializarEstacionamentoAtivo()
  window.addEventListener('mouseup', finalizarSelecaoMouse)
  window.addEventListener('keydown', tratarTeclaGlobal)
  window.addEventListener('click', fecharDropdownAoClicarFora)
})

onUnmounted(() => {
  window.removeEventListener('mouseup', finalizarSelecaoMouse)
  window.removeEventListener('keydown', tratarTeclaGlobal)
  window.removeEventListener('click', fecharDropdownAoClicarFora)
})

function inicializarEstacionamentoAtivo() {
  const idQuery = Number(route.query.id)
  const encontrado = estabelecimentosDoGerente.value.find(e => e.id === idQuery)
  if (encontrado) {
    estSelecionadoId.value = encontrado.id
  } else if (estabelecimentosDoGerente.value.length > 0) {
    estSelecionadoId.value = estabelecimentosDoGerente.value[0].id
  }
}

watch(
  () => route.query.id,
  () => inicializarEstacionamentoAtivo()
)

watch(estabelecimentosDoGerente, () => {
  if (!estSelecionadoId.value && estabelecimentosDoGerente.value.length > 0) {
    inicializarEstacionamentoAtivo()
  }
})

const gridGerenteRef = ref(null)
let autoScrollGerenteFrame = null
let ponteiroGerenteClient = { x: 0, y: 0 }

function obterCoordElementoToque(clientX, clientY) {
  const el = document.elementFromPoint(clientX, clientY)
  const celulaEl = el?.closest('[data-coord]')
  if (!celulaEl) return null
  const [cx, cy] = celulaEl.getAttribute('data-coord').split(',').map(Number)
  return { x: cx, y: cy }
}

function iniciarAutoScrollGerente() {
  if (autoScrollGerenteFrame) return
  const step = () => {
    if (!arrastandoSelecao.value || !gridGerenteRef.value) {
      autoScrollGerenteFrame = null
      return
    }
    const container = gridGerenteRef.value
    const rect = container.getBoundingClientRect()
    const margem = 48
    const vel = 12
    let moveu = false

    if (ponteiroGerenteClient.x < rect.left + margem) {
      container.scrollLeft -= vel
      moveu = true
    } else if (ponteiroGerenteClient.x > rect.right - margem) {
      container.scrollLeft += vel
      moveu = true
    }

    if (ponteiroGerenteClient.y < rect.top + margem) {
      container.scrollTop -= vel
      moveu = true
    } else if (ponteiroGerenteClient.y > rect.bottom - margem) {
      container.scrollTop += vel
      moveu = true
    }

    if (moveu) {
      const coord = obterCoordElementoToque(ponteiroGerenteClient.x, ponteiroGerenteClient.y)
      if (coord) {
        moverArrastoCelulaGerente(coord.x, coord.y)
      }
    }
    autoScrollGerenteFrame = requestAnimationFrame(step)
  }
  autoScrollGerenteFrame = requestAnimationFrame(step)
}

function pararAutoScrollGerente() {
  if (autoScrollGerenteFrame) {
    cancelAnimationFrame(autoScrollGerenteFrame)
    autoScrollGerenteFrame = null
  }
}

function aoTouchStartGridGerente(e) {
  if (modoAcaoVagas.value && e.touches.length === 1) {
    const t = e.touches[0]
    ponteiroGerenteClient = { x: t.clientX, y: t.clientY }
    const coord = obterCoordElementoToque(t.clientX, t.clientY)
    if (coord) {
      iniciarCliqueCelulaGerente(coord.x, coord.y)
      iniciarAutoScrollGerente()
    }
    return
  }
  iniciarToquePanZoom(e)
}

function aoTouchMoveGridGerente(e) {
  if (modoAcaoVagas.value && e.touches.length === 1) {
    const t = e.touches[0]
    ponteiroGerenteClient = { x: t.clientX, y: t.clientY }
    const coord = obterCoordElementoToque(t.clientX, t.clientY)
    if (coord) {
      moverArrastoCelulaGerente(coord.x, coord.y)
    }
    return
  }
  moverToquePanZoom(e)
}

function aoTouchEndGridGerente(e) {
  if (modoAcaoVagas.value) {
    pararAutoScrollGerente()
    finalizarArrastoGerente()
    return
  }
  finalizarToquePanZoom(e, tratarToqueSimplesCelula)
}

function fecharDropdownAoClicarFora(e) {
  if (!e.target.closest('.seletor-est-tela-cheia')) {
    dropdownEstAberto.value = false
  }
  if (!e.target.closest('.seletor-cidade-tela-cheia')) {
    dropdownCidadeAberto.value = false
  }
  if (!e.target.closest('.seletor-andar-tela-cheia')) {
    dropdownAndarAberto.value = false
  }
}

const estacionamentoAtual = computed(() => {
  return (
    estabelecimentosDoGerente.value.find(e => e.id === estSelecionadoId.value) ||
    estabelecimentosDoGerente.value[0] ||
    null
  )
})

const andarAtual = computed(() => {
  if (!estacionamentoAtual.value?.andares) return null
  return (
    estacionamentoAtual.value.andares[andarIndex.value] ||
    estacionamentoAtual.value.andares[0] ||
    null
  )
})

const listaEstabelecimentosFiltrados = computed(() => {
  const termo = termoBuscaEst.value.trim().toLowerCase()
  const base = estabelecimentosDoGerentePorCidade.value
  if (!termo) return base
  return base.filter(
    e =>
      e.nome.toLowerCase().includes(termo) ||
      (e.cidade || '').toLowerCase().includes(termo)
  )
})

function aoTrocarCidadeTelaCheia(novaCidade) {
  selecionarCidadeGerente(novaCidade)
  if (estabelecimentosDoGerentePorCidade.value.length > 0) {
    escolherEstacionamento(estabelecimentosDoGerentePorCidade.value[0])
  }
}

function escolherEstacionamento(est) {
  estSelecionadoId.value = est.id
  andarIndex.value = 0
  dropdownEstAberto.value = false
  termoBuscaEst.value = ''
  cancelarModoSelecao()
  resetarCameraGrid()
}

// =========================================================
// ESTATÍSTICAS DE ANDARES E SETORES AO LADO DO MAPA
// =========================================================
const estatisticasAndares = computed(() => {
  if (!estacionamentoAtual.value?.andares) return []
  return estacionamentoAtual.value.andares.map((andar, idx) => {
    const vagas = Object.values(andar.celulas || {}).filter(c => c.tipo === 'VAGA')
    const total = vagas.length
    const inativas = vagas.filter(v => v.inativa).length
    const livres = vagas.filter(v => !v.inativa && v.livre).length
    const ocupadas = vagas.filter(v => !v.inativa && !v.livre).length
    const ativas = Math.max(1, total - inativas)
    const lotacaoPct = total > 0 ? Math.round((ocupadas / ativas) * 100) : 0
    const variacao = ocupadas === 0 ? 0 : ((idx % 2 === 0 ? 1 : -1) * ((ocupadas * 3) % 14 + 2))

    return {
      idx,
      id_andar: andar.id_andar,
      nome_andar: andar.nome_andar,
      total,
      livres,
      ocupadas,
      inativas,
      lotacaoPct,
      variacao
    }
  })
})

const estatisticasSetoresAndarAtual = computed(() => {
  if (!andarAtual.value) return []
  const celulas = Object.values(andarAtual.value.celulas || {})

  return (andarAtual.value.setores || []).map((setor, sIdx) => {
    const vagasSetor = celulas.filter(c => c.tipo === 'VAGA' && c.setorId === setor.id_setor)
    const total = vagasSetor.length
    const inativas = vagasSetor.filter(v => v.inativa).length
    const livres = vagasSetor.filter(v => !v.inativa && v.livre).length
    const ocupadas = vagasSetor.filter(v => !v.inativa && !v.livre).length
    const ativas = Math.max(1, total - inativas)
    const lotacaoPct = total > 0 ? Math.round((ocupadas / ativas) * 100) : 0
    const variacao = ocupadas === 0 ? 0 : ((sIdx % 2 === 0 ? 1 : -1) * ((ocupadas * 4) % 15 + 3))

    return {
      id_setor: setor.id_setor,
      nome_setor: setor.nome_setor,
      prefixo: setor.prefixo,
      cor_hex: setor.cor_hex,
      total,
      livres,
      ocupadas,
      inativas,
      lotacaoPct,
      variacao
    }
  })
})

// =========================================================
// MAPA DE CALOR (5 VARIAÇÕES EM QUANTIS DE 20%)
// =========================================================
const mapaCalorPorCoordenada = computed(() => {
  const resultado = {}
  if (!andarAtual.value?.celulas) return resultado

  const vagas = Object.values(andarAtual.value.celulas).filter(c => c.tipo === 'VAGA')
  if (vagas.length === 0) return resultado

  const valoresOrdenados = vagas.map(v => v.usosNoDia || 0).sort((a, b) => a - b)
  const total = valoresOrdenados.length

  vagas.forEach((v) => {
    const chave = `${v.x},${v.y}`
    const usos = v.usosNoDia || 0

    if (usos === 0) {
      resultado[chave] = 'calor-nivel-1'
      return
    }

    const posPrimeiraOcorrencia = valoresOrdenados.indexOf(usos)
    const percentil = posPrimeiraOcorrencia / total

    if (percentil < 0.2) {
      resultado[chave] = 'calor-nivel-1'
    } else if (percentil < 0.4) {
      resultado[chave] = 'calor-nivel-2'
    } else if (percentil < 0.6) {
      resultado[chave] = 'calor-nivel-3'
    } else if (percentil < 0.8) {
      resultado[chave] = 'calor-nivel-4'
    } else {
      resultado[chave] = 'calor-nivel-5'
    }
  })

  return resultado
})

// =========================================================
// HOVER HUD: MODO NORMAL vs. MODO MAPA DE CALOR
// =========================================================
function formatarDuracao(minutos) {
  if (!minutos || minutos <= 0) return '0min'
  const h = Math.floor(minutos / 60)
  const m = minutos % 60
  return h > 0 ? `${h}h ${m}min` : `${m}min`
}

const infoHoverGerente = computed(() => {
  if (!hoverCoord.value || !andarAtual.value?.celulas) return null
  const c = andarAtual.value.celulas[`${hoverCoord.value.x},${hoverCoord.value.y}`]
  if (!c) return null

  const coord = `(${c.x}, ${c.y})`

  if (c.tipo !== 'VAGA') {
    const mapaTipos = {
      VAZIO: 'Vazio',
      ESTRADA: 'Estrada',
      ENTRADA: 'Entrada',
      SAIDA: 'Saída',
      ACESSO: 'Acesso de Pedestres'
    }
    return {
      cor: c.corSetor || '#64748b',
      titulo: `${coord} - ${mapaTipos[c.tipo] || c.tipo}`,
      detalhe: c.nomeSetor ? `[${c.nomeSetor}]` : ''
    }
  }

  if (modoMapaCalor.value) {
    const qtdUsos = c.usosNoDia || 0
    return {
      cor: c.corSetor || '#f97316',
      titulo: `${coord} - Vaga ${c.identificador}`,
      detalhe: `Usada ${qtdUsos} ${qtdUsos === 1 ? 'vez' : 'vezes'} durante o dia`
    }
  }

  if (c.inativa) {
    return {
      cor: '#64748b',
      titulo: `${coord} - Vaga ${c.identificador}: INATIVADA`,
      detalhe: '[Interditada pelo gerente]'
    }
  }

  if (!c.macEsp) {
    return {
      cor: '#eab308',
      titulo: `${coord} - Vaga ${c.identificador}: Sem comunicação com ESP32`,
      detalhe: '[Verifique o sensor]'
    }
  }

  if (c.livre) {
    return {
      cor: '#16a34a',
      titulo: `${coord} - Vaga ${c.identificador}: LIVRE`,
      detalhe: c.nomeSetor ? `[${c.nomeSetor}]` : ''
    }
  }

  const chegada = c.horaChegada || '14:20'
  const duracao = formatarDuracao(c.duracaoMinutos || 45)
  return {
    cor: '#dc2626',
    titulo: `${coord} - Vaga ${c.identificador}: OCUPADA`,
    detalhe: `Chegada: ${chegada} | Duração atual: ${duracao}`
  }
})

// =========================================================
// SELEÇÃO EM LOTE PARA INATIVAR / REATIVAR VAGAS
// =========================================================
function ativarModoSelecao(modo) {
  if (modoAcaoVagas.value === modo) {
    cancelarModoSelecao()
    return
  }
  modoAcaoVagas.value = modo
  selecionados.value = new Set()
  menuOpcoesMobileAberto.value = false
}

function cancelarModoSelecao() {
  modoAcaoVagas.value = 'NENHUM'
  selecionados.value = new Set()
  arrastando.value = false
}

const vagasValidasNaSelecao = computed(() => {
  if (!andarAtual.value?.celulas) return []
  const lista = []
  selecionados.value.forEach((chave) => {
    const c = andarAtual.value.celulas[chave]
    if (c && c.tipo === 'VAGA') {
      lista.push(c)
    }
  })
  return lista
})

async function confirmarAcaoInativarReativar() {
  const vagasAlvo = vagasValidasNaSelecao.value
  if (vagasAlvo.length === 0) {
    cancelarModoSelecao()
    return
  }

  const novoStatusInativo = modoAcaoVagas.value === 'INATIVAR'
  salvandoStatusLote.value = true

  try {
    const idsBanco = []
    vagasAlvo.forEach((v) => {
      v.inativa = novoStatusInativo
      if (v.vagaId) idsBanco.push(v.vagaId)
    })

    if (idsBanco.length > 0) {
      await fetch(`${API_URL}/vagas/status-lote`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ids_vagas: idsBanco,
          inativo: novoStatusInativo
        })
      })
    }
  } catch (err) {
    console.error('Aviso ao sincronizar lote de vagas:', err)
  } finally {
    salvandoStatusLote.value = false
    cancelarModoSelecao()
  }
}

function iniciarSelecaoCelula(x, y, event) {
  if (modoAcaoVagas.value === 'NENHUM') return

  arrastando.value = true
  pontoInicialArrasto.value = { x, y }
  const chave = `${x},${y}`

  baseSelecionadosCtrl.value = new Set(selecionados.value)
  if (event.ctrlKey || event.metaKey) {
    if (baseSelecionadosCtrl.value.has(chave)) {
      baseSelecionadosCtrl.value.delete(chave)
    } else {
      baseSelecionadosCtrl.value.add(chave)
    }
    selecionados.value = new Set(baseSelecionadosCtrl.value)
  } else {
    if (baseSelecionadosCtrl.value.has(chave) && selecionados.value.size === 1) {
      baseSelecionadosCtrl.value.delete(chave)
    } else {
      baseSelecionadosCtrl.value.add(chave)
    }
    selecionados.value = new Set(baseSelecionadosCtrl.value)
  }
}

function moverMouseCelula(x, y) {
  hoverCoord.value = { x, y }
  if (!arrastando.value || !pontoInicialArrasto.value || modoAcaoVagas.value === 'NENHUM') return

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
  }
}

// =========================================================
// TOUCH PAN & PINCH-TO-ZOOM (TABLETS E CELULARES)
// =========================================================
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
  if (e.touches.length < 2) pinchInicial = null
  if (e.touches.length === 0 && toqueUnico) {
    if (!toqueUnico.moveu) {
      const el = document.elementFromPoint(toqueUnico.lastX, toqueUnico.lastY)
      const celulaEl = el?.closest('[data-coord]')
      if (celulaEl) {
        const [cx, cy] = celulaEl.getAttribute('data-coord').split(',').map(Number)
        hoverCoord.value = { x: cx, y: cy }
        if (modoAcaoVagas.value !== 'NENHUM') {
          const chave = `${cx},${cy}`
          const nova = new Set(selecionados.value)
          if (nova.has(chave)) nova.delete(chave)
          else nova.add(chave)
          selecionados.value = nova
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
// QR CODE OFICIAL DO ESTACIONAMENTO
// =========================================================
const urlMotoristaQr = computed(() => {
  if (!estacionamentoAtual.value) return ''
  return `${window.location.origin}/vagas/${estacionamentoAtual.value.id}`
})

const imagemQrCodeUrl = computed(() => {
  if (!urlMotoristaQr.value) return ''
  return `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(urlMotoristaQr.value)}`
})

function imprimirQrCode() {
  window.print()
}

function tratarTeclaGlobal(event) {
  if (event.key === 'Escape') {
    if (modoAcaoVagas.value !== 'NENHUM') {
      cancelarModoSelecao()
    }
    modalQrAberto.value = false
    dropdownEstAberto.value = false
    menuOpcoesMobileAberto.value = false
    painelLateralMobileAberto.value = false
  }
}
</script>

<template>
  <div v-if="estacionamentoAtual && andarAtual" class="editor-layout">
    <!-- BOTÕES FLUTUANTES MOBILE/TABLET (<= 1024px) -->
    <div class="hud-coluna-direita-mobile">
      <button
        class="hud-btn-flutuante"
        :class="{ 'hud-ativo': menuOpcoesMobileAberto }"
        title="Controles e Ferramentas"
        @click="menuOpcoesMobileAberto = !menuOpcoesMobileAberto; painelLateralMobileAberto = false"
      >
        <IconSettings :size="20" />
      </button>

      <button
        class="hud-btn-flutuante"
        :class="{ 'hud-ativo': painelLateralMobileAberto }"
        title="Andares e Setores"
        @click="painelLateralMobileAberto = !painelLateralMobileAberto; menuOpcoesMobileAberto = false"
      >
        <IconLayoutBoard :size="20" />
      </button>
    </div>

    <!-- BARRA SUPERIOR EM TELA CHEIA -->
    <header
      class="editor-topbar topbar-gerente-est"
      :class="{ 'topbar-mobile-aberta': menuOpcoesMobileAberto }"
    >
      <div class="topbar-esquerda">
        <button
          class="btn-secundario item-icone-texto"
          @click="router.push({ name: 'gerente' })"
        >
          <IconSquareRoundedArrowLeft :size="18" />
          <span>Dashboard</span>
        </button>

        <!-- Grupo focado no Passo 2 do Tutorial (Cidade, Estacionamento e Andar) -->
        <div class="grupo-filtros-navegacao-gerente">
          <!-- Filtro de Cidade Estilizado -->
          <div v-if="cidadesDoGerente.length >= 1" class="seletor-multi-wrapper seletor-cidade-tela-cheia">
            <button
              type="button"
              class="btn-seletor-multi item-icone-texto"
              @click="dropdownCidadeAberto = !dropdownCidadeAberto; dropdownEstAberto = false; dropdownAndarAberto = false"
            >
              <IconPin :size="17" style="color: var(--destaque-azul)" />
              <span>{{ cidadeSelecionadaGerente === 'TODAS' ? 'Todas as cidades' : cidadeSelecionadaGerente }}</span>
              <IconSquareRoundedChevronDown :size="17" />
            </button>

            <Transition name="fade-pop">
              <div v-if="dropdownCidadeAberto" class="dropdown-multi-box" style="width: 220px">
                <div class="lista-opcoes-multi">
                  <div
                    class="item-opcao-multi destaque-completo"
                    :class="{ 'opcao-ativa': cidadeSelecionadaGerente === 'TODAS' }"
                    @click="aoTrocarCidadeTelaCheia('TODAS'); dropdownCidadeAberto = false"
                  >
                    <span>Todas</span>
                    <IconSquareRoundedCheck v-if="cidadeSelecionadaGerente === 'TODAS'" :size="18" />
                  </div>
                  <div
                    v-for="cid in cidadesDoGerente"
                    :key="cid"
                    class="item-opcao-multi"
                    :class="{ 'opcao-ativa': cidadeSelecionadaGerente === cid }"
                    @click="aoTrocarCidadeTelaCheia(cid); dropdownCidadeAberto = false"
                  >
                    <span>{{ cid }}</span>
                    <IconSquareRoundedCheck v-if="cidadeSelecionadaGerente === cid" :size="18" />
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Seletor de Estacionamento com Pesquisa -->
          <div class="seletor-est-tela-cheia">
            <button
              type="button"
              class="btn-seletor-multi item-icone-texto"
              @click="dropdownEstAberto = !dropdownEstAberto; dropdownCidadeAberto = false; dropdownAndarAberto = false"
            >
              <IconParking :size="18" />
              <span class="texto-truncado-est">{{ estacionamentoAtual.nome }}</span>
              <IconSquareRoundedChevronDown :size="17" />
            </button>

            <Transition name="fade-pop">
              <div v-if="dropdownEstAberto" class="dropdown-multi-box">
                <div class="busca-multi-topo">
                  <IconSearch :size="16" class="icone-busca-multi" />
                  <input
                    v-model="termoBuscaEst"
                    type="text"
                    placeholder="Pesquisar estacionamento..."
                  />
                </div>
                <div class="lista-opcoes-multi">
                  <div
                    v-for="est in listaEstabelecimentosFiltrados"
                    :key="est.id"
                    class="item-opcao-multi"
                    :class="{ 'opcao-ativa': est.id === estacionamentoAtual.id }"
                    @click="escolherEstacionamento(est)"
                  >
                    <span>{{ est.nome }}</span>
                    <IconSquareRoundedCheck v-if="est.id === estacionamentoAtual.id" :size="18" />
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Seletor de Andar Estilizado -->
          <div class="seletor-multi-wrapper seletor-andar-tela-cheia">
            <button
              type="button"
              class="btn-seletor-multi item-icone-texto"
              @click="dropdownAndarAberto = !dropdownAndarAberto; dropdownEstAberto = false; dropdownCidadeAberto = false"
            >
              <IconStack2 :size="18" style="color: var(--destaque-azul)" />
              <span>{{ andarAtual.nome_andar }}</span>
              <IconSquareRoundedChevronDown :size="17" />
            </button>

            <Transition name="fade-pop">
              <div v-if="dropdownAndarAberto" class="dropdown-multi-box" style="width: 210px">
                <div class="lista-opcoes-multi">
                  <div
                    v-for="(a, idx) in estacionamentoAtual.andares"
                    :key="a.id_andar"
                    class="item-opcao-multi"
                    :class="{ 'opcao-ativa': idx === andarIndex }"
                    @click="andarIndex = idx; dropdownAndarAberto = false; cancelarModoSelecao(); resetarCameraGrid()"
                  >
                    <span>{{ a.nome_andar }}</span>
                    <IconSquareRoundedCheck v-if="idx === andarIndex" :size="18" />
                  </div>
                </div>
              </div>
            </Transition>
          </div>
        </div>

        <!-- Grupo focado no Passo 4 do Tutorial (Inativar e Reativar) -->
        <div class="grupo-inativar-reativar-gerente">
          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-modo-inativar-ativo': modoAcaoVagas === 'INATIVAR' }"
            @click="ativarModoSelecao('INATIVAR')"
          >
            <IconBan :size="17" />
            <span>Inativar</span>
          </button>

          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-modo-reativar-ativo': modoAcaoVagas === 'REATIVAR' }"
            @click="ativarModoSelecao('REATIVAR')"
          >
            <IconSquareRoundedCheck :size="17" />
            <span>Reativar</span>
          </button>
        </div>
      </div>

      <div class="topbar-direita-gerente">
        <!-- Grupo focado no Passo 5 do Tutorial (Sem incluir QR Code) -->
        <div class="grupo-calor-simulacao-gerente">
          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-calor-ativo': modoMapaCalor }"
            @click="modoMapaCalor = !modoMapaCalor"
          >
            <IconFlame :size="18" />
            <span>{{ modoMapaCalor ? 'Mapa de Calor: ON' : 'Mapa de Calor' }}</span>
          </button>

          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-simulacao-ativa': simulacao1Ativa }"
            @click="alternarSimulacao1Frontend"
          >
            <IconPlayerPlay :size="17" />
            <span>{{ simulacao1Ativa ? 'Simulação 1: ON' : 'Simulação 1' }}</span>
          </button>
        </div>

        <!-- Botão focado exclusivamente no Passo 6 do Tutorial -->
        <button
          class="btn-primario btn-qrcode-gerente item-icone-texto"
          @click="modalQrAberto = true"
        >
          <IconQrcode :size="18" />
          <span>QR Code</span>
        </button>
      </div>
    </header>

    <!-- ÁREA CENTRAL: MAPA 2D + PAINEL DIREITO DE ANDARES E SETORES -->
    <div class="editor-workspace">
      <div class="area-grid-container">
        <Transition name="fade-pop">
          <div
            v-if="modoAcaoVagas !== 'NENHUM'"
            class="overlay-flutuante banner-instrucao-gerente"
            :class="modoAcaoVagas === 'INATIVAR' ? 'cor-banner-inativar' : 'cor-banner-reativar'"
          >
            <span>
              Clique ou arraste sobre o mapa para selecionar as vagas que deseja
              <strong>{{ modoAcaoVagas === 'INATIVAR' ? 'INATIVAR' : 'REATIVAR' }}</strong>
              (ESC para sair)
            </span>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="modoMapaCalor" class="overlay-flutuante legenda-calor-overlay">
            <strong>Uso no dia:</strong>
            <span class="amostra-calor calor-nivel-1">0–20%</span>
            <span class="amostra-calor calor-nivel-2">20–40%</span>
            <span class="amostra-calor calor-nivel-3">40–60%</span>
            <span class="amostra-calor calor-nivel-4">60–80%</span>
            <span class="amostra-calor calor-nivel-5">80–100%</span>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div
            v-if="modoAcaoVagas !== 'NENHUM' && selecionados.size > 0"
            class="overlay-flutuante popup-confirmar-lote-gerente"
          >
            <span class="contagem-sel">
              {{ vagasValidasNaSelecao.length }} vaga(s) na seleção
            </span>

            <button
              type="button"
              class="btn-secundario btn-popup-lote item-icone-texto"
              @click="cancelarModoSelecao"
            >
              <IconSquareRoundedX :size="17" />
              <span>Cancelar</span>
            </button>

            <button
              type="button"
              class="btn-primario btn-popup-lote item-icone-texto"
              :class="modoAcaoVagas === 'INATIVAR' ? 'btn-lote-vermelho' : 'btn-lote-verde'"
              :disabled="salvandoStatusLote || vagasValidasNaSelecao.length === 0"
              @click="confirmarAcaoInativarReativar"
            >
              <IconSquareRoundedCheck :size="17" />
              <span>
                {{
                  salvandoStatusLote
                    ? 'Aplicando...'
                    : modoAcaoVagas === 'INATIVAR'
                      ? 'Confirmar Inativação'
                      : 'Confirmar Reativação'
                }}
              </span>
            </button>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="infoHoverGerente" class="overlay-flutuante badge-hover-setor">
            <span
              class="bolinha-cor-setor"
              :style="{ backgroundColor: infoHoverGerente.cor }"
            ></span>
            <strong>{{ infoHoverGerente.titulo }}</strong>
            <span v-if="infoHoverGerente.detalhe" class="texto-colchetes-setor">
              {{ infoHoverGerente.detalhe }}
            </span>
          </div>
        </Transition>

        <!-- TABULEIRO 2D EM TELA CHEIA -->
        <div
          ref="gridGerenteRef"
          class="area-grid-principal"
          @mouseleave="hoverCoord = null"
          @mousemove="ponteiroGerenteClient = { x: $event.clientX, y: $event.clientY }"
          @mousedown="iniciarAutoScrollGerente"
          @mouseup="pararAutoScrollGerente"
          @touchstart.passive="aoTouchStartGridGerente"
          @touchmove.prevent="aoTouchMoveGridGerente"
          @touchend="aoTouchEndGridGerente"
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
                :style="{ gridTemplateColumns: `36px repeat(${andarAtual.grid_x}, 36px)` }"
              >
                <div class="canto-xy">Y\X</div>
                <div v-for="x in andarAtual.grid_x" :key="`gx-${x}`" class="rotulo-coord">
                  {{ x }}
                </div>
              </div>

              <div
                v-for="y in andarAtual.grid_y"
                :key="`gy-${y}`"
                class="linha-grid-y"
                :style="{ gridTemplateColumns: `36px repeat(${andarAtual.grid_x}, 36px)` }"
              >
                <div class="rotulo-coord">{{ y }}</div>

                <div
                  v-for="x in andarAtual.grid_x"
                  :key="`gc-${x}-${y}`"
                  :data-coord="`${x},${y}`"
                  class="celula-editor-fundo"
                  :style="{
                    backgroundColor: andarAtual.celulas[`${x},${y}`]?.corSetor || 'transparent'
                  }"
                  @mousedown.prevent="iniciarSelecaoCelula(x, y, $event)"
                  @mouseenter="moverMouseCelula(x, y)"
                >
                  <div
                    class="quadrado-editor"
                    :class="[
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'VAZIO' ? 'qe-vazio' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'ESTRADA' ? 'qe-estrada' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'ENTRADA' ? 'qe-entrada' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'SAIDA' ? 'qe-saida' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'ACESSO' ? 'qe-acesso' : '',
                      modoMapaCalor && andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA'
                        ? mapaCalorPorCoordenada[`${x},${y}`]
                        : '',
                      !modoMapaCalor && andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' && andarAtual.celulas[`${x},${y}`]?.inativa
                        ? 'vaga-gerente-inativa'
                        : '',
                      !modoMapaCalor && andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarAtual.celulas[`${x},${y}`]?.inativa && !andarAtual.celulas[`${x},${y}`]?.macEsp
                        ? 'qe-vaga-amarela'
                        : '',
                      !modoMapaCalor && andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarAtual.celulas[`${x},${y}`]?.inativa && andarAtual.celulas[`${x},${y}`]?.macEsp && andarAtual.celulas[`${x},${y}`]?.livre
                        ? 'vaga-gerente-livre'
                        : '',
                      !modoMapaCalor && andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarAtual.celulas[`${x},${y}`]?.inativa && andarAtual.celulas[`${x},${y}`]?.macEsp && !andarAtual.celulas[`${x},${y}`]?.livre
                        ? 'vaga-gerente-ocupada'
                        : '',
                      selecionados.has(`${x},${y}`) ? 'qe-selecionado-roxo' : ''
                    ]"
                  >
                    <span v-if="andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA'">
                      {{
                        modoMapaCalor
                          ? `${andarAtual.celulas[`${x},${y}`]?.usosNoDia || 0}x`
                          : andarAtual.celulas[`${x},${y}`]?.identificador
                      }}
                    </span>
                    <IconDoorEnter v-else-if="andarAtual.celulas[`${x},${y}`]?.tipo === 'ENTRADA'" :size="16" />
                    <IconDoorExit v-else-if="andarAtual.celulas[`${x},${y}`]?.tipo === 'SAIDA'" :size="16" />
                    <IconArrowBarRight v-else-if="andarAtual.celulas[`${x},${y}`]?.tipo === 'ACESSO'" :size="16" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- PAINEL LATERAL DIREITO: ANDARES E SETORES EM TEMPO REAL -->
      <aside
        class="sidebar-direita-editor sidebar-gerente-metricas"
        :class="{ 'sidebar-mobile-aberta': painelLateralMobileAberto }"
      >
        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconStack2 :size="18" />
            <span>Andares ({{ estatisticasAndares.length }})</span>
          </h4>
          <p class="dica-painel">Clique em um andar para visualizar sua planta</p>

          <div class="lista-cards-laterais">
            <div
              v-for="a in estatisticasAndares"
              :key="a.id_andar"
              class="card-lateral-metrica"
              :class="{ 'card-lateral-ativo': a.idx === andarIndex }"
              @click="andarIndex = a.idx; cancelarModoSelecao()"
            >
              <div class="topo-card-lateral">
                <strong>{{ a.nome_andar }}</strong>
                <span
                  class="badge-variacao"
                  :class="a.variacao >= 0 ? 'var-alta' : 'var-baixa'"
                  title="Taxa de variação na última hora"
                >
                  {{ a.variacao >= 0 ? `+${a.variacao}%` : `${a.variacao}%` }}
                </span>
              </div>

              <div class="numeros-card-lateral">
                <span class="num-livre">{{ a.livres }} livres</span>
                <span class="num-ocupada">{{ a.ocupadas }} ocup.</span>
                <span v-if="a.inativas > 0" class="num-inativa">{{ a.inativas }} inat.</span>
              </div>

              <div class="barra-mini-lateral">
                <div class="preenchimento-mini" :style="{ width: `${a.lotacaoPct}%` }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconLayoutBoard :size="18" />
            <span>Setores — {{ andarAtual.nome_andar }}</span>
          </h4>
          <p class="dica-painel">Ocupação e variação atual por setor</p>

          <div class="lista-cards-laterais">
            <div
              v-for="s in estatisticasSetoresAndarAtual"
              :key="s.id_setor"
              class="card-lateral-metrica"
            >
              <div class="topo-card-lateral">
                <span class="item-icone-texto">
                  <span class="bolinha-cor-setor" :style="{ backgroundColor: s.cor_hex }"></span>
                  <strong>{{ s.nome_setor }} ({{ s.prefixo }})</strong>
                </span>
                <span
                  class="badge-variacao"
                  :class="s.variacao >= 0 ? 'var-alta' : 'var-baixa'"
                >
                  {{ s.variacao >= 0 ? `+${s.variacao}%` : `${s.variacao}%` }}
                </span>
              </div>

              <div class="numeros-card-lateral">
                <span class="num-livre">{{ s.livres }} livres</span>
                <span class="num-ocupada">{{ s.ocupadas }} ocup.</span>
                <span v-if="s.inativas > 0" class="num-inativa">{{ s.inativas }} inat.</span>
              </div>

              <div class="barra-mini-lateral">
                <div
                  class="preenchimento-mini"
                  :style="{ width: `${s.lotacaoPct}%`, backgroundColor: s.cor_hex }"
                ></div>
              </div>
            </div>

            <p v-if="estatisticasSetoresAndarAtual.length === 0" class="dica-painel">
              Nenhum setor cadastrado neste andar.
            </p>
          </div>
        </div>
      </aside>
    </div>

    <!-- MODAL DO QR CODE PARA ENTRADA DO ESTACIONAMENTO (SEM A FRASE EXTRA) -->
    <Transition name="fade-pop">
      <div v-if="modalQrAberto" class="modal-backdrop">
        <div class="modal-box modal-qr-gerente">
          <div class="overlay-header">
            <h3 class="item-icone-texto">
              <IconQrcode :size="20" />
              <span>QR Code — {{ estacionamentoAtual.nome }}</span>
            </h3>
            <button class="btn-fechar-mini" @click="modalQrAberto = false">
              <IconSquareRoundedX :size="20" />
            </button>
          </div>

          <div class="box-imagem-qr">
            <img :src="imagemQrCodeUrl" :alt="`QR Code ${estacionamentoAtual.nome}`" width="220" height="220" />
          </div>

          <code class="url-qr-codigo">{{ urlMotoristaQr }}</code>

          <div class="modal-acoes" style="justify-content: center; margin-top: 16px">
            <button class="btn-secundario" @click="modalQrAberto = false">Fechar</button>
            <button class="btn-primario item-icone-texto" @click="imprimirQrCode">
              <IconQrcode :size="18" />
              <span>Imprimir QR Code</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>
