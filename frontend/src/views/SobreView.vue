<script setup>
import { IconInfoCircle } from '../icons'
</script>

<template>
  <main class="tela-inicial">
    <div class="hero-card card-em-breve">
      <div class="icone-destaque" style="color: var(--destaque-azul)">
        <IconInfoCircle :size="52" />
      </div>
      <h1 class="titulo-principal">Sobre</h1>
      <span class="badge-em-breve">Em breve</span>
    </div>
  </main>
</template>