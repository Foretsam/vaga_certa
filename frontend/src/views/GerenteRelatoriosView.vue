<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  estabelecimentosDoGerente,
  estabelecimentosFiltradosGerente,
  idsSelecionadosGerente,
  simulacao1Ativa,
  alternarSimulacao1Frontend,
  contarVagasEstabelecimento,
  carregarDadosDoBanco
} from '../store/estacionamentoStore'
import {
  IconChartBar,
  IconClock,
  IconParking,
  IconSearch,
  IconSquareRoundedChevronDown,
  IconSquareRoundedChevronLeft,
  IconSquareRoundedChevronRight,
  IconSquareRoundedArrowLeft,
  IconSquareRoundedCheck,
  IconSquareRoundedX,
  IconDownload,
  IconArrowsLeftRight,
  IconPlayerPlay,
  IconFlame,
  IconLayoutBoard
} from '../icons'

const router = useRouter()

// Dropdown de seleção múltipla no topo
const dropdownMultiAberto = ref(false)
const termoBuscaMulti = ref('')

// Comparador de 2 Estacionamentos
const idCompararA = ref(null)
const idCompararB = ref(null)

// Paginação e filtro do Histórico Detalhado
const buscaHistorico = ref('')
const paginaHistorico = ref(1)
const itensPorPaginaHistorico = 8

// Datas padrão (Hoje e 7 dias atrás)
const hojeIso = new Date().toISOString().slice(0, 10)
const seteDiasAtrasIso = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10)
const ontemIso = new Date(Date.now() - 86400000).toISOString().slice(0, 10)

// Seção de Exportação Completa
const dataInicioCompleto = ref(seteDiasAtrasIso)
const dataFimCompleto = ref(hojeIso)
const atalhoPeriodoCompleto = ref('')

// Modal Popup de Exportação Individual
const modalExportarAberto = ref(false)
const relatorioAlvoExportacao = ref({ chave: '', titulo: '' })
const dataInicioModal = ref(seteDiasAtrasIso)
const dataFimModal = ref(hojeIso)
const atalhoPeriodoModal = ref('')

onMounted(async () => {
  if (estabelecimentosDoGerente.value.length === 0) {
    await carregarDadosDoBanco()
  }
  inicializarComparador()
  window.addEventListener('click', fecharDropdownsAoClicarFora)
})

onUnmounted(() => {
  window.removeEventListener('click', fecharDropdownsAoClicarFora)
})

watch(estabelecimentosDoGerente, () => {
  inicializarComparador()
})

function inicializarComparador() {
  const lista = estabelecimentosDoGerente.value
  if (lista.length >= 1 && !idCompararA.value) {
    idCompararA.value = lista[0].id
  }
  if (lista.length >= 2 && !idCompararB.value) {
    idCompararB.value = lista[1].id
  } else if (lista.length === 1 && !idCompararB.value) {
    idCompararB.value = lista[0].id
  }
}

function fecharDropdownsAoClicarFora(e) {
  if (!e.target.closest('.seletor-multi-wrapper')) {
    dropdownMultiAberto.value = false
  }
}

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
    return `Todos (${total})`
  }
  if (qtdSel === 1) {
    const est = estabelecimentosDoGerente.value.find(e => e.id === idsSelecionadosGerente.value[0])
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
// DADOS ANALÍTICOS SOMADOS DOS ESTACIONAMENTOS SELECIONADOS
// =========================================================
const faixasHorariasPadrao = [
  { hora: '08h', entBase: 2, saiBase: 1 },
  { hora: '10h', entBase: 4, saiBase: 2 },
  { hora: '12h', entBase: 7, saiBase: 5 },
  { hora: '14h', entBase: 5, saiBase: 4 },
  { hora: '16h', entBase: 4, saiBase: 6 },
  { hora: '18h', entBase: 8, saiBase: 7 },
  { hora: '20h', entBase: 3, saiBase: 6 },
  { hora: '22h', entBase: 2, saiBase: 4 }
]

const dadosRelatorios = computed(() => {
  const lista = estabelecimentosFiltradosGerente.value
  if (lista.length === 0) {
    return {
      taxaOcupacao: 0,
      vagasLivres: 0,
      vagasOcupadas: 0,
      vagasTotais: 0,
      totalVeiculosDia: 0,
      tempoMedioFormatado: '0min',
      horarioPico: '18h',
      fluxoPorHora: [],
      maiorValorFluxo: 10,
      rankingSetores: [],
      rankingVagas: [],
      historicoDetalhado: []
    }
  }

  let somaLivres = 0
  let somaOcupadas = 0
  let somaTotais = 0
  let somaInativas = 0
  let somaTempoMin = 0
  let somaUsosDia = 0

  const listaSetoresRanking = []
  const listaVagasRanking = []
  const historicoGerado = []

  const mapaSomaHoras = faixasHorariasPadrao.map(f => ({
    hora: f.hora,
    entradas: 0,
    saidas: 0,
    entPct: 50,
    saiPct: 50
  }))

  const multSim = simulacao1Ativa.value ? 1.6 : 1

  lista.forEach((est) => {
    const m = contarVagasEstabelecimento(est)
    somaLivres += m.livres
    somaOcupadas += m.ocupadas
    somaTotais += m.total
    somaInativas += m.inativas
    somaTempoMin += m.tempoMedioMin
    somaUsosDia += m.somaUsosDia

    const pesoVagas = Math.max(1, Math.round(m.total / 3))
    const variacaoId = (Number(est.id) % 3) + 1

    faixasHorariasPadrao.forEach((f, idx) => {
      const ajusteHora = ((Number(est.id) + idx) % 2 === 0) ? 1 : 0
      mapaSomaHoras[idx].entradas += Math.max(
        1,
        Math.round((f.entBase * pesoVagas + variacaoId + ajusteHora) * multSim)
      )
      mapaSomaHoras[idx].saidas += Math.max(
        1,
        Math.round((f.saiBase * pesoVagas + (variacaoId - 1) + ajusteHora) * multSim)
      )
    })

    ;(est.andares || []).forEach((andar) => {
      const celulas = Object.values(andar.celulas || {})

      ;(andar.setores || []).forEach((setor, sIdx) => {
        const vagasSetor = celulas.filter(c => c.tipo === 'VAGA' && c.setorId === setor.id_setor)
        const totalS = vagasSetor.length
        const ocupS = vagasSetor.filter(v => !v.inativa && !v.livre).length
        const usosSetor = vagasSetor.reduce(
          (acc, v) => acc + (v.usosNoDia || (simulacao1Ativa.value ? 4 : 2) + (sIdx % 3)),
          0
        )
        listaSetoresRanking.push({
          estacionamento: est.nome,
          andar: andar.nome_andar,
          setor: `${setor.nome_setor} (${setor.prefixo})`,
          cor: setor.cor_hex,
          vagasTotais: totalS,
          ocupadasAgora: ocupS,
          giroDiario: usosSetor,
          taxaOcupacao: totalS > 0 ? Math.round((ocupS / totalS) * 100) : 0
        })
      })

      celulas
        .filter(c => c.tipo === 'VAGA')
        .forEach((v, vIdx) => {
          const giros = v.usosNoDia || (simulacao1Ativa.value ? ((vIdx * 3) % 9) + 2 : ((vIdx * 2) % 5) + 1)
          const duracaoMedia = v.duracaoMinutos || ((vIdx * 17) % 95) + 35

          listaVagasRanking.push({
            identificador: v.identificador || `V${vIdx + 1}`,
            setor: v.nomeSetor || 'Geral',
            andar: andar.nome_andar,
            estacionamento: est.nome,
            usosHoje: giros,
            tempoMedioMin: duracaoMedia,
            statusAtual: v.inativa ? 'Inativa' : v.livre ? 'Livre' : 'Ocupada'
          })

          const horaBase = 8 + (vIdx % 11)
          const minBase = (vIdx * 7) % 60
          const entradaStr = `${hojeIso} ${String(horaBase).padStart(2, '0')}:${String(minBase).padStart(2, '0')}`
          const horaSaida = Math.min(23, horaBase + Math.floor(duracaoMedia / 60))
          const minSaida = (minBase + (duracaoMedia % 60)) % 60
          const saidaStr = v.livre
            ? `${hojeIso} ${String(horaSaida).padStart(2, '0')}:${String(minSaida).padStart(2, '0')}`
            : 'Em andamento'

          historicoGerado.push({
            id: `${est.id}-${andar.id_andar}-${v.identificador}-${vIdx}`,
            estacionamento: est.nome,
            andar: andar.nome_andar,
            setor: v.nomeSetor || 'Geral',
            vaga: v.identificador || `V${vIdx + 1}`,
            dataEntrada: entradaStr,
            dataSaida: saidaStr,
            permanenciaMin: duracaoMedia,
            permanenciaTexto: formatarMinutos(duracaoMedia)
          })
        })
    })
  })

  const vagasAtivasSoma = Math.max(1, somaTotais - somaInativas)
  const taxaOcupacao = somaTotais > 0 ? Math.round((somaOcupadas / vagasAtivasSoma) * 100) : 0
  const tempoMedioMin = Math.round(somaTempoMin / lista.length) || 68

  const fluxoPorHora = mapaSomaHoras.map((item) => {
    const somaHora = Math.max(1, item.entradas + item.saidas)
    const entPct = Math.round((item.entradas / somaHora) * 100)
    return {
      hora: item.hora,
      entradas: item.entradas,
      saidas: item.saidas,
      entPct,
      saiPct: 100 - entPct
    }
  })

  const maiorValorFluxo = Math.max(10, ...fluxoPorHora.flatMap(f => [f.entradas, f.saidas]))
  const picoObj = [...fluxoPorHora].sort((a, b) => (b.entradas + b.saidas) - (a.entradas + a.saidas))[0]

  // Soma real de todos os veículos dos estacionamentos selecionados hoje
  const totalVeiculosDia =
    somaUsosDia > 0
      ? somaUsosDia
      : fluxoPorHora.reduce((acc, f) => acc + f.entradas, 0)

  listaSetoresRanking.sort((a, b) => b.giroDiario - a.giroDiario)
  listaVagasRanking.sort((a, b) => b.usosHoje - a.usosHoje)

  return {
    taxaOcupacao,
    vagasLivres: somaLivres,
    vagasOcupadas: somaOcupadas,
    vagasTotais: somaTotais,
    totalVeiculosDia,
    tempoMedioFormatado: formatarMinutos(tempoMedioMin),
    horarioPico: picoObj ? picoObj.hora : '18h',
    fluxoPorHora,
    maiorValorFluxo,
    rankingSetores: listaSetoresRanking.slice(0, 6),
    rankingVagas: listaVagasRanking.slice(0, 8),
    historicoDetalhado: historicoGerado
  }
})

function formatarMinutos(mins) {
  if (!mins || mins <= 0) return '0min'
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h > 0 ? `${h}h ${m}min` : `${m}min`
}

// =========================================================
// COMPARADOR LADO A LADO DE 2 ESTACIONAMENTOS
// =========================================================
function calcularResumoComparativo(idEst) {
  const est = estabelecimentosDoGerente.value.find(e => e.id === Number(idEst))
  if (!est) return null
  const m = contarVagasEstabelecimento(est)
  const qtdSetores = (est.andares || []).reduce((acc, a) => acc + (a.setores?.length || 0), 0)
  const giroEstimado = m.somaUsosDia > 0 ? m.somaUsosDia : Math.max(12, m.total * 3)

  return {
    id: est.id,
    nome: est.nome,
    andares: est.andares?.length || 0,
    setores: qtdSetores,
    totalVagas: m.total,
    livres: m.livres,
    ocupadas: m.ocupadas,
    inativas: m.inativas,
    taxaOcupacao: m.taxaOcupacao,
    tempoMedio: formatarMinutos(m.tempoMedioMin || 72),
    giroDiario: giroEstimado
  }
}

const comparativoA = computed(() => calcularResumoComparativo(idCompararA.value))
const comparativoB = computed(() => calcularResumoComparativo(idCompararB.value))

// =========================================================
// TABELA PAGINADA DO HISTÓRICO DETALHADO
// =========================================================
const historicoFiltrado = computed(() => {
  const termo = buscaHistorico.value.trim().toLowerCase()
  const lista = dadosRelatorios.value.historicoDetalhado
  if (!termo) return lista
  return lista.filter(
    item =>
      item.vaga.toLowerCase().includes(termo) ||
      item.setor.toLowerCase().includes(termo) ||
      item.estacionamento.toLowerCase().includes(termo)
  )
})

const totalPaginasHistorico = computed(() =>
  Math.max(1, Math.ceil(historicoFiltrado.value.length / itensPorPaginaHistorico))
)

const historicoPaginado = computed(() => {
  const inicio = (paginaHistorico.value - 1) * itensPorPaginaHistorico
  return historicoFiltrado.value.slice(inicio, inicio + itensPorPaginaHistorico)
})

// =========================================================
// ATALHOS DE DATA E EXPORTAÇÃO CSV (PADRÃO BRASILEIRO ';')
// =========================================================
function selecionarAtalhoCompleto(tipo) {
  if (atalhoPeriodoCompleto.value === tipo) {
    atalhoPeriodoCompleto.value = ''
    return
  }
  atalhoPeriodoCompleto.value = tipo
  if (tipo === 'ULTIMO_DIA') {
    dataInicioCompleto.value = ontemIso
    dataFimCompleto.value = hojeIso
  } else if (tipo === 'ULTIMA_SEMANA') {
    dataInicioCompleto.value = seteDiasAtrasIso
    dataFimCompleto.value = hojeIso
  }
}

function selecionarAtalhoModal(tipo) {
  if (atalhoPeriodoModal.value === tipo) {
    atalhoPeriodoModal.value = ''
    return
  }
  atalhoPeriodoModal.value = tipo
  if (tipo === 'ULTIMO_DIA') {
    dataInicioModal.value = ontemIso
    dataFimModal.value = hojeIso
  } else if (tipo === 'ULTIMA_SEMANA') {
    dataInicioModal.value = seteDiasAtrasIso
    dataFimModal.value = hojeIso
  }
}

function abrirModalExportarIndividual(chave, titulo) {
  relatorioAlvoExportacao.value = { chave, titulo }
  atalhoPeriodoModal.value = ''
  dataInicioModal.value = seteDiasAtrasIso
  dataFimModal.value = hojeIso
  modalExportarAberto.value = true
}

function obterLinhasRelatorioPorChave(chave, dtIni, dtFim) {
  const d = dadosRelatorios.value
  const periodoStr = `${dtIni} ate ${dtFim}`

  if (chave === 'FLUXO_BRUTO') {
    return [
      ['Periodo', 'Faixa Horaria', 'Entradas (Bruto)', 'Saidas (Bruto)', 'Total Movimentacoes'],
      ...d.fluxoPorHora.map(f => [periodoStr, f.hora, f.entradas, f.saidas, f.entradas + f.saidas])
    ]
  }
  if (chave === 'FLUXO_PCT') {
    return [
      ['Periodo', 'Faixa Horaria', 'Entradas (%)', 'Saidas (%)'],
      ...d.fluxoPorHora.map(f => [periodoStr, f.hora, `${f.entPct}%`, `${f.saiPct}%`])
    ]
  }
  if (chave === 'RANKING_SETORES') {
    return [
      ['Periodo', 'Estacionamento', 'Andar', 'Setor', 'Vagas Totais', 'Ocupadas Agora', 'Taxa Ocupacao (%)', 'Giro Diario'],
      ...d.rankingSetores.map(s => [
        periodoStr,
        s.estacionamento,
        s.andar,
        s.setor,
        s.vagasTotais,
        s.ocupadasAgora,
        `${s.taxaOcupacao}%`,
        s.giroDiario
      ])
    ]
  }
  if (chave === 'RANKING_VAGAS') {
    return [
      ['Periodo', 'Vaga', 'Setor', 'Andar', 'Estacionamento', 'Usos no Dia', 'Tempo Medio (min)', 'Status Atual'],
      ...d.rankingVagas.map(v => [
        periodoStr,
        v.identificador,
        v.setor,
        v.andar,
        v.estacionamento,
        v.usosHoje,
        v.tempoMedioMin,
        v.statusAtual
      ])
    ]
  }
  if (chave === 'COMPARATIVO') {
    const a = comparativoA.value
    const b = comparativoB.value
    return [
      ['Indicador', a ? a.nome : 'Unidade A', b ? b.nome : 'Unidade B'],
      ['Periodo Analisado', periodoStr, periodoStr],
      ['Total de Vagas', a?.totalVagas ?? 0, b?.totalVagas ?? 0],
      ['Vagas Livres', a?.livres ?? 0, b?.livres ?? 0],
      ['Vagas Ocupadas', a?.ocupadas ?? 0, b?.ocupadas ?? 0],
      ['Taxa de Ocupacao (%)', `${a?.taxaOcupacao ?? 0}%`, `${b?.taxaOcupacao ?? 0}%`],
      ['Tempo Medio de Permanencia', a?.tempoMedio ?? '0min', b?.tempoMedio ?? '0min'],
      ['Giro Diario de Veiculos', a?.giroDiario ?? 0, b?.giroDiario ?? 0]
    ]
  }
  if (chave === 'HISTORICO') {
    return [
      ['Estacionamento', 'Andar', 'Setor', 'Vaga', 'Data/Hora Entrada', 'Data/Hora Saida', 'Permanencia'],
      ...d.historicoDetalhado.map(h => [
        h.estacionamento,
        h.andar,
        h.setor,
        h.vaga,
        h.dataEntrada,
        h.dataSaida,
        h.permanenciaTexto
      ])
    ]
  }
  return [
    ['Indicador', 'Valor', 'Periodo'],
    ['Taxa de Ocupacao Atual', `${d.taxaOcupacao}%`, periodoStr],
    ['Vagas Livres (Soma)', d.vagasLivres, periodoStr],
    ['Vagas Ocupadas (Soma)', d.vagasOcupadas, periodoStr],
    ['Total de Veiculos no Dia (Soma)', d.totalVeiculosDia, periodoStr],
    ['Tempo Medio de Permanencia', d.tempoMedioFormatado, periodoStr],
    ['Horario de Maior Pico', d.horarioPico, periodoStr]
  ]
}

function dispararDownloadArquivo(conteudo, nomeArquivo, mimeType) {
  const blob = new Blob([conteudo], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = nomeArquivo
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function formatarLinhasParaCsvBrasil(linhas) {
  return linhas
    .map(row => row.map(val => `"${String(val ?? '').replace(/"/g, '""')}"`).join(';'))
    .join('\r\n')
}

function confirmarExportacaoCsvIndividual() {
  const { chave, titulo } = relatorioAlvoExportacao.value
  const linhas = obterLinhasRelatorioPorChave(chave, dataInicioModal.value, dataFimModal.value)
  const csvContent = '\uFEFF' + formatarLinhasParaCsvBrasil(linhas)

  const slug = titulo.toLowerCase().replace(/[^a-z0-9]+/g, '_')
  dispararDownloadArquivo(
    csvContent,
    `vaga_certa_${slug}_${dataInicioModal.value}_${dataFimModal.value}.csv`,
    'text/csv;charset=utf-8;'
  )
  modalExportarAberto.value = false
}

// Exporta TODOS os relatórios em um único arquivo .CSV padrão brasileiro (separado por ponto e vírgula ';')
function exportarRelatorioCompletoCsvPadrao() {
  const dtIni = dataInicioCompleto.value
  const dtFim = dataFimCompleto.value

  const secoes = [
    { titulo: '1. RESUMO DE KPIS', chave: 'RESUMO' },
    { titulo: '2. FLUXO POR HORA (NUMERO BRUTO)', chave: 'FLUXO_BRUTO' },
    { titulo: '3. FLUXO POR HORA (PORCENTAGEM)', chave: 'FLUXO_PCT' },
    { titulo: '4. RANKING DE SETORES', chave: 'RANKING_SETORES' },
    { titulo: '5. RANKING DE VAGAS', chave: 'RANKING_VAGAS' },
    { titulo: '6. COMPARATIVO DE UNIDADES', chave: 'COMPARATIVO' },
    { titulo: '7. HISTORICO DETALHADO DE OCUPACAO', chave: 'HISTORICO' }
  ]

  const blocosCsv = secoes.map((secao) => {
    const linhas = obterLinhasRelatorioPorChave(secao.chave, dtIni, dtFim)
    return `"=== ${secao.titulo} ==="\r\n` + formatarLinhasParaCsvBrasil(linhas)
  })

  const conteudoFinal = '\uFEFF' + blocosCsv.join('\r\n\r\n')
  dispararDownloadArquivo(
    conteudoFinal,
    `vaga_certa_relatorio_completo_BI_${dtIni}_a_${dtFim}.csv`,
    'text/csv;charset=utf-8;'
  )
}
</script>

<template>
  <div class="gerente-dashboard-container">
    <!-- CABEÇALHO DO TOPO + SELETOR MULTI-ESTACIONAMENTOS ALINHADO COM OS CARDS -->
    <header class="gerente-header-topo">
      <div class="gerente-boas-vindas">
        <div>
          <h1>Relatórios Detalhados e Exportação BI</h1>
          <p class="subtitulo">
            Análise de fluxo horário, permanência, rotatividade de vagas e comparativo entre unidades
          </p>
        </div>

        <div class="gerente-atalhos-topo">
          <button
            class="btn-secundario item-icone-texto"
            :class="{ 'btn-simulacao-ativa': simulacao1Ativa }"
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
            class="btn-secundario item-icone-texto"
            @click="router.push({ name: 'gerente' })"
          >
            <IconSquareRoundedArrowLeft :size="18" />
            <span>Voltar ao Dashboard</span>
          </button>
        </div>
      </div>

      <!-- Seletor Múltiplo alinhado à esquerda junto com os cards -->
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
                <span>Todos</span>
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

    <!-- 1. LINHA DE INDICADORES GERAIS (KPIs) -->
    <section class="grade-quatro-kpis-relatorio">
      <div class="card-kpi-gerente kpi-compacto">
        <div class="kpi-cabecalho">
          <span class="kpi-titulo">Taxa de Ocupação Atual</span>
          <IconParking :size="19" style="color: var(--destaque-azul)" />
        </div>
        <div class="kpi-valor-destaque">{{ dadosRelatorios.taxaOcupacao }}%</div>
        <div class="kpi-rodape-duplo">
          <span class="tag-kpi livre">{{ dadosRelatorios.vagasLivres }} livres</span>
          <span class="tag-kpi ocupada">{{ dadosRelatorios.vagasOcupadas }} ocupadas</span>
        </div>
      </div>

      <div class="card-kpi-gerente kpi-compacto">
        <div class="kpi-cabecalho">
          <span class="kpi-titulo">Total de Veículos Hoje</span>
          <IconChartBar :size="19" style="color: #22c55e" />
        </div>
        <div class="kpi-valor-destaque" style="color: #22c55e">
          {{ dadosRelatorios.totalVeiculosDia }}
        </div>
        <p class="kpi-descricao-apoio">Soma de entradas registradas hoje</p>
      </div>

      <div class="card-kpi-gerente kpi-compacto">
        <div class="kpi-cabecalho">
          <span class="kpi-titulo">Tempo Médio de Permanência</span>
          <IconClock :size="19" style="color: #14b8a6" />
        </div>
        <div class="kpi-valor-destaque" style="color: #14b8a6">
          {{ dadosRelatorios.tempoMedioFormatado }}
        </div>
        <p class="kpi-descricao-apoio">Duração média por estadia concluída</p>
      </div>

      <div class="card-kpi-gerente kpi-compacto">
        <div class="kpi-cabecalho">
          <span class="kpi-titulo">Horário de Maior Pico</span>
          <IconFlame :size="19" style="color: #f97316" />
        </div>
        <div class="kpi-valor-destaque" style="color: #f97316">
          {{ dadosRelatorios.horarioPico }}
        </div>
        <p class="kpi-descricao-apoio">Faixa com maior volume de movimentações</p>
      </div>
    </section>

    <!-- 2. FLUXO AO LONGO DAS HORAS DO DIA (NÚMERO BRUTO vs. PORCENTAGEM EM GRÁFICO DE BARRAS) -->
    <section class="grade-dupla-relatorios">
      <!-- Relatório A: Fluxo Horário em Número Bruto -->
      <div class="card-relatorio-bloco">
        <div class="header-relatorio-bloco">
          <div>
            <h3>Fluxo Total por Hora (Hoje)</h3>
            <p class="dica-painel">Soma de veículos entrando e saindo por faixa horária</p>
          </div>
          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportarIndividual('FLUXO_BRUTO', 'Fluxo Horário Bruto')"
          >
            <IconDownload :size="16" />
            <span>Exportar</span>
          </button>
        </div>

        <div class="grafico-barras-horarias grafico-relatorio-maior">
          <div
            v-for="item in dadosRelatorios.fluxoPorHora"
            :key="`bruto-${item.hora}`"
            class="coluna-hora-item"
          >
            <div class="par-barras-verticais">
              <div
                class="barra-v ent"
                :style="{ height: `${Math.max(10, (item.entradas / dadosRelatorios.maiorValorFluxo) * 100)}%` }"
                :title="`${item.hora} - Entradas: ${item.entradas}`"
              >
                <span class="valor-barra-topo">{{ item.entradas }}</span>
              </div>
              <div
                class="barra-v sai"
                :style="{ height: `${Math.max(10, (item.saidas / dadosRelatorios.maiorValorFluxo) * 100)}%` }"
                :title="`${item.hora} - Saídas: ${item.saidas}`"
              >
                <span class="valor-barra-topo">{{ item.saidas }}</span>
              </div>
            </div>
            <span class="rotulo-hora-eixo">{{ item.hora }}</span>
          </div>
        </div>

        <div class="legenda-fluxo-mini" style="justify-content: center; margin-top: 8px">
          <span><i class="ponto-legenda ent"></i> Entradas (veículos)</span>
          <span><i class="ponto-legenda sai"></i> Saídas (veículos)</span>
        </div>
      </div>

      <!-- Relatório B: Fluxo Horário em Porcentagem (%) em Gráfico de Barras Verticais -->
      <div class="card-relatorio-bloco">
        <div class="header-relatorio-bloco">
          <div>
            <h3>Fluxo em % por Hora (Hoje)</h3>
            <p class="dica-painel">Gráfico comparativo percentual entre entradas e saídas por hora</p>
          </div>
          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportarIndividual('FLUXO_PCT', 'Fluxo Horário Percentual')"
          >
            <IconDownload :size="16" />
            <span>Exportar</span>
          </button>
        </div>

        <div class="grafico-barras-horarias grafico-relatorio-maior">
          <div
            v-for="item in dadosRelatorios.fluxoPorHora"
            :key="`pct-rel-${item.hora}`"
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

        <div class="legenda-fluxo-mini" style="justify-content: center; margin-top: 8px">
          <span><i class="ponto-legenda ent"></i> % de Entradas</span>
          <span><i class="ponto-legenda sai"></i> % de Saídas</span>
        </div>
      </div>
    </section>

    <!-- 3. RANKING DE SETORES E RANKING DE VAGAS COM MAIOR ROTATIVIDADE -->
    <section class="grade-dupla-relatorios">
      <div class="card-relatorio-bloco">
        <div class="header-relatorio-bloco">
          <div>
            <h3>Ranking de Setores com Maior Rotatividade</h3>
            <p class="dica-painel">Setores ordenados pelo giro total de veículos e taxa de ocupação</p>
          </div>
          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportarIndividual('RANKING_SETORES', 'Ranking de Setores')"
          >
            <IconDownload :size="16" />
            <span>Exportar</span>
          </button>
        </div>

        <div class="tabela-responsiva-wrapper">
          <table class="tabela-relatorio">
            <thead>
              <tr>
                <th>Setor</th>
                <th>Unidade / Andar</th>
                <th>Ocupação</th>
                <th>Giro Diário</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(s, idx) in dadosRelatorios.rankingSetores" :key="`rk-s-${idx}`">
                <td>
                  <span class="item-icone-texto" style="justify-content: flex-start">
                    <span class="bolinha-cor-setor" :style="{ backgroundColor: s.cor }"></span>
                    <strong>{{ s.setor }}</strong>
                  </span>
                </td>
                <td>{{ s.estacionamento }} ({{ s.andar }})</td>
                <td>{{ s.ocupadasAgora }}/{{ s.vagasTotais }} ({{ s.taxaOcupacao }}%)</td>
                <td><strong>{{ s.giroDiario }} veículos</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card-relatorio-bloco">
        <div class="header-relatorio-bloco">
          <div>
            <h3>Vagas Mais Utilizadas do Dia</h3>
            <p class="dica-painel">Vagas com maior quantidade de estadias e tempo médio</p>
          </div>
          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportarIndividual('RANKING_VAGAS', 'Ranking de Vagas')"
          >
            <IconDownload :size="16" />
            <span>Exportar</span>
          </button>
        </div>

        <div class="tabela-responsiva-wrapper">
          <table class="tabela-relatorio">
            <thead>
              <tr>
                <th>Vaga</th>
                <th>Setor / Andar</th>
                <th>Usos Hoje</th>
                <th>Permanência Média</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, idx) in dadosRelatorios.rankingVagas" :key="`rk-v-${idx}`">
                <td><span class="id-badge">{{ v.identificador }}</span></td>
                <td>{{ v.setor }} ({{ v.andar }})</td>
                <td><strong>{{ v.usosHoje }}x</strong></td>
                <td>{{ formatarMinutos(v.tempoMedioMin) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 4. COMPARADOR ENTRE 2 ESTACIONAMENTOS SELECIONADOS PELO USUÁRIO -->
    <section class="card-relatorio-bloco">
      <div class="header-relatorio-bloco">
        <div>
          <h3 class="item-icone-texto" style="justify-content: flex-start">
            <IconArrowsLeftRight :size="20" style="color: var(--destaque-azul)" />
            <span>Comparar Dois Estacionamentos</span>
          </h3>
          <p class="dica-painel">Selecione duas unidades para comparar desempenho e capacidade lado a lado</p>
        </div>

        <button
          class="btn-secundario btn-exportar-card item-icone-texto"
          @click="abrirModalExportarIndividual('COMPARATIVO', 'Comparativo de Estacionamentos')"
        >
          <IconDownload :size="16" />
          <span>Exportar Comparativo</span>
        </button>
      </div>

      <div class="seletores-comparador-grid">
        <div class="campo-grupo" style="margin-bottom: 0">
          <label>Estacionamento 1</label>
          <select v-model="idCompararA" class="select-padrao">
            <option v-for="e in estabelecimentosDoGerente" :key="`ca-${e.id}`" :value="e.id">
              {{ e.nome }}
            </option>
          </select>
        </div>

        <div class="campo-grupo" style="margin-bottom: 0">
          <label>Estacionamento 2</label>
          <select v-model="idCompararB" class="select-padrao">
            <option v-for="e in estabelecimentosDoGerente" :key="`cb-${e.id}`" :value="e.id">
              {{ e.nome }}
            </option>
          </select>
        </div>
      </div>

      <div v-if="comparativoA && comparativoB" class="grade-cards-comparador">
        <div v-for="(comp, cIdx) in [comparativoA, comparativoB]" :key="`comp-card-${cIdx}`" class="card-unidade-comparada">
          <h4>{{ comp.nome }}</h4>
          <div class="linha-metrica-comp">
            <span>Taxa de Ocupação Atual:</span>
            <strong style="color: var(--destaque-azul)">{{ comp.taxaOcupacao }}%</strong>
          </div>
          <div class="linha-metrica-comp">
            <span>Capacidade Total:</span>
            <strong>{{ comp.totalVagas }} vagas ({{ comp.andares }} andar(es) / {{ comp.setores }} setor(es))</strong>
          </div>
          <div class="linha-metrica-comp">
            <span>Livres vs. Ocupadas:</span>
            <span>
              <strong style="color: #16a34a">{{ comp.livres }} livres</strong> /
              <strong style="color: #ef4444">{{ comp.ocupadas }} ocupadas</strong>
            </span>
          </div>
          <div class="linha-metrica-comp">
            <span>Tempo Médio de Permanência:</span>
            <strong>{{ comp.tempoMedio }}</strong>
          </div>
          <div class="linha-metrica-comp">
            <span>Giro Diário Estimado:</span>
            <strong>{{ comp.giroDiario }} veículos/dia</strong>
          </div>
        </div>
      </div>
    </section>

    <!-- 5. HISTÓRICO DETALHADO DE OCUPAÇÃO (ALTURA FIXA + ANIMAÇÃO DE TROCA DE PÁGINA) -->
    <section class="card-relatorio-bloco">
      <div class="header-relatorio-bloco">
        <div>
          <h3>Histórico Detalhado de Ocupação</h3>
          <p class="dica-painel">Registro individual de entradas, saídas e tempo total de permanência por vaga</p>
        </div>

        <div class="acoes-topo-historico">
          <div class="input-pesquisa-icone-wrapper" style="min-width: 220px">
            <IconSearch :size="16" class="icone-input-pesquisa" />
            <input
              v-model="buscaHistorico"
              type="text"
              placeholder="Filtrar por vaga ou setor..."
              class="input-pesquisa-grande com-icone input-historico-compacto"
              @input="paginaHistorico = 1"
            />
          </div>

          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportarIndividual('HISTORICO', 'Histórico Detalhado de Ocupação')"
          >
            <IconDownload :size="16" />
            <span>Exportar</span>
          </button>
        </div>
      </div>

      <!-- Container com altura fixa para não mudar de tamanho quando a página tiver menos de 8 linhas -->
      <div class="tabela-responsiva-wrapper tabela-historico-altura-fixa">
        <Transition name="fade-tabela" mode="out-in">
          <table :key="paginaHistorico" class="tabela-relatorio">
            <thead>
              <tr>
                <th>Estacionamento</th>
                <th>Andar / Setor</th>
                <th>Vaga</th>
                <th>Data/Hora Entrada</th>
                <th>Data/Hora Saída</th>
                <th>Permanência</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="reg in historicoPaginado" :key="reg.id">
                <td><strong>{{ reg.estacionamento }}</strong></td>
                <td>{{ reg.andar }} — {{ reg.setor }}</td>
                <td><span class="id-badge">{{ reg.vaga }}</span></td>
                <td>{{ reg.dataEntrada }}</td>
                <td>
                  <span :class="{ 'tag-em-andamento': reg.dataSaida === 'Em andamento' }">
                    {{ reg.dataSaida }}
                  </span>
                </td>
                <td><strong>{{ reg.permanenciaTexto }}</strong></td>
              </tr>
              <tr v-if="historicoPaginado.length === 0">
                <td colspan="6" style="text-align: center; padding: 32px; color: var(--texto-secundario)">
                  Nenhum registro encontrado para este filtro.
                </td>
              </tr>
            </tbody>
          </table>
        </Transition>
      </div>

      <div class="paginacao-admin">
        <button
          class="item-icone-texto"
          :disabled="paginaHistorico <= 1"
          @click="paginaHistorico--"
        >
          <IconSquareRoundedChevronLeft :size="18" />
          <span>Anterior</span>
        </button>
        <span>Página {{ paginaHistorico }} de {{ totalPaginasHistorico }}</span>
        <button
          class="item-icone-texto"
          :disabled="paginaHistorico >= totalPaginasHistorico"
          @click="paginaHistorico++"
        >
          <span>Próxima</span>
          <IconSquareRoundedChevronRight :size="18" />
        </button>
      </div>
    </section>

    <!-- 6. SEÇÃO RESERVADA: EXPORTAR RELATÓRIOS COMPLETOS (CSV PADRÃO BRASIL) -->
    <section class="card-relatorio-bloco card-exportacao-completa-bi">
      <div class="header-relatorio-bloco">
        <div>
          <h3 class="item-icone-texto" style="justify-content: flex-start">
            <IconLayoutBoard :size="20" style="color: #16a34a" />
            <span>Exportar Relatórios Completos para BI (CSV Padrão Brasil)</span>
          </h3>
          <p class="dica-painel">
            Exporta todos os relatórios consolidados no formato .csv
          </p>
        </div>
      </div>

      <div class="controles-exportacao-completa">
        <div
          class="campos-datas-exportacao"
          :class="{ 'datas-cinzadas': atalhoPeriodoCompleto !== '' }"
        >
          <div class="campo-grupo" style="margin-bottom: 0">
            <label>Data Início</label>
            <input
              v-model="dataInicioCompleto"
              type="date"
              class="input-data-nativo"
              :disabled="atalhoPeriodoCompleto !== ''"
            />
          </div>

          <div class="campo-grupo" style="margin-bottom: 0">
            <label>Data Fim</label>
            <input
              v-model="dataFimCompleto"
              type="date"
              class="input-data-nativo"
              :disabled="atalhoPeriodoCompleto !== ''"
            />
          </div>
        </div>

        <div class="atalhos-periodo-box">
          <span class="rotulo-atalho">Seleções Rápidas</span>
          <div class="botoes-atalhos-periodo">
            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoCompleto === 'ULTIMO_DIA' }"
              @click="selecionarAtalhoCompleto('ULTIMO_DIA')"
            >
              Último dia
            </button>

            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoCompleto === 'ULTIMA_SEMANA' }"
              @click="selecionarAtalhoCompleto('ULTIMA_SEMANA')"
            >
              Última semana
            </button>
          </div>
        </div>

        <button
          type="button"
          class="btn-primario btn-baixar-completo-bi item-icone-texto"
          @click="exportarRelatorioCompletoCsvPadrao"
        >
          <IconDownload :size="20" />
          <span>Baixar Relatório Completo (.CSV)</span>
        </button>
      </div>
    </section>

    <!-- MODAL POPUP DE EXPORTAÇÃO INDIVIDUAL DE CADA RELATÓRIO -->
    <Transition name="fade-pop">
      <div v-if="modalExportarAberto" class="modal-backdrop">
        <div class="modal-box modal-exportar-relatorio">
          <div class="overlay-header">
            <h3 class="item-icone-texto">
              <IconDownload :size="20" />
              <span>Exportar — {{ relatorioAlvoExportacao.titulo }}</span>
            </h3>
            <button class="btn-fechar-mini" @click="modalExportarAberto = false">
              <IconSquareRoundedX :size="20" />
            </button>
          </div>

          <p class="subtitulo" style="margin-bottom: 12px">
            Escolha o intervalo de datas ou selecione uma opção rápida abaixo:
          </p>

          <div
            class="campos-datas-modal"
            :class="{ 'datas-cinzadas': atalhoPeriodoModal !== '' }"
          >
            <div class="campo-grupo">
              <label>Data Início</label>
              <input
                v-model="dataInicioModal"
                type="date"
                class="input-data-nativo"
                :disabled="atalhoPeriodoModal !== ''"
              />
            </div>

            <div class="campo-grupo">
              <label>Data Fim</label>
              <input
                v-model="dataFimModal"
                type="date"
                class="input-data-nativo"
                :disabled="atalhoPeriodoModal !== ''"
              />
            </div>
          </div>

          <div class="botoes-atalhos-modal">
            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoModal === 'ULTIMO_DIA' }"
              @click="selecionarAtalhoModal('ULTIMO_DIA')"
            >
              Último dia
            </button>

            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoModal === 'ULTIMA_SEMANA' }"
              @click="selecionarAtalhoModal('ULTIMA_SEMANA')"
            >
              Última semana
            </button>
          </div>

          <button
            type="button"
            class="btn-primario btn-confirmar-sucesso item-icone-texto"
            @click="confirmarExportacaoCsvIndividual"
          >
            <IconDownload :size="19" />
            <span>Exportar / Baixar CSV</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>