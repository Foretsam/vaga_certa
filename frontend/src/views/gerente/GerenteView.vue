<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  usuarioLogado,
  estabelecimentosDoGerente,
  estabelecimentosFiltradosGerente,
  idsSelecionadosGerente,
  simulacao1Ativa,
  alternarSimulacao1Frontend,
  obterAndarEntradaSaida,
  contarVagasEstabelecimento,
  carregarDadosDoBanco,
  cidadeSelecionadaGerente,
  cidadesDoGerente,
  estabelecimentosDoGerentePorCidade,
  selecionarCidadeGerente
} from '@/stores/estacionamentoStore'
import {
  IconChartBar,
  IconClock,
  IconParking,
  IconMaximize,
  IconSearch,
  IconSquareRoundedChevronDown,
  IconSquareRoundedCheck,
  IconSquareRoundedX,
  IconAlertSquareRounded,
  IconDoorEnter,
  IconDoorExit,
  IconArrowBarRight,
  IconPlayerPlay,
  IconPin
} from '@/constants/icons'

const router = useRouter()

// Dropdown de seleção múltipla no topo
const dropdownMultiAberto = ref(false)
const dropdownCidadeAberto = ref(false)
const termoBuscaMulti = ref('')

// Modal Popup para celular/tablet ("Escolher Estacionamento")
const modalMobileEstAberto = ref(false)
const termoBuscaMobileEst = ref('')

onMounted(() => {
  carregarDadosDoBanco()
  window.addEventListener('click', fecharDropdownsAoClicarFora)
})

onUnmounted(() => {
  window.removeEventListener('click', fecharDropdownsAoClicarFora)
})

function fecharDropdownsAoClicarFora(e) {
  if (!e.target.closest('.seletor-multi-wrapper')) {
    dropdownMultiAberto.value = false
    dropdownCidadeAberto.value = false
  }
}

const totalOpcoesFiltro = computed(() => 1 + estabelecimentosDoGerente.value.length)
const mostrarPesquisaNoMulti = computed(() => totalOpcoesFiltro.value > 5)

const listaEstabelecimentosNoMulti = computed(() => {
  const termo = termoBuscaMulti.value.trim().toLowerCase()
  const base = estabelecimentosDoGerentePorCidade.value
  if (!termo) return base
  return base.filter(e => e.nome.toLowerCase().includes(termo))
})

const textoBotaoSeletorTopo = computed(() => {
  const qtdSel = idsSelecionadosGerente.value.length
  const total = estabelecimentosDoGerentePorCidade.value.length
  if (qtdSel === 0 || qtdSel === total) {
    return `Todos (${total})`
  }
  if (qtdSel === 1) {
    const est = estabelecimentosDoGerentePorCidade.value.find(e => e.id === idsSelecionadosGerente.value[0])
    return est ? est.nome : '1 selecionado'
  }
  return `${qtdSel} estacionamentos selecionados`
})

function selecionarDashboardCompleto() {
  idsSelecionadosGerente.value = []
}

function alternarSelecaoEstacionamento(idEst) {
  const atual = [...idsSelecionadosGerente.value]
  const idx = atual.indexOf(idEst)
  if (idx !== -1) {
    atual.splice(idx, 1)
  } else {
    atual.push(idEst)
  }
  if (atual.length === estabelecimentosDoGerente.value.length) {
    idsSelecionadosGerente.value = []
  } else {
    idsSelecionadosGerente.value = atual
  }
}

// =========================================================
// MÉTRICAS SOMADAS DOS ESTACIONAMENTOS SELECIONADOS
// =========================================================
const horasBasePadrao = [
  { hora: '08h', entBase: 2, saiBase: 1 },
  { hora: '10h', entBase: 4, saiBase: 2 },
  { hora: '12h', entBase: 7, saiBase: 5 },
  { hora: '14h', entBase: 5, saiBase: 4 },
  { hora: '16h', entBase: 4, saiBase: 6 },
  { hora: '18h', entBase: 8, saiBase: 7 },
  { hora: '20h', entBase: 3, saiBase: 6 }
]

function calcularFluxoUnitarioEstacionamento(est, metricasEst) {
  const multSim = simulacao1Ativa.value ? 1.6 : 1
  const pesoVagas = Math.max(1, Math.round(metricasEst.total / 3))
  const variacaoId = (Number(est.id) % 3) + 1

  return horasBasePadrao.map((h, idx) => {
    const ajusteHora = ((Number(est.id) + idx) % 2 === 0) ? 1 : 0
    const entradas = Math.max(
      1,
      Math.round((h.entBase * pesoVagas + variacaoId + ajusteHora) * multSim)
    )
    const saidas = Math.max(
      1,
      Math.round((h.saiBase * pesoVagas + (variacaoId - 1) + ajusteHora) * multSim)
    )
    return { hora: h.hora, entradas, saidas }
  })
}

const metricasConsolidadas = computed(() => {
  const lista = estabelecimentosFiltradosGerente.value
  if (lista.length === 0) {
    return {
      qtdEstacionamentos: 0,
      taxaOcupacaoTotal: 0,
      vagasLivresSoma: 0,
      vagasOcupadasSoma: 0,
      vagasTotaisSoma: 0,
      tempoMedioFormatado: '0min',
      fluxoPorHora: [],
      maiorValorFluxo: 10
    }
  }

  let somaLivres = 0
  let somaOcupadas = 0
  let somaTotais = 0
  let somaInativas = 0
  let somaTempoMin = 0

  const mapaSomaHoras = horasBasePadrao.map(h => ({
    hora: h.hora,
    entradas: 0,
    saidas: 0
  }))

  lista.forEach((est) => {
    const m = contarVagasEstabelecimento(est)
    somaLivres += m.livres
    somaOcupadas += m.ocupadas
    somaTotais += m.total
    somaInativas += m.inativas
    somaTempoMin += m.tempoMedioMin

    const fluxoEst = calcularFluxoUnitarioEstacionamento(est, m)
    fluxoEst.forEach((itemHora, idx) => {
      mapaSomaHoras[idx].entradas += itemHora.entradas
      mapaSomaHoras[idx].saidas += itemHora.saidas
    })
  })

  mapaSomaHoras.forEach((itemHora) => {
    const totalHora = Math.max(1, itemHora.entradas + itemHora.saidas)
    itemHora.entPct = Math.round((itemHora.entradas / totalHora) * 100)
    itemHora.saiPct = 100 - itemHora.entPct
  })

  const vagasAtivasSoma = Math.max(1, somaTotais - somaInativas)
  const taxaOcupacaoTotal = somaTotais > 0 ? Math.round((somaOcupadas / vagasAtivasSoma) * 100) : 0

  const tempoMedioMinutos = Math.round(somaTempoMin / lista.length)
  const horas = Math.floor(tempoMedioMinutos / 60)
  const mins = tempoMedioMinutos % 60
  const tempoMedioFormatado =
    tempoMedioMinutos === 0
      ? '0min'
      : horas > 0
        ? `${horas}h ${mins}min`
        : `${mins}min`

  const maiorValorFluxo = Math.max(
    10,
    ...mapaSomaHoras.flatMap(f => [f.entradas, f.saidas])
  )

  return {
    qtdEstacionamentos: lista.length,
    taxaOcupacaoTotal,
    vagasLivresSoma: somaLivres,
    vagasOcupadasSoma: somaOcupadas,
    vagasTotaisSoma: somaTotais,
    tempoMedioFormatado,
    fluxoPorHora: mapaSomaHoras,
    maiorValorFluxo
  }
})

// Os 2 estacionamentos com maior número de vagas cadastradas
const top2Estacionamentos = computed(() => {
  return [...estabelecimentosFiltradosGerente.value]
    .map(est => ({
      est,
      metricas: contarVagasEstabelecimento(est),
      andarPrincipal: obterAndarEntradaSaida(est)
    }))
    .sort((a, b) => b.metricas.total - a.metricas.total)
    .slice(0, 2)
})

const listaEstabelecimentosMobileBusca = computed(() => {
  const termo = termoBuscaMobileEst.value.trim().toLowerCase()
  if (!termo) return estabelecimentosDoGerente.value
  return estabelecimentosDoGerente.value.filter(e => e.nome.toLowerCase().includes(termo))
})

function abrirEstacionamentoTelaCheia(idEst) {
  modalMobileEstAberto.value = false
  router.push({ name: 'gerente-estacionamentos', query: { id: idEst } })
}
</script>

<template>
  <div class="gerente-dashboard-container">
    <!-- CABEÇALHO DO GERENTE + SELETOR MULTI-ESTACIONAMENTOS -->
    <header class="gerente-header-topo">
      <div class="gerente-boas-vindas">
        <div>
          <h1>Bem-vindo, {{ usuarioLogado?.nome || 'Gerente' }}</h1>
          <p class="subtitulo">Painel de controle operacional com indicadores em tempo real !</p>
        </div>

        <div class="gerente-atalhos-topo">
          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-simulacao-ativa': simulacao1Ativa }"
            title="Preenche 60% das vagas como ocupadas e gera usos de 1 a 10 no frontend"
            @click="alternarSimulacao1Frontend"
          >
            <IconPlayerPlay :size="17" />
            <span>{{ simulacao1Ativa ? 'Simulação: Ativa' : 'Simulação' }}</span>
          </button>

          <button
            class="btn-secundario item-icone-texto"
            @click="router.push({ name: 'gerente-estacionamentos' })"
          >
            <IconParking :size="18" />
            <span>Estacionamentos</span>
          </button>

          <button
            class="btn-primario item-icone-texto"
            @click="router.push({ name: 'gerente-relatorios' })"
          >
            <IconChartBar :size="18" />
            <span>Relatórios</span>
          </button>
        </div>
      </div>

      <!-- Seletor Múltiplo alinhado à esquerda junto com os cards -->
      <div v-if="estabelecimentosDoGerente.length >= 1" class="barra-filtros-gerente">
        <!-- 1. Filtro de Estacionamentos -->
        <div class="seletor-multi-wrapper">
          <button
            type="button"
            class="btn-seletor-multi item-icone-texto"
            @click="dropdownMultiAberto = !dropdownMultiAberto; dropdownCidadeAberto = false"
          >
            <span class="item-icone-texto" style="min-width: 0">
              <IconParking :size="18" style="color: var(--destaque-azul); flex-shrink: 0" />
              <span class="texto-truncado-filtro">{{ textoBotaoSeletorTopo }}</span>
            </span>
            <IconSquareRoundedChevronDown :size="17" style="flex-shrink: 0" />
          </button>

          <Transition name="fade-pop">
            <div v-if="dropdownMultiAberto" class="dropdown-multi-box">
              <div v-if="mostrarPesquisaNoMulti" class="busca-multi-topo">
                <IconSearch :size="16" class="icone-busca-multi" />
                <input
                  v-model="termoBuscaMulti"
                  type="text"
                  placeholder="Pesquisar estacionamento..."
                />
              </div>

              <div class="lista-opcoes-multi">
                <div
                  class="item-opcao-multi destaque-completo"
                  :class="{ 'opcao-ativa': idsSelecionadosGerente.length === 0 }"
                  @click="selecionarDashboardCompleto"
                >
                  <span>Todos ({{ estabelecimentosDoGerentePorCidade.length }})</span>
                  <IconSquareRoundedCheck v-if="idsSelecionadosGerente.length === 0" :size="18" />
                </div>

                <div
                  v-for="est in listaEstabelecimentosNoMulti"
                  :key="est.id"
                  class="item-opcao-multi"
                  :class="{ 'opcao-ativa': idsSelecionadosGerente.includes(est.id) }"
                  @click="alternarSelecaoEstacionamento(est.id)"
                >
                  <span>{{ est.nome }} <small class="cidade-op-muted">({{ est.cidade || 'Sorocaba' }})</small></span>
                  <IconSquareRoundedCheck v-if="idsSelecionadosGerente.includes(est.id)" :size="18" />
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Filtro de Cidade -->
        <div class="seletor-multi-wrapper">
          <button
            type="button"
            class="btn-seletor-multi item-icone-texto"
            @click="dropdownCidadeAberto = !dropdownCidadeAberto; dropdownMultiAberto = false"
          >
            <span class="item-icone-texto" style="min-width: 0">
              <IconPin :size="17" style="color: var(--destaque-azul); flex-shrink: 0" />
              <span class="texto-truncado-filtro">
                {{
                  cidadeSelecionadaGerente === 'TODAS'
                    ? `Cidades (${cidadesDoGerente.length})`
                    : cidadeSelecionadaGerente
                }}
              </span>
            </span>
            <IconSquareRoundedChevronDown :size="17" style="flex-shrink: 0" />
          </button>

          <Transition name="fade-pop">
            <div v-if="dropdownCidadeAberto" class="dropdown-multi-box" style="width: 230px">
              <div class="lista-opcoes-multi">
                <div
                  class="item-opcao-multi destaque-completo"
                  :class="{ 'opcao-ativa': cidadeSelecionadaGerente === 'TODAS' }"
                  @click="selecionarCidadeGerente('TODAS'); dropdownCidadeAberto = false"
                >
                  <span>Todas as cidades ({{ cidadesDoGerente.length }})</span>
                  <IconSquareRoundedCheck v-if="cidadeSelecionadaGerente === 'TODAS'" :size="18" />
                </div>
                <div
                  v-for="cid in cidadesDoGerente"
                  :key="cid"
                  class="item-opcao-multi"
                  :class="{ 'opcao-ativa': cidadeSelecionadaGerente === cid }"
                  @click="selecionarCidadeGerente(cid); dropdownCidadeAberto = false"
                >
                  <span>{{ cid }}</span>
                  <IconSquareRoundedCheck v-if="cidadeSelecionadaGerente === cid" :size="18" />
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </header>

    <!-- CASO O GERENTE NÃO TENHA NENHUM ESTACIONAMENTO VINCULADO -->
    <div v-if="estabelecimentosDoGerente.length === 0" class="lista-card aviso-sem-estacionamento">
      <IconAlertSquareRounded :size="44" style="color: #f59e0b; margin-bottom: 10px" />
      <h2>Nenhum estacionamento vinculado à sua conta</h2>
      <p class="subtitulo">
        Solicite ao administrador do sistema (Admin Dev) que vincule seu usuário ao seu estacionamento nas Informações Gerais.
      </p>
    </div>

    <!-- CONTEÚDO PRINCIPAL DO DASHBOARD -->
    <template v-else>
      <!-- SEÇÃO SUPERIOR: EXATAMENTE OS 3 CARDS DE RELATÓRIOS -->
      <section class="secao-relatorios-dashboard">
        <div class="grade-kpis-gerente">
          <!-- Card 1: Fluxo Horário do Dia (Soma de Entradas e Saídas) -->
          <div class="card-kpi-gerente">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Fluxo Total por Hora (Hoje)</span>
              <div class="legenda-fluxo-mini">
                <span class="ponto-legenda ent"></span> Entradas
                <span class="ponto-legenda sai"></span> Saídas
              </div>
            </div>

            <div class="grafico-barras-horarias">
              <div
                v-for="item in metricasConsolidadas.fluxoPorHora"
                :key="item.hora"
                class="coluna-hora-item"
              >
                <div class="par-barras-verticais">
                  <div
                    class="barra-v ent"
                    :style="{ height: `${Math.max(10, (item.entradas / metricasConsolidadas.maiorValorFluxo) * 100)}%` }"
                    :title="`${item.hora} - Entradas: ${item.entradas}`"
                  >
                    <span class="valor-barra-topo">{{ item.entradas }}</span>
                  </div>
                  <div
                    class="barra-v sai"
                    :style="{ height: `${Math.max(10, (item.saidas / metricasConsolidadas.maiorValorFluxo) * 100)}%` }"
                    :title="`${item.hora} - Saídas: ${item.saidas}`"
                  >
                    <span class="valor-barra-topo">{{ item.saidas }}</span>
                  </div>
                </div>
                <span class="rotulo-hora-eixo">{{ item.hora }}</span>
              </div>
            </div>
          </div>

          <!-- Card 2: Taxa de Ocupação Atual (Soma de Livres e Ocupadas) -->
          <div class="card-kpi-gerente kpi-centralizado">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Taxa de Ocupação Atual</span>
              <IconParking :size="20" style="color: var(--destaque-azul)" />
            </div>

            <div class="kpi-valor-destaque">
              {{ metricasConsolidadas.taxaOcupacaoTotal }}%
            </div>

            <div class="barra-progresso-ocupacao">
              <div
                class="preenchimento-ocupacao"
                :style="{ width: `${metricasConsolidadas.taxaOcupacaoTotal}%` }"
              ></div>
            </div>

            <div class="kpi-rodape-duplo">
              <span class="tag-kpi livre">{{ metricasConsolidadas.vagasLivresSoma }} livres</span>
              <span class="tag-kpi ocupada">{{ metricasConsolidadas.vagasOcupadasSoma }} ocupadas</span>
            </div>
          </div>

          <!-- Card 3: Tempo Médio de Permanência no Dia -->
          <div class="card-kpi-gerente kpi-centralizado">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Tempo Médio de Permanência (Hoje)</span>
              <IconClock :size="20" style="color: #14b8a6" />
            </div>

            <div class="kpi-valor-destaque" style="color: #14b8a6">
              {{ metricasConsolidadas.tempoMedioFormatado }}
            </div>

            <p class="kpi-descricao-apoio">
              Média calculada sobre os veículos estacionados hoje
              <span v-if="metricasConsolidadas.qtdEstacionamentos > 1">
                ({{ metricasConsolidadas.qtdEstacionamentos }} unidades)
              </span>
            </p>
          </div>
          <div class="card-kpi-gerente kpi-apenas-tablet">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Fluxo por Hora Hoje (%)</span>
              <div class="legenda-fluxo-mini">
                <span class="ponto-legenda ent"></span> % Ent.
                <span class="ponto-legenda sai"></span> % Saí.
              </div>
            </div>

            <div class="grafico-barras-horarias">
              <div
                v-for="item in metricasConsolidadas.fluxoPorHora"
                :key="`tab-pct-${item.hora}`"
                class="coluna-hora-item"
              >
                <div class="par-barras-verticais">
                  <div
                    class="barra-v ent"
                    :style="{ height: `${Math.max(10, item.entPct)}%` }"
                    :title="`${item.hora} - Entradas: ${item.entPct}%`"
                  >
                    <span class="valor-barra-topo">{{ item.entPct }}%</span>
                  </div>
                  <div
                    class="barra-v sai"
                    :style="{ height: `${Math.max(10, item.saiPct)}%` }"
                    :title="`${item.hora} - Saídas: ${item.saiPct}%`"
                  >
                    <span class="valor-barra-topo">{{ item.saiPct }}%</span>
                  </div>
                </div>
                <span class="rotulo-hora-eixo">{{ item.hora }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="acoes-abaixo-relatorios">
          <button
            class="btn-secundario item-icone-texto"
            @click="router.push({ name: 'gerente-relatorios' })"
          >
            <IconChartBar :size="18" />
            <span>Ver relatórios em detalhe</span>
          </button>
        </div>
      </section>

      <!-- BOTÃO QUE ABRE POPUP DE ESTACIONAMENTOS PARA TABLETS E CELULARES (<= 1024px) -->
      <section class="secao-seletor-mobile-est">
        <div class="card-kpi-gerente seletor-mobile-est-wrapper">
          <div class="kpi-cabecalho">
            <span class="kpi-titulo">Visualizar Estacionamentos em Tela Cheia</span>
          </div>
          <button
            type="button"
            class="btn-primario item-icone-texto"
            style="width: 100%; justify-content: space-between"
            @click="modalMobileEstAberto = true"
          >
            <span class="item-icone-texto">
              <IconParking :size="19" />
              <span>Escolher Estacionamento ({{ estabelecimentosDoGerente.length }})</span>
            </span>
            <IconSquareRoundedChevronDown :size="19" />
          </button>
        </div>
      </section>

      <!-- MODAL POPUP DE SELEÇÃO DE ESTACIONAMENTO (TABLET / MOBILE) -->
      <Transition name="fade-pop">
        <div
          v-if="modalMobileEstAberto"
          class="modal-backdrop"
          @click.self="modalMobileEstAberto = false"
        >
          <div class="modal-box modal-escolher-est-mobile">
            <div class="overlay-header">
              <h3 class="item-icone-texto">
                <IconParking :size="20" />
                <span>Escolher Estacionamento</span>
              </h3>
              <button class="btn-fechar-mini" @click="modalMobileEstAberto = false">
                <IconSquareRoundedX :size="20" />
              </button>
            </div>

            <div class="busca-multi-topo" style="padding: 8px 0; border-bottom: none">
              <IconSearch :size="16" class="icone-busca-multi" style="left: 12px" />
              <input
                v-model="termoBuscaMobileEst"
                type="text"
                placeholder="Pesquisar estacionamento..."
              />
            </div>

            <div class="lista-opcoes-multi lista-modal-est-mobile">
              <div
                v-for="est in listaEstabelecimentosMobileBusca"
                :key="`mob-${est.id}`"
                class="item-opcao-multi"
                @click="abrirEstacionamentoTelaCheia(est.id)"
              >
                <span>{{ est.nome }}</span>
                <IconMaximize :size="16" />
              </div>
              <div v-if="listaEstabelecimentosMobileBusca.length === 0" class="item-dropdown-vazio">
                Nenhum estacionamento encontrado.
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- SEÇÃO INFERIOR PC (> 1024px): OS 2 MAIORES ESTACIONAMENTOS LADO A LADO -->
      <section class="secao-estacionamentos-dupla-pc">
        <div
          v-for="item in top2Estacionamentos"
          :key="item.est.id"
          class="card-estacionamento-preview"
        >
          <div class="header-preview-est">
            <div>
              <h3>{{ item.est.nome }}</h3>
              <span class="subtitulo-preview">
                Planta de Entrada/Saída: <strong>{{ item.andarPrincipal?.nome_andar }}</strong>
                — {{ item.metricas.ocupadas }}/{{ item.metricas.total }} ocupadas ({{ item.metricas.taxaOcupacao }}%)
              </span>
            </div>
            <span class="badge-total-vagas">{{ item.metricas.total }} vagas</span>
          </div>

          <div v-if="item.andarPrincipal" class="preview-mapa-scroll">
            <div
              class="grid-preview-mini"
              :style="{
                gridTemplateColumns: `repeat(${item.andarPrincipal.grid_x}, 24px)`
              }"
            >
              <template v-for="y in item.andarPrincipal.grid_y" :key="`prev-r-${y}`">
                <div
                  v-for="x in item.andarPrincipal.grid_x"
                  :key="`prev-c-${x}-${y}`"
                  class="celula-preview-fundo"
                  :style="{
                    backgroundColor: item.andarPrincipal.celulas[`${x},${y}`]?.corSetor || 'transparent'
                  }"
                >
                  <div
                    class="quadrado-preview-interno"
                    :class="{
                      'qp-vazio': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'VAZIO',
                      'qp-estrada': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'ESTRADA',
                      'qp-entrada': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'ENTRADA',
                      'qp-saida': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'SAIDA',
                      'qp-acesso': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'ACESSO',
                      'qp-vaga-inativa': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'VAGA' && item.andarPrincipal.celulas[`${x},${y}`]?.inativa,
                      'qp-vaga-amarela': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'VAGA' && !item.andarPrincipal.celulas[`${x},${y}`]?.inativa && !item.andarPrincipal.celulas[`${x},${y}`]?.macEsp,
                      'qp-vaga-livre': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'VAGA' && !item.andarPrincipal.celulas[`${x},${y}`]?.inativa && item.andarPrincipal.celulas[`${x},${y}`]?.macEsp && item.andarPrincipal.celulas[`${x},${y}`]?.livre,
                      'qp-vaga-ocupada': item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'VAGA' && !item.andarPrincipal.celulas[`${x},${y}`]?.inativa && item.andarPrincipal.celulas[`${x},${y}`]?.macEsp && !item.andarPrincipal.celulas[`${x},${y}`]?.livre
                    }"
                  >
                    <span v-if="item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'VAGA'">
                      {{ item.andarPrincipal.celulas[`${x},${y}`]?.identificador }}
                    </span>
                    <IconDoorEnter v-else-if="item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'ENTRADA'" :size="12" />
                    <IconDoorExit v-else-if="item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'SAIDA'" :size="12" />
                    <IconArrowBarRight v-else-if="item.andarPrincipal.celulas[`${x},${y}`]?.tipo === 'ACESSO'" :size="12" />
                  </div>
                </div>
              </template>
            </div>
          </div>

          <button
            class="btn-primario btn-ver-tela-cheia item-icone-texto"
            @click="abrirEstacionamentoTelaCheia(item.est.id)"
          >
            <IconMaximize :size="18" />
            <span>Ver em tela cheia</span>
          </button>
        </div>
      </section>
    </template>
  </div>
</template>
