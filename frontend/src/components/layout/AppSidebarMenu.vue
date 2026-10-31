<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  iniciarNovoFormulario,
  usuarioLogado,
  idsSelecionadosGerente,
  simulacao1Ativa
} from '@/stores/estacionamentoStore'
import { encerrarSessaoUsuario } from '@/stores/authStore'
import { TUTORIAIS_POR_ROTA } from '@/constants/tutoriaisConfig'
import {
  IconMenu2,
  IconSquareRoundedX,
  IconSquareRoundedPlus,
  IconSettings,
  IconQrcode,
  IconLogin,
  IconUserPlus,
  IconInfoCircle,
  IconLogout,
  IconLayoutBoard,
  IconParking,
  IconChartBar,
  IconSun,
  IconMoon,
  IconChevronUp
} from '@/constants/icons'

const menuAberto = ref(false)
const router = useRouter()
const route = useRoute()

const temaEscuro = ref(true)
const animandoTrocaTema = ref(false)
const mostrarVoltarTopo = ref(false)

onMounted(() => {
  const salvo = localStorage.getItem('vagacerta_tema')
  if (salvo === 'light' || salvo === 'dark') {
    temaEscuro.value = salvo === 'dark'
  } else {
    temaEscuro.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  aplicarTemaDom()
  window.addEventListener('scroll', verificarScrollPagina, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', verificarScrollPagina)
})

function verificarScrollPagina() {
  mostrarVoltarTopo.value = window.scrollY > 180
}

function voltarAoTopoSuave() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function aplicarTemaDom() {
  document.documentElement.setAttribute('data-theme', temaEscuro.value ? 'dark' : 'light')
}

function alternarTema(event) {
  const x = event?.clientX ?? 140
  const y = event?.clientY ?? 32
  const raioMaximo = Math.hypot(
    Math.max(x, window.innerWidth - x),
    Math.max(y, window.innerHeight - y)
  )

  animandoTrocaTema.value = true
  setTimeout(() => {
    animandoTrocaTema.value = false
  }, 520)

  const executarTroca = () => {
    temaEscuro.value = !temaEscuro.value
    localStorage.setItem('vagacerta_tema', temaEscuro.value ? 'dark' : 'light')
    aplicarTemaDom()
  }

  if (document.startViewTransition) {
    const transicao = document.startViewTransition(() => {
      executarTroca()
    })
    transicao.ready.then(() => {
      document.documentElement.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${raioMaximo}px at ${x}px ${y}px)`
          ]
        },
        {
          duration: 480,
          easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
          pseudoElement: '::view-transition-new(root)'
        }
      )
    }).catch(() => {})
  } else {
    document.documentElement.classList.add('transicao-tema-global')
    executarTroca()
    setTimeout(() => {
      document.documentElement.classList.remove('transicao-tema-global')
    }, 450)
  }
}

function irPara(rota) {
  menuAberto.value = false
  router.push(rota)
}

function irParaHomePorNivel() {
  menuAberto.value = false
  const nivel = usuarioLogado.value?.nivel_acesso
  if (nivel === 'admin_dev') {
    router.push({ name: 'admin-lista' })
  } else if (nivel === 'admin_estabelecimento') {
    router.push({ name: 'gerente' })
  } else {
    router.push({ name: 'motorista-home' })
  }
}

function irParaNovoEstacionamento() {
  iniciarNovoFormulario()
  menuAberto.value = false
  router.push({ name: 'admin-info-gerais' })
}

function sairDaConta() {
  encerrarSessaoUsuario()
  idsSelecionadosGerente.value = []
  simulacao1Ativa.value = false
  menuAberto.value = false
  router.push({ name: 'motorista-home' })
}
</script>

<template>
  <button class="btn-hamburguer" title="Abrir Menu" @click="menuAberto = !menuAberto">
    <IconMenu2 :size="22" />
  </button>

  <button class="btn-logo-vc" title="Ir para a página inicial" @click="irParaHomePorNivel">
    <span class="vc-letra-v">V</span><span class="vc-letra-c">C</span>
  </button>

  <!-- Toggle Light / Dark Mode com animação elaborada -->
  <button
    type="button"
    class="btn-toggle-tema"
    :class="{
      'com-botao-tutorial': route.name && TUTORIAIS_POR_ROTA[route.name],
      'tema-pulsando': animandoTrocaTema
    }"
    :title="temaEscuro ? 'Mudar para Modo Claro (Light Mode)' : 'Mudar para Modo Escuro (Dark Mode)'"
    @click="alternarTema($event)"
  >
    <Transition name="icone-tema-spin" mode="out-in">
      <IconSun v-if="temaEscuro" key="sol" :size="19" class="icone-sol-animado" />
      <IconMoon v-else key="lua" :size="19" class="icone-lua-animada" />
    </Transition>
  </button>

  <!-- Botão sem bordas no formato de "V" apontado para cima ao usar scroll -->
  <Transition name="fade-pop">
    <button
      v-if="mostrarVoltarTopo"
      type="button"
      class="btn-voltar-topo-scroll"
      title="Voltar ao início da página"
      @click="voltarAoTopoSuave"
    >
      <IconChevronUp :size="28" stroke-width="2.5" />
    </button>
  </Transition>

  <Transition name="fade-backdrop">
    <div v-if="menuAberto" class="menu-backdrop" @click="menuAberto = false"></div>
  </Transition>

  <Transition name="slide-menu">
    <aside v-if="menuAberto" class="menu-lateral">
      <div class="menu-header">
        <div class="item-icone-texto">
          <span class="badge-logo-menu">VC</span>
          <h2>Vaga Certa</h2>
        </div>
        <button class="btn-fechar" @click="menuAberto = false">
          <IconSquareRoundedX :size="22" />
        </button>
      </div>

      <nav class="menu-links">
        <template v-if="usuarioLogado?.nivel_acesso === 'admin_dev'">
          <a href="#" class="item-icone-texto" @click.prevent="irParaNovoEstacionamento">
            <IconSquareRoundedPlus :size="19" />
            <span>Novo Estacionamento</span>
          </a>
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'admin-lista' })">
            <IconSettings :size="19" />
            <span>Gerenciar Estacionamentos</span>
          </a>
          <div class="menu-divisor"></div>
        </template>

        <template v-if="usuarioLogado?.nivel_acesso === 'admin_estabelecimento'">
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'gerente' })">
            <IconLayoutBoard :size="19" />
            <span>Dashboard Principal</span>
          </a>
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'gerente-estacionamentos' })">
            <IconParking :size="19" />
            <span>Visão dos Estacionamentos</span>
          </a>
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'gerente-relatorios' })">
            <IconChartBar :size="19" />
            <span>Relatórios e Exportação</span>
          </a>
          <div class="menu-divisor"></div>
        </template>

        <a
          v-if="usuarioLogado?.nivel_acesso !== 'admin_dev' && usuarioLogado?.nivel_acesso !== 'admin_estabelecimento'"
          href="#"
          class="item-icone-texto"
          @click.prevent="irPara({ name: 'motorista-home' })"
        >
          <IconQrcode :size="19" />
          <span>Escanear Estacionamento</span>
        </a>

        <template v-if="!usuarioLogado">
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'login' })">
            <IconLogin :size="19" />
            <span>Login</span>
          </a>
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'cadastro' })">
            <IconUserPlus :size="19" />
            <span>Cadastro</span>
          </a>
        </template>

        <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'sobre' })">
          <IconInfoCircle :size="19" />
          <span>Sobre</span>
        </a>

        <a
          v-if="usuarioLogado"
          href="#"
          class="item-icone-texto link-sair-menu"
          @click.prevent="sairDaConta"
        >
          <IconLogout :size="19" />
          <span>Sair</span>
        </a>
      </nav>
    </aside>
  </Transition>
</template>