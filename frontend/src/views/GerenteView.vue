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
  carregarDadosDoBanco
} from '../store/estacionamentoStore'
import {
  IconChartBar,
  IconClock,
  IconParking,
  IconMaximize,
  IconSearch,
  IconSquareRoundedChevronDown,
  IconSquareRoundedCheck,
  IconAlertSquareRounded,
  IconDoorEnter,
  IconDoorExit,
  IconArrowBarRight,
  IconPlayerPlay
} from '../icons'

const router = useRouter()

// Dropdown de seleção múltipla no topo
const dropdownMultiAberto = ref(false)
const termoBuscaMulti = ref('')

// Dropdown de busca para celular/tablet ("Visualizar estacionamentos")
const dropdownMobileEstAberto = ref(false)
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
  }
  if (!e.target.closest('.seletor-mobile-est-wrapper')) {
    dropdownMobileEstAberto.value = false
  }
}

// Regras do seletor do topo: 10 opções no PC (1 "Dashboard completo" + 9 estacionamentos)
const totalOpcoesFiltro = computed(() => 1 + estabelecimentosDoGerente.value.length)
const mostrarPesquisaNoMulti = computed(() => totalOpcoesFiltro.value > 5)

const listaEstabelecimentosNoMulti = computed(() => {
  const termo = termoBuscaMulti.value.trim().toLowerCase()
  if (!termo) return estabelecimentosDoGerente.value
  return estabelecimentosDoGerente.value.filter(e => e.nome.toLowerCase().includes(termo))
})

const textoBotaoSeletorTopo = computed(() => {
  const qtdSel = idsSelecionadosGerente.value.length
  const total = estabelecimentosDoGerente.value.length
  if (qtdSel === 0 || qtdSel === total) {
    return 'Dashboard completo (Todos)'
  }
  if (qtdSel === 1) {
    const est = estabelecimentosDoGerente.value.find(e => e.id === idsSelecionadosGerente.value[0])
    return est ? est.nome : '1 selecionado'
  }
  return `${qtdSel} estacionamentos selecionados (Média)`
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
// MÉTRICAS AGREGADAS / MÉDIAS DOS ESTACIONAMENTOS SELECIONADOS
// =========================================================
const metricasConsolidadas = computed(() => {
  const lista = estabelecimentosFiltradosGerente.value
  if (lista.length === 0) {
    return {
      taxaMediaOcupacao: 0,
      vagasLivresMedia: 0,
      vagasOcupadasMedia: 0,
      vagasTotaisMedia: 0,
      tempoMedioFormatado: '0min',
      tempoMedioMinutos: 0,
      fluxoPorHora: []
    }
  }

  let somaTaxa = 0
  let somaLivres = 0
  let somaOcupadas = 0
  let somaTotais = 0
  let somaTempoMin = 0

  lista.forEach((est) => {
    const m = contarVagasEstabelecimento(est)
    somaTaxa += m.taxaOcupacao
    somaLivres += m.livres
    somaOcupadas += m.ocupadas
    somaTotais += m.total
    somaTempoMin += m.tempoMedioMin
  })

  const divisor = lista.length
  const taxaMediaOcupacao = Math.round(somaTaxa / divisor)
  const vagasLivresMedia = Math.round(somaLivres / divisor)
  const vagasOcupadasMedia = Math.round(somaOcupadas / divisor)
  const vagasTotaisMedia = Math.round(somaTotais / divisor)
  const tempoMedioMinutos = Math.round(somaTempoMin / divisor)

  const horas = Math.floor(tempoMedioMinutos / 60)
  const mins = tempoMedioMinutos % 60
  const tempoMedioFormatado =
    tempoMedioMinutos === 0
      ? '0min'
      : horas > 0
        ? `${horas}h ${mins}min`
        : `${mins}min`

  // Gera série de Fluxo de Entradas e Saídas ao longo das horas do dia proporcional às vagas selecionadas
  const fatorEscala = Math.max(1, Math.round(vagasTotaisMedia / 12))
  const MultiplicadorSimulacao = simulacao1Ativa.value ? 1.4 : 0.75
  const horasBase = [
    { hora: '08h', entBase: 4, saiBase: 1 },
    { hora: '10h', entBase: 9, saiBase: 3 },
    { hora: '12h', entBase: 14, saiBase: 10 },
    { hora: '14h', entBase: 11, saiBase: 9 },
    { hora: '16h', entBase: 8, saiBase: 11 },
    { hora: '18h', entBase: 15, saiBase: 13 },
    { hora: '20h', entBase: 6, saiBase: 14 }
  ]

  const fluxoPorHora = horasBase.map((h) => {
    const entradas = Math.max(0, Math.round(h.entBase * fatorEscala * MultiplicadorSimulacao))
    const saidas = Math.max(0, Math.round(h.saiBase * fatorEscala * MultiplicadorSimulacao))
    const somaHora = Math.max(1, entradas + saidas)
    return {
      hora: h.hora,
      entradas,
      saidas,
      entPct: Math.round((entradas / somaHora) * 100),
      saiPct: Math.round((saidas / somaHora) * 100)
    }
  })

  const maiorValorFluxo = Math.max(10, ...fluxoPorHora.flatMap(f => [f.entradas, f.saidas]))

  return {
    qtdEstacionamentos: divisor,
    taxaMediaOcupacao,
    vagasLivresMedia,
    vagasOcupadasMedia,
    vagasTotaisMedia,
    tempoMedioFormatado,
    tempoMedioMinutos,
    fluxoPorHora,
    maiorValorFluxo
  }
})

// Os 2 estacionamentos com maior número de vagas cadastradas (para exibir na linha inferior do PC)
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
          <p class="subtitulo">Painel de controle operacional e indicadores em tempo real</p>
        </div>

        <div class="gerente-atalhos-topo">
          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-simulacao-ativa': simulacao1Ativa }"
            title="Preenche 60% das vagas como ocupadas e gera usos de 1 a 10 no frontend"
            @click="alternarSimulacao1Frontend"
          >
            <IconPlayerPlay :size="17" />
            <span>{{ simulacao1Ativa ? 'Simulação 1: ATIVA' : 'Simulação 1' }}</span>
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

      <!-- Seletor Múltiplo de Estacionamentos (Oculto caso tenha apenas 1 estacionamento) -->
      <div v-if="estabelecimentosDoGerente.length >= 2" class="seletor-multi-wrapper">
        <button
          type="button"
          class="btn-seletor-multi item-icone-texto"
          @click="dropdownMultiAberto = !dropdownMultiAberto"
        >
          <IconParking :size="18" />
          <span>{{ textoBotaoSeletorTopo }}</span>
          <IconSquareRoundedChevronDown :size="18" />
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
                <span>Dashboard completo</span>
                <IconSquareRoundedCheck v-if="idsSelecionadosGerente.length === 0" :size="18" />
              </div>

              <div
                v-for="est in listaEstabelecimentosNoMulti"
                :key="est.id"
                class="item-opcao-multi"
                :class="{ 'opcao-ativa': idsSelecionadosGerente.includes(est.id) }"
                @click="alternarSelecaoEstacionamento(est.id)"
              >
                <span>{{ est.nome }}</span>
                <IconSquareRoundedCheck v-if="idsSelecionadosGerente.includes(est.id)" :size="18" />
              </div>
            </div>
          </div>
        </Transition>
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
      <!-- SEÇÃO SUPERIOR (30-40%): LINHA DE RELATÓRIOS PRINCIPAIS -->
      <section class="secao-relatorios-dashboard">
        <div class="grade-kpis-gerente">
          <!-- Card 1: Fluxo Horário do Dia (Número Bruto de Entradas e Saídas) -->
          <div class="card-kpi-gerente">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Fluxo por Hora Hoje (Nº Bruto)</span>
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
                    :style="{ height: `${Math.max(8, (item.entradas / metricasConsolidadas.maiorValorFluxo) * 100)}%` }"
                    :title="`${item.hora} - Entradas: ${item.entradas}`"
                  >
                    <span class="valor-barra-topo">{{ item.entradas }}</span>
                  </div>
                  <div
                    class="barra-v sai"
                    :style="{ height: `${Math.max(8, (item.saidas / metricasConsolidadas.maiorValorFluxo) * 100)}%` }"
                    :title="`${item.hora} - Saídas: ${item.saidas}`"
                  >
                    <span class="valor-barra-topo">{{ item.saidas }}</span>
                  </div>
                </div>
                <span class="rotulo-hora-eixo">{{ item.hora }}</span>
              </div>
            </div>
          </div>

          <!-- Card 2: Taxa de Ocupação Atual -->
          <div class="card-kpi-gerente kpi-centralizado">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Taxa de Ocupação Atual</span>
              <IconParking :size="20" style="color: var(--destaque-azul)" />
            </div>

            <div class="kpi-valor-destaque">
              {{ metricasConsolidadas.taxaMediaOcupacao }}%
            </div>

            <div class="barra-progresso-ocupacao">
              <div
                class="preenchimento-ocupacao"
                :style="{ width: `${metricasConsolidadas.taxaMediaOcupacao}%` }"
              ></div>
            </div>

            <div class="kpi-rodape-duplo">
              <span class="tag-kpi livre">{{ metricasConsolidadas.vagasLivresMedia }} livres</span>
              <span class="tag-kpi ocupada">{{ metricasConsolidadas.vagasOcupadasMedia }} ocupadas</span>
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

          <!-- Card 4 (Exibido apenas em Tablets <= 1024px para fechar 2 linhas de 2 cards) -->
          <div class="card-kpi-gerente kpi-apenas-tablet">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Proporção Entradas vs. Saídas (%)</span>
              <IconChartBar :size="20" style="color: #f59e0b" />
            </div>
            <div class="lista-proporcao-horas">
              <div
                v-for="item in metricasConsolidadas.fluxoPorHora.slice(0, 4)"
                :key="`pct-${item.hora}`"
                class="linha-proporcao-item"
              >
                <span class="hora-pct">{{ item.hora }}</span>
                <div class="barra-pct-dupla">
                  <div class="fatia-ent" :style="{ width: `${item.entPct}%` }">
                    {{ item.entPct }}%
                  </div>
                  <div class="fatia-sai" :style="{ width: `${item.saiPct}%` }">
                    {{ item.saiPct }}%
                  </div>
                </div>
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

      <!-- SELETOR DE ESTACIONAMENTOS PARA TABLETS E CELULARES (<= 1024px) -->
      <section class="secao-seletor-mobile-est">
        <div class="card-kpi-gerente seletor-mobile-est-wrapper">
          <div class="kpi-cabecalho">
            <strong>Visualizar Estacionamentos em Tela Cheia</strong>
          </div>
          <button
            type="button"
            class="btn-primario item-icone-texto"
            style="width: 100%; justify-content: space-between"
            @click="dropdownMobileEstAberto = !dropdownMobileEstAberto"
          >
            <span class="item-icone-texto">
              <IconParking :size="19" />
              <span>Escolher Estacionamento ({{ estabelecimentosDoGerente.length }})</span>
            </span>
            <IconSquareRoundedChevronDown :size="19" />
          </button>

          <Transition name="fade-pop">
            <div v-if="dropdownMobileEstAberto" class="dropdown-mobile-est-box">
              <div class="busca-multi-topo">
                <IconSearch :size="16" class="icone-busca-multi" />
                <input
                  v-model="termoBuscaMobileEst"
                  type="text"
                  placeholder="Pesquisar estacionamento..."
                />
              </div>
              <div class="lista-opcoes-multi">
                <div
                  v-for="est in listaEstabelecimentosMobileBusca"
                  :key="`mob-${est.id}`"
                  class="item-opcao-multi"
                  @click="abrirEstacionamentoTelaCheia(est.id)"
                >
                  <span>{{ est.nome }}</span>
                  <IconMaximize :size="16" />
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </section>

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