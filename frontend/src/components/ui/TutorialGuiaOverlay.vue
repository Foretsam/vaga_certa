<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { TUTORIAIS_POR_ROTA } from '@/constants/tutoriaisConfig'
import {
  rotaTutorialAtivo,
  indiceEtapaTutorial,
  etapasTutorialAtual,
  etapaTutorialAtual,
  verificarPrimeiroAcessoTutorial,
  iniciarTutorial,
  avancarEtapaTutorial,
  voltarEtapaTutorial
} from '@/stores/tutorialStore'
import {
  IconInfoCircle,
  IconSquareRoundedChevronLeft,
  IconSquareRoundedChevronRight,
  IconSquareRoundedCheck
} from '@/constants/icons'

const route = useRoute()

const larguraTela = ref(window.innerWidth)
const alturaTela = ref(window.innerHeight)
const rectDestaque = ref(null)

const mostrarBotaoInfoTopo = computed(() => {
  return Boolean(route.name && TUTORIAIS_POR_ROTA[route.name])
})

const ehTabletOuMobile = computed(() => larguraTela.value <= 1024)

const textoExibidoEtapa = computed(() => {
  if (!etapaTutorialAtual.value) return ''
  if (ehTabletOuMobile.value && etapaTutorialAtual.value.textoTabletMobile) {
    return etapaTutorialAtual.value.textoTabletMobile
  }
  return etapaTutorialAtual.value.texto
})

function limparClassesTemporariasMobile() {
  document
    .querySelectorAll('.tutorial-forcar-painel-mobile')
    .forEach(el => el.classList.remove('tutorial-forcar-painel-mobile'))
}

function localizarElementoAlvo(etapa) {
  if (!etapa) return null
  const seletorAtivo =
    ehTabletOuMobile.value && etapa.seletorTabletMobile
      ? etapa.seletorTabletMobile
      : etapa.seletor

  if (!seletorAtivo) return null

  if (ehTabletOuMobile.value) {
    if (etapa.abrirTopbarMobile) {
      document.querySelector('.editor-topbar')?.classList.add('tutorial-forcar-painel-mobile')
    }
    if (etapa.abrirSidebarMobile) {
      document.querySelector('.sidebar-direita-editor')?.classList.add('tutorial-forcar-painel-mobile')
    }
  }

  let el = document.querySelector(seletorAtivo)
  if (el && etapa.subirParaPai) {
    el = el.closest(etapa.subirParaPai) || el
  }
  return el
}

async function calcularPosicaoDestaque() {
  limparClassesTemporariasMobile()
  await nextTick()

  const etapa = etapaTutorialAtual.value
  if (!etapa) {
    rectDestaque.value = null
    return
  }

  const el = localizarElementoAlvo(etapa)
  if (!el) {
    rectDestaque.value = null
    return
  }

  el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' })

  setTimeout(() => {
    const r = el.getBoundingClientRect()
    if (r.width === 0 && r.height === 0) {
      rectDestaque.value = null
      return
    }
    const pad = 6
    rectDestaque.value = {
      top: Math.max(4, r.top - pad),
      left: Math.max(4, r.left - pad),
      width: Math.min(larguraTela.value - 8, r.width + pad * 2),
      height: r.height + pad * 2,
      bottom: r.bottom + pad
    }
  }, 220)
}

const estiloSpotlight = computed(() => {
  if (!rectDestaque.value) return null
  return {
    top: `${rectDestaque.value.top}px`,
    left: `${rectDestaque.value.left}px`,
    width: `${rectDestaque.value.width}px`,
    height: `${rectDestaque.value.height}px`
  }
})

const estiloPopup = computed(() => {
  if (!rectDestaque.value) {
    return {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)'
    }
  }

  const larguraPopup = Math.min(370, larguraTela.value - 24)
  let left = rectDestaque.value.left + rectDestaque.value.width / 2 - larguraPopup / 2
  left = Math.max(12, Math.min(left, larguraTela.value - larguraPopup - 12))

  // Reserva margem segura para nunca cortar os botões inferiores do card
  const alturaEstimadaPopup = 250
  let top = rectDestaque.value.bottom + 12

  if (top + alturaEstimadaPopup > alturaTela.value - 16) {
    const topAcima = rectDestaque.value.top - alturaEstimadaPopup - 12
    if (topAcima >= 14) {
      top = topAcima
    } else {
      // Quando o elemento é grande (ex: Mapa 2D no Passo 3), ancora dentro da área visível com folga inferior
      top = Math.max(14, alturaTela.value - alturaEstimadaPopup - 24)
    }
  }

  return {
    top: `${top}px`,
    left: `${left}px`,
    width: `${larguraPopup}px`
  }
})

watch(
  () => route.name,
  (novaRota) => {
    limparClassesTemporariasMobile()
    rotaTutorialAtivo.value = null
    if (novaRota && TUTORIAIS_POR_ROTA[novaRota]) {
      setTimeout(() => {
        verificarPrimeiroAcessoTutorial(novaRota)
      }, 350)
    }
  },
  { immediate: true }
)

watch(
  [rotaTutorialAtivo, indiceEtapaTutorial],
  ([ativo]) => {
    if (ativo) {
      calcularPosicaoDestaque()
    } else {
      limparClassesTemporariasMobile()
      rectDestaque.value = null
    }
  }
)

function aoRedimensionarJanela() {
  larguraTela.value = window.innerWidth
  alturaTela.value = window.innerHeight
  if (rotaTutorialAtivo.value) {
    calcularPosicaoDestaque()
  }
}

onMounted(() => {
  window.addEventListener('resize', aoRedimensionarJanela)
})

onUnmounted(() => {
  limparClassesTemporariasMobile()
  window.removeEventListener('resize', aoRedimensionarJanela)
})
</script>

<template>
  <!-- Botão Superior Info Circle nas Views Gerente e Dev para Reabrir o Tutorial -->
  <button
    v-if="mostrarBotaoInfoTopo"
    type="button"
    class="btn-tutorial-info"
    title="Ver tutorial desta página"
    @click="iniciarTutorial(route.name)"
  >
    <IconInfoCircle :size="22" />
  </button>

  <!-- Camada de Bloqueio Total + Destaque Spotlight + Popup do Tutorial -->
  <Transition name="fade-backdrop">
    <div
      v-if="rotaTutorialAtivo && etapaTutorialAtual"
      class="tutorial-overlay-bloqueio"
      @click.stop.prevent
    >
      <!-- Recorte iluminado no elemento alvo (ou fundo escuro total quando central) -->
      <div
        v-if="estiloSpotlight"
        class="tutorial-spotlight-box"
        :style="estiloSpotlight"
      ></div>
      <div v-else class="tutorial-backdrop-central"></div>

      <!-- Popup Explicativo -->
      <div class="tutorial-popup-card" :style="estiloPopup">
        <div class="tutorial-popup-topo">
          <span class="badge-etapa-tutorial">
            Passo {{ indiceEtapaTutorial + 1 }} de {{ etapasTutorialAtual.length }}
          </span>
        </div>

        <h3 class="tutorial-popup-titulo">{{ etapaTutorialAtual.titulo }}</h3>
        <p class="tutorial-popup-texto">{{ textoExibidoEtapa }}</p>

        <div class="tutorial-popup-acoes">
          <button
            type="button"
            class="btn-secundario btn-tutorial-nav item-icone-texto"
            :disabled="indiceEtapaTutorial === 0"
            @click="voltarEtapaTutorial"
          >
            <IconSquareRoundedChevronLeft :size="18" />
            <span>Anterior</span>
          </button>

          <button
            type="button"
            class="btn-primario btn-tutorial-nav item-icone-texto"
            @click="avancarEtapaTutorial"
          >
            <span>
              {{ indiceEtapaTutorial === etapasTutorialAtual.length - 1 ? 'Concluir' : 'Próximo' }}
            </span>
            <IconSquareRoundedCheck
              v-if="indiceEtapaTutorial === etapasTutorialAtual.length - 1"
              :size="18"
            />
            <IconSquareRoundedChevronRight v-else :size="18" />
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>