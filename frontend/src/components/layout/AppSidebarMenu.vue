<script setup>
import { ref, onMounted } from 'vue'
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
  IconMoon
} from '@/constants/icons'

const menuAberto = ref(false)
const router = useRouter()
const route = useRoute()

const temaEscuro = ref(true)

onMounted(() => {
  const salvo = localStorage.getItem('vagacerta_tema')
  if (salvo === 'light' || salvo === 'dark') {
    temaEscuro.value = salvo === 'dark'
  } else {
    temaEscuro.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  aplicarTemaDom()
})

function aplicarTemaDom() {
  document.documentElement.setAttribute('data-theme', temaEscuro.value ? 'dark' : 'light')
}

function alternarTema() {
  temaEscuro.value = !temaEscuro.value
  localStorage.setItem('vagacerta_tema', temaEscuro.value ? 'dark' : 'light')
  aplicarTemaDom()
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

  <!-- Toggle Light / Dark Mode sutil (apenas ícone, com dica no hover) -->
  <button
    type="button"
    class="btn-toggle-tema"
    :class="{ 'com-botao-tutorial': route.name && TUTORIAIS_POR_ROTA[route.name] }"
    :title="temaEscuro ? 'Mudar para Modo Claro (Light Mode)' : 'Mudar para Modo Escuro (Dark Mode)'"
    @click="alternarTema"
  >
    <IconSun v-if="temaEscuro" :size="18" />
    <IconMoon v-else :size="18" />
  </button>

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