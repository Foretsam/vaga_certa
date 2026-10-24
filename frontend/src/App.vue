<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  carregarDadosDoBanco,
  iniciarNovoFormulario,
  usuarioLogado,
  idsSelecionadosGerente,
  simulacao1Ativa
} from './store/estacionamentoStore'
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
  IconChartBar
} from './icons'

const menuAberto = ref(false)
const router = useRouter()

onMounted(() => {
  carregarDadosDoBanco()
})

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
  usuarioLogado.value = null
  idsSelecionadosGerente.value = []
  simulacao1Ativa.value = false
  localStorage.removeItem('vagacerta_usuario')
  menuAberto.value = false
  router.push({ name: 'motorista-home' })
}
</script>

<template>
  <div class="app-container">
    <button class="btn-hamburguer" title="Abrir Menu" @click="menuAberto = !menuAberto">
      <IconMenu2 :size="22" />
    </button>

    <!-- Logo VC estilizado com redirecionamento inteligente para a Home de cada nível -->
    <button class="btn-logo-vc" title="Ir para a página inicial" @click="irParaHomePorNivel">
      <span class="vc-letra-v">V</span><span class="vc-letra-c">C</span>
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
          <!-- Atalhos exclusivos do Admin Dev -->
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

          <!-- Atalhos exclusivos do Gerente (Admin Estabelecimento) -->
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

          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'motorista-home' })">
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

    <router-view v-slot="{ Component }">
      <Transition name="fade-view" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </div>
</template>