<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Html5Qrcode } from 'html5-qrcode'

// =========================================================
// 1. NAVEGAÇÃO GLOBAL E MODO DE VISÃO
// =========================================================
const menuAberto = ref(false)
// Modos: 'motorista_inicio' | 'motorista_mapa' | 'admin_lista' | 'admin_form_p1' | 'admin_editor_p2'
const telaAtual = ref('motorista_inicio')

// =========================================================
// 2. PALETA DE 6 CORES CLARAS DE SETOR + FUNÇÃO ESCURECEDORA
// =========================================================
const paletaSetores = [
  { nome: 'Azul Céu', hex: '#bae6fd' },
  { nome: 'Turquesa Claro', hex: '#99f6e4' },
  { nome: 'Âmbar Suave', hex: '#fde68a' },
  { nome: 'Lavanda', hex: '#e0e7ff' },
  { nome: 'Rosa Pastel', hex: '#fbcfe8' },
  { nome: 'Trigo Claro', hex: '#fed7aa' }
]

// Gera automaticamente a versão mais escura da cor do setor para pintar as vagas vinculadas
function escurecerCorHex(hex, fator = 0.58) {
  if (!hex) return '#334155'
  const limpo = hex.replace('#', '')
  const num = parseInt(limpo, 16)
  const r = Math.max(0, Math.floor(((num >> 16) & 255) * fator))
  const g = Math.max(0, Math.floor(((num >> 8) & 255) * fator))
  const b = Math.max(0, Math.floor((num & 255) * fator))
  return `rgb(${r}, ${g}, ${b})`
}

// =========================================================
// 3. BANCO DE DADOS EM MEMÓRIA (Usuários e Estabelecimentos)
// =========================================================
const usuariosCadastrados = ref([
  { id_usuario: 1, nome: 'Carlos Tanaka', email: 'tanaka@estacionamento.com' },
  { id_usuario: 2, nome: 'Marcos Almeida', email: 'marcos@megashopping.com' },
  { id_usuario: 3, nome: 'Ana Clara Silva', email: 'ana@redeestacionar.com' }
])

// Função auxiliar para gerar um andar inicial limpo ou pré-populado
function criarMatrizVazia(largura, altura) {
  const celulas = {}
  for (let y = 1; y <= altura; y++) {
    for (let x = 1; x <= largura; x++) {
      celulas[`${x},${y}`] = {
        x,
        y,
        setorId: null,
        corSetor: null,
        nomeSetor: null,
        tipo: 'VAZIO', // 'VAZIO' | 'ESTRADA' | 'VAGA' | 'ENTRADA' | 'SAIDA' | 'ACESSO'
        orientacao: 'NENHUMA',
        vagaId: null,
        identificador: '',
        livre: true,
        macEsp: null
      }
    }
  }
  return celulas
}

// Cria a Maquete de 2 Vagas no formato de Grid 2D (12x8) para teste imediato
function gerarEstabelecimentoMaquete() {
  const celulas = criarMatrizVazia(12, 8)
  // Entrada na esquerda (1,4 e 1,5)
  celulas['1,4'].tipo = 'ENTRADA'
  celulas['1,5'].tipo = 'ENTRADA'
  // Estrada no meio (X: 2 até 10, Y: 4 e 5)
  for (let x = 2; x <= 10; x++) {
    celulas[`${x},4`].tipo = 'ESTRADA'
    celulas[`${x},5`].tipo = 'ESTRADA'
  }
  // Saída na direita (11,4 e 11,5)
  celulas['11,4'].tipo = 'SAIDA'
  celulas['11,5'].tipo = 'SAIDA'

  // Setor A (Online) com as 2 vagas da maquete em (4,3) e (5,3)
  ;[4, 5].forEach((x, idx) => {
    celulas[`${x},3`] = {
      x,
      y: 3,
      setorId: 100,
      nomeSetor: 'Setor A (Maquete)',
      corSetor: '#bae6fd',
      tipo: 'VAGA',
      orientacao: 'NENHUMA',
      vagaId: idx + 1,
      identificador: `A${idx + 1}`,
      livre: idx === 0, // A1 livre, A2 ocupada
      macEsp: 'AA:BB:CC:DD:EE:01'
    }
  })

  // Acesso de pedestres / elevador em (8,2)
  celulas['8,2'].tipo = 'ACESSO'

  return {
    id: 1,
    nome: 'Shopping Central (Maquete 2 Vagas)',
    id_usuario: 1,
    inativo: false,
    andares: [
      {
        id_andar: 10,
        nome_andar: 'Subsolo 1',
        grid_x: 12,
        grid_y: 8,
        setores: [{ id_setor: 100, nome_setor: 'Setor A (Maquete)', cor_hex: '#bae6fd', inativo_offline: false }],
        equipamentos: [{ id_equipamento: 1, codigo_mac: 'AA:BB:CC:DD:EE:01', id_setor: 100 }],
        celulas
      }
    ]
  }
}

const estabelecimentos = ref([gerarEstabelecimentoMaquete()])

// =========================================================
// 4. ESTADOS DO NÍVEL 1 (MOTORISTA + QR CODE)
// =========================================================
const estacionamentoAtual = ref(null)
const andarMotorista = ref(null)
const vagaFavorita = ref(null)
const filtrarOcupadas = ref(false)
const modoSimuladorSensor = ref(false)
const cameraAtiva = ref(false)
const erroCamera = ref('')
let leitorQrCode = null

function carregarEstacionamentoPorId(id) {
  const encontrado = estabelecimentos.value.find(e => e.id === parseInt(id) && !e.inativo)
  if (encontrado) {
    estacionamentoAtual.value = encontrado
    andarMotorista.value = encontrado.andares[0]
    vagaFavorita.value = null
    telaAtual.value = 'motorista_mapa'
    window.history.pushState({}, '', `?id=${encontrado.id}`)
    pararCamera()
  } else {
    alert('Estacionamento não encontrado ou inativo!')
  }
}

function voltarParaInicioMotorista() {
  estacionamentoAtual.value = null
  telaAtual.value = 'motorista_inicio'
  window.history.pushState({}, '', window.location.pathname)
}

async function iniciarCamera() {
  erroCamera.value = ''
  cameraAtiva.value = true
  await nextTick()
  try {
    leitorQrCode = new Html5Qrcode('leitor-qr')
    await leitorQrCode.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 240, height: 240 } },
      (textoLido) => {
        try {
          const url = new URL(textoLido)
          const idUrl = url.searchParams.get('id')
          if (idUrl) return carregarEstacionamentoPorId(idUrl)
        } catch {
          carregarEstacionamentoPorId(textoLido)
        }
      },
      () => {}
    )
  } catch {
    erroCamera.value = 'Câmera indisponível neste dispositivo. Use o botão de simulação abaixo.'
    cameraAtiva.value = false
  }
}

async function pararCamera() {
  if (leitorQrCode && cameraAtiva.value) {
    try {
      await leitorQrCode.stop()
      leitorQrCode.clear()
    } catch {}
  }
  cameraAtiva.value = false
}

function clicarCelulaMotorista(celula) {
  if (celula.tipo !== 'VAGA') return
  if (modoSimuladorSensor.value) {
    celula.livre = !celula.livre
    if (!celula.livre && vagaFavorita.value === `${celula.x},${celula.y}`) {
      vagaFavorita.value = null
    }
    return
  }
  if (!celula.livre) return
  const chave = `${celula.x},${celula.y}`
  vagaFavorita.value = vagaFavorita.value === chave ? null : chave
}

// =========================================================
// 5. ESTADOS DO NÍVEL 3: LISTA DE ESTACIONAMENTOS
// =========================================================
const termoPesquisaAdmin = ref('')
const paginaAtualAdmin = ref(1)
const itensPorPagina = 5

const estabelecimentosFiltrados = computed(() => {
  const termo = termoPesquisaAdmin.value.trim().toLowerCase()
  if (!termo) return estabelecimentos.value
  return estabelecimentos.value.filter(
    e => e.nome.toLowerCase().includes(termo) || String(e.id) === termo
  )
})

const totalPaginasAdmin = computed(() =>
  Math.max(1, Math.ceil(estabelecimentosFiltrados.value.length / itensPorPagina))
)

const estabelecimentosPaginados = computed(() => {
  const inicio = (paginaAtualAdmin.value - 1) * itensPorPagina
  return estabelecimentosFiltrados.value.slice(inicio, inicio + itensPorPagina)
})

function alternarInativoEstabelecimento(est) {
  est.inativo = !est.inativo
}

function removerEstabelecimento(est) {
  if (confirm(`Tem certeza que deseja REMOVER permanentemente "${est.nome}" e todos os seus andares e vagas?`)) {
    estabelecimentos.value = estabelecimentos.value.filter(item => item.id !== est.id)
  }
}

// =========================================================
// 6. ESTADOS DO NÍVEL 3: PARTE 1 (FORMULÁRIO DE CADASTRO/EDIÇÃO)
// =========================================================
const modoEdicaoId = ref(null)
const formEstabelecimento = ref({
  nome: '',
  id_usuario: 1,
  andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
})

function abrirNovoCadastro() {
  modoEdicaoId.value = null
  formEstabelecimento.value = {
    nome: '',
    id_usuario: usuariosCadastrados.value[0].id_usuario,
    andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
  }
  telaAtual.value = 'admin_form_p1'
}

function abrirEdicaoEstabelecimento(est) {
  modoEdicaoId.value = est.id
  // Faz cópia profunda (Deep Copy) para só alterar o banco ao clicar em Salvar no final
  formEstabelecimento.value = JSON.parse(JSON.stringify(est))
  telaAtual.value = 'admin_form_p1'
}

function adicionarAndarForm() {
  if (formEstabelecimento.value.andares.length >= 10) return
  const numero = formEstabelecimento.value.andares.length + 1
  formEstabelecimento.value.andares.push({
    id_andar: Date.now() + numero,
    nome_andar: `Andar ${numero}`,
    grid_x: 30,
    grid_y: 20
  })
}

function removerAndarForm(index) {
  if (index === 0) return
  formEstabelecimento.value.andares.splice(index, 1)
}

function avancarParaEditorP2() {
  if (!formEstabelecimento.value.nome.trim()) {
    alert('Digite o nome do estabelecimento antes de continuar.')
    return
  }
  if (formEstabelecimento.value.andares.some(a => !a.nome_andar.trim())) {
    alert('Preencha o nome de todos os andares.')
    return
  }

  // Garante que cada andar possua sua matriz de células inicializada (padrão 30x20)
  formEstabelecimento.value.andares.forEach((andar) => {
    if (!andar.celulas) {
      andar.grid_x = andar.grid_x || 30
      andar.grid_y = andar.grid_y || 20
      andar.setores = andar.setores || []
      andar.equipamentos = andar.equipamentos || []
      andar.celulas = criarMatrizVazia(andar.grid_x, andar.grid_y)
    }
  })

  andarEditorIndex.value = 0
  historicoUndo.value = []
  historicoRedo.value = []
  selecionados.value.clear()
  ferramentaCarimbo.value = null
  telaAtual.value = 'admin_editor_p2'
}

// =========================================================
// 7. ESTADOS DO NÍVEL 3: PARTE 2 (EDITOR GAMIFICADO 2D)
// =========================================================
const andarEditorIndex = ref(0)
const andarEditorAtual = computed(() => formEstabelecimento.value.andares[andarEditorIndex.value])

// Pilhas de Desfazer / Refazer
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

// Avisos de Validação em Tempo Real no Topo Esquerdo
const haVagasSemEquipamento = computed(() => {
  if (!andarEditorAtual.value || !andarEditorAtual.value.celulas) return false
  return Object.values(andarEditorAtual.value.celulas).some(
    c => c.tipo === 'VAGA' && !c.macEsp
  )
})

const haVagasSemSetor = computed(() => {
  if (!andarEditorAtual.value || !andarEditorAtual.value.celulas) return false
  return Object.values(andarEditorAtual.value.celulas).some(
    c => c.tipo === 'VAGA' && !c.setorId
  )
})

// Seleção de Quadrados (Clique, Ctrl+Clique e Arrastar)
const selecionados = ref(new Set())
const arrastando = ref(false)
const pontoInicialArrasto = ref(null)
const baseSelecionadosCtrl = ref(new Set())
const mostrarMenuFlutuante = ref(false)

function iniciarSelecaoCelula(x, y, event) {
  // Se estiver com um carimbo (Entrada/Saída/Acesso/Equipamento) grudado no mouse, aplica o carimbo!
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
// 8. AÇÕES DO MENU FLUTUANTE (ESTRADAS, SETORES E VAGAS)
// =========================================================
function aplicarTipoSelecao(novoTipo) {
  const celulas = andarEditorAtual.value.celulas
  const chaves = Array.from(selecionados.value)

  // Verifica conflito de sobreposição entre VAGA e ESTRADA
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

  chaves.forEach((k) => {
    const c = celulas[k]
    if (!c) return
    c.tipo = novoTipo
    c.orientacao = 'NENHUMA'
    if (novoTipo === 'VAGA') {
      c.macEsp = null // Começa amarela (não vinculada)
      c.identificador = ''
      c.livre = true
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
    } else if (c.tipo === tipoAlvo) {
      c.tipo = 'VAZIO'
      c.macEsp = null
      c.identificador = ''
    }
  })
  mostrarMenuFlutuante.value = false
  selecionados.value.clear()
}

// Modal de Criação de Setor (Nome + 6 Cores Claras)
const modalSetorAberto = ref(false)
const novoSetorNome = ref('')
const novoSetorCor = ref(paletaSetores[0].hex)

function abrirModalSetor() {
  novoSetorNome.value = ''
  novoSetorCor.value = paletaSetores[0].hex
  modalSetorAberto.value = true
}

function confirmarSetorSelecao() {
  if (!novoSetorNome.value.trim()) {
    alert('Digite um nome para o setor!')
    return
  }
  salvarSnapshot()
  const idSetor = Date.now()
  andarEditorAtual.value.setores.push({
    id_setor: idSetor,
    nome_setor: novoSetorNome.value.trim(),
    cor_hex: novoSetorCor.value,
    inativo_offline: false
  })

  selecionados.value.forEach((k) => {
    const c = andarEditorAtual.value.celulas[k]
    if (c) {
      c.setorId = idSetor
      c.nomeSetor = novoSetorNome.value.trim()
      c.corSetor = novoSetorCor.value
    }
  })

  modalSetorAberto.value = false
  mostrarMenuFlutuante.value = false
  selecionados.value.clear()
}

// Modal de Redimensionamento do Grid (Máx 100x100)
const modalGridAberto = ref(false)
const inputGridX = ref(30)
const inputGridY = ref(20)

function abrirModalTamanhoGrid() {
  inputGridX.value = andarEditorAtual.value.grid_x
  inputGridY.value = andarEditorAtual.value.grid_y
  modalGridAberto.value = true
}

function confirmarTamanhoGrid() {
  const nx = Math.min(100, Math.max(5, parseInt(inputGridX.value) || 30))
  const ny = Math.min(100, Math.max(5, parseInt(inputGridY.value) || 20))
  salvarSnapshot()

  const novasCelulas = criarMatrizVazia(nx, ny)
  // Preserva o que já estava desenhado dentro dos limites
  Object.values(andarEditorAtual.value.celulas).forEach((antiga) => {
    if (antiga.x <= nx && antiga.y <= ny) {
      novasCelulas[`${antiga.x},${antiga.y}`] = antiga
    }
  })

  andarEditorAtual.value.grid_x = nx
  andarEditorAtual.value.grid_y = ny
  andarEditorAtual.value.celulas = novasCelulas
  modalGridAberto.value = false
}

// =========================================================
// 9. MENU DIREITO: GRUPO 1 (ACESSOS) E GRUPO 2 (EQUIPAMENTOS)
// =========================================================
const hoverCoord = ref(null)
const ferramentaCarimbo = ref(null) // { categoria: 'ACESSO' | 'EQUIPAMENTO', tipo, orientacao, w, h }

// Modal para escolher tamanho variável de Entrada/Saída/Acesso
const modalAcessoAberto = ref(false)
const configAcessoTemp = ref({ tipo: 'ENTRADA', orientacao: 'H', x: 2, y: 1 })

function prepararAcesso(tipo, orientacao) {
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
  configAcessoTemp.value = {
    tipo,
    orientacao,
    x: orientacao === 'H' ? 2 : 1,
    y: orientacao === 'V' ? 2 : 1
  }
  modalAcessoAberto.value = true
}

function ativarCarimboAcesso() {
  const w = Math.max(1, Math.min(20, parseInt(configAcessoTemp.value.x) || 1))
  const h = Math.max(1, Math.min(20, parseInt(configAcessoTemp.value.y) || 1))
  ferramentaCarimbo.value = {
    categoria: 'ACESSO',
    tipo: configAcessoTemp.value.tipo,
    orientacao: configAcessoTemp.value.orientacao,
    w,
    h
  }
  modalAcessoAberto.value = false
}

// Grupo 2: Lista exata de formatos de Equipamentos do roteiro
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
  ferramentaCarimbo.value = {
    categoria: 'EQUIPAMENTO',
    tipo: 'ESP32',
    w,
    h
  }
}

// Verifica se a célula (x,y) está debaixo da sombra verde do carimbo no mouse
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

// Modal para informar o MAC do ESP32 ao carimbar vagas amarelas
const modalMacAberto = ref(false)
const inputMacEsp = ref('AA:BB:CC:DD:EE:01')
const inputPrefixoVaga = ref('A')
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

  // CASO 1: Carimbo de Entrada / Saída / Acesso
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

  // CASO 2: Carimbo de Equipamento (ESP32) sobre Vagas
  if (carimbo.categoria === 'EQUIPAMENTO') {
    const vagasDebaixo = coordsAfetadas.filter(k => celulas[k].tipo === 'VAGA')
    if (vagasDebaixo.length === 0) {
      alert('Nenhuma VAGA amarela encontrada sob este carimbo de equipamento! Crie as vagas primeiro.')
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
  const prefixo = inputPrefixoVaga.value.trim().toUpperCase() || 'V'

  coordenadasCarimboPendente.value.forEach((k, idx) => {
    celulas[k].macEsp = inputMacEsp.value.trim().toUpperCase()
    celulas[k].identificador = `${prefixo}${idx + 1}`
  })

  modalMacAberto.value = false
  ferramentaCarimbo.value = null
}

// =========================================================
// 10. SALVAR / FINALIZAR ESTACIONAMENTO (BATCH SAVE)
// =========================================================
function finalizarSalvarEstacionamento() {
  // Verifica em TODOS os andares se há vagas amarelas ou sem setor
  for (const andar of formEstabelecimento.value.andares) {
    const listaCelulas = Object.values(andar.celulas)
    const temSemEquip = listaCelulas.some(c => c.tipo === 'VAGA' && !c.macEsp)
    const temSemSetor = listaCelulas.some(c => c.tipo === 'VAGA' && !c.setorId)

    if (temSemEquip || temSemSetor) {
      alert(`Não é possível salvar! O andar "${andar.nome_andar}" ainda possui vagas amarelas sem equipamento ou vagas fora de um setor.`)
      return
    }
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

  alert('✅ Estacionamento salvo com sucesso! (Apenas os quadrados preenchidos foram registrados).')
  telaAtual.value = 'admin_lista'
}

// =========================================================
// 11. CICLO DE VIDA INICIAL
// =========================================================
onMounted(() => {
  window.addEventListener('mouseup', finalizarSelecaoMouse)
  const parametrosUrl = new URLSearchParams(window.location.search)
  const idEstacionamento = parametrosUrl.get('id')
  if (idEstacionamento) {
    carregarEstacionamentoPorId(idEstacionamento)
  }
})

onUnmounted(() => {
  window.removeEventListener('mouseup', finalizarSelecaoMouse)
  pararCamera()
})
</script>

<template>
  <div class="app-container">
    <!-- BOTÃO HAMBÚRGUER GLOBAL -->
    <button class="btn-hamburguer" @click="menuAberto = !menuAberto">☰</button>

    <!-- MENU LATERAL DE NAVEGAÇÃO ENTRE OS NÍVEIS -->
    <aside v-if="menuAberto" class="menu-lateral">
      <div class="menu-header">
        <h2>Vaga Certa</h2>
        <button class="btn-fechar" @click="menuAberto = false">✖</button>
      </div>
      <nav class="menu-links">
        <span class="menu-secao">📱 NÍVEL 1 (MOTORISTA)</span>
        <a href="#" @click.prevent="voltarParaInicioMotorista(); menuAberto = false">📷 Leitor de QR Code</a>
        <a
          v-for="est in estabelecimentos.filter(e => !e.inativo)"
          :key="est.id"
          href="#"
          @click.prevent="carregarEstacionamentoPorId(est.id); menuAberto = false"
        >
          🅿️ {{ est.nome }}
        </a>

        <span class="menu-secao">🛠️ NÍVEL 3 (ADMIN DEV)</span>
        <a href="#" @click.prevent="telaAtual = 'admin_lista'; menuAberto = false">
          📋 Gerenciar Estacionamentos
        </a>
        <a href="#" @click.prevent="abrirNovoCadastro(); menuAberto = false">
          ➕ Novo Estacionamento (Editor 2D)
        </a>
      </nav>
    </aside>

    <!-- =======================================================
         TELA 1 (NÍVEL 1): PÁGINA PRINCIPAL COM BOTÃO DE QR CODE
         ======================================================= -->
    <main v-if="telaAtual === 'motorista_inicio'" class="tela-inicial">
      <div class="hero-card">
        <div class="icone-destaque">🅿️</div>
        <h1 class="titulo-principal">Encontre sua vaga em segundos</h1>
        <p class="descricao-principal">
          Aponte a câmera para o <strong>QR Code</strong> localizado na entrada do estacionamento para abrir o mapa de vagas em tempo real.
        </p>

        <div v-if="cameraAtiva" class="camera-wrapper">
          <div id="leitor-qr"></div>
          <button class="btn-cancelar-camera" @click="pararCamera">✖ Fechar Câmera</button>
        </div>

        <button v-else class="btn-ler-qr" @click="iniciarCamera">
          📷 Ler QR Code do Estacionamento
        </button>

        <p v-if="erroCamera" class="msg-erro">{{ erroCamera }}</p>

        <div class="area-teste-dev">
          <span>Acesso Rápido de Demonstração:</span>
          <button
            v-for="est in estabelecimentos.filter(e => !e.inativo)"
            :key="est.id"
            class="btn-teste-dev"
            @click="carregarEstacionamentoPorId(est.id)"
          >
            ⚡ Abrir {{ est.nome }} (ID: {{ est.id }})
          </button>
          <button class="btn-teste-dev destaque-admin" @click="telaAtual = 'admin_lista'">
            🛠️ Ir para Painel Admin Dev (Criar / Editar Mapas 2D)
          </button>
        </div>
      </div>
    </main>

    <!-- =======================================================
         TELA 2 (NÍVEL 1): MAPA 2D DO MOTORISTA (COORDENADAS X,Y)
         ======================================================= -->
    <div v-else-if="telaAtual === 'motorista_mapa' && estacionamentoAtual" class="painel-estacionamento">
      <header class="painel-header">
        <div>
          <h1>{{ estacionamentoAtual.nome }}</h1>
          <p class="subtitulo">Toque em uma vaga livre (verde) para marcá-la em roxo</p>
        </div>
        <button class="btn-secundario" @click="voltarParaInicioMotorista">📷 Ler outro QR Code</button>
      </header>

      <div class="abas-andares">
        <button
          v-for="andar in estacionamentoAtual.andares"
          :key="andar.id_andar"
          class="aba-btn"
          :class="{ 'aba-ativa': andarMotorista.id_andar === andar.id_andar }"
          @click="andarMotorista = andar"
        >
          {{ andar.nome_andar }}
        </button>
      </div>

      <div class="barra-controles">
        <div class="controles-esquerda">
          <label class="filtro-toggle">
            <input type="checkbox" v-model="filtrarOcupadas" />
            Deixar vagas ocupadas cinzas
          </label>
          <label class="filtro-toggle">
            <input type="checkbox" v-model="modoSimuladorSensor" />
            🔄 Clique simula Sensor HC-SR04 (Carro Entrando/Saindo)
          </label>
        </div>

        <div class="legenda">
          <span class="badge" style="background:#2563eb">Entrada</span>
          <span class="badge" style="background:#ea580c">Saída</span>
          <span class="badge" style="background:#16a34a">Vaga Livre</span>
          <span class="badge" style="background:#9333ea">Sua Vaga</span>
          <span class="badge" style="background:#dc2626">Ocupada</span>
        </div>
      </div>

      <!-- Renderização Fiel da Matriz 2D para o Motorista -->
      <div class="grid-scroll-wrapper">
        <div
          class="grid-tabuleiro"
          :style="{
            gridTemplateColumns: `repeat(${andarMotorista.grid_x}, 42px)`
          }"
        >
          <template v-for="y in andarMotorista.grid_y" :key="`mot-row-${y}`">
            <div
              v-for="x in andarMotorista.grid_x"
              :key="`mot-cell-${x}-${y}`"
              class="celula-fundo-setor"
              :style="{
                backgroundColor: andarMotorista.celulas[`${x},${y}`]?.corSetor || 'transparent'
              }"
              @click="clicarCelulaMotorista(andarMotorista.celulas[`${x},${y}`])"
            >
              <div
                class="quadrado-interno"
                :class="{
                  'q-invisivel': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAZIO',
                  'q-estrada': andarMotorista.celulas[`${x},${y}`]?.tipo === 'ESTRADA',
                  'q-entrada': andarMotorista.celulas[`${x},${y}`]?.tipo === 'ENTRADA',
                  'q-saida': andarMotorista.celulas[`${x},${y}`]?.tipo === 'SAIDA',
                  'q-acesso': andarMotorista.celulas[`${x},${y}`]?.tipo === 'ACESSO',
                  'q-vaga-livre': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && andarMotorista.celulas[`${x},${y}`]?.livre && vagaFavorita !== `${x},${y}`,
                  'q-vaga-roxa': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && andarMotorista.celulas[`${x},${y}`]?.livre && vagaFavorita === `${x},${y}`,
                  'q-vaga-ocupada': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarMotorista.celulas[`${x},${y}`]?.livre && !filtrarOcupadas,
                  'q-vaga-cinza': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarMotorista.celulas[`${x},${y}`]?.livre && filtrarOcupadas
                }"
              >
                <span v-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA'">
                  {{ andarMotorista.celulas[`${x},${y}`]?.identificador }}
                </span>
                <span v-else-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'ENTRADA'">ENT</span>
                <span v-else-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'SAIDA'">SAI</span>
                <span v-else-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'ACESSO'">🚶</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- =======================================================
         TELA 3 (NÍVEL 3): LISTA DE ESTACIONAMENTOS (ADMIN DEV)
         ======================================================= -->
    <div v-else-if="telaAtual === 'admin_lista'" class="admin-container">
      <header class="painel-header">
        <div>
          <h1>Gerenciamento de Estacionamentos (Admin Dev)</h1>
          <p class="subtitulo">Pesquise, adicione, edite o mapa 2D, inative ou remova estabelecimentos</p>
        </div>
      </header>

      <!-- Barra de Pesquisa + Botão de Adicionar -->
      <div class="barra-pesquisa-admin">
        <input
          v-model="termoPesquisaAdmin"
          type="text"
          placeholder="🔍 Pesquisar por nome ou ID..."
          class="input-pesquisa-grande"
          @input="paginaAtualAdmin = 1"
        />
        <button class="btn-primario" @click="abrirNovoCadastro">
          ➕ Adicionar Estacionamento
        </button>
      </div>

      <!-- Lista Paginada -->
      <div class="lista-card">
        <div
          v-for="est in estabelecimentosPaginados"
          :key="est.id"
          class="linha-estabelecimento"
          :class="{ 'linha-inativa': est.inativo }"
        >
          <div class="info-est">
            <span class="id-badge">#{{ est.id }}</span>
            <div>
              <h3>
                {{ est.nome }}
                <span v-if="est.inativo" class="tag-inativo">INATIVO</span>
              </h3>
              <p class="meta-est">
                Andares: {{ est.andares.length }} |
                Responsável ID: #{{ est.id_usuario }}
              </p>
            </div>
          </div>

          <!-- Ícones à direita: Editar, Inativar e Remover -->
          <div class="acoes-direita">
            <button class="btn-icone" title="Visualizar como Motorista" @click="carregarEstacionamentoPorId(est.id)">
              👁️
            </button>
            <button class="btn-icone editar" title="Editar Estacionamento" @click="abrirEdicaoEstabelecimento(est)">
              ✏️
            </button>
            <button
              class="btn-icone inativar"
              :title="est.inativo ? 'Reativar' : 'Inativar'"
              @click="alternarInativoEstabelecimento(est)"
            >
              {{ est.inativo ? '✅' : '🚫' }}
            </button>
            <button class="btn-icone remover" title="Remover Permanentemente" @click="removerEstabelecimento(est)">
              🗑️
            </button>
          </div>
        </div>

        <div v-if="estabelecimentosPaginados.length === 0" class="lista-vazia">
          Nenhum estacionamento encontrado.
        </div>
      </div>

      <!-- Paginação -->
      <div class="paginacao-admin">
        <button :disabled="paginaAtualAdmin <= 1" @click="paginaAtualAdmin--">⬅️ Anterior</button>
        <span>Página {{ paginaAtualAdmin }} de {{ totalPaginasAdmin }}</span>
        <button :disabled="paginaAtualAdmin >= totalPaginasAdmin" @click="paginaAtualAdmin++">Próxima ➡️</button>
      </div>
    </div>

    <!-- =======================================================
         TELA 4 (NÍVEL 3): ADICIONAR / EDITAR - PARTE 1 (DADOS E ANDARES)
         ======================================================= -->
    <div v-else-if="telaAtual === 'admin_form_p1'" class="admin-container">
      <header class="painel-header">
        <div>
          <h1>{{ modoEdicaoId ? 'Editar Estacionamento' : 'Novo Estacionamento' }} — Parte 1</h1>
          <p class="subtitulo">Defina os dados gerais e a lista de andares (máx. 10 andares)</p>
        </div>
        <button class="btn-secundario" @click="telaAtual = 'admin_lista'">⬅️ Voltar à Lista</button>
      </header>

      <div class="form-card">
        <div class="campo-grupo">
          <label>Nome do Estabelecimento (máx. 50 caracteres)</label>
          <input
            v-model="formEstabelecimento.nome"
            type="text"
            maxlength="50"
            placeholder="Ex: Shopping Sorocaba Center"
          />
        </div>

        <div class="campo-grupo">
          <label>Vincular Usuário Responsável (Dono do Estacionamento)</label>
          <select v-model="formEstabelecimento.id_usuario">
            <option v-for="u in usuariosCadastrados" :key="u.id_usuario" :value="u.id_usuario">
              #{{ u.id_usuario }} - {{ u.nome }} ({{ u.email }})
            </option>
          </select>
        </div>

        <!-- Lista Dinâmica de Andares com botões + e - -->
        <div class="campo-grupo">
          <label>Andares do Estacionamento ({{ formEstabelecimento.andares.length }}/10)</label>
          <div
            v-for="(andar, idx) in formEstabelecimento.andares"
            :key="andar.id_andar"
            class="linha-andar-dinamica"
          >
            <input
              v-model="andar.nome_andar"
              type="text"
              maxlength="25"
              :placeholder="`Nome do Andar ${idx + 1}`"
            />

            <!-- Do 2º em diante todos têm o botão de '-' para remover -->
            <button
              v-if="idx >= 1"
              class="btn-mais-menos btn-menos"
              title="Remover este andar"
              @click="removerAndarForm(idx)"
            >
              −
            </button>

            <!-- O botão de '+' sempre se move para o último andar (até o limite de 10) -->
            <button
              v-if="idx === formEstabelecimento.andares.length - 1 && formEstabelecimento.andares.length < 10"
              class="btn-mais-menos btn-mais"
              title="Adicionar novo andar abaixo"
              @click="adicionarAndarForm"
            >
              +
            </button>
          </div>
        </div>

        <div class="rodape-form">
          <button class="btn-primario btn-grande" @click="avancarParaEditorP2">
            🎮 Avançar para Parte 2: Editor de Mapa 2D ➡️
          </button>
        </div>
      </div>
    </div>

    <!-- =======================================================
         TELA 5 (NÍVEL 3): PARTE 2 - EDITOR GAMIFICADO DE GRID 2D
         ======================================================= -->
    <div v-else-if="telaAtual === 'admin_editor_p2' && andarEditorAtual" class="editor-layout">
      <!-- BARRA SUPERIOR DO EDITOR -->
      <header class="editor-topbar">
        <div class="topbar-esquerda">
          <button class="btn-secundario" @click="telaAtual = 'admin_form_p1'">⬅️ Parte 1</button>

          <!-- Seletor de Andar (ou texto fixo se houver apenas 1) -->
          <div class="seletor-andar-box">
            <span>Andar:</span>
            <select
              v-if="formEstabelecimento.andares.length > 1"
              v-model="andarEditorIndex"
              @change="selecionados.clear(); historicoUndo = []; historicoRedo = []"
            >
              <option v-for="(a, idx) in formEstabelecimento.andares" :key="a.id_andar" :value="idx">
                {{ a.nome_andar }} ({{ a.grid_x }}x{{ a.grid_y }})
              </option>
            </select>
            <strong v-else>{{ andarEditorAtual.nome_andar }}</strong>
          </div>

          <button class="btn-secundario" @click="abrirModalTamanhoGrid">
            📐 Tamanho do Grid ({{ andarEditorAtual.grid_x }}x{{ andarEditorAtual.grid_y }})
          </button>

          <button class="btn-secundario" :disabled="historicoUndo.length === 0" @click="desfazer">
            ↩️ Desfazer
          </button>
          <button class="btn-secundario" :disabled="historicoRedo.length === 0" @click="refazer">
            ↪️ Refazer
          </button>
        </div>

        <button
          class="btn-salvar-final"
          :disabled="haVagasSemEquipamento || haVagasSemSetor"
          @click="finalizarSalvarEstacionamento"
        >
          💾 Finalizar e Salvar no Banco
        </button>
      </header>

      <!-- AVISOS DE VALIDAÇÃO E INSTRUÇÃO NO TOPO ESQUERDO ACIMA DO GRID -->
      <div class="barra-avisos-editor">
        <div class="avisos-esquerda">
          <span v-if="haVagasSemEquipamento" class="alerta-tag erro">
            ⚠️ Há vagas não linkadas a equipamentos
          </span>
          <span v-if="haVagasSemSetor" class="alerta-tag erro">
            ⚠️ Há vagas que não estão linkadas a um setor
          </span>
          <span v-if="!haVagasSemEquipamento && !haVagasSemSetor" class="alerta-tag ok">
            ✅ Todas as vagas deste andar estão validadas!
          </span>
        </div>

        <div v-if="ferramentaCarimbo" class="modo-carimbo-ativo">
          <span>
            🎯 Carimbo Ativo: <strong>{{ ferramentaCarimbo.tipo }} ({{ ferramentaCarimbo.w }}x{{ ferramentaCarimbo.h }})</strong> — Clique no Grid para posicionar
          </span>
          <button @click="ferramentaCarimbo = null">✖ Cancelar Carimbo</button>
        </div>

        <!-- MENU DE CONTEXTO ACIMA DO GRID QUANDO HÁ QUADRADOS ROXOS SELECIONADOS -->
        <div v-if="mostrarMenuFlutuante && selecionados.size > 0" class="menu-selecao-flutuante">
          <span class="contagem-sel">{{ selecionados.size }} quadrado(s) selecionado(s):</span>

          <div class="grupo-acao-item">
            <span>🛣️ Estrada:</span>
            <button class="btn-mini add" title="Adicionar Estrada" @click="aplicarTipoSelecao('ESTRADA')">➕</button>
            <button class="btn-mini rem" title="Remover Estrada" @click="removerTipoSelecao('ESTRADA')">➖</button>
          </div>

          <div class="grupo-acao-item">
            <span>🎨 Setor:</span>
            <button class="btn-mini add" title="Definir Setor e Cor" @click="abrirModalSetor">➕</button>
            <button class="btn-mini rem" title="Remover Setor" @click="removerTipoSelecao('SETOR')">➖</button>
          </div>

          <div class="grupo-acao-item">
            <span>🅿️ Vagas:</span>
            <button class="btn-mini add" title="Adicionar Vagas Amarelas" @click="aplicarTipoSelecao('VAGA')">➕</button>
            <button class="btn-mini rem" title="Remover Vagas" @click="removerTipoSelecao('VAGA')">➖</button>
          </div>

          <button class="btn-mini limpar" @click="selecionados.clear(); mostrarMenuFlutuante = false">✖</button>
        </div>
      </div>

      <!-- CORPO PRINCIPAL: GRID À ESQUERDA + MENU DE FERRAMENTAS À DIREITA -->
      <div class="editor-workspace">
        <!-- ÁREA DO GRID COM COORDENADAS X (TOPO) E Y (ESQUERDA) -->
        <div class="area-grid-principal">
          <div class="matriz-com-coordenadas">
            <!-- Linha de Cabeçalho com Coordenadas X -->
            <div
              class="linha-coordenadas-x"
              :style="{ gridTemplateColumns: `36px repeat(${andarEditorAtual.grid_x}, 34px)` }"
            >
              <div class="canto-xy">Y\X</div>
              <div v-for="x in andarEditorAtual.grid_x" :key="`coord-x-${x}`" class="rotulo-coord">
                {{ x }}
              </div>
            </div>

            <!-- Linhas Y + Quadrados do Grid -->
            <div
              v-for="y in andarEditorAtual.grid_y"
              :key="`row-${y}`"
              class="linha-grid-y"
              :style="{ gridTemplateColumns: `36px repeat(${andarEditorAtual.grid_x}, 34px)` }"
            >
              <!-- Coordenada Y na esquerda -->
              <div class="rotulo-coord">{{ y }}</div>

              <!-- Célula do Grid (Plano de fundo recebe a cor clara do Setor) -->
              <div
                v-for="x in andarEditorAtual.grid_x"
                :key="`cell-${x}-${y}`"
                class="celula-editor-fundo"
                :style="{
                  backgroundColor: andarEditorAtual.celulas[`${x},${y}`]?.corSetor || 'transparent'
                }"
                @mousedown.prevent="iniciarSelecaoCelula(x, y, $event)"
                @mouseenter="moverMouseCelula(x, y)"
              >
                <!-- Quadrado Interno (Com borda e espaçamento nas 4 direções) -->
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
                  :title="`(${x}, ${y}) ${andarEditorAtual.celulas[`${x},${y}`]?.identificador || andarEditorAtual.celulas[`${x},${y}`]?.tipo}`"
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

        <!-- MENU LATERAL DIREITO (GRUPO 1 E GRUPO 2) -->
        <aside class="sidebar-direita-editor">
          <!-- GRUPO 1: ENTRADAS / SAÍDAS / ACESSOS -->
          <div class="painel-ferramentas">
            <h4>🚪 Grupo 1: Entradas / Saídas / Acessos</h4>
            <p class="dica-painel">Clique para definir o tamanho e posicionar no Grid</p>

            <!-- Linha 1: Entrada (Azul) -->
            <div class="linha-botoes-dupla">
              <button class="btn-ferramenta cor-entrada" @click="prepararAcesso('ENTRADA', 'H')">
                ➡️ Entrada (Horiz.)
              </button>
              <button class="btn-ferramenta cor-entrada" @click="prepararAcesso('ENTRADA', 'V')">
                ⬇️ Entrada (Vert.)
              </button>
            </div>

            <!-- Linha 2: Saída (Laranja) -->
            <div class="linha-botoes-dupla">
              <button class="btn-ferramenta cor-saida" @click="prepararAcesso('SAIDA', 'H')">
                ➡️ Saída (Horiz.)
              </button>
              <button class="btn-ferramenta cor-saida" @click="prepararAcesso('SAIDA', 'V')">
                ⬇️ Saída (Vert.)
              </button>
            </div>

            <!-- Linha 3: Acesso (Verde) -->
            <div class="linha-botoes-dupla">
              <button class="btn-ferramenta cor-acesso" @click="prepararAcesso('ACESSO', 'H')">
                🚶 Acesso (Horiz.)
              </button>
              <button class="btn-ferramenta cor-acesso" @click="prepararAcesso('ACESSO', 'V')">
                🚶 Acesso (Vert.)
              </button>
            </div>
          </div>

          <!-- GRUPO 2: EQUIPAMENTOS (ESP32) -->
          <div class="painel-ferramentas">
            <h4>📡 Grupo 2: Equipamentos (ESP32)</h4>
            <p class="dica-painel">Escolha o formato (X por Y) e clique sobre as vagas amarelas para vincular</p>

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

          <!-- LEGENDA RÁPIDA DO EDITOR -->
          <div class="painel-ferramentas legenda-editor">
            <h4>📌 Cores do Editor</h4>
            <div><span class="amostra" style="background:#cbd5e1"></span> Cinza Claro: Vazio (Ignorado no BD)</div>
            <div><span class="amostra" style="background:#1e293b"></span> Asfalto Escuro: Estrada</div>
            <div><span class="amostra" style="background:#eab308"></span> Amarelo: Vaga sem ESP32</div>
            <div><span class="amostra" style="background:#0284c7"></span> Cor Escura do Setor: Vaga Vinculada</div>
          </div>
        </aside>
      </div>
    </div>

    <!-- =======================================================
         MODAIS POP-UP DO EDITOR GAMIFICADO
         ======================================================= -->

    <!-- Modal 1: Criar Setor (Nome + 6 Cores Claras) -->
    <div v-if="modalSetorAberto" class="modal-backdrop">
      <div class="modal-box">
        <h3>🎨 Definir Setor para a Seleção</h3>
        <div class="campo-grupo">
          <label>Nome do Setor</label>
          <input v-model="novoSetorNome" type="text" maxlength="25" placeholder="Ex: Setor A - Subsolo" />
        </div>
        <div class="campo-grupo">
          <label>Escolha uma das 6 cores claras de fundo:</label>
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

    <!-- Modal 2: Tamanho do Grid (X e Y máx 100) -->
    <div v-if="modalGridAberto" class="modal-backdrop">
      <div class="modal-box">
        <h3>📐 Alterar Tamanho do Grid</h3>
        <p class="subtitulo">Máximo permitido: 100 x 100 quadrados</p>
        <div class="linha-botoes-dupla" style="margin-top:12px">
          <div class="campo-grupo">
            <label>Largura (Eixo X)</label>
            <input v-model="inputGridX" type="number" min="5" max="100" />
          </div>
          <div class="campo-grupo">
            <label>Altura (Eixo Y)</label>
            <input v-model="inputGridY" type="number" min="5" max="100" />
          </div>
        </div>
        <div class="modal-acoes">
          <button class="btn-secundario" @click="modalGridAberto = false">Cancelar</button>
          <button class="btn-primario" @click="confirmarTamanhoGrid">Aplicar</button>
        </div>
      </div>
    </div>

    <!-- Modal 3: Dimensões de Entrada / Saída / Acesso -->
    <div v-if="modalAcessoAberto" class="modal-backdrop">
      <div class="modal-box">
        <h3>🚪 Configurar {{ configAcessoTemp.tipo }} ({{ configAcessoTemp.orientacao === 'H' ? 'Horizontal' : 'Vertical' }})</h3>
        <div class="linha-botoes-dupla" style="margin-top:12px">
          <div class="campo-grupo">
            <label>Largura X {{ configAcessoTemp.orientacao === 'V' ? '(Fixo em 1)' : '' }}</label>
            <input
              v-model="configAcessoTemp.x"
              type="number"
              min="1"
              max="20"
              :disabled="configAcessoTemp.orientacao === 'V'"
            />
          </div>
          <div class="campo-grupo">
            <label>Altura Y {{ configAcessoTemp.orientacao === 'H' ? '(Fixo em 1)' : '' }}</label>
            <input
              v-model="configAcessoTemp.y"
              type="number"
              min="1"
              max="20"
              :disabled="configAcessoTemp.orientacao === 'H'"
            />
          </div>
        </div>
        <div class="modal-acoes">
          <button class="btn-secundario" @click="modalAcessoAberto = false">Cancelar</button>
          <button class="btn-primario" @click="ativarCarimboAcesso">OK (Grudar no Mouse)</button>
        </div>
      </div>
    </div>

    <!-- Modal 4: Vincular Equipamento ESP32 às Vagas Amarelas -->
    <div v-if="modalMacAberto" class="modal-backdrop">
      <div class="modal-box">
        <h3>📡 Vincular Equipamento ESP32</h3>
        <p class="subtitulo">
          Vinculando {{ coordenadasCarimboPendente.length }} vaga(s) selecionadas ao microcontrolador.
        </p>
        <div class="campo-grupo" style="margin-top:12px">
          <label>Código MAC do ESP32</label>
          <input v-model="inputMacEsp" type="text" maxlength="17" placeholder="AA:BB:CC:DD:EE:FF" />
        </div>
        <div class="campo-grupo">
          <label>Prefixo das Vagas (Ex: A gera A1, A2...)</label>
          <input v-model="inputPrefixoVaga" type="text" maxlength="4" placeholder="A" />
        </div>
        <div class="modal-acoes">
          <button class="btn-secundario" @click="modalMacAberto = false">Cancelar</button>
          <button class="btn-primario" @click="confirmarVinculoEquipamento">Vincular Vagas</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style>
:root {
  --bg-painel: #f1f5f9;
  --bg-card: #ffffff;
  --texto-principal: #0f172a;
  --texto-secundario: #475569;
  --borda: #cbd5e1;
  --destaque-azul: #2563eb;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-painel: #0f172a;
    --bg-card: #1e293b;
    --texto-principal: #f8fafc;
    --texto-secundario: #94a3b8;
    --borda: #334155;
    --destaque-azul: #3b82f6;
  }
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
}

body { overflow-x: hidden; }

.app-container {
  width: 100%;
  min-height: 100vh;
  background: var(--bg-painel);
  color: var(--texto-principal);
}

/* Menu Hambúrguer e Lateral */
.btn-hamburguer {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 1000;
  background: var(--bg-card);
  color: var(--texto-principal);
  border: 1px solid var(--borda);
  width: 44px;
  height: 44px;
  border-radius: 10px;
  font-size: 22px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.menu-lateral {
  position: fixed;
  top: 0;
  left: 0;
  width: 290px;
  height: 100%;
  background: var(--bg-card);
  color: var(--texto-principal);
  z-index: 1001;
  padding: 20px;
  box-shadow: 4px 0 15px rgba(0,0,0,0.3);
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--borda);
}

.btn-fechar {
  background: none;
  border: none;
  color: var(--texto-principal);
  font-size: 20px;
  cursor: pointer;
}

.menu-links {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-secao {
  font-size: 11px;
  font-weight: 800;
  color: var(--texto-secundario);
  margin-top: 12px;
  letter-spacing: 1px;
}

.menu-links a {
  color: var(--texto-principal);
  text-decoration: none;
  font-size: 14px;
  padding: 10px;
  border-radius: 8px;
}
.menu-links a:hover { background: var(--borda); }

/* Tela Inicial (Nível 1) */
.tela-inicial {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.hero-card {
  background: var(--bg-card);
  border: 1px solid var(--borda);
  border-radius: 20px;
  padding: 36px 28px;
  max-width: 540px;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.icone-destaque { font-size: 60px; margin-bottom: 12px; }
.titulo-principal { font-size: 28px; margin-bottom: 12px; }
.descricao-principal { color: var(--texto-secundario); margin-bottom: 24px; line-height: 1.5; }

.btn-ler-qr {
  width: 100%;
  background: var(--destaque-azul);
  color: #fff;
  border: none;
  padding: 16px;
  font-size: 17px;
  font-weight: bold;
  border-radius: 12px;
  cursor: pointer;
}

.area-teste-dev {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px dashed var(--borda);
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: var(--texto-secundario);
}

.btn-teste-dev {
  background: transparent;
  color: var(--texto-principal);
  border: 1px solid var(--borda);
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}
.btn-teste-dev.destaque-admin {
  border-color: #9333ea;
  color: #9333ea;
}

/* Containers Gerais */
.painel-estacionamento, .admin-container {
  padding: 70px 24px 40px 24px;
  max-width: 1280px;
  margin: 0 auto;
}

.painel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.subtitulo { color: var(--texto-secundario); font-size: 14px; }

.btn-primario {
  background: var(--destaque-azul);
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

.btn-secundario {
  background: var(--bg-card);
  color: var(--texto-principal);
  border: 1px solid var(--borda);
  padding: 8px 14px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

/* Nível 3: Lista de Estacionamentos */
.barra-pesquisa-admin {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.input-pesquisa-grande {
  flex: 1;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--borda);
  background: var(--bg-card);
  color: var(--texto-principal);
  font-size: 15px;
}

.lista-card, .form-card {
  background: var(--bg-card);
  border: 1px solid var(--borda);
  border-radius: 12px;
  padding: 20px;
}

.linha-estabelecimento {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px;
  border-bottom: 1px solid var(--borda);
}
.linha-estabelecimento:last-child { border-bottom: none; }
.linha-inativa { opacity: 0.55; }

.info-est { display: flex; align-items: center; gap: 14px; }
.id-badge {
  background: var(--borda);
  padding: 6px 10px;
  border-radius: 6px;
  font-weight: bold;
}
.tag-inativo {
  background: #dc2626;
  color: #fff;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 8px;
}
.meta-est { font-size: 13px; color: var(--texto-secundario); margin-top: 4px; }

.acoes-direita { display: flex; gap: 8px; }
.btn-icone {
  background: var(--bg-painel);
  border: 1px solid var(--borda);
  width: 38px;
  height: 38px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

.paginacao-admin {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}
.paginacao-admin button {
  padding: 8px 14px;
  border-radius: 6px;
  border: 1px solid var(--borda);
  background: var(--bg-card);
  color: var(--texto-principal);
  cursor: pointer;
}

/* Parte 1: Formulário */
.campo-grupo {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.campo-grupo label { font-weight: 600; font-size: 14px; }
.campo-grupo input, .campo-grupo select {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--borda);
  background: var(--bg-painel);
  color: var(--texto-principal);
  font-size: 15px;
}

.linha-andar-dinamica {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.linha-andar-dinamica input { flex: 1; }

.btn-mais-menos {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  border: none;
  font-size: 20px;
  font-weight: bold;
  color: #fff;
  cursor: pointer;
}
.btn-mais { background: #16a34a; }
.btn-menos { background: #dc2626; }

/* Parte 2: Editor Gamificado 2D */
.editor-layout {
  padding: 12px 16px 16px 70px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.editor-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid var(--borda);
}

.topbar-esquerda {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.seletor-andar-box {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-painel);
  padding: 6px 12px;
  border-radius: 8px;
}
.seletor-andar-box select {
  background: transparent;
  border: none;
  color: var(--texto-principal);
  font-weight: bold;
}

.btn-salvar-final {
  background: #16a34a;
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}
.btn-salvar-final:disabled {
  background: #64748b;
  opacity: 0.5;
  cursor: not-allowed;
}

/* Barra de Avisos e Menu Contextual de Seleção */
.barra-avisos-editor {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  min-height: 42px;
}

.avisos-esquerda { display: flex; gap: 10px; flex-wrap: wrap; }
.alerta-tag {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: bold;
}
.alerta-tag.erro { background: #fef2f2; color: #dc2626; border: 1px solid #f87171; }
.alerta-tag.ok { background: #f0fdf4; color: #16a34a; border: 1px solid #4ade80; }

.modo-carimbo-ativo {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #10b981;
  padding: 6px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}
.modo-carimbo-ativo button {
  background: #dc2626;
  color: #fff;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.menu-selecao-flutuante {
  background: #1e1b4b;
  color: #fff;
  padding: 6px 14px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.25);
}
.contagem-sel { font-size: 13px; font-weight: bold; color: #c4b5fd; }
.grupo-acao-item { display: flex; align-items: center; gap: 4px; font-size: 13px; }
.btn-mini {
  border: none;
  width: 26px;
  height: 26px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-mini.add { background: #22c55e; color: #fff; }
.btn-mini.rem { background: #ef4444; color: #fff; }
.btn-mini.limpar { background: #475569; color: #fff; }

/* Workspace: Grid + Sidebar Direita */
.editor-workspace {
  flex: 1;
  display: flex;
  gap: 14px;
  overflow: hidden;
}

.area-grid-principal {
  flex: 1;
  background: #ffffff;
  border: 2px solid var(--borda);
  border-radius: 12px;
  overflow: auto;
  padding: 12px;
  user-select: none;
}

.matriz-com-coordenadas {
  display: inline-block;
}

.linha-coordenadas-x, .linha-grid-y {
  display: grid;
}

.canto-xy, .rotulo-coord {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 11px;
  font-weight: bold;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}

/* Célula e Quadrado do Editor */
.celula-editor-fundo {
  width: 34px;
  height: 34px;
  padding: 3px; /* Espaço entre os quadrados que deixa o fundo do Setor visível! */
}

.quadrado-editor {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  border: 1px solid #94a3b8;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  cursor: pointer;
}

/* Cores Exatas das Regras do Editor */
.qe-vazio { background-color: #cbd5e1; color: transparent; } /* Cinza claro inicial */
.qe-estrada { background-color: #1e293b; border-color: #0f172a; } /* Asfalto escuro */
.qe-vaga-amarela { background-color: #eab308; color: #0f172a; border-color: #ca8a04; } /* Vaga sem ESP32 */
.qe-entrada { background-color: #2563eb; } /* Azul */
.qe-saida { background-color: #ea580c; } /* Laranja */
.qe-acesso { background-color: #16a34a; } /* Verde */
.qe-selecionado-roxo {
  background-color: #9333ea !important;
  border: 2px solid #ffffff !important;
  color: #fff !important;
}
.qe-sombra-verde {
  background-color: rgba(34, 197, 94, 0.75) !important;
  border: 2px dashed #15803d !important;
}

/* Sidebar Direita do Editor */
.sidebar-direita-editor {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.painel-ferramentas {
  background: var(--bg-card);
  border: 1px solid var(--borda);
  border-radius: 10px;
  padding: 14px;
}
.painel-ferramentas h4 { font-size: 14px; margin-bottom: 4px; }
.dica-painel { font-size: 12px; color: var(--texto-secundario); margin-bottom: 10px; }

.linha-botoes-dupla {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 6px;
}

.btn-ferramenta {
  border: none;
  padding: 8px;
  border-radius: 6px;
  color: #fff;
  font-weight: bold;
  font-size: 12px;
  cursor: pointer;
}
.cor-entrada { background: #2563eb; }
.cor-saida { background: #ea580c; }
.cor-acesso { background: #16a34a; }

.linha-equipamentos {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}
.btn-equipamento {
  flex: 1;
  background: var(--bg-painel);
  color: var(--texto-principal);
  border: 1px solid var(--borda);
  padding: 8px 4px;
  border-radius: 6px;
  font-weight: bold;
  font-size: 12px;
  cursor: pointer;
}
.btn-equipamento:hover {
  border-color: var(--destaque-azul);
  color: var(--destaque-azul);
}

.legenda-editor { font-size: 12px; display: flex; flex-direction: column; gap: 6px; }
.amostra {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-right: 6px;
  vertical-align: middle;
}

/* Grid do Motorista (Nível 1) */
.abas-andares { display: flex; gap: 10px; margin-bottom: 16px; }
.aba-btn {
  background: var(--bg-card);
  color: var(--texto-principal);
  border: 1px solid var(--borda);
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}
.aba-ativa { background: var(--destaque-azul); color: #fff; }

.barra-controles {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--bg-card);
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 16px;
  border: 1px solid var(--borda);
}
.controles-esquerda { display: flex; gap: 16px; flex-wrap: wrap; }
.filtro-toggle { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }
.legenda { display: flex; gap: 8px; flex-wrap: wrap; }
.badge { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; color: #fff; }

.grid-scroll-wrapper {
  background: #ffffff;
  border: 2px solid var(--borda);
  border-radius: 12px;
  padding: 20px;
  overflow: auto;
}
.grid-tabuleiro { display: grid; }
.celula-fundo-setor { width: 42px; height: 42px; padding: 3px; }
.quadrado-interno {
  width: 100%;
  height: 100%;
  border-radius: 5px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 11px;
  font-weight: bold;
  color: #fff;
}
.q-invisivel { background: transparent; }
.q-estrada { background: #1e293b; }
.q-entrada { background: #2563eb; }
.q-saida { background: #ea580c; }
.q-acesso { background: #16a34a; }
.q-vaga-livre { background: #16a34a; cursor: pointer; border: 2px dashed rgba(255,255,255,0.6); }
.q-vaga-roxa { background: #9333ea; cursor: pointer; outline: 2px solid #fff; }
.q-vaga-ocupada { background: #dc2626; cursor: not-allowed; }
.q-vaga-cinza { background: #64748b; opacity: 0.4; cursor: not-allowed; }

/* Modais */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}
.modal-box {
  background: var(--bg-card);
  color: var(--texto-principal);
  border-radius: 14px;
  padding: 24px;
  max-width: 440px;
  width: 100%;
  box-shadow: 0 15px 30px rgba(0,0,0,0.3);
}
.grade-cores-setor {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 8px;
}
.botao-cor-setor {
  padding: 10px;
  border-radius: 8px;
  border: 2px solid transparent;
  color: #0f172a;
  font-weight: bold;
  cursor: pointer;
}
.cor-selecionada { border-color: #0f172a; transform: scale(1.03); }
.modal-acoes {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
</style>