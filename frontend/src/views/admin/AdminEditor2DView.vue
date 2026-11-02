<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  paletaSetores,
  escurecerCorHex,
  formEstabelecimento,
  salvarEstacionamentoNoBanco
} from '@/stores/estacionamentoStore'
import {
  IconSquareRoundedArrowLeft,
  IconStack2,
  IconLayoutGrid,
  IconArrowBackUp,
  IconArrowForwardUp,
  IconAlertSquareRounded,
  IconDeviceFloppy,
  IconSettings,
  IconSquareRoundedPlus,
  IconSquareRoundedMinus,
  IconSquareRoundedCheck,
  IconSquareRoundedX,
  IconSquareRoundedChevronDown,
  IconRoad,
  IconLayoutBoard,
  IconParking,
  IconEraser,
  IconDoorEnter,
  IconDoorExit,
  IconArrowBarRight,
  IconCpu,
  IconPencil,
  IconTrash,
  IconSearch,
  IconHandMove
} from '@/constants/icons'

const router = useRouter()

const andarEditorIndex = ref(0)
const dropdownAndarEditorAberto = ref(false)
const gridPrincipalRef = ref(null)
const modoMoverMapa = ref(false)

const selecionados = ref(new Set())
const baseSelecionadosCtrl = ref(new Set())
const arrastando = ref(false)
const pontoInicialArrasto = ref(null)
const mostrarMenuFlutuante = ref(false)
const hoverCoord = ref(null)
const mostrarPainelAvisos = ref(false)

const menuTopoMobileAberto = ref(false)
const menuAdicionarMobileAberto = ref(false)

const panX = ref(0)
const panY = ref(0)
const zoomEscala = ref(1)

let toqueUnico = null
let pinchInicial = null
let arrastandoMapaMouse = null
let autoScrollFrame = null
let ponteiroAtualClient = { x: 0, y: 0 }
let ultimoToqueMaoTimestamp = 0
let ultimoToqueMaoPos = { x: 0, y: 0 }
let bloqueioSelecaoAte = 0

function resetarCameraGrid() {
  panX.value = 0
  panY.value = 0
  zoomEscala.value = 1
}

function alternarModoMoverMapa() {
  modoMoverMapa.value = !modoMoverMapa.value
  ultimoToqueMaoTimestamp = 0
  if (modoMoverMapa.value) {
    ferramentaCarimbo.value = null
    arrastando.value = false
    selecionados.value.clear()
    mostrarMenuFlutuante.value = false
    pararLoopAutoScroll()
  }
}

// Sai do modo mão com duplo toque/clique sem selecionar o quadrado abaixo
function sairModoMoverComDuploClique() {
  if (!modoMoverMapa.value) return
  modoMoverMapa.value = false
  bloqueioSelecaoAte = Date.now() + 400
  ultimoToqueMaoTimestamp = 0
  toqueUnico = null
  arrastando.value = false
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
}

function distanciaEntreToques(t1, t2) {
  return Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY)
}

function pontoMedioToques(t1, t2) {
  return {
    x: (t1.clientX + t2.clientX) / 2,
    y: (t1.clientY + t2.clientY) / 2
  }
}

function obterCoordenadaPorPontoTela(clientX, clientY) {
  const el = document.elementFromPoint(clientX, clientY)
  const celulaEl = el?.closest('[data-coord]')
  if (!celulaEl) return null
  const [cx, cy] = celulaEl.getAttribute('data-coord').split(',').map(Number)
  return { x: cx, y: cy }
}

function atualizarRetanguloSelecao(x, y) {
  if (!pontoInicialArrasto.value) return
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

function iniciarLoopAutoScroll() {
  if (autoScrollFrame) return
  const step = () => {
    if (!arrastando.value || !gridPrincipalRef.value) {
      autoScrollFrame = null
      return
    }
    const container = gridPrincipalRef.value
    const rect = container.getBoundingClientRect()
    const margem = 48
    const vel = 12
    let mudouScroll = false

    if (ponteiroAtualClient.x < rect.left + margem) {
      container.scrollLeft -= vel
      mudouScroll = true
    } else if (ponteiroAtualClient.x > rect.right - margem) {
      container.scrollLeft += vel
      mudouScroll = true
    }

    if (ponteiroAtualClient.y < rect.top + margem) {
      container.scrollTop -= vel
      mudouScroll = true
    } else if (ponteiroAtualClient.y > rect.bottom - margem) {
      container.scrollTop += vel
      mudouScroll = true
    }

    if (mudouScroll) {
      const coord = obterCoordenadaPorPontoTela(ponteiroAtualClient.x, ponteiroAtualClient.y)
      if (coord) {
        hoverCoord.value = coord
        atualizarRetanguloSelecao(coord.x, coord.y)
      }
    }
    autoScrollFrame = requestAnimationFrame(step)
  }
  autoScrollFrame = requestAnimationFrame(step)
}

function pararLoopAutoScroll() {
  if (autoScrollFrame) {
    cancelAnimationFrame(autoScrollFrame)
    autoScrollFrame = null
  }
}

function aoIniciarToqueGrid(e) {
  if (Date.now() < bloqueioSelecaoAte) return

  if (e.touches.length === 2) {
    arrastando.value = false
    pararLoopAutoScroll()
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
    return
  }

  if (e.touches.length === 1) {
    pinchInicial = null
    const t = e.touches[0]

    if (modoMoverMapa.value) {
      const agora = Date.now()
      const distUltimoToque = Math.hypot(
        t.clientX - ultimoToqueMaoPos.x,
        t.clientY - ultimoToqueMaoPos.y
      )

      // Dois toques em sequência desativam o modo de mover tela sem selecionar células
      if (agora - ultimoToqueMaoTimestamp < 360 && distUltimoToque < 48) {
        sairModoMoverComDuploClique()
        return
      }

      ultimoToqueMaoTimestamp = agora
      ultimoToqueMaoPos = { x: t.clientX, y: t.clientY }

      toqueUnico = {
        modo: 'PAN',
        startX: t.clientX,
        startY: t.clientY,
        panXInicial: panX.value,
        panYInicial: panY.value
      }
      return
    }

    ponteiroAtualClient = { x: t.clientX, y: t.clientY }
    const coord = obterCoordenadaPorPontoTela(t.clientX, t.clientY)

    toqueUnico = {
      modo: 'SELECT',
      startX: t.clientX,
      startY: t.clientY,
      lastX: t.clientX,
      lastY: t.clientY,
      coordInicial: coord,
      moveu: false
    }

    if (coord && !ferramentaCarimbo.value) {
      arrastando.value = true
      mostrarMenuFlutuante.value = false
      pontoInicialArrasto.value = coord
      baseSelecionadosCtrl.value = new Set()
      selecionados.value = new Set([`${coord.x},${coord.y}`])
      iniciarLoopAutoScroll()
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
    return
  }

  if (e.touches.length === 1 && toqueUnico) {
    const t = e.touches[0]
    if (toqueUnico.modo === 'PAN') {
      const dx = t.clientX - toqueUnico.startX
      const dy = t.clientY - toqueUnico.startY
      if (Math.hypot(dx, dy) > 10) {
        ultimoToqueMaoTimestamp = 0
      }
      panX.value = toqueUnico.panXInicial + dx
      panY.value = toqueUnico.panYInicial + dy
      return
    }

    toqueUnico.lastX = t.clientX
    toqueUnico.lastY = t.clientY
    ponteiroAtualClient = { x: t.clientX, y: t.clientY }

    if (Math.hypot(t.clientX - toqueUnico.startX, t.clientY - toqueUnico.startY) > 6) {
      toqueUnico.moveu = true
    }

    const coord = obterCoordenadaPorPontoTela(t.clientX, t.clientY)
    if (coord && arrastando.value) {
      hoverCoord.value = coord
      atualizarRetanguloSelecao(coord.x, coord.y)
    }
  }
}

function aoFinalizarToqueGrid(e) {
  if (e.touches.length < 2) {
    pinchInicial = null
  }
  if (e.touches.length === 0) {
    pararLoopAutoScroll()
    arrastando.value = false

    if (toqueUnico) {
      if (toqueUnico.modo === 'SELECT' && Date.now() >= bloqueioSelecaoAte) {
        if (!toqueUnico.moveu && toqueUnico.coordInicial && ferramentaCarimbo.value) {
          aplicarCarimboNoGrid(toqueUnico.coordInicial.x, toqueUnico.coordInicial.y)
        }
        mostrarMenuFlutuante.value = selecionados.value.size > 0
      }
      toqueUnico = null
    }
  }
}

const historicoUndo = ref([])
const historicoRedo = ref([])

const ferramentaCarimbo = ref(null)
const modalTamanhoAberto = ref(false)
const tempGridX = ref(30)
const tempGridY = ref(20)

const modalSetorAberto = ref(false)
const nomeNovoSetor = ref('')
const prefixoNovoSetor = ref('')
const corNovoSetor = ref(paletaSetores[0].hex)

const modalAlterarSetoresAberto = ref(false)
const termoBuscaSetor = ref('')
const dropdownSetoresAberto = ref(false)
const setorEmEdicaoId = ref(null)
const editNomeSetor = ref('')
const editPrefixoSetor = ref('')
const editCorSetor = ref(paletaSetores[0].hex)

const modalAcessoAberto = ref(false)
const tipoAcessoTemp = ref('ENTRADA')
const orientacaoAcessoTemp = ref('H')
const tamanhoAcessoTemp = ref(2)

const modalMacAberto = ref(false)
const macTemp = ref('')
const coordsParaVincularMac = ref([])
const modalSucessoSalvarAberto = ref(false)
const salvandoNoBanco = ref(false)

const andarEditorAtual = computed(() => {
  return formEstabelecimento.value.andares[andarEditorIndex.value] || null
})

function alternarPainelAvisos() {
  mostrarPainelAvisos.value = !mostrarPainelAvisos.value
  if (mostrarPainelAvisos.value) {
    menuTopoMobileAberto.value = false
    menuAdicionarMobileAberto.value = false
  }
}

function alternarMenuTopoMobile() {
  menuTopoMobileAberto.value = !menuTopoMobileAberto.value
  if (menuTopoMobileAberto.value) {
    menuAdicionarMobileAberto.value = false
    mostrarPainelAvisos.value = false
  }
}

function alternarMenuAdicionarMobile() {
  menuAdicionarMobileAberto.value = !menuAdicionarMobileAberto.value
  if (menuAdicionarMobileAberto.value) {
    menuTopoMobileAberto.value = false
    mostrarPainelAvisos.value = false
  }
}

const celulaInspecionadaHover = computed(() => {
  if (!hoverCoord.value || !andarEditorAtual.value) return null
  const c = andarEditorAtual.value.celulas[`${hoverCoord.value.x},${hoverCoord.value.y}`]
  if (!c) return null

  if (c.tipo === 'VAGA') {
    const corFundo = c.macEsp ? escurecerCorHex(c.corSetor, 0.55) : '#eab308'
    const statusEsp = c.macEsp ? `ESP32: ${c.macEsp}` : 'Sem ESP32 (Amarela)'
    const infoSetor = c.nomeSetor ? `Setor ${c.nomeSetor} (${c.prefixoSetor})` : 'Sem Setor'
    return {
      cor: corFundo,
      titulo: `Vaga ${c.identificador || ''} — (${c.x},${c.y})`,
      detalhe: `${infoSetor} • ${statusEsp}`
    }
  }

  if (c.tipo === 'ESTRADA') {
    return {
      cor: '#1e293b',
      titulo: `Estrada (${c.x},${c.y})`,
      detalhe: c.nomeSetor ? `Setor ${c.nomeSetor} (${c.prefixoSetor})` : null
    }
  }

  if (c.tipo === 'ENTRADA') {
    return {
      cor: '#2563eb',
      titulo: `Entrada (${c.x},${c.y})`,
      detalhe: `Orientação: ${c.orientacao === 'V' ? 'Vertical' : 'Horizontal'}`
    }
  }

  if (c.tipo === 'SAIDA') {
    return {
      cor: '#ea580c',
      titulo: `Saída (${c.x},${c.y})`,
      detalhe: `Orientação: ${c.orientacao === 'V' ? 'Vertical' : 'Horizontal'}`
    }
  }

  if (c.tipo === 'ACESSO') {
    return {
      cor: '#16a34a',
      titulo: `Acesso Interno (${c.x},${c.y})`,
      detalhe: `Orientação: ${c.orientacao === 'V' ? 'Vertical' : 'Horizontal'}`
    }
  }

  if (c.setorId) {
    return {
      cor: c.corSetor,
      titulo: `Setor ${c.nomeSetor} (${c.x},${c.y})`,
      detalhe: `Prefixo: ${c.prefixoSetor}`
    }
  }

  return null
})

function renumerarVagasDoAndar(andar) {
  if (!andar) return
  const contadoresPorSetor = {}

  for (let y = 0; y < andar.grid_y; y++) {
    for (let x = 0; x < andar.grid_x; x++) {
      const c = andar.celulas[`${x},${y}`]
      if (c && c.tipo === 'VAGA') {
        const sId = c.setorId || 'PADRAO'
        const pref = c.prefixoSetor || 'A'
        contadoresPorSetor[sId] = (contadoresPorSetor[sId] || 0) + 1
        c.identificador = `${pref}${contadoresPorSetor[sId]}`
      }
    }
  }
}

function registrarSnapshot() {
  if (!andarEditorAtual.value) return
  historicoUndo.value.push(
    JSON.stringify({
      grid_x: andarEditorAtual.value.grid_x,
      grid_y: andarEditorAtual.value.grid_y,
      setores: andarEditorAtual.value.setores,
      equipamentos: andarEditorAtual.value.equipamentos,
      celulas: andarEditorAtual.value.celulas
    })
  )
  if (historicoUndo.value.length > 40) historicoUndo.value.shift()
  historicoRedo.value = []
}

function desfazer() {
  if (historicoUndo.value.length === 0 || !andarEditorAtual.value) return
  historicoRedo.value.push(
    JSON.stringify({
      grid_x: andarEditorAtual.value.grid_x,
      grid_y: andarEditorAtual.value.grid_y,
      setores: andarEditorAtual.value.setores,
      equipamentos: andarEditorAtual.value.equipamentos,
      celulas: andarEditorAtual.value.celulas
    })
  )
  const anterior = JSON.parse(historicoUndo.value.pop())
  Object.assign(andarEditorAtual.value, anterior)
}

function refazer() {
  if (historicoRedo.value.length === 0 || !andarEditorAtual.value) return
  historicoUndo.value.push(
    JSON.stringify({
      grid_x: andarEditorAtual.value.grid_x,
      grid_y: andarEditorAtual.value.grid_y,
      setores: andarEditorAtual.value.setores,
      equipamentos: andarEditorAtual.value.equipamentos,
      celulas: andarEditorAtual.value.celulas
    })
  )
  const futuro = JSON.parse(historicoRedo.value.pop())
  Object.assign(andarEditorAtual.value, futuro)
}

function iniciarSelecaoCelula(x, y, event) {
  if (Date.now() < bloqueioSelecaoAte) return

  if (modoMoverMapa.value) {
    const agora = Date.now()
    const dist = Math.hypot(
      event.clientX - ultimoToqueMaoPos.x,
      event.clientY - ultimoToqueMaoPos.y
    )
    if (agora - ultimoToqueMaoTimestamp < 360 && dist < 48) {
      sairModoMoverComDuploClique()
      return
    }
    ultimoToqueMaoTimestamp = agora
    ultimoToqueMaoPos = { x: event.clientX, y: event.clientY }

    arrastandoMapaMouse = {
      startX: event.clientX,
      startY: event.clientY,
      panXInicial: panX.value,
      panYInicial: panY.value
    }
    return
  }

  if (ferramentaCarimbo.value) {
    aplicarCarimboNoGrid(x, y)
    return
  }

  arrastando.value = true
  mostrarMenuFlutuante.value = false
  pontoInicialArrasto.value = { x, y }
  ponteiroAtualClient = { x: event.clientX, y: event.clientY }
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
  iniciarLoopAutoScroll()
}

function moverMouseCelula(x, y, event) {
  hoverCoord.value = { x, y }
  if (arrastandoMapaMouse && event) {
    const dx = event.clientX - arrastandoMapaMouse.startX
    const dy = event.clientY - arrastandoMapaMouse.startY
    if (Math.hypot(dx, dy) > 8) {
      ultimoToqueMaoTimestamp = 0
    }
    panX.value = arrastandoMapaMouse.panXInicial + dx
    panY.value = arrastandoMapaMouse.panYInicial + dy
    return
  }
  if (event) {
    ponteiroAtualClient = { x: event.clientX, y: event.clientY }
  }
  if (!arrastando.value || !pontoInicialArrasto.value) return
  atualizarRetanguloSelecao(x, y)
}

function finalizarSelecaoMouse() {
  arrastandoMapaMouse = null
  pararLoopAutoScroll()
  if (arrastando.value) {
    arrastando.value = false
    if (selecionados.value.size > 0 && Date.now() >= bloqueioSelecaoAte) {
      mostrarMenuFlutuante.value = true
    }
  }
}

function tratarTeclaGlobal(event) {
  const tagAtiva = document.activeElement?.tagName
  const digitandoEmInput = tagAtiva === 'INPUT' || tagAtiva === 'TEXTAREA' || tagAtiva === 'SELECT'

  if (!digitandoEmInput && (event.ctrlKey || event.metaKey)) {
    const tecla = event.key.toLowerCase()
    if (tecla === 'z' && !event.shiftKey) {
      event.preventDefault()
      desfazer()
      return
    }
    if (tecla === 'y' || (tecla === 'z' && event.shiftKey)) {
      event.preventDefault()
      refazer()
      return
    }
  }

  if (event.key === 'Escape') {
    if (modoMoverMapa.value) {
      modoMoverMapa.value = false
      return
    }
    if (ferramentaCarimbo.value) ferramentaCarimbo.value = null
    if (mostrarMenuFlutuante.value) {
      mostrarMenuFlutuante.value = false
      selecionados.value.clear()
    }
    mostrarPainelAvisos.value = false
    menuTopoMobileAberto.value = false
    menuAdicionarMobileAberto.value = false
    dropdownSetoresAberto.value = false
    dropdownAndarEditorAberto.value = false
  }
}

onMounted(() => {
  window.addEventListener('mouseup', finalizarSelecaoMouse)
  window.addEventListener('keydown', tratarTeclaGlobal)
})

onUnmounted(() => {
  pararLoopAutoScroll()
  window.removeEventListener('mouseup', finalizarSelecaoMouse)
  window.removeEventListener('keydown', tratarTeclaGlobal)
})

function abrirModalTamanhoGrid() {
  if (!andarEditorAtual.value) return
  tempGridX.value = andarEditorAtual.value.grid_x
  tempGridY.value = andarEditorAtual.value.grid_y
  menuTopoMobileAberto.value = false
  modalTamanhoAberto.value = true
}

function confirmarTamanhoGrid() {
  const nx = Math.min(100, Math.max(5, Number(tempGridX.value) || 5))
  const ny = Math.min(100, Math.max(5, Number(tempGridY.value) || 5))
  registrarSnapshot()

  const novasCelulas = {}
  for (let y = 0; y < ny; y++) {
    for (let x = 0; x < nx; x++) {
      const chave = `${x},${y}`
      novasCelulas[chave] = andarEditorAtual.value.celulas[chave] || {
        x,
        y,
        tipo: 'VAZIO',
        orientacao: 'NENHUMA',
        setorId: null,
        nomeSetor: null,
        prefixoSetor: null,
        corSetor: null,
        identificador: null,
        livre: true,
        inativa: false,
        macEsp: null
      }
    }
  }

  andarEditorAtual.value.grid_x = nx
  andarEditorAtual.value.grid_y = ny
  andarEditorAtual.value.celulas = novasCelulas
  renumerarVagasDoAndar(andarEditorAtual.value)
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
  modalTamanhoAberto.value = false
}

function aplicarEstradaNaSelecao(adicionar) {
  registrarSnapshot()
  selecionados.value.forEach((chave) => {
    const c = andarEditorAtual.value.celulas[chave]
    if (!c) return
    if (adicionar) {
      c.tipo = 'ESTRADA'
      c.identificador = null
      c.macEsp = null
    } else if (c.tipo === 'ESTRADA') {
      c.tipo = 'VAZIO'
    }
  })
  renumerarVagasDoAndar(andarEditorAtual.value)
}

const coresUsadasNoAndar = computed(() => {
  if (!andarEditorAtual.value) return new Set()
  return new Set((andarEditorAtual.value.setores || []).map(s => s.cor_hex))
})

function sugerirProximoPrefixo() {
  const usados = new Set((andarEditorAtual.value?.setores || []).map(s => s.prefixo.toUpperCase()))
  const alfabeto = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  for (const letra of alfabeto) {
    if (!usados.has(letra)) return letra
  }
  return 'S1'
}

function abrirModalSetor() {
  const primeiraCorLivre = paletaSetores.find(p => !coresUsadasNoAndar.value.has(p.hex))
  if (!primeiraCorLivre) {
    alert('Todas as 10 cores de setores já foram utilizadas neste andar!')
    return
  }
  corNovoSetor.value = primeiraCorLivre.hex
  nomeNovoSetor.value = ''
  prefixoNovoSetor.value = sugerirProximoPrefixo()
  modalSetorAberto.value = true
}

function formatarInputPrefixo(valor) {
  return valor.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 3)
}

function confirmarAdicionarSetor() {
  const nomeLimpo = nomeNovoSetor.value.trim()
  const prefixoLimpo = formatarInputPrefixo(prefixoNovoSetor.value)

  if (!nomeLimpo) {
    alert('Informe o nome do setor.')
    return
  }
  if (!prefixoLimpo) {
    alert('Informe o prefixo de numeração (1 a 3 letras/números, ex: A, B, VIP).')
    return
  }

  const nomeRepetido = andarEditorAtual.value.setores.some(
    s => s.nome_setor.trim().toLowerCase() === nomeLimpo.toLowerCase()
  )
  if (nomeRepetido) {
    alert('Já existe um setor com esse nome neste andar!')
    return
  }

  const prefixoRepetido = andarEditorAtual.value.setores.some(
    s => (s.prefixo || '').toUpperCase() === prefixoLimpo
  )
  if (prefixoRepetido) {
    alert(`O prefixo "${prefixoLimpo}" já está sendo usado por outro setor neste andar!`)
    return
  }

  registrarSnapshot()
  let setor = andarEditorAtual.value.setores.find(s => s.cor_hex === corNovoSetor.value)
  if (!setor) {
    setor = {
      id_setor: Date.now(),
      nome_setor: nomeLimpo,
      prefixo: prefixoLimpo,
      cor_hex: corNovoSetor.value
    }
    andarEditorAtual.value.setores.push(setor)
  }

  selecionados.value.forEach((chave) => {
    const c = andarEditorAtual.value.celulas[chave]
    if (!c) return
    c.setorId = setor.id_setor
    c.nomeSetor = setor.nome_setor
    c.prefixoSetor = setor.prefixo
    c.corSetor = setor.cor_hex
  })

  renumerarVagasDoAndar(andarEditorAtual.value)
  modalSetorAberto.value = false
}

function removerSetorDaSelecao() {
  registrarSnapshot()
  selecionados.value.forEach((chave) => {
    const c = andarEditorAtual.value.celulas[chave]
    if (!c) return
    c.setorId = null
    c.nomeSetor = null
    c.prefixoSetor = null
    c.corSetor = null
    if (c.tipo === 'VAGA') {
      c.tipo = 'VAZIO'
      c.identificador = null
      c.macEsp = null
    }
  })
  renumerarVagasDoAndar(andarEditorAtual.value)
}

const setoresFiltradosBusca = computed(() => {
  const lista = andarEditorAtual.value?.setores || []
  const termo = termoBuscaSetor.value.trim().toLowerCase()
  if (!termo) return lista
  return lista.filter(
    s =>
      s.nome_setor.toLowerCase().includes(termo) ||
      (s.prefixo || '').toLowerCase().includes(termo)
  )
})

const setorSelecionadoParaEdicao = computed(() => {
  if (!setorEmEdicaoId.value || !andarEditorAtual.value) return null
  return andarEditorAtual.value.setores.find(s => s.id_setor === setorEmEdicaoId.value) || null
})

function abrirModalAlterarSetores() {
  termoBuscaSetor.value = ''
  dropdownSetoresAberto.value = false
  setorEmEdicaoId.value = null
  editNomeSetor.value = ''
  editPrefixoSetor.value = ''
  editCorSetor.value = paletaSetores[0].hex
  menuAdicionarMobileAberto.value = false
  modalAlterarSetoresAberto.value = true
}

function aoDigitarBuscaSetor() {
  dropdownSetoresAberto.value = true
  const correspondenciaExata = (andarEditorAtual.value?.setores || []).find(
    s => s.nome_setor.toLowerCase() === termoBuscaSetor.value.trim().toLowerCase()
  )
  if (correspondenciaExata) {
    carregarDadosSetorNoForm(correspondenciaExata)
  } else {
    setorEmEdicaoId.value = null
  }
}

function carregarDadosSetorNoForm(setor) {
  setorEmEdicaoId.value = setor.id_setor
  termoBuscaSetor.value = setor.nome_setor
  editNomeSetor.value = setor.nome_setor
  editPrefixoSetor.value = setor.prefixo || 'A'
  editCorSetor.value = setor.cor_hex
  dropdownSetoresAberto.value = false
}

function corOcupadaPorOutroSetor(hex) {
  if (!andarEditorAtual.value) return false
  return andarEditorAtual.value.setores.some(
    s => s.cor_hex === hex && s.id_setor !== setorEmEdicaoId.value
  )
}

function salvarAlteracoesSetor() {
  if (!setorSelecionadoParaEdicao.value) return
  const novoNome = editNomeSetor.value.trim()
  const novoPref = formatarInputPrefixo(editPrefixoSetor.value)

  if (!novoNome) {
    alert('O nome do setor não pode ficar vazio.')
    return
  }
  if (!novoPref) {
    alert('O prefixo do setor não pode ficar vazio.')
    return
  }

  const nomeDuplicado = andarEditorAtual.value.setores.some(
    s =>
      s.id_setor !== setorEmEdicaoId.value &&
      s.nome_setor.trim().toLowerCase() === novoNome.toLowerCase()
  )
  if (nomeDuplicado) {
    alert('Outro setor neste andar já utiliza esse nome!')
    return
  }

  const prefixoDuplicado = andarEditorAtual.value.setores.some(
    s =>
      s.id_setor !== setorEmEdicaoId.value &&
      (s.prefixo || '').toUpperCase() === novoPref
  )
  if (prefixoDuplicado) {
    alert(`Outro setor neste andar já utiliza o prefixo "${novoPref}"!`)
    return
  }

  registrarSnapshot()
  const alvo = setorSelecionadoParaEdicao.value
  alvo.nome_setor = novoNome
  alvo.prefixo = novoPref
  alvo.cor_hex = editCorSetor.value

  Object.values(andarEditorAtual.value.celulas).forEach((c) => {
    if (c.setorId === alvo.id_setor) {
      c.nomeSetor = alvo.nome_setor
      c.prefixoSetor = alvo.prefixo
      c.corSetor = alvo.cor_hex
    }
  })

  renumerarVagasDoAndar(andarEditorAtual.value)
  modalAlterarSetoresAberto.value = false
}

function excluirSetorInteiro() {
  if (!setorSelecionadoParaEdicao.value) return
  const alvo = setorSelecionadoParaEdicao.value

  registrarSnapshot()
  andarEditorAtual.value.setores = andarEditorAtual.value.setores.filter(
    s => s.id_setor !== alvo.id_setor
  )

  Object.values(andarEditorAtual.value.celulas).forEach((c) => {
    if (c.setorId === alvo.id_setor) {
      c.setorId = null
      c.nomeSetor = null
      c.prefixoSetor = null
      c.corSetor = null
      if (c.tipo === 'VAGA') {
        c.tipo = 'VAZIO'
        c.identificador = null
        c.macEsp = null
      }
    }
  })

  renumerarVagasDoAndar(andarEditorAtual.value)
  modalAlterarSetoresAberto.value = false
}

function aplicarVagaNaSelecao(adicionar) {
  if (adicionar) {
    const algumaSemSetor = Array.from(selecionados.value).some((chave) => {
      const c = andarEditorAtual.value.celulas[chave]
      return !c || !c.setorId
    })
    if (algumaSemSetor) {
      alert('Todas as vagas precisam estar dentro de um Setor! Adicione um Setor à área selecionada primeiro.')
      return
    }
  }

  registrarSnapshot()
  selecionados.value.forEach((chave) => {
    const c = andarEditorAtual.value.celulas[chave]
    if (!c) return
    if (adicionar) {
      c.tipo = 'VAGA'
      c.macEsp = null
    } else if (c.tipo === 'VAGA') {
      c.tipo = 'VAZIO'
      c.identificador = null
      c.macEsp = null
    }
  })

  renumerarVagasDoAndar(andarEditorAtual.value)
}

function apagarTudoNaSelecao() {
  registrarSnapshot()
  const chavesApagadas = new Set(selecionados.value)

  chavesApagadas.forEach((chave) => {
    const c = andarEditorAtual.value.celulas[chave]
    if (!c) return
    c.tipo = 'VAZIO'
    c.orientacao = 'NENHUMA'
    c.setorId = null
    c.nomeSetor = null
    c.prefixoSetor = null
    c.corSetor = null
    c.identificador = null
    c.macEsp = null
  })

  andarEditorAtual.value.equipamentos = (andarEditorAtual.value.equipamentos || []).filter(
    eq => !eq.vagasCoords.some(coord => chavesApagadas.has(coord))
  )

  const idsSetoresPresentesNoGrid = new Set()
  Object.values(andarEditorAtual.value.celulas).forEach((c) => {
    if (c.setorId) idsSetoresPresentesNoGrid.add(c.setorId)
  })
  andarEditorAtual.value.setores = (andarEditorAtual.value.setores || []).filter(s =>
    idsSetoresPresentesNoGrid.has(s.id_setor)
  )

  renumerarVagasDoAndar(andarEditorAtual.value)
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
}

function abrirConfigAcesso(tipo, orientacao) {
  tipoAcessoTemp.value = tipo
  orientacaoAcessoTemp.value = orientacao
  tamanhoAcessoTemp.value = 2
  menuAdicionarMobileAberto.value = false
  modalAcessoAberto.value = true
}

function ativarCarimboAcesso() {
  const tam = Math.max(1, Math.min(10, Number(tamanhoAcessoTemp.value) || 1))
  ferramentaCarimbo.value = {
    modo: 'ACESSO',
    tipo: tipoAcessoTemp.value,
    orientacao: orientacaoAcessoTemp.value,
    largura: orientacaoAcessoTemp.value === 'H' ? tam : 1,
    altura: orientacaoAcessoTemp.value === 'V' ? tam : 1
  }
  modoMoverMapa.value = false
  modalAcessoAberto.value = false
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
}

function ativarCarimboEquipamento(largura, altura) {
  ferramentaCarimbo.value = {
    modo: 'EQUIPAMENTO',
    largura,
    altura
  }
  modoMoverMapa.value = false
  menuAdicionarMobileAberto.value = false
  selecionados.value.clear()
  mostrarMenuFlutuante.value = false
}

const coordsSombraCarimbo = computed(() => {
  const conjunto = new Set()
  if (!ferramentaCarimbo.value || !hoverCoord.value || !andarEditorAtual.value) return conjunto

  for (let dy = 0; dy < ferramentaCarimbo.value.altura; dy++) {
    for (let dx = 0; dx < ferramentaCarimbo.value.largura; dx++) {
      const cx = hoverCoord.value.x + dx
      const cy = hoverCoord.value.y + dy
      if (cx < andarEditorAtual.value.grid_x && cy < andarEditorAtual.value.grid_y) {
        conjunto.add(`${cx},${cy}`)
      }
    }
  }
  return conjunto
})

function aplicarCarimboNoGrid(x, y) {
  const carimbo = ferramentaCarimbo.value
  if (!carimbo || !andarEditorAtual.value) return

  const coords = []
  for (let dy = 0; dy < carimbo.altura; dy++) {
    for (let dx = 0; dx < carimbo.largura; dx++) {
      const cx = x + dx
      const cy = y + dy
      if (cx >= andarEditorAtual.value.grid_x || cy >= andarEditorAtual.value.grid_y) {
        alert('O elemento ultrapassa a borda do grid!')
        return
      }
      coords.push(`${cx},${cy}`)
    }
  }

  if (carimbo.modo === 'ACESSO') {
    registrarSnapshot()
    coords.forEach((chave) => {
      const c = andarEditorAtual.value.celulas[chave]
      c.tipo = carimbo.tipo
      c.orientacao = carimbo.orientacao
      c.identificador = null
      c.macEsp = null
    })
    renumerarVagasDoAndar(andarEditorAtual.value)
    ferramentaCarimbo.value = null
  } else if (carimbo.modo === 'EQUIPAMENTO') {
    const vagasEncontradas = coords.filter(
      chave => andarEditorAtual.value.celulas[chave]?.tipo === 'VAGA'
    )
    if (vagasEncontradas.length === 0) {
      alert('Nenhuma vaga amarela encontrada nessa área! Posicione sobre as vagas amarelas.')
      return
    }
    coordsParaVincularMac.value = vagasEncontradas
    macTemp.value = ''
    modalMacAberto.value = true
  }
}

function confirmarVinculoMac() {
  const macLimpo = macTemp.value.trim().toUpperCase()
  if (!macLimpo) {
    alert('Digite o endereço MAC do ESP32.')
    return
  }

  const macJaExiste = formEstabelecimento.value.andares.some(andar =>
    Object.values(andar.celulas || {}).some(c => c.macEsp === macLimpo)
  )
  if (macJaExiste) {
    alert(`O endereço MAC "${macLimpo}" já está vinculado a outro equipamento neste estacionamento!`)
    return
  }

  registrarSnapshot()
  coordsParaVincularMac.value.forEach((chave) => {
    const c = andarEditorAtual.value.celulas[chave]
    if (c && c.tipo === 'VAGA') {
      c.macEsp = macLimpo
    }
  })

  andarEditorAtual.value.equipamentos.push({
    id: Date.now(),
    mac: macLimpo,
    vagasCoords: [...coordsParaVincularMac.value]
  })

  modalMacAberto.value = false
  ferramentaCarimbo.value = null
}

const listaAvisosValidacao = computed(() => {
  const avisos = []
  const andares = formEstabelecimento.value.andares || []

  let totalEntradasEst = 0
  let totalSaidasEst = 0

  andares.forEach((andar) => {
    const celulas = Object.values(andar.celulas || {})
    const entradas = celulas.filter(c => c.tipo === 'ENTRADA').length
    const saidas = celulas.filter(c => c.tipo === 'SAIDA').length
    const acessos = celulas.filter(c => c.tipo === 'ACESSO').length
    const estradas = celulas.filter(c => c.tipo === 'ESTRADA').length
    const vagas = celulas.filter(c => c.tipo === 'VAGA')
    const vagasSemEsp = vagas.filter(c => !c.macEsp).length

    totalEntradasEst += entradas
    totalSaidasEst += saidas

    if (estradas === 0) {
      avisos.push(`[${andar.nome_andar}] Adicione estradas de circulação.`)
    }
    if ((andar.setores || []).length === 0) {
      avisos.push(`[${andar.nome_andar}] Crie ao menos 1 Setor.`)
    }
    if (vagas.length === 0) {
      avisos.push(`[${andar.nome_andar}] Adicione vagas ao andar.`)
    }
    if (vagasSemEsp > 0) {
      avisos.push(`[${andar.nome_andar}] Há ${vagasSemEsp} vaga(s) amarela(s) sem equipamento ESP32.`)
    }
    if (andares.length > 1 && entradas === 0 && saidas === 0 && acessos === 0) {
      avisos.push(`[${andar.nome_andar}] Andar isolado: adicione um Acesso ou Entrada/Saída.`)
    }
  })

  if (totalEntradasEst === 0) {
    avisos.push('O estacionamento precisa ter ao menos 1 Entrada.')
  }
  if (totalSaidasEst === 0) {
    avisos.push('O estacionamento precisa ter ao menos 1 Saída.')
  }

  return avisos
})

const podeSalvarEstacionamento = computed(() => listaAvisosValidacao.value.length === 0)

async function finalizarSalvarEstacionamento() {
  if (!podeSalvarEstacionamento.value || salvandoNoBanco.value) return
  salvandoNoBanco.value = true
  try {
    await salvarEstacionamentoNoBanco()
    modalSucessoSalvarAberto.value = true
  } catch (err) {
    alert(err.message)
  } finally {
    salvandoNoBanco.value = false
  }
}

function confirmarSucessoEVoltarLista() {
  modalSucessoSalvarAberto.value = false
  router.push({ name: 'admin-lista' })
}
</script>

<template>
  <div v-if="andarEditorAtual" class="editor-layout">
    <!-- Grupo Esquerdo de Botões Flutuantes Mobile/Tablet (Alertas + Mão sem sobreposição) -->
    <div class="hud-coluna-esquerda-mobile">
      <button
        class="hud-btn-flutuante hud-esquerda-alertas"
        :class="{ 'caution-ok': podeSalvarEstacionamento, 'caution-pendente': !podeSalvarEstacionamento }"
        title="Avisos de validação"
        @click="alternarPainelAvisos"
      >
        <IconAlertSquareRounded :size="20" />
        <span class="hud-mini-badge">{{ listaAvisosValidacao.length }}</span>
      </button>

      <button
        class="hud-btn-flutuante hud-esquerda-mao"
        :class="{ 'hud-ativo': modoMoverMapa }"
        title="Mover Mapa (Arrastar Tela)"
        @click="alternarModoMoverMapa"
      >
        <IconHandMove :size="20" />
      </button>
    </div>

    <div class="hud-coluna-direita-mobile">
      <button
        class="hud-btn-flutuante hud-btn-salvar"
        :disabled="!podeSalvarEstacionamento || salvandoNoBanco"
        title="Finalizar e Salvar"
        @click="finalizarSalvarEstacionamento"
      >
        <IconDeviceFloppy :size="20" />
      </button>

      <button
        class="hud-btn-flutuante"
        :class="{ 'hud-ativo': menuTopoMobileAberto }"
        title="Opções do Grid e Andar"
        @click="alternarMenuTopoMobile"
      >
        <IconSettings :size="20" />
      </button>

      <button
        class="hud-btn-flutuante hud-btn-add"
        :class="{ 'hud-ativo': menuAdicionarMobileAberto }"
        title="Adicionar Acessos e Equipamentos"
        @click="alternarMenuAdicionarMobile"
      >
        <IconSquareRoundedPlus :size="20" />
      </button>
    </div>

    <!-- Barra Superior do Editor -->
    <header class="editor-topbar" :class="{ 'topbar-mobile-aberta': menuTopoMobileAberto }">
      <div class="topbar-esquerda">
        <button
          class="btn-secundario item-icone-texto"
          title="Informações Gerais"
          @click="router.push({ name: 'admin-info-gerais' })"
        >
          <IconSquareRoundedArrowLeft :size="19" />
          <span class="texto-voltar-menu-engrenagem">Informações Gerais</span>
        </button>

        <div class="seletor-multi-wrapper wrapper-andar-editor">
          <button
            type="button"
            class="btn-seletor-multi item-icone-texto"
            @click="dropdownAndarEditorAberto = !dropdownAndarEditorAberto"
          >
            <IconStack2 :size="18" style="color: var(--destaque-azul)" />
            <span>{{ andarEditorAtual.nome_andar }} ({{ andarEditorAtual.grid_x }}x{{ andarEditorAtual.grid_y }})</span>
            <IconSquareRoundedChevronDown :size="17" />
          </button>

          <Transition name="fade-pop">
            <div v-if="dropdownAndarEditorAberto" class="dropdown-multi-box" style="width: 240px">
              <div class="lista-opcoes-multi">
                <div
                  v-for="(a, idx) in formEstabelecimento.andares"
                  :key="a.id_andar"
                  class="item-opcao-multi"
                  :class="{ 'opcao-ativa': idx === andarEditorIndex }"
                  @click="andarEditorIndex = idx; dropdownAndarEditorAberto = false; selecionados.clear(); historicoUndo = []; historicoRedo = []; resetarCameraGrid(); menuTopoMobileAberto = false"
                >
                  <span>{{ a.nome_andar }} ({{ a.grid_x }}x{{ a.grid_y }})</span>
                  <IconSquareRoundedCheck v-if="idx === andarEditorIndex" :size="18" />
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <button class="btn-secundario btn-duas-linhas item-icone-texto" @click="abrirModalTamanhoGrid">
          <IconLayoutGrid :size="18" />
          <div>Tamanho do Grid<br /><span>({{ andarEditorAtual.grid_x }}x{{ andarEditorAtual.grid_y }})</span></div>
        </button>

        <button
          class="btn-secundario item-icone-texto"
          :disabled="historicoUndo.length === 0"
          title="Desfazer (Ctrl + Z)"
          @click="desfazer"
        >
          <IconArrowBackUp :size="18" />
          <span>Desfazer</span>
        </button>
        <button
          class="btn-secundario item-icone-texto"
          :disabled="historicoRedo.length === 0"
          title="Refazer (Ctrl + Y)"
          @click="refazer"
        >
          <IconArrowForwardUp :size="18" />
          <span>Refazer</span>
        </button>
        <button
          v-if="panX !== 0 || panY !== 0 || zoomEscala !== 1"
          class="btn-secundario item-icone-texto"
          title="Centralizar Zoom"
          @click="resetarCameraGrid"
        >
          <IconSearch :size="16" />
          <span>{{ Math.round(zoomEscala * 100) }}%</span>
        </button>
      </div>

      <div class="topbar-direita">
        <button
          type="button"
          class="btn-caution-avisos"
          :class="{ 'btn-mao-ativa': modoMoverMapa }"
          title="Alternar modo Mover Mapa (ESC para sair)"
          @click="alternarModoMoverMapa"
        >
          <IconHandMove :size="20" />
        </button>

        <button
          class="btn-caution-avisos"
          :class="{ 'caution-ok': podeSalvarEstacionamento, 'caution-pendente': !podeSalvarEstacionamento }"
          title="Clique para mostrar/ocultar avisos de validação"
          @click="alternarPainelAvisos"
        >
          <IconAlertSquareRounded :size="20" />
          <span class="caution-badge">{{ listaAvisosValidacao.length }}</span>
        </button>

        <button
          class="btn-salvar-final btn-duas-linhas item-icone-texto"
          :disabled="!podeSalvarEstacionamento || salvandoNoBanco"
          @click="finalizarSalvarEstacionamento"
        >
          <IconDeviceFloppy :size="18" />
          <div>
            {{ salvandoNoBanco ? 'Salvando...' : 'Finalizar e' }}<br />
            <span v-if="!salvandoNoBanco">Salvar</span>
          </div>
        </button>
      </div>
    </header>

    <div class="editor-workspace">
      <div class="area-grid-container">
        <Transition name="fade-pop">
          <div v-if="mostrarPainelAvisos" class="overlay-flutuante painel-avisos-overlay">
            <div class="overlay-header">
              <strong class="item-icone-texto">
                <IconAlertSquareRounded :size="18" />
                <span>Requisitos para liberar o salvamento:</span>
              </strong>
              <button class="btn-fechar-mini" @click="mostrarPainelAvisos = false">
                <IconSquareRoundedX :size="18" />
              </button>
            </div>
            <ul v-if="listaAvisosValidacao.length > 0" class="lista-avisos-ul">
              <li v-for="(aviso, i) in listaAvisosValidacao" :key="i">{{ aviso }}</li>
            </ul>
            <p v-else class="aviso-tudo-ok item-icone-texto">
              <IconSquareRoundedCheck :size="18" />
              <span>Tudo pronto! O estacionamento já pode ser salvo.</span>
            </p>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="ferramentaCarimbo" class="overlay-flutuante banner-carimbo-overlay">
            <span>
              Modo posicionamento ativo (<strong>{{ ferramentaCarimbo.largura }}x{{ ferramentaCarimbo.altura }}</strong>) — Clique no grid ou aperte <strong>ESC</strong>
            </span>
            <button class="btn-cancelar-carimbo" @click="ferramentaCarimbo = null">
              <IconSquareRoundedX :size="16" />
            </button>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="modoMoverMapa" class="overlay-flutuante banner-carimbo-overlay banner-mao-ativa">
            <span class="item-icone-texto texto-mao-desktop">
              <IconHandMove :size="18" />
              <strong>Modo mover tela ativo</strong> — Pressione <strong>ESC</strong> ou clique na mão para sair
            </span>
            <span class="item-icone-texto texto-mao-mobile">
              <IconHandMove :size="17" />
              <span><strong>Modo mover ativo</strong> — Dê <strong>2 toques seguidos</strong> para sair</span>
            </span>
            <button class="btn-cancelar-carimbo" @click="sairModoMoverComDuploClique">
              <IconSquareRoundedX :size="16" />
            </button>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="mostrarMenuFlutuante && selecionados.size > 0" class="overlay-flutuante menu-selecao-overlay">
            <span class="contagem-sel">{{ selecionados.size }} cél.</span>

            <div class="grupo-acao-item">
              <span class="icone-com-tooltip" data-tooltip="Estrada">
                <IconRoad :size="18" />
              </span>
              <button class="btn-mini add" title="Adicionar Estrada" @click="aplicarEstradaNaSelecao(true)">
                <IconSquareRoundedPlus :size="15" />
              </button>
              <button class="btn-mini rem" title="Remover Estrada" @click="aplicarEstradaNaSelecao(false)">
                <IconSquareRoundedMinus :size="15" />
              </button>
            </div>

            <div class="grupo-acao-item">
              <span class="icone-com-tooltip" data-tooltip="Setor">
                <IconLayoutBoard :size="18" />
              </span>
              <button class="btn-mini add" title="Definir Setor" @click="abrirModalSetor">
                <IconSquareRoundedPlus :size="15" />
              </button>
              <button class="btn-mini rem" title="Remover Setor" @click="removerSetorDaSelecao">
                <IconSquareRoundedMinus :size="15" />
              </button>
            </div>

            <div class="grupo-acao-item">
              <span class="icone-com-tooltip" data-tooltip="Vagas">
                <IconParking :size="18" />
              </span>
              <button class="btn-mini add" title="Criar Vagas" @click="aplicarVagaNaSelecao(true)">
                <IconSquareRoundedPlus :size="15" />
              </button>
              <button class="btn-mini rem" title="Remover Vagas" @click="aplicarVagaNaSelecao(false)">
                <IconSquareRoundedMinus :size="15" />
              </button>
            </div>

            <button
              class="btn-mini borracha-tudo"
              title="Borracha: Apagar tudo na área selecionada"
              @click="apagarTudoNaSelecao"
            >
              <IconEraser :size="16" />
            </button>

            <button
              class="btn-mini limpar"
              title="Fechar seleção (ESC)"
              @click="selecionados.clear(); mostrarMenuFlutuante = false"
            >
              <IconSquareRoundedX :size="16" />
            </button>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="celulaInspecionadaHover" class="overlay-flutuante badge-hover-setor">
            <span
              class="bolinha-cor-setor"
              :style="{ backgroundColor: celulaInspecionadaHover.cor }"
            ></span>
            <strong>{{ celulaInspecionadaHover.titulo }}</strong>
            <span v-if="celulaInspecionadaHover.detalhe" class="texto-colchetes-setor">
              [{{ celulaInspecionadaHover.detalhe }}]
            </span>
          </div>
        </Transition>

        <div
          ref="gridPrincipalRef"
          class="area-grid-principal"
          @mouseleave="hoverCoord = null"
          @dblclick.stop.prevent="sairModoMoverComDuploClique"
          @touchstart.passive="aoIniciarToqueGrid"
          @touchmove.prevent="aoMoverToqueGrid"
          @touchend="aoFinalizarToqueGrid"
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
              <div :key="andarEditorAtual.id_andar" class="matriz-com-coordenadas">
                <div
                  class="linha-coordenadas-x"
                  :style="{ gridTemplateColumns: `36px repeat(${andarEditorAtual.grid_x}, 36px)` }"
                >
                  <div class="canto-xy">Y\X</div>
                  <div v-for="x in andarEditorAtual.grid_x" :key="`cx-${x}`" class="rotulo-coord">
                    {{ x - 1 }}
                  </div>
                </div>

                <div
                  v-for="y in andarEditorAtual.grid_y"
                  :key="`row-${y}`"
                  class="linha-grid-y"
                  :style="{ gridTemplateColumns: `36px repeat(${andarEditorAtual.grid_x}, 36px)` }"
                >
                  <div class="rotulo-coord">{{ y - 1 }}</div>

                  <div
                    v-for="x in andarEditorAtual.grid_x"
                    :key="`cell-${x - 1}-${y - 1}`"
                    :data-coord="`${x - 1},${y - 1}`"
                    class="celula-editor-fundo"
                    :style="{
                      backgroundColor:
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.corSetor || 'transparent'
                    }"
                    @mousedown.prevent="iniciarSelecaoCelula(x - 1, y - 1, $event)"
                    @mouseenter="moverMouseCelula(x - 1, y - 1, $event)"
                  >
                    <div
                      class="quadrado-editor"
                      :class="[
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAZIO' ? 'qe-vazio' : '',
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ESTRADA' ? 'qe-estrada' : '',
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA' &&
                        !andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.macEsp
                          ? 'qe-vaga-amarela'
                          : '',
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ENTRADA' ? 'qe-entrada' : '',
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'SAIDA' ? 'qe-saida' : '',
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ACESSO' ? 'qe-acesso' : '',
                        selecionados.has(`${x - 1},${y - 1}`) ? 'qe-selecionado-roxo' : '',
                        coordsSombraCarimbo.has(`${x - 1},${y - 1}`) ? 'qe-sombra-verde' : ''
                      ]"
                      :style="
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA' &&
                        andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.macEsp &&
                        !selecionados.has(`${x - 1},${y - 1}`)
                          ? {
                              backgroundColor: escurecerCorHex(
                                andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.corSetor,
                                0.55
                              ),
                              borderColor: '#0f172a',
                              color: '#ffffff'
                            }
                          : {}
                      "
                    >
                      <span v-if="andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'VAGA'">
                        {{ andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.identificador }}
                      </span>
                      <IconDoorEnter
                        v-else-if="andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ENTRADA'"
                        :size="17"
                      />
                      <IconDoorExit
                        v-else-if="andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'SAIDA'"
                        :size="17"
                      />
                      <IconArrowBarRight
                        v-else-if="andarEditorAtual.celulas[`${x - 1},${y - 1}`]?.tipo === 'ACESSO'"
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

      <!-- Painel Lateral Direito -->
      <aside class="sidebar-direita-editor" :class="{ 'sidebar-mobile-aberta': menuAdicionarMobileAberto }">
        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconDoorEnter :size="18" />
            <span>Entradas / Saídas / Acessos</span>
          </h4>
          <p class="dica-painel">Escolha a orientação (H = Horizontal, V = Vertical):</p>

          <div class="linha-botoes-dupla">
            <button class="btn-ferramenta cor-entrada item-icone-texto" @click="abrirConfigAcesso('ENTRADA', 'H')">
              <IconDoorEnter :size="16" />
              <span>Entrada (H)</span>
            </button>
            <button class="btn-ferramenta cor-entrada item-icone-texto" @click="abrirConfigAcesso('ENTRADA', 'V')">
              <IconDoorEnter :size="16" />
              <span>Entrada (V)</span>
            </button>
          </div>

          <div class="linha-botoes-dupla">
            <button class="btn-ferramenta cor-saida item-icone-texto" @click="abrirConfigAcesso('SAIDA', 'H')">
              <IconDoorExit :size="16" />
              <span>Saída (H)</span>
            </button>
            <button class="btn-ferramenta cor-saida item-icone-texto" @click="abrirConfigAcesso('SAIDA', 'V')">
              <IconDoorExit :size="16" />
              <span>Saída (V)</span>
            </button>
          </div>

          <div class="linha-botoes-dupla">
            <button class="btn-ferramenta cor-acesso item-icone-texto" @click="abrirConfigAcesso('ACESSO', 'H')">
              <IconArrowBarRight :size="16" />
              <span>Acesso (H)</span>
            </button>
            <button class="btn-ferramenta cor-acesso item-icone-texto" @click="abrirConfigAcesso('ACESSO', 'V')">
              <IconArrowBarRight :size="16" />
              <span>Acesso (V)</span>
            </button>
          </div>
        </div>

        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconCpu :size="18" />
            <span>Equipamentos (ESP32)</span>
          </h4>
          <p class="dica-painel">Clique num modelo e posicione sobre as vagas amarelas:</p>

          <div class="linha-equipamentos">
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(1, 2)">
              <IconCpu :size="16" />
              <span>1x2</span>
            </button>
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(1, 3)">
              <IconCpu :size="16" />
              <span>1x3</span>
            </button>
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(1, 4)">
              <IconCpu :size="16" />
              <span>1x4</span>
            </button>
          </div>

          <div class="linha-equipamentos">
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(2, 1)">
              <IconCpu :size="16" />
              <span>2x1</span>
            </button>
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(3, 1)">
              <IconCpu :size="16" />
              <span>3x1</span>
            </button>
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(4, 1)">
              <IconCpu :size="16" />
              <span>4x1</span>
            </button>
          </div>

          <div class="linha-equipamentos">
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(2, 2)">
              <IconCpu :size="16" />
              <span>2x2</span>
            </button>
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(2, 4)">
              <IconCpu :size="16" />
              <span>2x4</span>
            </button>
            <button class="btn-equipamento item-icone-texto" @click="ativarCarimboEquipamento(4, 2)">
              <IconCpu :size="16" />
              <span>4x2</span>
            </button>
          </div>
        </div>

        <div class="painel-ferramentas">
          <h4 class="item-icone-texto">
            <IconLayoutBoard :size="18" />
            <span>Setores do Andar</span>
          </h4>
          <p class="dica-painel">Edite nome, prefixo, cor ou exclua setores:</p>
          <button class="btn-alterar-setores-menu item-icone-texto" @click="abrirModalAlterarSetores">
            <IconPencil :size="17" />
            <span>Alterar Setores ({{ andarEditorAtual.setores?.length || 0 }})</span>
          </button>
        </div>
      </aside>
    </div>

    <!-- Modal: Tamanho do Grid -->
    <Transition name="fade-backdrop">
      <div v-if="modalTamanhoAberto" class="modal-backdrop" @click.self="modalTamanhoAberto = false">
        <div class="modal-box modal-compacto">
          <h3 class="item-icone-texto">
            <IconLayoutGrid :size="20" />
            <span>Tamanho do Grid (5 a 100)</span>
          </h3>
          <div class="linha-inputs-compactos">
            <div class="campo-compacto">
              <label>Largura (X)</label>
              <input v-model.number="tempGridX" type="number" min="5" max="100" class="input-numero-compacto" />
            </div>
            <span class="separador-x">×</span>
            <div class="campo-compacto">
              <label>Altura (Y)</label>
              <input v-model.number="tempGridY" type="number" min="5" max="100" class="input-numero-compacto" />
            </div>
          </div>
          <div class="modal-acoes modal-acoes-centralizadas">
            <button class="btn-secundario item-icone-texto" @click="modalTamanhoAberto = false">
              <IconSquareRoundedX :size="17" />
              <span>Cancelar</span>
            </button>
            <button class="btn-primario item-icone-texto" @click="confirmarTamanhoGrid">
              <IconSquareRoundedCheck :size="17" />
              <span>Aplicar</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal: Definir Setor -->
    <Transition name="fade-backdrop">
      <div v-if="modalSetorAberto" class="modal-backdrop" @click.self="modalSetorAberto = false">
        <div class="modal-box">
          <h3 class="item-icone-texto">
            <IconLayoutBoard :size="20" />
            <span>Definir Setor na Área Selecionada</span>
          </h3>
          <div class="campo-grupo" style="margin-top: 12px">
            <label>Nome do Setor</label>
            <input v-model="nomeNovoSetor" type="text" maxlength="25" placeholder="Ex: Setor Norte" />
          </div>
          <div class="campo-grupo">
            <label>Prefixo das Vagas (1 a 3 letras/números)</label>
            <input
              :value="prefixoNovoSetor"
              type="text"
              maxlength="3"
              placeholder="Ex: A, B, VIP"
              class="input-curto-prefixo"
              @input="prefixoNovoSetor = formatarInputPrefixo($event.target.value)"
            />
          </div>
          <div class="campo-grupo">
            <label>Escolha uma das 10 cores exclusivas do andar</label>
            <div class="grade-cores-setor">
              <button
                v-for="cor in paletaSetores"
                :key="cor.hex"
                type="button"
                class="botao-cor-setor"
                :class="{ 'cor-selecionada': corNovoSetor === cor.hex }"
                :disabled="coresUsadasNoAndar.has(cor.hex)"
                :style="{
                  backgroundColor: cor.hex,
                  opacity: coresUsadasNoAndar.has(cor.hex) ? 0.25 : 1,
                  cursor: coresUsadasNoAndar.has(cor.hex) ? 'not-allowed' : 'pointer'
                }"
                @click="corNovoSetor = cor.hex"
              >
                {{ cor.nome }} {{ coresUsadasNoAndar.has(cor.hex) ? '(Em uso)' : '' }}
              </button>
            </div>
          </div>
          <div class="modal-acoes modal-acoes-centralizadas">
            <button class="btn-secundario item-icone-texto" @click="modalSetorAberto = false">
              <IconSquareRoundedX :size="17" />
              <span>Cancelar</span>
            </button>
            <button class="btn-primario item-icone-texto" @click="confirmarAdicionarSetor">
              <IconSquareRoundedCheck :size="17" />
              <span>Aplicar Setor</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal: Alterar ou Excluir Setores -->
    <Transition name="fade-backdrop">
      <div v-if="modalAlterarSetoresAberto" class="modal-backdrop" @click.self="modalAlterarSetoresAberto = false">
        <div class="modal-box modal-alterar-setor">
          <div class="overlay-header">
            <h3 class="item-icone-texto">
              <IconPencil :size="19" />
              <span>Alterar Setores do Andar</span>
            </h3>
            <button class="btn-fechar-mini" @click="modalAlterarSetoresAberto = false">
              <IconSquareRoundedX :size="18" />
            </button>
          </div>

          <div class="campo-grupo" style="margin-top: 10px">
            <label>Pesquisar ou Selecionar Setor</label>
            <div class="combobox-setor-wrapper">
              <input
                v-model="termoBuscaSetor"
                type="text"
                placeholder="Digite o nome ou clique na seta..."
                @focus="dropdownSetoresAberto = true"
                @input="aoDigitarBuscaSetor"
              />
              <button
                type="button"
                class="btn-seta-combobox"
                @click="dropdownSetoresAberto = !dropdownSetoresAberto"
              >
                <IconSquareRoundedChevronDown :size="18" />
              </button>

              <div v-if="dropdownSetoresAberto" class="lista-dropdown-setores">
                <div
                  v-for="s in setoresFiltradosBusca"
                  :key="s.id_setor"
                  class="item-dropdown-setor"
                  @click="carregarDadosSetorNoForm(s)"
                >
                  <span class="bolinha-cor-setor" :style="{ backgroundColor: s.cor_hex }"></span>
                  <strong>{{ s.nome_setor }}</strong>
                  <span class="texto-colchetes-setor">[Prefixo: {{ s.prefixo }}]</span>
                </div>
                <div v-if="setoresFiltradosBusca.length === 0" class="item-dropdown-vazio">
                  Nenhum setor encontrado neste andar.
                </div>
              </div>
            </div>
          </div>

          <div
            class="area-edicao-setor-campos"
            :class="{ 'campos-desabilitados': !setorSelecionadoParaEdicao }"
          >
            <p v-if="!setorSelecionadoParaEdicao" class="msg-preencha-setor">
              Preencha o campo de setor acima para liberar a edição
            </p>

            <div class="campo-grupo">
              <label>Novo Nome do Setor</label>
              <input
                v-model="editNomeSetor"
                type="text"
                maxlength="25"
                :disabled="!setorSelecionadoParaEdicao"
              />
            </div>

            <div class="campo-grupo">
              <label>Prefixo das Vagas (1 a 3 caracteres)</label>
              <input
                :value="editPrefixoSetor"
                type="text"
                maxlength="3"
                class="input-curto-prefixo"
                :disabled="!setorSelecionadoParaEdicao"
                @input="editPrefixoSetor = formatarInputPrefixo($event.target.value)"
              />
            </div>

            <div class="campo-grupo">
              <label>Cor do Setor</label>
              <div class="grade-cores-setor">
                <button
                  v-for="cor in paletaSetores"
                  :key="`ed-${cor.hex}`"
                  type="button"
                  class="botao-cor-setor"
                  :class="{ 'cor-selecionada': editCorSetor === cor.hex }"
                  :disabled="!setorSelecionadoParaEdicao || corOcupadaPorOutroSetor(cor.hex)"
                  :style="{
                    backgroundColor: cor.hex,
                    opacity: corOcupadaPorOutroSetor(cor.hex) ? 0.22 : 1
                  }"
                  @click="editCorSetor = cor.hex"
                >
                  {{ cor.nome }}
                </button>
              </div>
            </div>

            <div class="botoes-empilhados-setor">
              <button
                type="button"
                class="btn-excluir-setor item-icone-texto"
                :disabled="!setorSelecionadoParaEdicao"
                @click="excluirSetorInteiro"
              >
                <IconTrash :size="17" />
                <span>Excluir Setor</span>
              </button>
              <button
                type="button"
                class="btn-confirmar-setor item-icone-texto"
                :disabled="!setorSelecionadoParaEdicao"
                @click="salvarAlteracoesSetor"
              >
                <IconSquareRoundedCheck :size="17" />
                <span>Confirmar Alterações</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal: Tamanho da Entrada / Saída / Acesso (Botões Cancelar/Posicionar Centralizados) -->
    <Transition name="fade-backdrop">
      <div v-if="modalAcessoAberto" class="modal-backdrop" @click.self="modalAcessoAberto = false">
        <div class="modal-box modal-compacto">
          <h3 class="item-icone-texto">
            <IconDoorEnter v-if="tipoAcessoTemp === 'ENTRADA'" :size="20" />
            <IconDoorExit v-else-if="tipoAcessoTemp === 'SAIDA'" :size="20" />
            <IconArrowBarRight v-else :size="20" />
            <span>Configurar {{ tipoAcessoTemp }} ({{ orientacaoAcessoTemp }})</span>
          </h3>
          <div class="linha-inputs-compactos">
            <div class="campo-compacto">
              <label>Largura em células (1 a 10)</label>
              <input
                v-model.number="tamanhoAcessoTemp"
                type="number"
                min="1"
                max="10"
                class="input-numero-compacto"
              />
            </div>
          </div>
          <div class="modal-acoes modal-acoes-centralizadas">
            <button class="btn-secundario item-icone-texto" @click="modalAcessoAberto = false">
              <IconSquareRoundedX :size="17" />
              <span>Cancelar</span>
            </button>
            <button class="btn-primario item-icone-texto" @click="ativarCarimboAcesso">
              <IconSquareRoundedCheck :size="17" />
              <span>Posicionar</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal: Vincular MAC do ESP32 -->
    <Transition name="fade-backdrop">
      <div v-if="modalMacAberto" class="modal-backdrop" @click.self="modalMacAberto = false">
        <div class="modal-box">
          <h3 class="item-icone-texto">
            <IconCpu :size="20" />
            <span>Vincular Equipamento ESP32</span>
          </h3>
          <p class="subtitulo">
            Vinculando {{ coordsParaVincularMac.length }} vaga(s) selecionada(s).
          </p>
          <div class="campo-grupo" style="margin-top: 12px">
            <label>Código MAC Único do ESP32</label>
            <input
              v-model="macTemp"
              type="text"
              maxlength="17"
              placeholder="Ex: AA:BB:CC:DD:EE:01"
            />
          </div>
          <div class="modal-acoes modal-acoes-centralizadas">
            <button class="btn-secundario item-icone-texto" @click="modalMacAberto = false">
              <IconSquareRoundedX :size="17" />
              <span>Cancelar</span>
            </button>
            <button class="btn-primario item-icone-texto" @click="confirmarVinculoMac">
              <IconSquareRoundedCheck :size="17" />
              <span>Vincular Vagas</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal: Sucesso ao Salvar -->
    <Transition name="fade-backdrop">
      <div v-if="modalSucessoSalvarAberto" class="modal-backdrop">
        <div class="modal-box modal-sucesso-salvar">
          <div class="icone-sucesso-modal" style="color: #22c55e">
            <IconSquareRoundedCheck :size="48" />
          </div>
          <h3>Estacionamento Salvo!</h3>
          <p class="subtitulo" style="margin-top: 6px">
            Todas as configurações de andares, setores, vagas e equipamentos foram gravadas no banco de dados MySQL com sucesso.
          </p>
          <button
            type="button"
            class="btn-confirmar-sucesso item-icone-texto"
            @click="confirmarSucessoEVoltarLista"
          >
            <IconSquareRoundedCheck :size="20" />
            <span>Voltar para a Lista de Estacionamentos</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>