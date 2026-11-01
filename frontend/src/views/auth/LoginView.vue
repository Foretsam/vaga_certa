<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginUsuarioApi } from '@/services/authService'
import { salvarSessaoUsuario } from '@/stores/authStore'
import { carregarDadosDoBanco } from '@/stores/estacionamentoStore'
import {
  IconLogin,
  IconMail,
  IconLock,
  IconEye,
  IconEyeOff,
  IconAlertSquareRounded
} from '@/constants/icons'

const router = useRouter()

const email = ref('')
const senha = ref('')
const mostrarSenha = ref(false)
const carregando = ref(false)
const erroLogin = ref('')

async function realizarLogin() {
  erroLogin.value = ''
  if (!email.value.trim() || !senha.value) {
    erroLogin.value = 'Preencha seu e-mail e sua senha.'
    return
  }

  carregando.value = true
  try {
    const resposta = await loginUsuarioApi(email.value.trim(), senha.value)
    salvarSessaoUsuario(resposta.usuario)
    await carregarDadosDoBanco()

    const nivel = resposta.usuario.nivel_acesso
    if (nivel === 'admin_dev') {
      router.push({ name: 'admin-lista' })
    } else if (nivel === 'admin_estabelecimento') {
      router.push({ name: 'gerente' })
    } else {
      router.push({ name: 'motorista-home' })
    }
  } catch (err) {
    erroLogin.value = err.message || 'Falha ao autenticar.'
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <main class="tela-inicial">
    <div class="auth-card">
      <div class="auth-cabecalho">
        <div class="auth-icone-topo">
          <IconLogin :size="30" />
        </div>
        <h1>Entrar no Vaga Certa</h1>
        <p class="subtitulo">Acesse sua conta para gerenciar ou localizar vagas</p>
      </div>

      <Transition name="fade-pop">
        <div v-if="erroLogin" class="alerta-auth erro item-icone-texto">
          <IconAlertSquareRounded :size="18" />
          <span>{{ erroLogin }}</span>
        </div>
      </Transition>

      <form @submit.prevent="realizarLogin">
        <div class="campo-grupo">
          <label>E-mail</label>
          <div class="input-icone-container">
            <IconMail :size="18" class="icone-interno-esquerda" />
            <input
              v-model="email"
              type="email"
              placeholder="seu@email.com"
              autocomplete="email"
              required
            />
          </div>
        </div>

        <div class="campo-grupo">
          <label>Senha</label>
          <div class="input-icone-container">
            <IconLock :size="18" class="icone-interno-esquerda" />
            <input
              v-model="senha"
              :type="mostrarSenha ? 'text' : 'password'"
              placeholder="Digite sua senha"
              autocomplete="current-password"
              required
            />
            <button
              type="button"
              class="btn-toggle-senha"
              :title="mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'"
              @click="mostrarSenha = !mostrarSenha"
            >
              <IconEyeOff v-if="mostrarSenha" :size="18" />
              <IconEye v-else :size="18" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          class="btn-primario btn-auth-submit item-icone-texto"
          :disabled="carregando"
        >
          <span v-if="carregando" class="spinner-btn"></span>
          <IconLogin v-else :size="20" />
          <span>{{ carregando ? 'Autenticando...' : 'Entrar' }}</span>
        </button>
      </form>

      <div class="auth-rodape">
        <span>Ainda não possui uma conta?</span>
        <router-link :to="{ name: 'cadastro' }" class="link-auth">
          Criar conta grátis
        </router-link>
      </div>
    </div>
  </main>
</template>