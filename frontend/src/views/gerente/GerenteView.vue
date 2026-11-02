<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  usuarioLogado,
  usuariosCadastrados,
  idsSelecionadosGerente,
  cidadeSelecionadaGerente,
  cidadesDoGerente,
  estabelecimentosDoGerentePorCidade,
  selecionarCidadeGerente,
  simulacao1Ativa,
  estabelecimentosDoGerente,
  estabelecimentosFiltradosGerente,
  alternarSimulacao1Frontend,
  obterAndarEntradaSaida,
  contarVagasEstabelecimento,
  carregarDadosDoBanco
} from '@/stores/estacionamentoStore'
import {
  IconParking,
  IconChartBar,
  IconSearch,
  IconSquareRoundedChevronDown,
  IconSquareRoundedCheck,
  IconSquareRoundedX,
  IconClock,
  IconMaximize,
  IconPlayerPlay,
  IconPin
} from '@/constants/icons'

const router = useRouter()

const dropdownMultiAberto = ref(false)
const dropdownCidadeAberto = ref(false)
const termoBuscaMulti = ref('')
const modalEstMobileAberto = ref(false)
const termoBuscaModalMobile = ref('')

// Extrai o primeiro nome do gerente com fallback para a lista de usuários cadastrados
const primeiroNomeGerente = computed(() => {
  const nomeSessao = usuarioLogado.value?.nome?.trim()
  if (nomeSessao) {
    return nomeSessao.split(/\s+/)[0]
  }
  const encontrado = usuariosCadastrados.value.find(
    u => Number(u.id_usuario) === Number(usuarioLogado.value?.id_usuario)
  )
  if (encontrado?.nome?.trim()) {
    return encontrado.nome.trim().split(/\s+/)[0]
  }
  return 'Gerente'
})

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

const listaEstabelecimentosModalMobile = computed(() => {
  const termo = termoBuscaModalMobile.value.trim().toLowerCase()
  if (!termo) return estabelecimentosFiltradosGerente.value
  return estabelecimentosFiltradosGerente.value.filter(
    e =>
      e.nome.toLowerCase().includes(termo) ||
      (e.cidade || '').toLowerCase().includes(termo)
  )
})

const textoBotaoSeletorTopo = computed(() => {
  const totalUnidades = estabelecimentosDoGerentePorCidade.value.length
  const qtdSel = idsSelecionadosGerente.value.length
  if (qtdSel === 0 || qtdSel === totalUnidades) {
    return `Todos (${totalUnidades})`
  }
  if (qtdSel === 1) {
    const unico = estabelecimentosDoGerentePorCidade.value.find(
      e => e.id === idsSelecionadosGerente.value[0]
    )
    return unico ? unico.nome : '1 selecionado'
  }
  return `${qtdSel} selecionados`
})

function selecionarDashboardCompleto() {
  idsSelecionadosGerente.value = []
}

function alternarSelecaoEstacionamento(idEst) {
  const idx = idsSelecionadosGerente.value.indexOf(idEst)
  if (idx >= 0) {
    idsSelecionadosGerente.value.splice(idx, 1)
  } else {
    idsSelecionadosGerente.value.push(idEst)
  }
}

const resumoMetricas = computed(() => {
  let total = 0
  let livres = 0
  let ocupadas = 0
  let inativas = 0
  let somaDuracao = 0
  let qtdComDuracao = 0
  let usosHoje = 0

  estabelecimentosFiltradosGerente.value.forEach((est) => {
    const m = contarVagasEstabelecimento(est)
    total += m.total
    livres += m.livres
    ocupadas += m.ocupadas
    inativas += m.inativas

    ;(est.andares || []).forEach((andar) => {
      Object.values(andar.celulas || {}).forEach((c) => {
        if (c.tipo === 'VAGA' && !c.inativa) {
          usosHoje += c.usosNoDia || 0
          if (!c.livre && c.duracaoMinutos) {
            somaDuracao += c.duracaoMinutos
            qtdComDuracao++
          }
        }
      })
    })
  })

  const taxaOcupacao = total > 0 ? Math.round((ocupadas / total) * 100) : 0
  const mediaMinutos =
    qtdComDuracao > 0 ? Math.round(somaDuracao / qtdComDuracao) : ocupadas > 0 ? 74 : 0
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
    textoPermanencia,
    giroEstimado: usosHoje > 0 ? usosHoje : ocupadas * 2
  }
})

const serieFluxoHorario = computed(() => {
  const horasRotulos = ['08h', '10h', '12h', '14h', '16h', '18h', '20h']
  const baseOcupadas = resumoMetricas.value.ocupadas
  const multiplicadoresEntrada = [0.28, 0.52, 0.85, 0.64, 0.72, 0.95, 0.45]
  const multiplicadoresSaida = [0.12, 0.34, 0.78, 0.58, 0.62, 0.88, 0.74]

  const dados = horasRotulos.map((rotulo, i) => {
    const entradas =
      baseOcupadas === 0 ? 0 : Math.max(1, Math.round(baseOcupadas * multiplicadoresEntrada[i]))
    const saidas =
      baseOcupadas === 0 ? 0 : Math.max(1, Math.round(baseOcupadas * multiplicadoresSaida[i]))
    return { rotulo, entradas, saidas }
  })

  const maiorValor = Math.max(1, ...dados.flatMap(d => [d.entradas, d.saidas]))

  return dados.map(d => ({
    ...d,
    alturaEntradaPct: d.entradas === 0 ? 4 : Math.max(10, Math.round((d.entradas / maiorValor) * 100)),
    alturaSaidaPct: d.saidas === 0 ? 4 : Math.max(10, Math.round((d.saidas / maiorValor) * 100))
  }))
})

const doisMaioresEstacionamentos = computed(() => {
  return [...estabelecimentosFiltradosGerente.value]
    .map((est) => {
      const metricas = contarVagasEstabelecimento(est)
      const andarPreview = obterAndarEntradaSaida(est)
      return {
        est,
        metricas,
        andarPreview
      }
    })
    .sort((a, b) => b.metricas.total - a.metricas.total)
    .slice(0, 2)
})

function abrirEstacionamentoTelaCheia(idEst) {
  modalEstMobileAberto.value = false
  router.push({ name: 'gerente-estacionamentos', query: { id: idEst } })
}
</script>

<template>
  <main class="gerente-dashboard-container">
    <header class="gerente-header-topo">
      <div class="gerente-boas-vindas">
        <div class="bloco-texto-boas-vindas">
          <h1>Bem-vindo, {{ primeiroNomeGerente }}!</h1>
          <p class="subtitulo ocultar-subtitulo-tablet-mobile">
            Painel operacional e indicadores em tempo real dos seus estacionamentos
          </p>
        </div>

        <div class="gerente-atalhos-topo">
          <button
            class="btn-secundario btn-simulacao-topo item-icone-texto"
            :class="{ 'btn-simulacao-ativa': simulacao1Ativa }"
            title="Simula 60% de vagas ocupadas nos seus estacionamentos"
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
            @click="router.push({ name: 'gerente-relatorios' })"
          >
            <IconChartBar :size="18" />
            <span>Relatórios</span>
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

    <div v-if="estabelecimentosDoGerente.length === 0" class="card-kpi-gerente aviso-sem-estacionamento">
      <h3>Nenhum estacionamento vinculado à sua conta</h3>
      <p class="subtitulo">Solicite ao administrador desenvolvedor o vínculo do seu estabelecimento.</p>
    </div>

    <template v-else>
      <section class="secao-relatorios-dashboard">
        <div class="grade-kpis-gerente">
          <div class="card-kpi-gerente">
            <div class="kpi-cabecalho">
              <span class="kpi-titulo">Entradas e Saídas por Hora (Hoje)</span>
              <div class="legenda-fluxo-mini">
                <span class="ponto-legenda ent"></span> Entradas
                <span class="ponto-legenda sai"></span> Saídas
              </div>
            </div>

            <div class="grafico-barras-horarias">
              <div
                v-for="item in serieFluxoHorario"
                :key="item.rotulo"
                class="coluna-hora-item"
              >
                <div class="par-barras-verticais">
                  <div
                    class="barra-v ent"
                    :style="{ height: `${item.alturaEntradaPct}%` }"
                    :title="`Entradas (${item.rotulo}): ${item.entradas}`"
                  >
                    <span class="valor-barra-topo">{{ item.entradas }}</span>
                  </div>
                  <div
                    class="barra-v sai"
                    :style="{ height: `${item.alturaSaidaPct}%` }"
                    :title="`Saídas (${item.rotulo}): ${item.saidas}`"
                  >
                    <span class="valor-barra-topo">{{ item.saidas }}</span>
                  </div>
                </div>
                <span class="rotulo-hora-eixo">{{ item.rotulo }}</span>
              </div>
            </div>
          </div>

          <div class="card-kpi-gerente kpi-centralizado">
            <span class="kpi-titulo">Ocupação Atual</span>
            <div class="kpi-valor-destaque">{{ resumoMetricas.taxaOcupacao }}%</div>
            <div class="barra-progresso-ocupacao">
              <div
                class="preenchimento-ocupacao"
                :style="{ width: `${resumoMetricas.taxaOcupacao}%` }"
              ></div>
            </div>
            <div class="kpi-rodape-duplo">
              <span class="tag-kpi livre">{{ resumoMetricas.livres }} livres</span>
              <span class="tag-kpi ocupada">{{ resumoMetricas.ocupadas }} ocupadas</span>
            </div>
          </div>

          <div class="card-kpi-gerente kpi-centralizado">
            <span class="kpi-titulo">Tempo Médio de Permanência</span>
            <div class="kpi-valor-destaque item-icone-texto">
              <IconClock :size="28" />
              <span>{{ resumoMetricas.textoPermanencia }}</span>
            </div>
            <p class="kpi-descricao-apoio">
              Média calculada entre os veículos estacionados hoje nas unidades selecionadas
            </p>
          </div>

          <div class="card-kpi-gerente kpi-centralizado kpi-apenas-tablet">
            <span class="kpi-titulo">Rotatividade Estimada Hoje</span>
            <div class="kpi-valor-destaque">{{ resumoMetricas.giroEstimado }}</div>
            <p class="kpi-descricao-apoio">
              Total acumulado de veículos atendidos nas vagas ativas ({{ resumoMetricas.inativas }} inativas)
            </p>
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

      <section class="secao-seletor-mobile-est">
        <div class="card-kpi-gerente kpi-centralizado seletor-mobile-est-wrapper">
          <span class="kpi-titulo">Planta Operacional dos Estacionamentos</span>
          <p class="kpi-descricao-apoio" style="margin-bottom: 10px">
            Selecione um estacionamento para visualizar o mapa 2D completo, gerenciar vagas e mapa de calor
          </p>
          <button
            type="button"
            class="btn-primario btn-escolher-est-responsivo item-icone-texto"
            @click="modalEstMobileAberto = true"
          >
            <IconParking :size="19" />
            <span>Escolher Estacionamento ({{ estabelecimentosFiltradosGerente.length }})</span>
          </button>
        </div>
      </section>

      <section class="secao-estacionamentos-dupla-pc">
        <div
          v-for="item in doisMaioresEstacionamentos"
          :key="item.est.id"
          class="card-estacionamento-preview"
        >
          <div class="header-preview-est">
            <div>
              <h3>{{ item.est.nome }}</h3>
              <p class="subtitulo-preview">
                Andar exibido: <strong>{{ item.andarPreview?.nome_andar || 'Principal' }}</strong>
                • {{ item.metricas.livres }} livres / {{ item.metricas.ocupadas }} ocupadas
              </p>
            </div>
            <span class="badge-total-vagas">{{ item.metricas.total }} vagas</span>
          </div>

          <div v-if="item.andarPreview" class="preview-mapa-scroll">
            <div
              class="grid-preview-mini"
              :style="{
                gridTemplateColumns: `repeat(${item.andarPreview.grid_x}, 24px)`
              }"
            >
              <template v-for="y in item.andarPreview.grid_y" :key="`py-${y}`">
                <div
                  v-for="x in item.andarPreview.grid_x"
                  :key="`px-${x}-${y}`"
                  class="celula-preview-fundo"
                  :style="{
                    backgroundColor:
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.corSetor || 'transparent'
                  }"
                >
                  <div
                    class="quadrado-preview-interno"
                    :class="[
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAZIO' ? 'qp-vazio' : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'ESTRADA' ? 'qp-estrada' : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'ENTRADA' ? 'qp-entrada' : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'SAIDA' ? 'qp-saida' : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'ACESSO' ? 'qp-acesso' : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA' &&
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.inativa
                        ? 'qp-vaga-inativa'
                        : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA' &&
                      !item.andarPreview.celulas[`${x - 1},${y - 1}`]?.inativa &&
                      !item.andarPreview.celulas[`${x - 1},${y - 1}`]?.macEsp
                        ? 'qp-vaga-amarela'
                        : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA' &&
                      !item.andarPreview.celulas[`${x - 1},${y - 1}`]?.inativa &&
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.macEsp &&
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.livre
                        ? 'qp-vaga-livre'
                        : '',
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA' &&
                      !item.andarPreview.celulas[`${x - 1},${y - 1}`]?.inativa &&
                      item.andarPreview.celulas[`${x - 1},${y - 1}`]?.macEsp &&
                      !item.andarPreview.celulas[`${x - 1},${y - 1}`]?.livre
                        ? 'qp-vaga-ocupada'
                        : ''
                    ]"
                  >
                    <span v-if="item.andarPreview.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA'">
                      {{ item.andarPreview.celulas[`${x - 1},${y - 1}`]?.identificador }}
                    </span>
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

    <Transition name="fade-backdrop">
      <div
        v-if="modalEstMobileAberto"
        class="modal-backdrop"
        @click.self="modalEstMobileAberto = false"
      >
        <div class="modal-box modal-escolher-est-mobile">
          <div class="overlay-header">
            <h3 class="item-icone-texto">
              <IconParking :size="20" />
              <span>Escolher Estacionamento</span>
            </h3>
            <button class="btn-fechar-mini" @click="modalEstMobileAberto = false">
              <IconSquareRoundedX :size="20" />
            </button>
          </div>

          <div v-if="estabelecimentosFiltradosGerente.length > 5" class="busca-multi-topo" style="padding: 8px 0">
            <IconSearch :size="16" class="icone-busca-multi" style="left: 10px" />
            <input
              v-model="termoBuscaModalMobile"
              type="text"
              placeholder="Pesquisar estacionamento..."
            />
          </div>

          <div class="lista-modal-est-mobile">
            <div
              v-for="est in listaEstabelecimentosModalMobile"
              :key="est.id"
              class="item-opcao-multi"
              @click="abrirEstacionamentoTelaCheia(est.id)"
            >
              <span><strong>#{{ est.id }}</strong> — {{ est.nome }}</span>
              <IconMaximize :size="16" />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </main>
</template>