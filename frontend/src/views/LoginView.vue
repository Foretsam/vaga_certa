<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usuarioLogado } from '../store/estacionamentoStore'
import {
  IconLogin,
  IconMail,
  IconLock,
  IconEye,
  IconEyeOff,
  IconAlertSquareRounded
} from '../icons'

const API_URL = 'http://127.0.0.1:8000'
const router = useRouter()

const email = ref('')
const senha = ref('')
const mostrarSenha = ref(false)
const carregando = ref(false)
const erroMensagem = ref('')

async function realizarLogin() {
  if (carregando.value) return
  erroMensagem.value = ''

  if (!email.value.trim() || !senha.value) {
    erroMensagem.value = 'Preencha seu e-mail e sua senha para entrar.'
    return
  }

  carregando.value = true
  try {
    const resposta = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value.trim(),
        senha: senha.value
      })
    })

    const dados = await resposta.json().catch(() => ({}))
    if (!resposta.ok) {
      throw new Error(dados.detail || 'Não foi possível realizar o login.')
    }

    if (usuarioLogado) {
      usuarioLogado.value = dados.usuario
    }
    localStorage.setItem('vagacerta_usuario', JSON.stringify(dados.usuario))
    const nivel = dados.usuario?.nivel_acesso
    if (nivel === 'admin_dev') {
      router.push({ name: 'admin-lista' })
    } else if (nivel === 'admin_estabelecimento') {
      router.push({ name: 'gerente' })
    } else {
      router.push({ name: 'motorista-home' })
    }
  } catch (err) {
    erroMensagem.value = err.message || 'Erro inesperado ao realizar o login.'
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
          <IconLogin :size="32" />
        </div>
        <h1>Bem-vindo de volta</h1>
        <p class="subtitulo">Acesse sua conta para gerenciar estacionamentos</p>
      </div>

      <Transition name="fade-pop">
        <div v-if="erroMensagem" class="alerta-auth erro item-icone-texto">
          <IconAlertSquareRounded :size="18" />
          <span>{{ erroMensagem }}</span>
        </div>
      </Transition>

      <form class="auth-form" @submit.prevent="realizarLogin">
        <div class="campo-grupo">
          <label for="login-email">E-mail</label>
          <div class="input-icone-container">
            <IconMail :size="18" class="icone-interno-esquerda" />
            <input
              id="login-email"
              v-model="email"
              type="email"
              placeholder="seu@email.com"
              autocomplete="email"
              :disabled="carregando"
              required
            />
          </div>
        </div>

        <div class="campo-grupo">
          <label for="login-senha">Senha</label>
          <div class="input-icone-container">
            <IconLock :size="18" class="icone-interno-esquerda" />
            <input
              id="login-senha"
              v-model="senha"
              :type="mostrarSenha ? 'text' : 'password'"
              placeholder="Digite sua senha"
              autocomplete="current-password"
              :disabled="carregando"
              required
            />
            <button
              type="button"
              class="btn-toggle-senha"
              :title="mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'"
              @click="mostrarSenha = !mostrarSenha"
            >
              <IconEyeOff v-if="mostrarSenha" :size="19" />
              <IconEye v-else :size="19" />
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
        <span>Ainda não tem uma conta?</span>
        <router-link :to="{ name: 'cadastro' }" class="link-auth">
          Cadastre-se
        </router-link>
      </div>
    </div>
  </main>
</template>