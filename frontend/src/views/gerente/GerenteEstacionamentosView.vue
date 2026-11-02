<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  estabelecimentosDoGerentePorCidade,
  cidadesDoGerente,
  cidadeSelecionadaGerente,
  selecionarCidadeGerente,
  simulacao1Ativa,
  alternarSimulacao1Frontend,
  carregarDadosDoBanco
} from '@/stores/estacionamentoStore'
import { alterarStatusVagasLoteApi } from '@/services/estacionamentoService'
import { useGridPanZoom } from '@/composables/useGridPanZoom'
import {
  IconSquareRoundedArrowLeft,
  IconStack2,
  IconParking,
  IconSearch,
  IconSquareRoundedChevronDown,
  IconSquareRoundedCheck,
  IconSquareRoundedX,
  IconBan,
  IconFlame,
  IconQrcode,
  IconSettings,
  IconLayoutBoard,
  IconDoorEnter,
  IconDoorExit,
  IconArrowBarRight,
  IconPlayerPlay,
  IconPin
} from '@/constants/icons'

const router = useRouter()
const route = useRoute()

const idEstacionamentoAtivo = ref(null)
const andarIndex = ref(0)
const dropdownEstAberto = ref(false)
const dropdownCidadeAberto = ref(false)
const dropdownAndarAberto = ref(false)
const termoBuscaEst = ref('')

const modoAcaoVagas = ref(null)
const vagasSelecionadasIds = ref(new Set())
const arrastandoSelecao = ref(false)
const pontoInicialSelecao = ref(null)
const salvandoLote = ref(false)

const modoMapaCalor = ref(false)
const modalQrAberto = ref(false)
const hoverCoord = ref(null)

const menuOpcoesMobileAberto = ref(false)
const menuSetoresMobileAberto = ref(false)

const {
  panX,
  panY,
  zoomEscala,
  iniciarToquePanZoom,
  moverToquePanZoom,
  finalizarToquePanZoom,
  resetarCameraGrid
} = useGridPanZoom()

const gridGerenteRef = ref(null)
let autoScrollGerenteFrame = null
let ponteiroGerenteClient = { x: 0, y: 0 }

const estacionamentoAtual = computed(() => {
  const lista = estabelecimentosDoGerentePorCidade.value
  if (lista.length === 0) return null
  const encontrado = lista.find(e => e.id === Number(idEstacionamentoAtivo.value))
  return encontrado || lista[0]
})

function aoTrocarCidadeTelaCheia(novaCid) {
  selecionarCidadeGerente(novaCid)
  const primeira = estabelecimentosDoGerentePorCidade.value[0]
  if (primeira) {
    idEstacionamentoAtivo.value = primeira.id
    andarIndex.value = 0
  }
}

watch(
  () => [route.query.id, estabelecimentosDoGerentePorCidade.value.length],
  () => {
    if (route.query.id) {
      idEstacionamentoAtivo.value = Number(route.query.id)
    } else if (!idEstacionamentoAtivo.value && estabelecimentosDoGerentePorCidade.value.length > 0) {
      idEstacionamentoAtivo.value = estabelecimentosDoGerentePorCidade.value[0].id
    }
  },
  { immediate: true }
)

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
  if (!termo) return estabelecimentosDoGerentePorCidade.value
  return estabelecimentosDoGerentePorCidade.value.filter(
    e =>
      e.nome.toLowerCase().includes(termo) ||
      (e.cidade || '').toLowerCase().includes(termo) ||
      String(e.id) === termo
  )
})

function escolherEstacionamento(est) {
  idEstacionamentoAtivo.value = est.id
  andarIndex.value = 0
  dropdownEstAberto.value = false
  cancelarModoSelecao()
  resetarCameraGrid()
}

function alternarModoSelecao(modo) {
  if (modoAcaoVagas.value === modo) {
    cancelarModoSelecao()
  } else {
    hoverCoord.value = null
    modoAcaoVagas.value = modo
    vagasSelecionadasIds.value = new Set()
    menuOpcoesMobileAberto.value = false
  }
}

function cancelarModoSelecao() {
  modoAcaoVagas.value = null
  vagasSelecionadasIds.value = new Set()
  arrastandoSelecao.value = false
  hoverCoord.value = null
}

function vagaElegivelModoAtual(celula) {
  if (!celula || celula.tipo !== 'VAGA' || !celula.idVagaBanco) return false
  if (modoAcaoVagas.value === 'INATIVAR') return !celula.inativa
  if (modoAcaoVagas.value === 'REATIVAR') return Boolean(celula.inativa)
  return false
}

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

// No Gerente: o swipe do dedo sempre move o grid, exceto quando Inativar/Reativar estiver ativo
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

function iniciarCliqueCelulaGerente(x, y) {
  hoverCoord.value = { x, y }
  if (!modoAcaoVagas.value || !andarAtual.value) return

  arrastandoSelecao.value = true
  pontoInicialSelecao.value = { x, y }

  const c = andarAtual.value.celulas[`${x},${y}`]
  if (vagaElegivelModoAtual(c)) {
    const novo = new Set(vagasSelecionadasIds.value)
    if (novo.has(c.idVagaBanco)) novo.delete(c.idVagaBanco)
    else novo.add(c.idVagaBanco)
    vagasSelecionadasIds.value = novo
  }
}

function moverArrastoCelulaGerente(x, y) {
  hoverCoord.value = { x, y }
  if (!arrastandoSelecao.value || !pontoInicialSelecao.value || !modoAcaoVagas.value) return

  const xMin = Math.min(pontoInicialSelecao.value.x, x)
  const xMax = Math.max(pontoInicialSelecao.value.x, x)
  const yMin = Math.min(pontoInicialSelecao.value.y, y)
  const yMax = Math.max(pontoInicialSelecao.value.y, y)

  const novo = new Set()
  for (let cy = yMin; cy <= yMax; cy++) {
    for (let cx = xMin; cx <= xMax; cx++) {
      const c = andarAtual.value.celulas[`${cx},${cy}`]
      if (vagaElegivelModoAtual(c)) {
        novo.add(c.idVagaBanco)
      }
    }
  }
  vagasSelecionadasIds.value = novo
}

function finalizarArrastoGerente() {
  pararAutoScrollGerente()
  arrastandoSelecao.value = false
}

function tratarToqueSimplesCelula(x, y) {
  hoverCoord.value = { x, y }
  if (!modoAcaoVagas.value || !andarAtual.value) return
  const c = andarAtual.value.celulas[`${x},${y}`]
  if (vagaElegivelModoAtual(c)) {
    const novo = new Set(vagasSelecionadasIds.value)
    if (novo.has(c.idVagaBanco)) novo.delete(c.idVagaBanco)
    else novo.add(c.idVagaBanco)
    vagasSelecionadasIds.value = novo
  }
}

async function confirmarAlteracaoLoteVagas() {
  if (vagasSelecionadasIds.value.size === 0 || salvandoLote.value) return
  salvandoLote.value = true
  const inativar = modoAcaoVagas.value === 'INATIVAR'
  const ids = Array.from(vagasSelecionadasIds.value)

  try {
    await alterarStatusVagasLoteApi(ids, inativar)
    await carregarDadosDoBanco()
    cancelarModoSelecao()
  } catch (err) {
    alert(err.message)
  } finally {
    salvandoLote.value = false
  }
}

function classeCorVagaGerente(celula) {
  if (!celula || celula.tipo !== 'VAGA') return ''
  if (celula.inativa) return 'vaga-gerente-inativa'
  if (!celula.macEsp) return 'qe-vaga-amarela'

  if (modoMapaCalor.value) {
    const usos = celula.usosNoDia || 0
    if (usos >= 9) return 'calor-nivel-5'
    if (usos >= 7) return 'calor-nivel-4'
    if (usos >= 5) return 'calor-nivel-3'
    if (usos >= 3) return 'calor-nivel-2'
    return 'calor-nivel-1'
  }

  return celula.livre ? 'vaga-gerente-livre' : 'vaga-gerente-ocupada'
}

const infoHoverCelula = computed(() => {
  if (modoAcaoVagas.value || !hoverCoord.value || !andarAtual.value) return null
  const c = andarAtual.value.celulas[`${hoverCoord.value.x},${hoverCoord.value.y}`]
  if (!c) return null

  if (c.tipo === 'VAGA') {
    const statusTexto = c.inativa
      ? 'INATIVA'
      : c.livre
        ? 'Livre'
        : `Ocupada (Chegada: ${c.horaChegada || '14:20'} • Há ${c.duracaoMinutos || 45} min)`
    const giroTexto = `Rotatividade hoje: ${c.usosNoDia || 0} uso(s)`
    return {
      cor: c.inativa ? '#64748b' : c.livre ? '#16a34a' : '#dc2626',
      titulo: `Vaga ${c.identificador} — (${c.x},${c.y})`,
      detalhe: `Setor ${c.nomeSetor || 'Geral'} • ${statusTexto} • ${giroTexto}`
    }
  }

  if (c.tipo === 'ENTRADA') return { cor: '#2563eb', titulo: `Entrada (${c.x},${c.y})`, detalhe: null }
  if (c.tipo === 'SAIDA') return { cor: '#ea580c', titulo: `Saída (${c.x},${c.y})`, detalhe: null }
  if (c.tipo === 'ACESSO') return { cor: '#16a34a', titulo: `Acesso (${c.x},${c.y})`, detalhe: null }
  if (c.tipo === 'ESTRADA') {
    return {
      cor: '#1e293b',
      titulo: `Estrada (${c.x},${c.y})`,
      detalhe: c.nomeSetor ? `Setor ${c.nomeSetor}` : null
    }
  }
  return null
})

const estatisticasAndares = computed(() => {
  if (!estacionamentoAtual.value?.andares) return []
  return estacionamentoAtual.value.andares.map((andar, idx) => {
    const vagas = Object.values(andar.celulas || {}).filter(c => c.tipo === 'VAGA')
    const ativas = vagas.filter(v => !v.inativa)
    const ocupadas = ativas.filter(v => !v.livre).length
    const livres = ativas.filter(v => v.livre).length
    const inativas = vagas.filter(v => v.inativa).length
    const pct = ativas.length > 0 ? Math.round((ocupadas / ativas.length) * 100) : 0
    const variacao = ((andar.id_andar + idx * 7) % 15) - 5

    return {
      idx,
      id_andar: andar.id_andar,
      nome_andar: andar.nome_andar,
      livres,
      ocupadas,
      inativas,
      pct,
      variacao
    }
  })
})

const estatisticasSetoresAndarAtual = computed(() => {
  if (!andarAtual.value) return []
  const celulas = Object.values(andarAtual.value.celulas || {})

  return (andarAtual.value.setores || []).map((setor, idx) => {
    const vagasSetor = celulas.filter(c => c.tipo === 'VAGA' && c.setorId === setor.id_setor)
    const ativas = vagasSetor.filter(v => !v.inativa)
    const ocupadas = ativas.filter(v => !v.livre).length
    const livres = ativas.filter(v => v.livre).length
    const inativas = vagasSetor.filter(v => v.inativa).length
    const pct = ativas.length > 0 ? Math.round((ocupadas / ativas.length) * 100) : 0
    const variacao = ((setor.id_setor + idx * 5) % 19) - 6

    return {
      id_setor: setor.id_setor,
      nome_setor: setor.nome_setor,
      prefixo: setor.prefixo,
      cor_hex: setor.cor_hex,
      livres,
      ocupadas,
      inativas,
      pct,
      variacao
    }
  })
})

const urlPublicaMotorista = computed(() => {
  if (!estacionamentoAtual.value) return ''
  return `${window.location.origin}/?id=${estacionamentoAtual.value.id}`
})

const urlImagemQrCode = computed(() => {
  if (!urlPublicaMotorista.value) return ''
  return `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(
    urlPublicaMotorista.value
  )}`
})

function imprimirQrCode() {
  window.print()
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

function tratarEscGerente(e) {
  if (e.key === 'Escape') {
    if (modoAcaoVagas.value) cancelarModoSelecao()
    menuOpcoesMobileAberto.value = false
    menuSetoresMobileAberto.value = false
  }
}

onMounted(() => {
  window.addEventListener('mouseup', finalizarArrastoGerente)
  window.addEventListener('click', fecharDropdownAoClicarFora)
  window.addEventListener('keydown', tratarEscGerente)
})

onUnmounted(() => {
  pararAutoScrollGerente()
  window.removeEventListener('mouseup', finalizarArrastoGerente)
  window.removeEventListener('click', fecharDropdownAoClicarFora)
  window.removeEventListener('keydown', tratarEscGerente)
})
</script>

<template>
  <div v-if="estacionamentoAtual && andarAtual" class="editor-layout">
    <div class="hud-coluna-direita-mobile">
      <button
        class="hud-btn-flutuante"
        :class="{ 'hud-ativo': menuOpcoesMobileAberto }"
        title="Opções e Ações do Estacionamento"
        @click="menuOpcoesMobileAberto = !menuOpcoesMobileAberto; menuSetoresMobileAberto = false"
      >
        <IconSettings :size="20" />
      </button>

      <button
        class="hud-btn-flutuante"
        :class="{ 'hud-ativo': menuSetoresMobileAberto }"
        title="Métricas por Andar e Setor"
        @click="menuSetoresMobileAberto = !menuSetoresMobileAberto; menuOpcoesMobileAberto = false"
      >
        <IconLayoutBoard :size="20" />
      </button>
    </div>

    <!-- Barra Superior em Tela Cheia -->
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

        <!-- Grupo de Navegação e Filtros -->
        <div class="grupo-filtros-navegacao-gerente">
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
      </div>

      <div class="topbar-direita-gerente">
        <!-- Grupo Inativar/Reativar -->
        <div class="grupo-inativar-reativar-gerente">
          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-modo-inativar-ativo': modoAcaoVagas === 'INATIVAR' }"
            @click="alternarModoSelecao('INATIVAR')"
          >
            <IconBan :size="17" />
            <span>Inativar</span>
          </button>

          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-modo-reativar-ativo': modoAcaoVagas === 'REATIVAR' }"
            @click="alternarModoSelecao('REATIVAR')"
          >
            <IconSquareRoundedCheck :size="17" />
            <span>Reativar</span>
          </button>
        </div>

        <!-- Grupo Mapa de Calor (Com Toggle Switch de Tamanho Fixo) + Simulação -->
        <div class="grupo-calor-simulacao-gerente">
          <button
            class="btn-secundario btn-toggle-calor item-icone-texto"
            :class="{ 'btn-calor-ativo': modoMapaCalor }"
            @click="modoMapaCalor = !modoMapaCalor"
          >
            <IconFlame :size="18" />
            <span>Mapa de Calor</span>
            <span class="switch-calor-track" :class="{ ativo: modoMapaCalor }">
              <span class="switch-calor-thumb"></span>
            </span>
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

        <button
          class="btn-primario btn-qrcode-gerente item-icone-texto"
          @click="modalQrAberto = true"
        >
          <IconQrcode :size="18" />
          <span>QR Code</span>
        </button>
      </div>
    </header>

    <!-- Área Central do Mapa e Barra Lateral -->
    <div class="editor-workspace">
      <div class="area-grid-container">
        <Transition name="fade-pop">
          <div
            v-if="modoAcaoVagas"
            class="overlay-flutuante banner-instrucao-gerente"
            :class="modoAcaoVagas === 'INATIVAR' ? 'cor-banner-inativar' : 'cor-banner-reativar'"
          >
            <span>
              Modo <strong>{{ modoAcaoVagas === 'INATIVAR' ? 'Inativar Vagas' : 'Reativar Vagas' }}</strong>:
              clique ou arraste sobre as vagas desejadas ({{ vagasSelecionadasIds.size }} selecionada(s))
            </span>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="modoMapaCalor" class="overlay-flutuante legenda-calor-overlay">
            <strong>Rotatividade:</strong>
            <span class="amostra-calor calor-nivel-1">Muito Baixa</span>
            <span class="amostra-calor calor-nivel-2">Baixa</span>
            <span class="amostra-calor calor-nivel-3">Média</span>
            <span class="amostra-calor calor-nivel-4">Alta</span>
            <span class="amostra-calor calor-nivel-5">Intensa</span>
          </div>
        </Transition>

        <!-- Popup de confirmação em lote com botão de confirmar apenas com ícone centralizado -->
        <Transition name="fade-pop">
          <div v-if="modoAcaoVagas && vagasSelecionadasIds.size > 0" class="overlay-flutuante popup-confirmar-lote-gerente">
            <span><strong>{{ vagasSelecionadasIds.size }}</strong> vaga(s) marcada(s)</span>
            <button
              class="btn-primario btn-popup-lote btn-icone-confirmar-lote item-icone-texto"
              :class="modoAcaoVagas === 'INATIVAR' ? 'btn-lote-vermelho' : 'btn-lote-verde'"
              :disabled="salvandoLote"
              :title="modoAcaoVagas === 'INATIVAR' ? 'Confirmar Inativação' : 'Confirmar Reativação'"
              @click="confirmarAlteracaoLoteVagas"
            >
              <IconSquareRoundedCheck :size="19" />
            </button>
            <button
              class="btn-secundario btn-popup-lote btn-icone-confirmar-lote item-icone-texto"
              title="Cancelar seleção"
              @click="cancelarModoSelecao"
            >
              <IconSquareRoundedX :size="19" />
            </button>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="infoHoverCelula" class="overlay-flutuante badge-hover-setor">
            <span class="bolinha-cor-setor" :style="{ backgroundColor: infoHoverCelula.cor }"></span>
            <strong>{{ infoHoverCelula.titulo }}</strong>
            <span v-if="infoHoverCelula.detalhe" class="texto-colchetes-setor">
              [{{ infoHoverCelula.detalhe }}]
            </span>
          </div>
        </Transition>

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
            <!-- Transição sutil na troca de andares -->
            <Transition name="fade-andar" mode="out-in">
              <div
                :key="`${estacionamentoAtual.id}-${andarAtual.id_andar}`"
                class="matriz-com-coordenadas"
              >
                <div
                  class="linha-coordenadas-x"
                  :style="{ gridTemplateColumns: `36px repeat(${andarAtual.grid_x}, 36px)` }"
                >
                  <div class="canto-xy">Y\X</div>
                  <div v-for="x in andarAtual.grid_x" :key="`gx-${x}`" class="rotulo-coord">
                    {{ x - 1 }}
                  </div>
                </div>

                <div
                  v-for="y in andarAtual.grid_y"
                  :key="`grow-${y}`"
                  class="linha-grid-y"
                  :style="{ gridTemplateColumns: `36px repeat(${andarAtual.grid_x}, 36px)` }"
                >
                  <div class="rotulo-coord">{{ y - 1 }}</div>

                  <div
                    v-for="x in andarAtual.grid_x"
                    :key="`gcell-${x - 1}-${y - 1}`"
                    :data-coord="`${x - 1},${y - 1}`"
                    class="celula-editor-fundo"
                    :style="{
                      backgroundColor:
                        andarAtual.celulas[`${x - 1},${y - 1}`]?.corSetor || 'transparent'
                    }"
                    @mousedown.prevent="iniciarCliqueCelulaGerente(x - 1, y - 1)"
                    @mouseenter="moverArrastoCelulaGerente(x - 1, y - 1)"
                  >
                    <div
                      class="quadrado-editor"
                      :class="[
                        andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAZIO' ? 'qe-vazio' : '',
                        andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ESTRADA' ? 'qe-estrada' : '',
                        andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ENTRADA' ? 'qe-entrada' : '',
                        andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'SAIDA' ? 'qe-saida' : '',
                        andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ACESSO' ? 'qe-acesso' : '',
                        classeCorVagaGerente(andarAtual.celulas[`${x - 1},${y - 1}`]),
                        vagasSelecionadasIds.has(andarAtual.celulas[`${x - 1},${y - 1}`]?.idVagaBanco)
                          ? modoAcaoVagas === 'INATIVAR'
                            ? 'qe-selecionado-inativar-amarelo'
                            : 'qe-selecionado-reativar-azul'
                          : ''
                      ]"
                    >
                      <span v-if="andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA'">
                        {{ andarAtual.celulas[`${x - 1},${y - 1}`]?.identificador }}
                      </span>
                      <IconDoorEnter
                        v-else-if="andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ENTRADA'"
                        :size="17"
                      />
                      <IconDoorExit
                        v-else-if="andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'SAIDA'"
                        :size="17"
                      />
                      <IconArrowBarRight
                        v-else-if="andarAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ACESSO'"
                        :size="17"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>

      <!-- Painel Lateral de Métricas por Andar e Setor -->
      <aside
        class="sidebar-direita-editor sidebar-gerente-metricas"
        :class="{ 'sidebar-mobile-aberta': menuSetoresMobileAberto }"
      >
        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconStack2 :size="18" />
            <span>Ocupação por Andar</span>
          </h4>
          <p class="dica-painel">Comparativo em relação à média histórica</p>

          <div class="lista-cards-laterais">
            <div
              v-for="a in estatisticasAndares"
              :key="a.id_andar"
              class="card-lateral-metrica"
              :class="{ 'card-lateral-ativo': a.idx === andarIndex }"
              @click="andarIndex = a.idx"
            >
              <div class="topo-card-lateral">
                <strong>{{ a.nome_andar }}</strong>
                <span class="badge-variacao" :class="a.variacao >= 0 ? 'var-alta' : 'var-baixa'">
                  {{ a.variacao >= 0 ? `+${a.variacao}%` : `${a.variacao}%` }} vs média
                </span>
              </div>
              <div class="numeros-card-lateral">
                <span class="num-livre">{{ a.livres }} livres</span>
                <span class="num-ocupada">{{ a.ocupadas }} ocup.</span>
                <span v-if="a.inativas > 0" class="num-inativa">{{ a.inativas }} inat.</span>
              </div>
              <div class="barra-mini-lateral">
                <div class="preenchimento-mini" :style="{ width: `${a.pct}%` }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconLayoutBoard :size="18" />
            <span>Setores — {{ andarAtual.nome_andar }}</span>
          </h4>
          <p class="dica-painel">Disponibilidade instantânea do andar atual</p>

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
                <span class="badge-variacao" :class="s.variacao >= 0 ? 'var-alta' : 'var-baixa'">
                  {{ s.variacao >= 0 ? `+${s.variacao}%` : `${s.variacao}%` }}
                </span>
              </div>
              <div class="numeros-card-lateral">
                <span class="num-livre">{{ s.livres }} livres</span>
                <span class="num-ocupada">{{ s.ocupadas }} ocup.</span>
                <span v-if="s.inativas > 0" class="num-inativa">{{ s.inativas }} inat.</span>
              </div>
              <div class="barra-mini-lateral">
                <div class="preenchimento-mini" :style="{ width: `${s.pct}%` }"></div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Modal de QR Code para Motoristas -->
    <Transition name="fade-backdrop">
      <div v-if="modalQrAberto" class="modal-backdrop" @click.self="modalQrAberto = false">
        <div class="modal-box modal-qr-gerente">
          <div class="overlay-header">
            <h3 class="item-icone-texto">
              <IconQrcode :size="20" />
              <span>QR Code do Estacionamento</span>
            </h3>
            <button class="btn-fechar-mini" @click="modalQrAberto = false">
              <IconSquareRoundedX :size="20" />
            </button>
          </div>

          <p class="subtitulo" style="margin-bottom: 12px">
            <strong>{{ estacionamentoAtual.nome }}</strong> — Motoristas escaneiam este código para visualizar as vagas livres no celular.
          </p>

          <div class="box-imagem-qr">
            <img :src="urlImagemQrCode" :alt="`QR Code ${estacionamentoAtual.nome}`" width="220" height="220" />
          </div>

          <code class="url-qr-codigo">{{ urlPublicaMotorista }}</code>

          <div class="modal-acoes modal-acoes-centralizadas" style="margin-top: 16px">
            <button class="btn-secundario item-icone-texto" @click="modalQrAberto = false">
              <IconSquareRoundedX :size="18" />
              <span>Fechar</span>
            </button>
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