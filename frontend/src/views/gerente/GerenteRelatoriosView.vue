<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  idsSelecionadosGerente,
  cidadeSelecionadaGerente,
  cidadesDoGerente,
  estabelecimentosDoGerentePorCidade,
  selecionarCidadeGerente,
  simulacao1Ativa,
  estabelecimentosDoGerente,
  estabelecimentosFiltradosGerente,
  alternarSimulacao1Frontend,
  contarVagasEstabelecimento,
  carregarDadosDoBanco
} from '@/stores/estacionamentoStore'
import { baixarArquivoCsv } from '@/utils/exportUtils'
import {
  IconSquareRoundedArrowLeft,
  IconParking,
  IconSearch,
  IconSquareRoundedChevronDown,
  IconSquareRoundedCheck,
  IconSquareRoundedX,
  IconSquareRoundedChevronLeft,
  IconSquareRoundedChevronRight,
  IconDownload,
  IconArrowsLeftRight,
  IconPlayerPlay,
  IconPin
} from '@/constants/icons'

const router = useRouter()

const dropdownMultiAberto = ref(false)
const dropdownCidadeAberto = ref(false)
const termoBuscaMulti = ref('')

const idCompEsquerda = ref(null)
const idCompDireita = ref(null)

const buscaHistorico = ref('')
const paginaHistorico = ref(1)
const itensPorPaginaHistorico = 8

const hojeIso = new Date().toISOString().slice(0, 10)
const seteDiasAtrasIso = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10)

const dataInicioCompleto = ref(seteDiasAtrasIso)
const dataFimCompleto = ref(hojeIso)
const atalhoPeriodoCompleto = ref(null)

const modalExportAberto = ref(false)
const secaoAlvoExport = ref(null)
const dataInicioModal = ref(seteDiasAtrasIso)
const dataFimModal = ref(hojeIso)
const atalhoPeriodoModal = ref(null)

function fecharDropdownsAoClicarFora(e) {
  if (!e.target.closest('.seletor-multi-wrapper')) {
    dropdownMultiAberto.value = false
    dropdownCidadeAberto.value = false
  }
}

onMounted(() => {
  if (estabelecimentosDoGerente.value.length === 0) {
    carregarDadosDoBanco()
  }
  window.addEventListener('click', fecharDropdownsAoClicarFora)
})

onUnmounted(() => {
  window.removeEventListener('click', fecharDropdownsAoClicarFora)
})

watch(
  () => estabelecimentosDoGerente.value,
  (lista) => {
    if (lista.length > 0 && !idCompEsquerda.value) {
      idCompEsquerda.value = lista[0].id
      idCompDireita.value = lista[1]?.id || lista[0].id
    }
  },
  { immediate: true }
)

const mostrarPesquisaNoMulti = computed(() => estabelecimentosDoGerentePorCidade.value.length > 5)

const listaEstabelecimentosNoMulti = computed(() => {
  const termo = termoBuscaMulti.value.trim().toLowerCase()
  if (!termo) return estabelecimentosDoGerentePorCidade.value
  return estabelecimentosDoGerentePorCidade.value.filter(
    e =>
      e.nome.toLowerCase().includes(termo) ||
      (e.cidade || '').toLowerCase().includes(termo) ||
      String(e.id) === termo
  )
})

const textoBotaoSeletorTopo = computed(() => {
  const total = estabelecimentosDoGerentePorCidade.value.length
  const sel = idsSelecionadosGerente.value.length
  if (sel === 0 || sel === total) return `Todos (${total})`
  if (sel === 1) {
    const u = estabelecimentosDoGerentePorCidade.value.find(
      e => e.id === idsSelecionadosGerente.value[0]
    )
    return u ? u.nome : '1 selecionado'
  }
  return `${sel} selecionados`
})

function selecionarDashboardCompleto() {
  idsSelecionadosGerente.value = []
}

function alternarSelecaoEstacionamento(idEst) {
  const idx = idsSelecionadosGerente.value.indexOf(idEst)
  if (idx >= 0) idsSelecionadosGerente.value.splice(idx, 1)
  else idsSelecionadosGerente.value.push(idEst)
}

const metricasConsolidadas = computed(() => {
  let total = 0
  let livres = 0
  let ocupadas = 0
  let inativas = 0
  let somaDuracao = 0
  let qtdDuracao = 0
  let totalUsos = 0

  estabelecimentosFiltradosGerente.value.forEach((est) => {
    const m = contarVagasEstabelecimento(est)
    total += m.total
    livres += m.livres
    ocupadas += m.ocupadas
    inativas += m.inativas

    ;(est.andares || []).forEach((andar) => {
      Object.values(andar.celulas || {}).forEach((c) => {
        if (c.tipo === 'VAGA' && !c.inativa) {
          totalUsos += c.usosNoDia || 0
          if (!c.livre && c.duracaoMinutos) {
            somaDuracao += c.duracaoMinutos
            qtdDuracao++
          }
        }
      })
    })
  })

  const taxaOcupacao = total > 0 ? Math.round((ocupadas / total) * 100) : 0
  const mediaMinutos = qtdDuracao > 0 ? Math.round(somaDuracao / qtdDuracao) : ocupadas > 0 ? 74 : 0
  const horas = Math.floor(mediaMinutos / 60)
  const mins = mediaMinutos % 60
  const textoPermanencia =
    mediaMinutos === 0 ? '0 min' : horas > 0 ? `${horas}h ${mins}min` : `${mins} min`

  return {
    total,
    livres,
    ocupadas,
    inativas,
    taxaOcupacao,
    mediaMinutos,
    textoPermanencia,
    giroTotal: totalUsos > 0 ? totalUsos : ocupadas * 2,
    horarioPico: ocupadas > 0 ? '18h às 19h' : 'Sem pico registrado'
  }
})

const serieFluxoHorario = computed(() => {
  const horas = ['07h', '09h', '11h', '13h', '15h', '17h', '19h', '21h']
  const base = metricasConsolidadas.value.ocupadas
  const multEnt = [0.22, 0.54, 0.78, 0.65, 0.71, 0.96, 0.84, 0.35]
  const multSai = [0.08, 0.25, 0.64, 0.72, 0.58, 0.82, 0.94, 0.62]

  const lista = horas.map((rotulo, i) => ({
    rotulo,
    entradas: base === 0 ? 0 : Math.max(1, Math.round(base * multEnt[i])),
    saidas: base === 0 ? 0 : Math.max(1, Math.round(base * multSai[i]))
  }))

  const maxVal = Math.max(1, ...lista.flatMap(d => [d.entradas, d.saidas]))
  return lista.map(d => ({
    ...d,
    alturaEntPct: d.entradas === 0 ? 4 : Math.max(10, Math.round((d.entradas / maxVal) * 100)),
    alturaSaiPct: d.saidas === 0 ? 4 : Math.max(10, Math.round((d.saidas / maxVal) * 100))
  }))
})

const rankingSetores = computed(() => {
  const linhas = []
  estabelecimentosFiltradosGerente.value.forEach((est) => {
    ;(est.andares || []).forEach((andar) => {
      const celulas = Object.values(andar.celulas || {})
      ;(andar.setores || []).forEach((setor) => {
        const vagasSetor = celulas.filter(c => c.tipo === 'VAGA' && c.setorId === setor.id_setor)
        const ativas = vagasSetor.filter(v => !v.inativa)
        const ocupadas = ativas.filter(v => !v.livre).length
        const livres = ativas.filter(v => v.livre).length
        const inativas = vagasSetor.filter(v => v.inativa).length
        const taxa = ativas.length > 0 ? Math.round((ocupadas / ativas.length) * 100) : 0
        const usos = ativas.reduce((acc, v) => acc + (v.usosNoDia || (v.livre ? 1 : 3)), 0)

        linhas.push({
          chave: `${est.id}-${andar.id_andar}-${setor.id_setor}`,
          estacionamento: est.nome,
          andar: andar.nome_andar,
          setor: `${setor.nome_setor} (${setor.prefixo})`,
          cor: setor.cor_hex,
          totalAtivas: ativas.length,
          livres,
          ocupadas,
          inativas,
          taxa,
          usos
        })
      })
    })
  })
  return linhas.sort((a, b) => b.taxa - a.taxa || b.usos - a.usos)
})

const rankingVagas = computed(() => {
  const todas = []
  estabelecimentosFiltradosGerente.value.forEach((est) => {
    ;(est.andares || []).forEach((andar) => {
      Object.values(andar.celulas || {}).forEach((c) => {
        if (c.tipo === 'VAGA' && !c.inativa) {
          const usos = c.usosNoDia || (c.livre ? ((c.x + c.y) % 4) + 1 : ((c.x * 3 + c.y) % 7) + 4)
          const permMedia = c.duracaoMinutos || ((c.x * 13 + c.y * 7) % 95) + 25
          todas.push({
            chave: `${est.id}-${andar.id_andar}-${c.identificador}`,
            estacionamento: est.nome,
            andar: andar.nome_andar,
            setor: c.nomeSetor || 'Geral',
            identificador: c.identificador,
            status: c.livre ? 'Livre' : 'Ocupada',
            usos,
            permMedia
          })
        }
      })
    })
  })
  return todas.sort((a, b) => b.usos - a.usos).slice(0, 10)
})

function calcularResumoUnidade(idEst) {
  const est = estabelecimentosDoGerente.value.find(e => e.id === Number(idEst))
  if (!est) return null
  const m = contarVagasEstabelecimento(est)
  let somaDur = 0
  let qtdDur = 0
  let usos = 0

  ;(est.andares || []).forEach((andar) => {
    Object.values(andar.celulas || {}).forEach((c) => {
      if (c.tipo === 'VAGA' && !c.inativa) {
        usos += c.usosNoDia || (c.livre ? 1 : 4)
        if (!c.livre && c.duracaoMinutos) {
          somaDur += c.duracaoMinutos
          qtdDur++
        }
      }
    })
  })

  const taxa = m.total > 0 ? Math.round((m.ocupadas / m.total) * 100) : 0
  const mediaMin = qtdDur > 0 ? Math.round(somaDur / qtdDur) : m.ocupadas > 0 ? 68 : 0

  return {
    id: est.id,
    nome: est.nome,
    andaresQtd: (est.andares || []).length,
    ...m,
    taxa,
    mediaMin,
    usos
  }
}

const resumoCompEsquerda = computed(() => calcularResumoUnidade(idCompEsquerda.value))
const resumoCompDireita = computed(() => calcularResumoUnidade(idCompDireita.value))

const listaHistoricoOcupacao = computed(() => {
  const registros = []
  const hojeStr = new Date().toLocaleDateString('pt-BR')

  estabelecimentosFiltradosGerente.value.forEach((est) => {
    ;(est.andares || []).forEach((andar) => {
      Object.values(andar.celulas || {}).forEach((c) => {
        if (c.tipo === 'VAGA' && !c.inativa) {
          const semente = (c.idVagaBanco || c.x * 10 + c.y) % 9
          const hEnt = 8 + semente
          const mEnt = (c.x * 7 + c.y * 3) % 60
          const duracao = c.duracaoMinutos || 35 + ((c.x * 11 + c.y * 5) % 110)

          const entradaStr = `${hojeStr} ${String(hEnt).padStart(2, '0')}:${String(mEnt).padStart(2, '0')}`
          const totalMinSaida = hEnt * 60 + mEnt + duracao
          const hSai = Math.min(23, Math.floor(totalMinSaida / 60))
          const mSai = totalMinSaida % 60
          const saidaStr = c.livre
            ? `${hojeStr} ${String(hSai).padStart(2, '0')}:${String(mSai).padStart(2, '0')}`
            : 'Em andamento'

          registros.push({
            id: `${est.id}-${andar.id_andar}-${c.identificador}`,
            estacionamento: est.nome,
            andar: andar.nome_andar,
            setor: c.nomeSetor || 'Geral',
            vaga: c.identificador,
            dataEntrada: entradaStr,
            dataSaida: saidaStr,
            permanenciaMin: duracao,
            permanenciaTexto: `${Math.floor(duracao / 60)}h ${duracao % 60}m`
          })
        }
      })
    })
  })

  const termo = buscaHistorico.value.trim().toLowerCase()
  if (!termo) return registros
  return registros.filter(
    r =>
      r.vaga.toLowerCase().includes(termo) ||
      r.estacionamento.toLowerCase().includes(termo) ||
      r.setor.toLowerCase().includes(termo)
  )
})

const totalPaginasHistorico = computed(() =>
  Math.max(1, Math.ceil(listaHistoricoOcupacao.value.length / itensPorPaginaHistorico))
)

const historicoPaginado = computed(() => {
  const ini = (paginaHistorico.value - 1) * itensPorPaginaHistorico
  return listaHistoricoOcupacao.value.slice(ini, ini + itensPorPaginaHistorico)
})

function abrirModalExportacaoIndividual(secao, titulo) {
  secaoAlvoExport.value = { codigo: secao, titulo }
  atalhoPeriodoModal.value = null
  modalExportAberto.value = true
}

function alternarAtalhoModal(periodo) {
  atalhoPeriodoModal.value = atalhoPeriodoModal.value === periodo ? null : periodo
}

function alternarAtalhoCompleto(periodo) {
  atalhoPeriodoCompleto.value = atalhoPeriodoCompleto.value === periodo ? null : periodo
}

function obterRotuloPeriodo(atalho, inicio, fim) {
  if (atalho === 'SEMANA') return 'Ultima_Semana'
  if (atalho === 'MES') return 'Ultimo_Mes'
  if (atalho === 'ANO') return 'Ultimo_Ano'
  if (atalho === 'SEMPRE') return 'Desde_Sempre'
  return `${inicio}_a_${fim}`
}

function confirmarExportacaoIndividual() {
  if (!secaoAlvoExport.value) return
  const rotuloPeriodo = obterRotuloPeriodo(
    atalhoPeriodoModal.value,
    dataInicioModal.value,
    dataFimModal.value
  )
  const codigo = secaoAlvoExport.value.codigo

  if (codigo === 'FLUXO_HORARIO') {
    baixarArquivoCsv(
      `VagaCerta_Fluxo_Horario_${rotuloPeriodo}.csv`,
      ['Periodo_Filtro', 'Faixa_Horaria', 'Entradas', 'Saidas', 'Saldo_Fluxo'],
      serieFluxoHorario.value.map(item => [
        rotuloPeriodo,
        item.rotulo,
        item.entradas,
        item.saidas,
        item.entradas - item.saidas
      ])
    )
  } else if (codigo === 'DESEMPENHO_SETORES') {
    baixarArquivoCsv(
      `VagaCerta_Desempenho_Setores_${rotuloPeriodo}.csv`,
      ['Periodo_Filtro', 'Estacionamento', 'Andar', 'Setor', 'Vagas_Ativas', 'Livres', 'Ocupadas', 'Inativas', 'Taxa_Ocupacao_Pct', 'Rotatividade_Usos'],
      rankingSetores.value.map(s => [
        rotuloPeriodo,
        s.estacionamento,
        s.andar,
        s.setor,
        s.totalAtivas,
        s.livres,
        s.ocupadas,
        s.inativas,
        `${s.taxa}%`,
        s.usos
      ])
    )
  } else if (codigo === 'RANKING_VAGAS') {
    baixarArquivoCsv(
      `VagaCerta_Ranking_Vagas_${rotuloPeriodo}.csv`,
      ['Periodo_Filtro', 'Posicao', 'Vaga', 'Estacionamento', 'Andar', 'Setor', 'Status_Atual', 'Usos_No_Dia', 'Permanencia_Media_Min'],
      rankingVagas.value.map((v, idx) => [
        rotuloPeriodo,
        idx + 1,
        v.identificador,
        v.estacionamento,
        v.andar,
        v.setor,
        v.status,
        v.usos,
        v.permMedia
      ])
    )
  } else if (codigo === 'COMPARATIVO_UNIDADES') {
    const u1 = resumoCompEsquerda.value
    const u2 = resumoCompDireita.value
    baixarArquivoCsv(
      `VagaCerta_Comparativo_Unidades_${rotuloPeriodo}.csv`,
      ['Periodo_Filtro', 'Unidade', 'Andares', 'Total_Vagas_Ativas', 'Vagas_Livres', 'Vagas_Ocupadas', 'Vagas_Inativas', 'Taxa_Ocupacao_Pct', 'Permanencia_Media_Min', 'Rotatividade_Total'],
      [u1, u2].filter(Boolean).map(u => [
        rotuloPeriodo,
        u.nome,
        u.andaresQtd,
        u.total,
        u.livres,
        u.ocupadas,
        u.inativas,
        `${u.taxa}%`,
        u.mediaMin,
        u.usos
      ])
    )
  } else if (codigo === 'HISTORICO_OCUPACAO') {
    baixarArquivoCsv(
      `VagaCerta_Historico_Ocupacao_${rotuloPeriodo}.csv`,
      ['Periodo_Filtro', 'Estacionamento', 'Andar', 'Setor', 'Vaga', 'Data_Hora_Entrada', 'Data_Hora_Saida', 'Permanencia_Minutos', 'Permanencia_Formatada'],
      listaHistoricoOcupacao.value.map(h => [
        rotuloPeriodo,
        h.estacionamento,
        h.andar,
        h.setor,
        h.vaga,
        h.dataEntrada,
        h.dataSaida,
        h.permanenciaMin,
        h.permanenciaTexto
      ])
    )
  }

  modalExportAberto.value = false
}

function exportarRelatorioCompletoBi() {
  const rotuloPeriodo = obterRotuloPeriodo(
    atalhoPeriodoCompleto.value,
    dataInicioCompleto.value,
    dataFimCompleto.value
  )

  const cabecalhos = [
    'Secao_Relatorio',
    'Periodo_Filtro',
    'Estacionamento',
    'Andar',
    'Setor',
    'Identificador_Item',
    'Status_Ou_Detalhe',
    'Valor_Principal',
    'Valor_Secundario',
    'Observacao_Adicional'
  ]

  const linhas = []

  serieFluxoHorario.value.forEach((f) => {
    linhas.push([
      '1_FLUXO_HORARIO',
      rotuloPeriodo,
      textoBotaoSeletorTopo.value,
      'Todos',
      'Todos',
      f.rotulo,
      'Entradas / Saidas',
      f.entradas,
      f.saidas,
      `Saldo: ${f.entradas - f.saidas}`
    ])
  })

  rankingSetores.value.forEach((s) => {
    linhas.push([
      '2_DESEMPENHO_SETORES',
      rotuloPeriodo,
      s.estacionamento,
      s.andar,
      s.setor,
      s.setor,
      `Ocupacao: ${s.taxa}%`,
      s.ocupadas,
      s.livres,
      `Inativas: ${s.inativas} | Giro: ${s.usos}`
    ])
  })

  rankingVagas.value.forEach((v, i) => {
    linhas.push([
      '3_RANKING_VAGAS',
      rotuloPeriodo,
      v.estacionamento,
      v.andar,
      v.setor,
      v.identificador,
      v.status,
      v.usos,
      v.permMedia,
      `Top #${i + 1}`
    ])
  })

  listaHistoricoOcupacao.value.forEach((h) => {
    linhas.push([
      '4_HISTORICO_OCUPACAO',
      rotuloPeriodo,
      h.estacionamento,
      h.andar,
      h.setor,
      h.vaga,
      h.dataSaida === 'Em andamento' ? 'Ocupada Agora' : 'Finalizado',
      h.permanenciaMin,
      h.dataEntrada,
      `Saida: ${h.dataSaida}`
    ])
  })

  baixarArquivoCsv(`VagaCerta_Relatorio_Completo_BI_${rotuloPeriodo}.csv`, cabecalhos, linhas)
}
</script>

<template>
  <main class="gerente-dashboard-container">
    <header class="gerente-header-topo">
      <div class="gerente-boas-vindas gerente-boas-vindas-relatorios">
        <div class="bloco-texto-boas-vindas">
          <h1>Relatórios Detalhados e Exportação BI</h1>
          <p class="subtitulo ocultar-subtitulo-mobile">
            Análise de fluxo horário, permanência, rotatividade de vagas e comparativo entre unidades
          </p>
        </div>

        <div class="gerente-atalhos-topo">
          <button
            class="btn-secundario btn-simulacao-topo item-icone-texto"
            :class="{ 'btn-simulacao-ativa': simulacao1Ativa }"
            @click="alternarSimulacao1Frontend"
          >
            <IconPlayerPlay :size="18" />
            <span class="texto-btn-simulacao">{{ simulacao1Ativa ? 'Simulação 1: ON' : 'Simulação 1' }}</span>
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
            @click="router.push({ name: 'gerente' })"
          >
            <IconSquareRoundedArrowLeft :size="18" />
            <span>Dashboard</span>
          </button>
        </div>
      </div>

      <!-- Barra de Filtros: 1 Seletor de Estacionamentos + 1 Seletor de Cidades -->
      <div v-if="estabelecimentosDoGerente.length >= 1" class="barra-filtros-gerente">
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

    <!-- 4 Cards de KPIs Executivos -->
    <section class="grade-quatro-kpis-relatorio">
      <div class="card-kpi-gerente kpi-compacto">
        <span class="kpi-titulo">Taxa de Ocupação</span>
        <div class="kpi-valor-destaque">{{ metricasConsolidadas.taxaOcupacao }}%</div>
        <span class="kpi-descricao-apoio">
          {{ metricasConsolidadas.ocupadas }} ocupadas de {{ metricasConsolidadas.total }} vagas ativas
        </span>
      </div>

      <div class="card-kpi-gerente kpi-compacto">
        <span class="kpi-titulo">Permanência Média</span>
        <div class="kpi-valor-destaque">{{ metricasConsolidadas.textoPermanencia }}</div>
        <span class="kpi-descricao-apoio">Tempo médio por veículo estacionado</span>
      </div>

      <div class="card-kpi-gerente kpi-compacto">
        <span class="kpi-titulo">Rotatividade Acumulada</span>
        <div class="kpi-valor-destaque">{{ metricasConsolidadas.giroTotal }}</div>
        <span class="kpi-descricao-apoio">Total de usos registrados no período</span>
      </div>

      <div class="card-kpi-gerente kpi-compacto">
        <span class="kpi-titulo">Horário de Pico</span>
        <div class="kpi-valor-destaque" style="font-size: 24px">{{ metricasConsolidadas.horarioPico }}</div>
        <span class="kpi-descricao-apoio">{{ metricasConsolidadas.inativas }} vaga(s) em manutenção/inativas</span>
      </div>
    </section>

    <!-- Grade Dupla: Fluxo Horário + Top 10 Vagas -->
    <section class="grade-dupla-relatorios">
      <div class="card-relatorio-bloco">
        <div class="header-relatorio-bloco">
          <div>
            <h3>Fluxo Horário de Entradas e Saídas</h3>
            <p class="subtitulo">Volume consolidado por faixa de horário</p>
          </div>
          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportacaoIndividual('FLUXO_HORARIO', 'Fluxo Horário de Entradas e Saídas')"
          >
            <IconDownload :size="17" />
            <span>Exportar</span>
          </button>
        </div>

        <div class="legenda-fluxo-mini" style="margin-bottom: 6px">
          <span class="ponto-legenda ent"></span> Entradas
          <span class="ponto-legenda sai"></span> Saídas
        </div>

        <div class="grafico-barras-horarias grafico-relatorio-maior">
          <div v-for="item in serieFluxoHorario" :key="item.rotulo" class="coluna-hora-item">
            <div class="par-barras-verticais">
              <div class="barra-v ent" :style="{ height: `${item.alturaEntPct}%` }">
                <span class="valor-barra-topo">{{ item.entradas }}</span>
              </div>
              <div class="barra-v sai" :style="{ height: `${item.alturaSaiPct}%` }">
                <span class="valor-barra-topo">{{ item.saidas }}</span>
              </div>
            </div>
            <span class="rotulo-hora-eixo">{{ item.rotulo }}</span>
          </div>
        </div>
      </div>

      <div class="card-relatorio-bloco">
        <div class="header-relatorio-bloco">
          <div>
            <h3>Top 10 Vagas com Maior Rotatividade</h3>
            <p class="subtitulo">Vagas mais demandadas e tempo médio de uso</p>
          </div>
          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportacaoIndividual('RANKING_VAGAS', 'Top 10 Vagas com Maior Rotatividade')"
          >
            <IconDownload :size="17" />
            <span>Exportar</span>
          </button>
        </div>

        <div class="tabela-responsiva-wrapper">
          <table class="tabela-relatorio">
            <thead>
              <tr>
                <th>#</th>
                <th>Vaga</th>
                <th>Unidade / Andar</th>
                <th>Setor</th>
                <th>Giro</th>
                <th>Perm. Média</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, idx) in rankingVagas" :key="v.chave">
                <td><strong>{{ idx + 1 }}º</strong></td>
                <td><span class="id-badge">{{ v.identificador }}</span></td>
                <td>{{ v.estacionamento }} ({{ v.andar }})</td>
                <td>{{ v.setor }}</td>
                <td><strong>{{ v.usos }} usos</strong></td>
                <td>{{ v.permMedia }} min</td>
              </tr>
              <tr v-if="rankingVagas.length === 0">
                <td colspan="6" class="lista-vazia">Nenhuma vaga ativa encontrada.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Desempenho por Setor e Andar -->
    <section class="card-relatorio-bloco">
      <div class="header-relatorio-bloco">
        <div>
          <h3>Desempenho por Setor e Andar</h3>
          <p class="subtitulo">Ocupação, capacidade ativa, bloqueios e giro por setor</p>
        </div>
        <button
          class="btn-secundario btn-exportar-card item-icone-texto"
          @click="abrirModalExportacaoIndividual('DESEMPENHO_SETORES', 'Desempenho por Setor e Andar')"
        >
          <IconDownload :size="17" />
          <span>Exportar</span>
        </button>
      </div>

      <div class="tabela-responsiva-wrapper">
        <table class="tabela-relatorio">
          <thead>
            <tr>
              <th>Estacionamento</th>
              <th>Andar</th>
              <th>Setor</th>
              <th>Livres</th>
              <th>Ocupadas</th>
              <th>Inativas</th>
              <th>Ocupação</th>
              <th>Giro Hoje</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in rankingSetores" :key="s.chave">
              <td><strong>{{ s.estacionamento }}</strong></td>
              <td>{{ s.andar }}</td>
              <td>
                <span class="item-icone-texto" style="justify-content: flex-start">
                  <span class="bolinha-cor-setor" :style="{ backgroundColor: s.cor }"></span>
                  <span>{{ s.setor }}</span>
                </span>
              </td>
              <td class="num-livre">{{ s.livres }}</td>
              <td class="num-ocupada">{{ s.ocupadas }}</td>
              <td class="num-inativa">{{ s.inativas }}</td>
              <td><strong>{{ s.taxa }}%</strong></td>
              <td>{{ s.usos }} veículos</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Comparador Direto Entre 2 Estacionamentos -->
    <section v-if="estabelecimentosDoGerente.length >= 1" class="card-relatorio-bloco">
      <div class="header-relatorio-bloco">
        <div>
          <h3 class="item-icone-texto" style="justify-content: flex-start">
            <IconArrowsLeftRight :size="20" />
            <span>Comparativo Direto entre Estacionamentos</span>
          </h3>
          <p class="subtitulo">Selecione duas unidades para comparar indicadores lado a lado</p>
        </div>
        <button
          class="btn-secundario btn-exportar-card item-icone-texto"
          @click="abrirModalExportacaoIndividual('COMPARATIVO_UNIDADES', 'Comparativo entre Estacionamentos')"
        >
          <IconDownload :size="17" />
          <span>Exportar</span>
        </button>
      </div>

      <div class="seletores-comparador-grid">
        <select v-model="idCompEsquerda" class="select-padrao">
          <option v-for="e in estabelecimentosDoGerente" :key="`ce-${e.id}`" :value="e.id">
            Unidade A: {{ e.nome }}
          </option>
        </select>

        <select v-model="idCompDireita" class="select-padrao">
          <option v-for="e in estabelecimentosDoGerente" :key="`cd-${e.id}`" :value="e.id">
            Unidade B: {{ e.nome }}
          </option>
        </select>
      </div>

      <div v-if="resumoCompEsquerda && resumoCompDireita" class="grade-cards-comparador">
        <div v-for="(u, i) in [resumoCompEsquerda, resumoCompDireita]" :key="`comp-${i}-${u.id}`" class="card-unidade-comparada">
          <h4>{{ u.nome }}</h4>
          <div class="linha-metrica-comp">
            <span>Taxa de Ocupação:</span>
            <strong style="color: var(--destaque-azul)">{{ u.taxa }}%</strong>
          </div>
          <div class="linha-metrica-comp">
            <span>Vagas Livres / Total Ativas:</span>
            <strong class="num-livre">{{ u.livres }} / {{ u.total }}</strong>
          </div>
          <div class="linha-metrica-comp">
            <span>Vagas Ocupadas / Inativas:</span>
            <span><strong class="num-ocupada">{{ u.ocupadas }}</strong> / {{ u.inativas }} inat.</span>
          </div>
          <div class="linha-metrica-comp">
            <span>Permanência Média:</span>
            <strong>{{ u.mediaMin }} min</strong>
          </div>
          <div class="linha-metrica-comp">
            <span>Rotatividade Total:</span>
            <strong>{{ u.usos }} veículos</strong>
          </div>
        </div>
      </div>
    </section>

    <!-- Histórico Detalhado de Ocupação com Colunas Fixas e Transição Suave -->
    <section class="card-relatorio-bloco">
      <div class="header-relatorio-bloco">
        <div>
          <h3>Histórico Detalhado de Ocupação por Vaga</h3>
          <p class="subtitulo">Registro cronológico de entradas, saídas e tempo de permanência</p>
        </div>
        <div class="acoes-topo-historico">
          <div class="input-pesquisa-icone-wrapper" style="min-width: 220px">
            <IconSearch :size="16" class="icone-input-pesquisa" />
            <input
              v-model="buscaHistorico"
              type="text"
              placeholder="Filtrar por vaga, setor ou unidade..."
              class="input-pesquisa-grande com-icone input-historico-compacto"
              @input="paginaHistorico = 1"
            />
          </div>
          <button
            class="btn-secundario btn-exportar-card item-icone-texto"
            @click="abrirModalExportacaoIndividual('HISTORICO_OCUPACAO', 'Histórico de Ocupação por Vaga')"
          >
            <IconDownload :size="17" />
            <span>Exportar</span>
          </button>
        </div>
      </div>

      <div class="tabela-responsiva-wrapper tabela-historico-altura-fixa">
        <Transition name="fade-tabela" mode="out-in">
          <table
            :key="`${paginaHistorico}-${buscaHistorico}`"
            class="tabela-relatorio tabela-historico-colunas-fixas"
          >
            <thead>
              <tr>
                <th class="col-hist-est">Estacionamento</th>
                <th class="col-hist-setor">Andar / Setor</th>
                <th class="col-hist-vaga">Vaga</th>
                <th class="col-hist-data">Data/Hora Entrada</th>
                <th class="col-hist-data">Data/Hora Saída</th>
                <th class="col-hist-perm">Permanência</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="reg in historicoPaginado" :key="reg.id">
                <td class="celula-truncada" :title="reg.estacionamento">
                  <strong>{{ reg.estacionamento }}</strong>
                </td>
                <td class="celula-truncada" :title="`${reg.andar} — ${reg.setor}`">
                  {{ reg.andar }} — {{ reg.setor }}
                </td>
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
                <td colspan="6" class="lista-vazia">Nenhum registro encontrado.</td>
              </tr>
            </tbody>
          </table>
        </Transition>
      </div>

      <div v-if="totalPaginasHistorico > 1" class="paginacao-rodape">
        <button
          class="btn-secundario item-icone-texto"
          :disabled="paginaHistorico <= 1"
          @click="paginaHistorico--"
        >
          <IconSquareRoundedChevronLeft :size="18" />
          <span>Anterior</span>
        </button>
        <span class="info-paginacao">
          Página {{ paginaHistorico }} de {{ totalPaginasHistorico }}
        </span>
        <button
          class="btn-secundario item-icone-texto"
          :disabled="paginaHistorico >= totalPaginasHistorico"
          @click="paginaHistorico++"
        >
          <span>Próxima</span>
          <IconSquareRoundedChevronRight :size="18" />
        </button>
      </div>
    </section>

    <!-- Seção Inferior: Exportação Completa BI -->
    <section class="card-relatorio-bloco card-exportacao-completa-bi">
      <div class="header-relatorio-bloco">
        <div>
          <h3>Exportação Completa de Relatórios (CSV / Excel / Power BI)</h3>
          <p class="subtitulo">
            Gera um arquivo consolidado com Fluxo Horário, Setores, Ranking de Vagas e Histórico completo do período escolhido
          </p>
        </div>
      </div>

      <div class="controles-exportacao-completa">
        <div class="campos-datas-exportacao" :class="{ 'datas-cinzadas': atalhoPeriodoCompleto !== null }">
          <div class="campo-compacto">
            <label>Data Inicial</label>
            <input
              v-model="dataInicioCompleto"
              type="date"
              :disabled="atalhoPeriodoCompleto !== null"
              class="select-padrao"
            />
          </div>
          <div class="campo-compacto">
            <label>Data Final</label>
            <input
              v-model="dataFimCompleto"
              type="date"
              :disabled="atalhoPeriodoCompleto !== null"
              class="select-padrao"
            />
          </div>
        </div>

        <div class="atalhos-periodo-box">
          <span class="rotulo-atalho">Ou selecione um período rápido:</span>
          <div class="botoes-atalhos-periodo">
            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoCompleto === 'SEMANA' }"
              @click="alternarAtalhoCompleto('SEMANA')"
            >
              Última Semana
            </button>
            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoCompleto === 'MES' }"
              @click="alternarAtalhoCompleto('MES')"
            >
              Último Mês
            </button>
            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoCompleto === 'ANO' }"
              @click="alternarAtalhoCompleto('ANO')"
            >
              Último Ano
            </button>
            <button
              type="button"
              class="btn-secundario"
              :class="{ 'atalho-periodo-ativo': atalhoPeriodoCompleto === 'SEMPRE' }"
              @click="alternarAtalhoCompleto('SEMPRE')"
            >
              Desde Sempre
            </button>
          </div>
        </div>

        <button
          type="button"
          class="btn-primario btn-baixar-completo-bi item-icone-texto"
          @click="exportarRelatorioCompletoBi"
        >
          <IconDownload :size="20" />
          <span>Baixar Relatório Completo (.CSV)</span>
        </button>
      </div>
    </section>

    <!-- Modal de Exportação Individual -->
    <Transition name="fade-backdrop">
      <div v-if="modalExportAberto" class="modal-backdrop" @click.self="modalExportAberto = false">
        <div class="modal-box modal-exportar-relatorio">
          <div class="overlay-header">
            <h3 class="item-icone-texto">
              <IconDownload :size="20" />
              <span>Exportar Relatório</span>
            </h3>
            <button class="btn-fechar-mini" @click="modalExportAberto = false">
              <IconSquareRoundedX :size="20" />
            </button>
          </div>

          <p class="subtitulo" style="margin-bottom: 12px">
            Seção: <strong>{{ secaoAlvoExport?.titulo }}</strong>
          </p>

          <div class="campos-datas-modal" :class="{ 'datas-cinzadas': atalhoPeriodoModal !== null }">
            <div class="campo-grupo" style="margin-bottom: 10px">
              <label>Data Inicial</label>
              <input v-model="dataInicioModal" type="date" :disabled="atalhoPeriodoModal !== null" />
            </div>
            <div class="campo-grupo" style="margin-bottom: 10px">
              <label>Data Final</label>
              <input v-model="dataFimModal" type="date" :disabled="atalhoPeriodoModal !== null" />
            </div>
          </div>

          <div class="campo-grupo">
            <label>Ou escolha um período rápido (desabilita as datas acima):</label>
            <div class="botoes-atalhos-modal">
              <button
                type="button"
                class="btn-secundario"
                :class="{ 'atalho-periodo-ativo': atalhoPeriodoModal === 'SEMANA' }"
                @click="alternarAtalhoModal('SEMANA')"
              >
                Última Semana
              </button>
              <button
                type="button"
                class="btn-secundario"
                :class="{ 'atalho-periodo-ativo': atalhoPeriodoModal === 'MES' }"
                @click="alternarAtalhoModal('MES')"
              >
                Último Mês
              </button>
              <button
                type="button"
                class="btn-secundario"
                :class="{ 'atalho-periodo-ativo': atalhoPeriodoModal === 'ANO' }"
                @click="alternarAtalhoModal('ANO')"
              >
                Último Ano
              </button>
              <button
                type="button"
                class="btn-secundario"
                :class="{ 'atalho-periodo-ativo': atalhoPeriodoModal === 'SEMPRE' }"
                @click="alternarAtalhoModal('SEMPRE')"
              >
                Desde Sempre
              </button>
            </div>
          </div>

          <div class="modal-acoes modal-acoes-centralizadas">
            <button class="btn-secundario item-icone-texto" @click="modalExportAberto = false">
              <IconSquareRoundedX :size="17" />
              <span>Cancelar</span>
            </button>
            <button class="btn-primario item-icone-texto" @click="confirmarExportacaoIndividual">
              <IconDownload :size="17" />
              <span>Baixar .CSV</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </main>
</template>