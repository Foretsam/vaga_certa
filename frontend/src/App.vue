<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  carregarDadosDoBanco,
  iniciarNovoFormulario,
  usuarioLogado
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
  IconLogout
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

function irParaNovoEstacionamento() {
  iniciarNovoFormulario()
  menuAberto.value = false
  router.push({ name: 'admin-info-gerais' })
}

function sairDaConta() {
  usuarioLogado.value = null
  localStorage.removeItem('vagacerta_usuario')
  menuAberto.value = false
  router.push({ name: 'motorista-home' })
}
</script>

<template>
  <div class="app-container">
    <button class="btn-hamburguer" @click="menuAberto = !menuAberto">
      <IconMenu2 :size="22" />
    </button>

    <Transition name="fade-backdrop">
      <div v-if="menuAberto" class="menu-backdrop" @click="menuAberto = false"></div>
    </Transition>

    <Transition name="slide-menu">
      <aside v-if="menuAberto" class="menu-lateral">
        <div class="menu-header">
          <h2>Vaga Certa</h2>
          <button class="btn-fechar" @click="menuAberto = false">
            <IconSquareRoundedX :size="22" />
          </button>
        </div>

        <nav class="menu-links">
          <!-- Opções exclusivas do Admin Dev acima de Escanear Estacionamento -->
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