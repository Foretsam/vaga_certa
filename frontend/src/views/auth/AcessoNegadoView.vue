<script setup>
import { useRouter } from 'vue-router'
import { usuarioLogado } from '@/stores/authStore'
import {
  IconBan,
  IconSquareRoundedArrowLeft,
  IconLogin
} from '@/constants/icons'

const router = useRouter()

function voltarInicioPermitido() {
  const nivel = usuarioLogado.value?.nivel_acesso
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
        <IconBan :size="36" />
      </div>
      <h1>Acesso Restrito</h1>
      <p class="subtitulo texto-erro-acesso">
        Sua conta não possui permissão para acessar esta área do sistema.
      </p>

      <div class="acoes-erro-acesso">
        <button
          class="btn-primario btn-auth-submit item-icone-texto"
          @click="voltarInicioPermitido"
        >
          <IconSquareRoundedArrowLeft :size="20" />
          <span>Voltar para minha página inicial</span>
        </button>

        <button
          v-if="!usuarioLogado"
          class="btn-secundario btn-auth-submit item-icone-texto"
          @click="router.push({ name: 'login' })"
        >
          <IconLogin :size="20" />
          <span>Entrar com outra conta</span>
        </button>
      </div>
    </div>
  </main>
</template>