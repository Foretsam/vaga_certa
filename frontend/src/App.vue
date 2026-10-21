<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  estabelecimentos,
  iniciarNovoFormulario,
  carregarDadosDoBanco
} from './store/estacionamentoStore'
import {
  IconMenu2,
  IconSquareRoundedX,
  IconSearch,
  IconParking,
  IconSquareRoundedPlus,
  IconSettings
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
          <span class="menu-secao">NÍVEL 1 (MOTORISTA)</span>
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'motorista-home' })">
            <IconSearch :size="18" />
            <span>Leitor de QR Code</span>
          </a>
          <a
            v-for="est in estabelecimentos.filter(e => !e.inativo)"
            :key="est.id"
            href="#"
            class="item-icone-texto"
            @click.prevent="irPara({ name: 'motorista-mapa', params: { id: est.id } })"
          >
            <IconParking :size="18" />
            <span>{{ est.nome }}</span>
          </a>

          <span class="menu-secao">NÍVEL 3 (ADMIN DEV)</span>
          <a href="#" class="item-icone-texto" @click.prevent="irPara({ name: 'admin-lista' })">
            <IconSettings :size="18" />
            <span>Gerenciar Estacionamentos</span>
          </a>
          <a href="#" class="item-icone-texto" @click.prevent="irParaNovoEstacionamento">
            <IconSquareRoundedPlus :size="18" />
            <span>Novo Estacionamento (Editor 2D)</span>
          </a>
        </nav>
      </aside>
    </Transition>

    <!-- Animação leve, sutil e rápida ao alternar entre as views -->
    <router-view v-slot="{ Component }">
      <Transition name="fade-view" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </div>
</template>