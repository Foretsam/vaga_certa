<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usuarioLogado } from '@/stores/estacionamentoStore'
import {
  IconBan,
  IconLogin,
  IconSquareRoundedArrowLeft
} from '@/constants/icons'

const router = useRouter()

const mensagemErro = computed(() => {
  if (!usuarioLogado.value) {
    return 'Você precisa estar autenticado com uma conta autorizada para acessar esta página.'
  }
  return 'Sua conta atual não possui permissão de nível suficiente para acessar esta área restrita.'
})

function voltarParaInicioSeguro() {
  if (!usuarioLogado.value) {
    router.push({ name: 'motorista-home' })
    return
  }
  const nivel = usuarioLogado.value.nivel_acesso
  if (nivel === 'admin_dev') {
    router.push({ name: 'admin-lista' })
  } else if (nivel === 'admin_estabelecimento') {
    router.push({ name: 'gerente' })
  } else {
    router.push({ name: 'motorista-home' })
  }
}
</script>

<template>
  <main class="tela-inicial">
    <div class="auth-card card-erro-acesso">
      <div class="icone-erro-acesso">
        <IconBan :size="44" />
      </div>
      <h1>Acesso Restrito</h1>
      <p class="subtitulo texto-erro-acesso">
        {{ mensagemErro }}
      </p>

      <div class="acoes-erro-acesso">
        <button
          v-if="!usuarioLogado"
          class="btn-primario btn-auth-submit item-icone-texto"
          @click="router.push({ name: 'login' })"
        >
          <IconLogin :size="20" />
          <span>Fazer Login</span>
        </button>

        <button
          class="btn-secundario btn-auth-submit item-icone-texto"
          @click="voltarParaInicioSeguro"
        >
          <IconSquareRoundedArrowLeft :size="20" />
          <span>Voltar para Página Inicial</span>
        </button>
      </div>
    </div>
  </main>
</template>
