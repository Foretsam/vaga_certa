<script setup>
import { onMounted } from 'vue'
import { carregarDadosDoBanco } from '@/stores/estacionamentoStore'
import AppSidebarMenu from '@/components/layout/AppSidebarMenu.vue'

onMounted(() => {
  carregarDadosDoBanco()
})
</script>

<template>
  <div class="app-container">
    <AppSidebarMenu />

    <router-view v-slot="{ Component }">
      <Transition name="fade-view" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </div>
</template>
