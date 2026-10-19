<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { estabelecimentos, iniciarNovoFormulario } from './store/estacionamentoStore'

const menuAberto = ref(false)
const router = useRouter()

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
    <button class="btn-hamburguer" @click="menuAberto = !menuAberto">☰</button>

    <Transition name="fade-backdrop">
      <div v-if="menuAberto" class="menu-backdrop" @click="menuAberto = false"></div>
    </Transition>

    <Transition name="slide-menu">
      <aside v-if="menuAberto" class="menu-lateral">
        <div class="menu-header">
          <h2>Vaga Certa</h2>
          <button class="btn-fechar" @click="menuAberto = false">✖</button>
        </div>
        <nav class="menu-links">
          <span class="menu-secao">📱 NÍVEL 1 (MOTORISTA)</span>
          <a href="#" @click.prevent="irPara({ name: 'motorista-home' })">📷 Leitor de QR Code</a>
          <a
            v-for="est in estabelecimentos.filter(e => !e.inativo)"
            :key="est.id"
            href="#"
            @click.prevent="irPara({ name: 'motorista-mapa', params: { id: est.id } })"
          >
            🅿️ {{ est.nome }}
          </a>

          <span class="menu-secao">🛠️ NÍVEL 3 (ADMIN DEV)</span>
          <a href="#" @click.prevent="irPara({ name: 'admin-lista' })">
            📋 Gerenciar Estacionamentos
          </a>
          <a href="#" @click.prevent="irParaNovoEstacionamento">
            ➕ Novo Estacionamento (Editor 2D)
          </a>
        </nav>
      </aside>
    </Transition>

    <!-- Renderiza a página correspondente à rota atual -->
    <router-view />
  </div>
</template>