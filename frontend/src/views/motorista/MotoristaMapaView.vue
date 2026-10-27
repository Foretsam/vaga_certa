<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  estabelecimentos,
  carregarDadosDoBanco,
  contarVagasEstabelecimento
} from '@/stores/estacionamentoStore'
import { useGridPanZoom } from '@/composables/useGridPanZoom'
import {
  IconSquareRoundedArrowLeft,
  IconParking,
  IconPin,
  IconStack2,
  IconLayoutBoard,
  IconSearch,
  IconDoorEnter,
  IconDoorExit,
  IconArrowBarRight,
  IconAlertSquareRounded
} from '@/constants/icons'

const route = useRoute()
const router = useRouter()

const andarIndex = ref(0)
const setorDestacadoId = ref(null)
const celulaInspecionada = ref(null)
const painelSetoresMobileAberto = ref(false)

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
})

const estacionamentoAtual = computed(() => {
  const idParam = Number(route.params.id)
  return estabelecimentos.value.find(e => e.id === idParam && !e.inativo) || null
})

watch(
  () => route.params.id,
  () => {
    andarIndex.value = 0
    setorDestacadoId.value = null
    celulaInspecionada.value = null
    resetarCameraGrid()
  }
)

const andarAtual = computed(() => {
  if (!estacionamentoAtual.value?.andares) return null
  return (
    estacionamentoAtual.value.andares[andarIndex.value] ||
    estacionamentoAtual.value.andares[0] ||
    null
  )
})

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
  if (setorDestacadoId.value === idSetor) {
    setorDestacadoId.value = null
  } else {
    setorDestacadoId.value = idSetor
  }
}

function inspecionarCelula(x, y) {
  if (!andarAtual.value?.celulas) return
  const c = andarAtual.value.celulas[`${x},${y}`]
  if (!c || c.tipo === 'VAZIO') {
    celulaInspecionada.value = null
    return
  }
  celulaInspecionada.value = c
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
  <!-- Caso o ID não exista ou esteja inativo -->
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

  <!-- VISÃO DO MAPA 2D PARA O MOTORISTA -->
  <div v-else-if="andarAtual" class="editor-layout">
    <!-- Botão Flutuante Mobile para abrir lista de Andares/Setores -->
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

        <!-- Seletor de Andar -->
        <div class="seletor-andar-box">
          <IconStack2 :size="18" />
          <span>Andar:</span>
          <select
            v-if="estacionamentoAtual.andares.length > 1"
            v-model="andarIndex"
            class="select-andar-editor"
            @change="setorDestacadoId = null; resetarCameraGrid()"
          >
            <option
              v-for="a in estatisticasAndaresMotorista"
              :key="a.id_andar"
              :value="a.idx"
            >
              {{ a.nome_andar }} ({{ a.livres }} livres)
            </option>
          </select>
          <strong v-else>{{ andarAtual.nome_andar }}</strong>
        </div>

        <button
          v-if="panX !== 0 || panY !== 0 || zoomEscala !== 1"
          class="btn-secundario item-icone-texto"
          title="Centralizar Mapa"
          @click="resetarCameraGrid"
        >
          <IconSearch :size="16" />
          <span>{{ Math.round(zoomEscala * 100) }}%</span>
        </button>
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

    <!-- ÁREA DO MAPA + PAINEL LATERAL DE ANDARES E SETORES -->
    <div class="editor-workspace">
      <div class="area-grid-container">
        <!-- HUD Inferior ao tocar ou passar o mouse sobre uma vaga -->
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
          class="area-grid-principal"
          @mouseleave="celulaInspecionada = null"
          @touchstart.passive="iniciarToquePanZoom"
          @touchmove.prevent="moverToquePanZoom"
          @touchend="finalizarToquePanZoom($event, inspecionarCelula)"
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
                <div v-for="x in andarAtual.grid_x" :key="`mx-${x}`" class="rotulo-coord">
                  {{ x }}
                </div>
              </div>

              <div
                v-for="y in andarAtual.grid_y"
                :key="`my-${y}`"
                class="linha-grid-y"
                :style="{ gridTemplateColumns: `36px repeat(${andarAtual.grid_x}, 36px)` }"
              >
                <div class="rotulo-coord">{{ y }}</div>

                <div
                  v-for="x in andarAtual.grid_x"
                  :key="`mc-${x}-${y}`"
                  :data-coord="`${x},${y}`"
                  class="celula-editor-fundo"
                  :class="{
                    'celula-esmaecida-setor':
                      setorDestacadoId &&
                      andarAtual.celulas[`${x},${y}`]?.setorId !== setorDestacadoId &&
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA'
                  }"
                  :style="{
                    backgroundColor: andarAtual.celulas[`${x},${y}`]?.corSetor || 'transparent'
                  }"
                  @mouseenter="inspecionarCelula(x, y)"
                  @click="inspecionarCelula(x, y)"
                >
                  <div
                    class="quadrado-editor"
                    :class="[
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'VAZIO' ? 'qe-vazio' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'ESTRADA' ? 'qe-estrada' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'ENTRADA' ? 'qe-entrada' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'SAIDA' ? 'qe-saida' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'ACESSO' ? 'qe-acesso' : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' &&
                      (andarAtual.celulas[`${x},${y}`]?.inativa || !andarAtual.celulas[`${x},${y}`]?.macEsp)
                        ? 'vaga-gerente-inativa'
                        : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' &&
                      !andarAtual.celulas[`${x},${y}`]?.inativa &&
                      andarAtual.celulas[`${x},${y}`]?.macEsp &&
                      andarAtual.celulas[`${x},${y}`]?.livre
                        ? 'vaga-gerente-livre'
                        : '',
                      andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA' &&
                      !andarAtual.celulas[`${x},${y}`]?.inativa &&
                      andarAtual.celulas[`${x},${y}`]?.macEsp &&
                      !andarAtual.celulas[`${x},${y}`]?.livre
                        ? 'vaga-gerente-ocupada'
                        : ''
                    ]"
                  >
                    <span v-if="andarAtual.celulas[`${x},${y}`]?.tipo === 'VAGA'">
                      {{ andarAtual.celulas[`${x},${y}`]?.identificador }}
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