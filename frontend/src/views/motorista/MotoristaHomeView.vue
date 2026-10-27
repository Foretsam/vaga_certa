<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  estabelecimentos,
  carregarDadosDoBanco,
  contarVagasEstabelecimento
} from '@/stores/estacionamentoStore'
import {
  IconQrcode,
  IconSearch,
  IconPin,
  IconParking,
  IconSquareRoundedArrowRight,
  IconSquareRoundedX,
  IconAlertSquareRounded
} from '@/constants/icons'

const router = useRouter()

const termoBuscaNome = ref('')
const cidadeFiltro = ref('TODAS')

// Estado do Leitor de QR Code via Câmera
const cameraAtiva = ref(false)
const erroCamera = ref('')
const videoRef = ref(null)
const canvasRef = ref(null)
let streamMidia = null
let loopLeituraId = null

onMounted(() => {
  if (estabelecimentos.value.length === 0) {
    carregarDadosDoBanco()
  }
})

onUnmounted(() => {
  pararCameraQr()
})

// Apenas estacionamentos ativos para o motorista
const estacionamentosAtivos = computed(() => {
  return estabelecimentos.value.filter(e => !e.inativo)
})

const cidadesDisponiveis = computed(() => {
  const setCidades = new Set(
    estacionamentosAtivos.value
      .map(e => (e.cidade || 'Sorocaba').trim())
      .filter(Boolean)
  )
  return Array.from(setCidades).sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

const estacionamentosFiltrados = computed(() => {
  const termo = termoBuscaNome.value.trim().toLowerCase()
  return estacionamentosAtivos.value
    .filter((est) => {
      const cidadeEst = (est.cidade || 'Sorocaba').trim()
      const bateCidade =
        cidadeFiltro.value === 'TODAS' ||
        cidadeEst.toLowerCase() === cidadeFiltro.value.toLowerCase()
      const bateNome =
        !termo ||
        est.nome.toLowerCase().includes(termo) ||
        cidadeEst.toLowerCase().includes(termo) ||
        String(est.id) === termo
      return bateCidade && bateNome
    })
    .map(est => ({
      ...est,
      metricas: contarVagasEstabelecimento(est)
    }))
})

function abrirEstacionamentoMotorista(idEst) {
  pararCameraQr()
  router.push({ name: 'motorista-mapa', params: { id: idEst } })
}

// =========================================================
// LEITOR DE QR CODE PELA CÂMERA (NATIVO + FALLBACK JSQR)
// =========================================================
function carregarJsQrFallback() {
  return new Promise((resolve) => {
    if (window.jsQR) return resolve(window.jsQR)
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js'
    script.onload = () => resolve(window.jsQR)
    script.onerror = () => resolve(null)
    document.head.appendChild(script)
  })
}

function extrairIdDoTextoQr(textoLido) {
  if (!textoLido) return null
  const limpo = textoLido.trim()

  // Caso 1: URL do formato /vagas/12 ou ?id=12
  const matchVagas = limpo.match(/\/vagas\/(\d+)/i)
  if (matchVagas) return Number(matchVagas[1])

  const matchQuery = limpo.match(/[?&]id=(\d+)/i)
  if (matchQuery) return Number(matchQuery[1])

  // Caso 2: Apenas o número do ID
  if (/^\d+$/.test(limpo)) return Number(limpo)

  return null
}

async function iniciarCameraQr() {
  erroCamera.value = ''
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    erroCamera.value = 'Seu navegador não suporta acesso direto à câmera. Utilize a busca abaixo.'
    return
  }

  try {
    streamMidia = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' } },
      audio: false
    })
    cameraAtiva.value = true

    let detectorNativo = null
    if ('BarcodeDetector' in window) {
      try {
        detectorNativo = new window.BarcodeDetector({ formats: ['qr_code'] })
      } catch {
        detectorNativo = null
      }
    }
    if (!detectorNativo) {
      await carregarJsQrFallback()
    }

    setTimeout(() => {
      if (videoRef.value && streamMidia) {
        videoRef.value.srcObject = streamMidia
        videoRef.value.setAttribute('playsinline', true)
        videoRef.value.play()
        monitorarQuadroVideo(detectorNativo)
      }
    }, 100)
  } catch (err) {
    erroCamera.value = 'Permissão de câmera negada ou câmera indisponível. Pesquise o estacionamento abaixo.'
    cameraAtiva.value = false
  }
}

function monitorarQuadroVideo(detectorNativo) {
  const lerFrame = async () => {
    if (!cameraAtiva.value || !videoRef.value) return

    const video = videoRef.value
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      // 1. Tenta pelo BarcodeDetector nativo
      if (detectorNativo) {
        try {
          const codigos = await detectorNativo.detect(video)
          if (codigos.length > 0) {
            const idEncontrado = extrairIdDoTextoQr(codigos[0].rawValue)
            if (idEncontrado) {
              abrirEstacionamentoMotorista(idEncontrado)
              return
            }
          }
        } catch {
          // Segue para fallback
        }
      }

      // 2. Fallback via Canvas + jsQR
      if (window.jsQR && canvasRef.value) {
        const canvas = canvasRef.value
        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const code = window.jsQR(imgData.data, imgData.width, imgData.height)
        if (code && code.data) {
          const idEncontrado = extrairIdDoTextoQr(code.data)
          if (idEncontrado) {
            abrirEstacionamentoMotorista(idEncontrado)
            return
          }
        }
      }
    }

    loopLeituraId = requestAnimationFrame(lerFrame)
  }

  loopLeituraId = requestAnimationFrame(lerFrame)
}

function pararCameraQr() {
  cameraAtiva.value = false
  if (loopLeituraId) {
    cancelAnimationFrame(loopLeituraId)
    loopLeituraId = null
  }
  if (streamMidia) {
    streamMidia.getTracks().forEach(track => track.stop())
    streamMidia = null
  }
}
</script>

<template>
  <main class="motorista-home-layout">
    <div class="motorista-home-card">
      <!-- TOPO: ESCANEAR QR CODE -->
      <div class="motorista-qr-secao">
        <div class="icone-destaque-qr">
          <IconQrcode :size="44" />
        </div>
        <h1 class="titulo-principal">Encontrar Vaga Certa</h1>
        <p class="subtitulo">
          Aponte a câmera para o QR Code na entrada do estacionamento ou pesquise pelo nome e cidade abaixo
        </p>

        <button
          v-if="!cameraAtiva"
          type="button"
          class="btn-primario btn-escanear-qr item-icone-texto"
          @click="iniciarCameraQr"
        >
          <IconQrcode :size="21" />
          <span>Escanear QR Code com a Câmera</span>
        </button>

        <!-- Visor da Câmera quando ativado -->
        <Transition name="fade-pop">
          <div v-if="cameraAtiva" class="camera-qr-box">
            <div class="camera-video-wrapper">
              <video ref="videoRef" class="video-leitor-qr" muted playsinline></video>
              <div class="mira-qr-overlay"></div>
            </div>
            <canvas ref="canvasRef" style="display: none"></canvas>

            <button
              type="button"
              class="btn-secundario item-icone-texto"
              style="width: 100%; margin-top: 10px"
              @click="pararCameraQr"
            >
              <IconSquareRoundedX :size="18" />
              <span>Fechar Câmera</span>
            </button>
          </div>
        </Transition>

        <Transition name="fade-pop">
          <div v-if="erroCamera" class="alerta-auth erro item-icone-texto" style="margin-top: 12px; margin-bottom: 0">
            <IconAlertSquareRounded :size="18" />
            <span>{{ erroCamera }}</span>
          </div>
        </Transition>
      </div>

      <div class="divisor-ou-motorista">
        <span>OU PESQUISE O ESTACIONAMENTO</span>
      </div>

      <!-- FILTROS: BUSCA POR NOME E FILTRO DE CIDADE -->
      <div class="filtros-motorista-grid">
        <div class="input-pesquisa-icone-wrapper">
          <IconSearch :size="18" class="icone-input-pesquisa" />
          <input
            v-model="termoBuscaNome"
            type="text"
            placeholder="Pesquisar por nome do estacionamento..."
            class="input-pesquisa-grande com-icone"
          />
        </div>

        <div class="select-cidade-motorista-wrapper">
          <IconPin :size="18" class="icone-input-pesquisa" style="color: var(--destaque-azul)" />
          <select v-model="cidadeFiltro" class="select-padrao select-com-icone-esq">
            <option value="TODAS">Todas as cidades ({{ cidadesDisponiveis.length }})</option>
            <option v-for="cid in cidadesDisponiveis" :key="cid" :value="cid">
              {{ cid }}
            </option>
          </select>
        </div>
      </div>

      <!-- LISTA DE ESTACIONAMENTOS DISPONÍVEIS -->
      <div class="lista-estacionamentos-motorista">
        <div
          v-for="est in estacionamentosFiltrados"
          :key="est.id"
          class="item-est-motorista"
          @click="abrirEstacionamentoMotorista(est.id)"
        >
          <div class="info-est-motorista">
            <div class="icone-p-motorista">
              <IconParking :size="22" />
            </div>
            <div class="textos-est-motorista">
              <h3>{{ est.nome }}</h3>
              <div class="sub-meta-motorista">
                <span class="item-icone-texto badge-cidade-motorista">
                  <IconPin :size="13" />
                  {{ est.cidade || 'Sorocaba' }}
                </span>
                <span class="ocultar-info-mobile">•</span>
                <span class="ocultar-info-mobile">{{ est.andares?.length || 1 }} andar(es)</span>
              </div>
            </div>
          </div>

          <div class="status-vagas-motorista">
            <span
              class="badge-livres-motorista ocultar-info-mobile"
              :class="est.metricas.livres > 0 ? 'tem-vaga' : 'lotado'"
            >
              {{ est.metricas.livres > 0 ? `${est.metricas.livres} livres` : 'Lotado' }}
            </span>
            <IconSquareRoundedArrowRight :size="20" class="seta-ir-mapa" />
          </div>
        </div>

        <div v-if="estacionamentosFiltrados.length === 0" class="lista-vazia">
          Nenhum estacionamento encontrado para este filtro.
        </div>
      </div>
    </div>
  </main>
</template>