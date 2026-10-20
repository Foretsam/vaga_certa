<script setup>
import { ref, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Html5Qrcode } from 'html5-qrcode'
import { estabelecimentos } from '../store/estacionamentoStore'

const router = useRouter()
const cameraAtiva = ref(false)
const erroCamera = ref('')
let leitorQrCode = null

function abrirEstacionamento(id) {
  pararCamera()
  router.push({ name: 'motorista-mapa', params: { id } })
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
          if (idUrl) return abrirEstacionamento(idUrl)
          const partes = url.pathname.split('/')
          const ultimo = partes[partes.length - 1]
          if (ultimo && !isNaN(ultimo)) return abrirEstacionamento(ultimo)
        } catch {
          abrirEstacionamento(textoLido)
        }
      },
      () => {}
    )
  } catch {
    erroCamera.value = 'Câmera indisponível neste dispositivo. Utilize os botões de acesso rápido abaixo.'
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

onUnmounted(() => {
  pararCamera()
})
</script>

<template>
  <main class="tela-inicial">
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
          @click="abrirEstacionamento(est.id)"
        >
          ⚡ Abrir {{ est.nome }} (ID: {{ est.id }})
        </button>
        <button class="btn-teste-dev destaque-admin" @click="router.push({ name: 'admin-lista' })">
          🛠️ Ir para Painel Admin Dev (Criar / Editar Mapas 2D)
        </button>
      </div>
    </div>
  </main>
</template>