<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  estabelecimentos,
  carregarDadosDoBanco,
  contarVagasEstabelecimento
} from '@/stores/estacionamentoStore'
import { useGridPanZoom } from '@/composables/useGridPanZoom'
import {
  IconSquareRoundedArrowLeft,
  IconSquareRoundedChevronDown,
  IconSquareRoundedCheck,
  IconSquareRoundedPlus,
  IconSquareRoundedMinus,
  IconParking,
  IconPin,
  IconStack2,
  IconLayoutBoard,
  IconDoorEnter,
  IconDoorExit,
  IconArrowBarRight,
  IconAlertSquareRounded
} from '@/constants/icons'

const route = useRoute()
const router = useRouter()

const andarIndex = ref(0)
const dropdownAndarAberto = ref(false)
const setorDestacadoId = ref(null)
const celulaInspecionada = ref(null)
const painelSetoresMobileAberto = ref(false)
const containerMapaRef = ref(null)

const {
  panX,
  panY,
  zoomEscala,
  iniciarToquePanZoom,
  moverToquePanZoom,
  finalizarToquePanZoom,
  resetarCameraGrid
} = useGridPanZoom()

onMounted(async () => {
  if (estabelecimentos.value.length === 0) {
    await carregarDadosDoBanco()
  }
  await nextTick()
  ajustarZoomERolagemParaEntrada()
  window.addEventListener('click', fecharDropdownAndarFora)
  window.addEventListener('resize', ajustarZoomERolagemParaEntrada)
})

onUnmounted(() => {
  window.removeEventListener('click', fecharDropdownAndarFora)
  window.removeEventListener('resize', ajustarZoomERolagemParaEntrada)
})

function fecharDropdownAndarFora(e) {
  if (!e.target.closest('.seletor-andar-custom')) {
    dropdownAndarAberto.value = false
  }
}

const estacionamentoAtual = computed(() => {
  const idParam = Number(route.params.id)
  return estabelecimentos.value.find(e => e.id === idParam && !e.inativo) || null
})

const andarAtual = computed(() => {
  if (!estacionamentoAtual.value?.andares) return null
  return (
    estacionamentoAtual.value.andares[andarIndex.value] ||
    estacionamentoAtual.value.andares[0] ||
    null
  )
})

// =========================================================
// RECORTE DE EXTREMIDADES VAZIAS E ROTAÇÃO COM ENTRADA EMBAIXO
// =========================================================
const mapaProcessadoMotorista = computed(() => {
  const andar = andarAtual.value
  if (!andar?.celulas) return null

  const todas = Object.values(andar.celulas)
  const preenchidas = todas.filter(c => c.tipo !== 'VAZIO' || c.setorId)

  if (preenchidas.length === 0) {
    return {
      largura: 1,
      altura: 1,
      linhas: [[todas[0]]]
    }
  }

  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity

  preenchidas.forEach((c) => {
    if (c.x < minX) minX = c.x
    if (c.x > maxX) maxX = c.x
    if (c.y < minY) minY = c.y
    if (c.y > maxY) maxY = c.y
  })

  // Matriz recortada apenas onde existem elementos
  let matriz = []
  for (let y = minY; y <= maxY; y++) {
    const linha = []
    for (let x = minX; x <= maxX; x++) {
      linha.push(andar.celulas[`${x},${y}`])
    }
    matriz.push(linha)
  }

  // Descobre onde está a ENTRADA (ou SAIDA) para rotacionar e deixá-la sempre na borda inferior
  const entradas = preenchidas.filter(c => c.tipo === 'ENTRADA')
  const alvosRef = entradas.length > 0 ? entradas : preenchidas.filter(c => c.tipo === 'SAIDA')

  let rotacoes90Horario = 0
  if (alvosRef.length > 0) {
    const mediaX = alvosRef.reduce((acc, c) => acc + c.x, 0) / alvosRef.length
    const mediaY = alvosRef.reduce((acc, c) => acc + c.y, 0) / alvosRef.length

    const distTopo = Math.abs(mediaY - minY)
    const distBase = Math.abs(maxY - mediaY)
    const distEsq = Math.abs(mediaX - minX)
    const distDir = Math.abs(maxX - mediaX)

    const menor = Math.min(distBase, distTopo, distEsq, distDir)
    if (menor === distBase) {
      rotacoes90Horario = 0 // Já está embaixo
    } else if (menor === distTopo) {
      rotacoes90Horario = 2 // 180 graus (topo vai para baixo)
    } else if (menor === distDir) {
      rotacoes90Horario = 1 // 90 graus horário (direita vai para baixo)
    } else {
      rotacoes90Horario = 3 // 270 graus horário (esquerda vai para baixo)
    }
  }

  for (let r = 0; r < rotacoes90Horario; r++) {
    const h = matriz.length
    const w = matriz[0].length
    const nova = Array.from({ length: w }, () => Array(h))
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        nova[x][h - 1 - y] = matriz[y][x]
      }
    }
    matriz = nova
  }

  return {
    largura: matriz[0]?.length || 1,
    altura: matriz.length || 1,
    linhas: matriz
  }
})

// =========================================================
// AUTO-ZOOM SE MENOR QUE A TELA E SCROLL NA ENTRADA (INFERIOR)
// =========================================================
function ajustarZoomERolagemParaEntrada() {
  const container = containerMapaRef.value
  const dados = mapaProcessadoMotorista.value
  if (!container || !dados) return

  resetarCameraGrid()

  const tamanhoCelulaPx = 30
  const larguraMapaPx = dados.largura * tamanhoCelulaPx
  const alturaMapaPx = dados.altura * tamanhoCelulaPx

  const largDisp = container.clientWidth - 36
  const altDisp = container.clientHeight - 36

  if (larguraMapaPx < largDisp && alturaMapaPx < altDisp) {
    const escalaIdeal = Math.min(largDisp / larguraMapaPx, altDisp / alturaMapaPx, 2.1)
    zoomEscala.value = Number(Math.max(1, escalaIdeal).toFixed(2))
  } else {
    zoomEscala.value = 1
  }

  // Posiciona a rolagem para que a Entrada (parte inferior) fique totalmente visível
  setTimeout(() => {
    if (!containerMapaRef.value) return
    containerMapaRef.value.scrollTop = containerMapaRef.value.scrollHeight
    const sobraH = containerMapaRef.value.scrollWidth - containerMapaRef.value.clientWidth
    if (sobraH > 0) {
      containerMapaRef.value.scrollLeft = Math.floor(sobraH / 2)
    }
  }, 60)
}

function alterarZoomBotao(delta) {
  const novo = Math.min(2.6, Math.max(0.5, Number((zoomEscala.value + delta).toFixed(2))))
  zoomEscala.value = novo
}

function aoRolarMouseMapa(e) {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    const delta = e.deltaY < 0 ? 0.12 : -0.12
    alterarZoomBotao(delta)
  }
}

watch(
  () => [route.params.id, andarIndex.value, estacionamentoAtual.value?.id],
  async () => {
    setorDestacadoId.value = null
    celulaInspecionada.value = null
    await nextTick()
    ajustarZoomERolagemParaEntrada()
  }
)

const metricasGerais = computed(() => {
  if (!estacionamentoAtual.value) return { total: 0, livres: 0, ocupadas: 0 }
  return contarVagasEstabelecimento(estacionamentoAtual.value)
})

const estatisticasAndaresMotorista = computed(() => {
  if (!estacionamentoAtual.value?.andares) return []
  return estacionamentoAtual.value.andares.map((andar, idx) => {
    const vagas = Object.values(andar.celulas || {}).filter(c => c.tipo === 'VAGA')
    const livres = vagas.filter(v => !v.inativa && v.macEsp && v.livre).length
    const total = vagas.filter(v => !v.inativa).length
    return {
      idx,
      id_andar: andar.id_andar,
      nome_andar: andar.nome_andar,
      livres,
      total
    }
  })
})

function escolherAndarDropdown(idx) {
  andarIndex.value = idx
  dropdownAndarAberto.value = false
}

const setoresAndarAtual = computed(() => {
  if (!andarAtual.value) return []
  const celulas = Object.values(andarAtual.value.celulas || {})

  return (andarAtual.value.setores || []).map((setor) => {
    const vagasSetor = celulas.filter(
      c => c.tipo === 'VAGA' && c.setorId === setor.id_setor && !c.inativa
    )
    const livres = vagasSetor.filter(v => v.macEsp && v.livre).length
    return {
      id_setor: setor.id_setor,
      nome_setor: setor.nome_setor,
      prefixo: setor.prefixo,
      cor_hex: setor.cor_hex,
      livres,
      total: vagasSetor.length
    }
  })
})

function alternarFiltroSetor(idSetor) {
  setorDestacadoId.value = setorDestacadoId.value === idSetor ? null : idSetor
}

function inspecionarCelula(c) {
  if (!c || c.tipo === 'VAZIO') {
    celulaInspecionada.value = null
    return
  }
  celulaInspecionada.value = c
}

function inspecionarPorCoordenada(x, y) {
  if (!andarAtual.value?.celulas) return
  inspecionarCelula(andarAtual.value.celulas[`${x},${y}`])
}

const infoBadgeMotorista = computed(() => {
  const c = celulaInspecionada.value
  if (!c) return null

  if (c.tipo === 'ENTRADA') {
    return { cor: '#2563eb', titulo: 'Entrada de Veículos', detalhe: andarAtual.value?.nome_andar }
  }
  if (c.tipo === 'SAIDA') {
    return { cor: '#ea580c', titulo: 'Saída de Veículos', detalhe: andarAtual.value?.nome_andar }
  }
  if (c.tipo === 'ACESSO') {
    return { cor: '#16a34a', titulo: 'Acesso de Pedestres / Elevador', detalhe: andarAtual.value?.nome_andar }
  }
  if (c.tipo === 'ESTRADA') {
    return { cor: '#475569', titulo: 'Via de Circulação', detalhe: c.nomeSetor || andarAtual.value?.nome_andar }
  }
  if (c.tipo === 'VAGA') {
    if (c.inativa || !c.macEsp) {
      return {
        cor: '#64748b',
        titulo: `Vaga ${c.identificador} — Indisponível`,
        detalhe: c.nomeSetor ? `Setor ${c.nomeSetor}` : ''
      }
    }
    if (c.livre) {
      return {
        cor: '#16a34a',
        titulo: `Vaga ${c.identificador} — LIVRE PARA ESTACIONAR`,
        detalhe: c.nomeSetor ? `Setor ${c.nomeSetor} (${andarAtual.value?.nome_andar})` : andarAtual.value?.nome_andar
      }
    }
    return {
      cor: '#dc2626',
      titulo: `Vaga ${c.identificador} — OCUPADA`,
      detalhe: c.nomeSetor ? `Setor ${c.nomeSetor}` : ''
    }
  }
  return null
})
</script>

<template>
  <main v-if="!estacionamentoAtual" class="tela-inicial">
    <div class="auth-card card-erro-acesso">
      <div class="icone-erro-acesso" style="color: #f59e0b; background: rgba(245, 158, 11, 0.12)">
        <IconAlertSquareRounded :size="44" />
      </div>
      <h1>Estacionamento não encontrado</h1>
      <p class="subtitulo texto-erro-acesso">
        O estacionamento solicitado não existe ou está temporariamente indisponível.
      </p>
      <button
        class="btn-primario btn-auth-submit item-icone-texto"
        @click="router.push({ name: 'motorista-home' })"
      >
        <IconSquareRoundedArrowLeft :size="20" />
        <span>Buscar outro estacionamento</span>
      </button>
    </div>
  </main>

  <div v-else-if="andarAtual && mapaProcessadoMotorista" class="editor-layout">
    <div class="hud-coluna-direita-mobile">
      <button
        class="hud-btn-flutuante"
        :class="{ 'hud-ativo': painelSetoresMobileAberto }"
        title="Ver Setores e Andares"
        @click="painelSetoresMobileAberto = !painelSetoresMobileAberto"
      >
        <IconLayoutBoard :size="20" />
      </button>
    </div>

    <!-- BARRA SUPERIOR DO MOTORISTA -->
    <header class="editor-topbar topbar-motorista-mapa">
      <div class="topbar-esquerda">
        <button
          class="btn-secundario item-icone-texto"
          @click="router.push({ name: 'motorista-home' })"
        >
          <IconSquareRoundedArrowLeft :size="18" />
          <span>Trocar Estacionamento</span>
        </button>

        <div class="identificacao-est-motorista">
          <strong>{{ estacionamentoAtual.nome }}</strong>
          <span class="badge-cidade-inline">
            <IconPin :size="12" style="vertical-align: -1px" />
            {{ estacionamentoAtual.cidade || 'Sorocaba' }}
          </span>
        </div>

        <!-- Seletor de Andar Estilizado como os demais -->
        <div class="seletor-multi-wrapper seletor-andar-custom">
          <button
            type="button"
            class="btn-seletor-multi item-icone-texto"
            @click="dropdownAndarAberto = !dropdownAndarAberto"
          >
            <IconStack2 :size="18" style="color: var(--destaque-azul)" />
            <span>
              {{ andarAtual.nome_andar }}
              ({{ estatisticasAndaresMotorista[andarIndex]?.livres ?? 0 }} livres)
            </span>
            <IconSquareRoundedChevronDown :size="17" />
          </button>

          <Transition name="fade-pop">
            <div v-if="dropdownAndarAberto" class="dropdown-multi-box">
              <div class="lista-opcoes-multi">
                <div
                  v-for="a in estatisticasAndaresMotorista"
                  :key="a.id_andar"
                  class="item-opcao-multi"
                  :class="{ 'opcao-ativa': a.idx === andarIndex }"
                  @click="escolherAndarDropdown(a.idx)"
                >
                  <span>{{ a.nome_andar }} ({{ a.livres }} livres)</span>
                  <IconSquareRoundedCheck v-if="a.idx === andarIndex" :size="18" />
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Controles de Zoom na Tela -->
        <div class="controles-zoom-motorista">
          <button
            type="button"
            class="btn-zoom-acao"
            title="Diminuir Zoom (ou Ctrl + Roda do Mouse)"
            @click="alterarZoomBotao(-0.15)"
          >
            <IconSquareRoundedMinus :size="17" />
          </button>
          <button
            type="button"
            class="btn-zoom-reset"
            title="Reajustar Zoom Padrão"
            @click="ajustarZoomERolagemParaEntrada"
          >
            {{ Math.round(zoomEscala * 100) }}%
          </button>
          <button
            type="button"
            class="btn-zoom-acao"
            title="Aumentar Zoom (ou Ctrl + Roda do Mouse)"
            @click="alterarZoomBotao(0.15)"
          >
            <IconSquareRoundedPlus :size="17" />
          </button>
        </div>
      </div>

      <div class="topbar-direita-motorista">
        <div class="legenda-motorista-inline">
          <span class="item-legenda-mot"><i class="cor-mot livre"></i> Livre</span>
          <span class="item-legenda-mot"><i class="cor-mot ocupada"></i> Ocupada</span>
          <span class="item-legenda-mot"><i class="cor-mot entrada"></i> Entrada</span>
          <span class="item-legenda-mot"><i class="cor-mot saida"></i> Saída</span>
        </div>

        <span
          class="badge-livres-motorista ocultar-info-mobile"
          :class="metricasGerais.livres > 0 ? 'tem-vaga' : 'lotado'"
        >
          <IconParking :size="16" />
          {{ metricasGerais.livres }} vagas livres no total
        </span>
      </div>
    </header>

    <!-- ÁREA DO MAPA (SEM COORDENADAS, SEM QUADRADOS VAZIOS, COM ENTRADA EMBAIXO) -->
    <div class="editor-workspace">
      <div class="area-grid-container">
        <Transition name="fade-pop">
          <div v-if="infoBadgeMotorista" class="overlay-flutuante badge-hover-setor">
            <span
              class="bolinha-cor-setor"
              :style="{ backgroundColor: infoBadgeMotorista.cor }"
            ></span>
            <strong>{{ infoBadgeMotorista.titulo }}</strong>
            <span v-if="infoBadgeMotorista.detalhe" class="texto-colchetes-setor">
              [{{ infoBadgeMotorista.detalhe }}]
            </span>
          </div>
        </Transition>

        <div
          ref="containerMapaRef"
          class="area-grid-principal area-grid-motorista-limpa"
          @mouseleave="celulaInspecionada = null"
          @wheel="aoRolarMouseMapa"
          @touchstart.passive="iniciarToquePanZoom"
          @touchmove.prevent="moverToquePanZoom"
          @touchend="finalizarToquePanZoom($event, inspecionarPorCoordenada)"
        >
          <div
            class="viewport-touch-canvas viewport-motorista-central"
            :style="{
              transform: `translate(${panX}px, ${panY}px) scale(${zoomEscala})`,
              transformOrigin: 'center bottom'
            }"
          >
            <div class="matriz-motorista-sem-coordenadas">
              <div
                v-for="(linha, rIdx) in mapaProcessadoMotorista.linhas"
                :key="`m-row-${rIdx}`"
                class="linha-grid-y"
                :style="{
                  gridTemplateColumns: `repeat(${mapaProcessadoMotorista.largura}, 30px)`
                }"
              >
                <div
                  v-for="(cel, cIdx) in linha"
                  :key="`m-cel-${rIdx}-${cIdx}`"
                  :data-coord="cel ? `${cel.x},${cel.y}` : ''"
                  class="celula-motorista-compacta"
                  :class="{
                    'celula-esmaecida-setor':
                      setorDestacadoId &&
                      cel?.setorId !== setorDestacadoId &&
                      cel?.tipo === 'VAGA'
                  }"
                  :style="{
                    backgroundColor: cel?.corSetor || 'transparent'
                  }"
                  @mouseenter="inspecionarCelula(cel)"
                  @click="inspecionarCelula(cel)"
                >
                  <!-- Renderiza o quadrado apenas quando NÃO for vazio -->
                  <div
                    v-if="cel && cel.tipo !== 'VAZIO'"
                    class="quadrado-editor quadrado-motorista"
                    :class="[
                      cel.tipo === 'ESTRADA' ? 'qe-estrada' : '',
                      cel.tipo === 'ENTRADA' ? 'qe-entrada' : '',
                      cel.tipo === 'SAIDA' ? 'qe-saida' : '',
                      cel.tipo === 'ACESSO' ? 'qe-acesso' : '',
                      cel.tipo === 'VAGA' && (cel.inativa || !cel.macEsp)
                        ? 'vaga-gerente-inativa'
                        : '',
                      cel.tipo === 'VAGA' && !cel.inativa && cel.macEsp && cel.livre
                        ? 'vaga-gerente-livre'
                        : '',
                      cel.tipo === 'VAGA' && !cel.inativa && cel.macEsp && !cel.livre
                        ? 'vaga-gerente-ocupada'
                        : ''
                    ]"
                  >
                    <span v-if="cel.tipo === 'VAGA'">
                      {{ cel.identificador }}
                    </span>
                    <IconDoorEnter v-else-if="cel.tipo === 'ENTRADA'" :size="15" />
                    <IconDoorExit v-else-if="cel.tipo === 'SAIDA'" :size="15" />
                    <IconArrowBarRight v-else-if="cel.tipo === 'ACESSO'" :size="15" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- PAINEL LATERAL: DISPONIBILIDADE POR ANDAR E SETOR -->
      <aside
        class="sidebar-direita-editor sidebar-gerente-metricas"
        :class="{ 'sidebar-mobile-aberta': painelSetoresMobileAberto }"
      >
        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconStack2 :size="18" />
            <span>Andares do Estacionamento</span>
          </h4>
          <p class="dica-painel">Toque para alternar de andar</p>

          <div class="lista-cards-laterais">
            <div
              v-for="a in estatisticasAndaresMotorista"
              :key="a.id_andar"
              class="card-lateral-metrica"
              :class="{ 'card-lateral-ativo': a.idx === andarIndex }"
              @click="andarIndex = a.idx; setorDestacadoId = null; painelSetoresMobileAberto = false"
            >
              <div class="topo-card-lateral">
                <strong>{{ a.nome_andar }}</strong>
                <span class="badge-variacao" :class="a.livres > 0 ? 'var-alta' : 'var-baixa'">
                  {{ a.livres > 0 ? `${a.livres} livres` : 'Lotado' }}
                </span>
              </div>
              <div class="numeros-card-lateral">
                <span class="num-livre">{{ a.livres }} vagas disponíveis de {{ a.total }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconLayoutBoard :size="18" />
            <span>Setores — {{ andarAtual.nome_andar }}</span>
          </h4>
          <p class="dica-painel">Toque em um setor para destacá-lo no mapa</p>

          <div class="lista-cards-laterais">
            <div
              v-for="s in setoresAndarAtual"
              :key="s.id_setor"
              class="card-lateral-metrica"
              :class="{ 'card-lateral-ativo': setorDestacadoId === s.id_setor }"
              @click="alternarFiltroSetor(s.id_setor)"
            >
              <div class="topo-card-lateral">
                <span class="item-icone-texto">
                  <span class="bolinha-cor-setor" :style="{ backgroundColor: s.cor_hex }"></span>
                  <strong>{{ s.nome_setor }} ({{ s.prefixo }})</strong>
                </span>
                <span class="badge-variacao" :class="s.livres > 0 ? 'var-alta' : 'var-baixa'">
                  {{ s.livres }} livres
                </span>
              </div>
              <div class="numeros-card-lateral">
                <span>Capacidade do setor: {{ s.total }} vagas</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>