<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { cadastrarUsuarioApi } from '@/services/authService'
import { salvarSessaoUsuario } from '@/stores/authStore'
import { carregarDadosDoBanco } from '@/stores/estacionamentoStore'
import {
  IconUserPlus,
  IconUser,
  IconMail,
  IconLock,
  IconEye,
  IconEyeOff,
  IconAlertSquareRounded,
  IconSquareRoundedCheck
} from '@/constants/icons'

const router = useRouter()

const nome = ref('')
const email = ref('')
const senha = ref('')
const confirmarSenha = ref('')

const mostrarSenha = ref(false)
const mostrarConfirmar = ref(false)
const carregando = ref(false)
const erroServidor = ref('')
const cadastroConcluido = ref(false)

// Valida em tempo real os critérios de segurança da senha
const avisoValidacaoSenha = computed(() => {
  if (!senha.value) return ''
  if (senha.value.length < 8) return 'A senha deve ter no mínimo 8 caracteres.'
  if (/\s/.test(senha.value)) return 'A senha não pode conter espaços em branco.'
  if (!/[A-Z]/.test(senha.value)) return 'Inclua ao menos uma letra maiúscula.'
  if (!/[a-z]/.test(senha.value)) return 'Inclua ao menos uma letra minúscula.'
  if (!/\d/.test(senha.value)) return 'Inclua ao menos um número.'
  if (!/[^A-Za-z0-9]/.test(senha.value)) return 'Inclua ao menos um símbolo (ex: @, #, !).'

  const emailLimpo = email.value.trim().toLowerCase()
  const prefixoEmail = emailLimpo.split('@')[0]
  if (prefixoEmail && prefixoEmail.length >= 3 && senha.value.toLowerCase().includes(prefixoEmail)) {
    return 'A senha não pode conter partes do seu e-mail.'
  }
  return ''
})

const avisoConfirmacaoSenha = computed(() => {
  if (!confirmarSenha.value) return ''
  if (confirmarSenha.value !== senha.value) return 'As senhas digitadas não coincidem.'
  return ''
})

const formularioValido = computed(() => {
  return (
    nome.value.trim().length >= 3 &&
    /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value.trim()) &&
    senha.value.length >= 8 &&
    !avisoValidacaoSenha.value &&
    confirmarSenha.value === senha.value
  )
})

async function realizarCadastro() {
  if (!formularioValido.value) return
  erroServidor.value = ''
  carregando.value = true

  try {
    const resposta = await cadastrarUsuarioApi(
      nome.value.trim(),
      email.value.trim(),
      senha.value
    )
    salvarSessaoUsuario(resposta.usuario)
    await carregarDadosDoBanco()
    cadastroConcluido.value = true

    setTimeout(() => {
      router.push({ name: 'motorista-home' })
    }, 1100)
  } catch (err) {
    erroServidor.value = err.message || 'Não foi possível concluir o cadastro.'
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <main class="tela-inicial">
    <div class="auth-card auth-card-cadastro">
      <div class="auth-cabecalho">
        <div class="auth-icone-topo">
          <IconUserPlus :size="30" />
        </div>
        <h1>Criar Conta</h1>
        <p class="subtitulo">Cadastre-se rapidamente para utilizar o Vaga Certa</p>
      </div>

      <Transition name="fade-pop">
        <div v-if="erroServidor" class="alerta-auth erro item-icone-texto">
          <IconAlertSquareRounded :size="18" />
          <span>{{ erroServidor }}</span>
        </div>
      </Transition>

      <div v-if="cadastroConcluido" class="sucesso-cadastro-box">
        <div class="auth-icone-topo" style="color: #16a34a; background: rgba(22, 163, 74, 0.14)">
          <IconSquareRoundedCheck :size="34" />
        </div>
        <h3>Conta criada com sucesso!</h3>
        <p class="subtitulo">Redirecionando para a página inicial...</p>
      </div>

      <form v-else @submit.prevent="realizarCadastro">
        <div class="campo-grupo">
          <label>Nome Completo</label>
          <div class="input-icone-container">
            <IconUser :size="18" class="icone-interno-esquerda" />
            <input
              v-model="nome"
              type="text"
              maxlength="100"
              placeholder="Seu nome completo"
              required
            />
          </div>
        </div>

        <div class="campo-grupo">
          <label>E-mail</label>
          <div class="input-icone-container">
            <IconMail :size="18" class="icone-interno-esquerda" />
            <input
              v-model="email"
              type="email"
              maxlength="150"
              placeholder="seu@email.com"
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
              placeholder="Mínimo 8 caracteres, maiúscula, número e símbolo"
              required
            />
            <button
              type="button"
              class="btn-toggle-senha"
              @click="mostrarSenha = !mostrarSenha"
            >
              <IconEyeOff v-if="mostrarSenha" :size="18" />
              <IconEye v-else :size="18" />
            </button>
          </div>
          <!-- Slot de altura fixa para evitar deslocamento do card -->
          <div class="slot-aviso-senha slot-duas-linhas">
            <span v-if="avisoValidacaoSenha" class="aviso-inline-senha">
              {{ avisoValidacaoSenha }}
            </span>
          </div>
        </div>

        <div class="campo-grupo">
          <label>Confirmar Senha</label>
          <div class="input-icone-container">
            <IconLock :size="18" class="icone-interno-esquerda" />
            <input
              v-model="confirmarSenha"
              :type="mostrarConfirmar ? 'text' : 'password'"
              placeholder="Repita a senha criada"
              required
            />
            <button
              type="button"
              class="btn-toggle-senha"
              @click="mostrarConfirmar = !mostrarConfirmar"
            >
              <IconEyeOff v-if="mostrarConfirmar" :size="18" />
              <IconEye v-else :size="18" />
            </button>
          </div>
          <div class="slot-aviso-senha slot-uma-linha">
            <span v-if="avisoConfirmacaoSenha" class="aviso-inline-senha">
              {{ avisoConfirmacaoSenha }}
            </span>
          </div>
        </div>

        <button
          type="submit"
          class="btn-primario btn-auth-submit item-icone-texto"
          :disabled="!formularioValido || carregando"
        >
          <span v-if="carregando" class="spinner-btn"></span>
          <IconUserPlus v-else :size="20" />
          <span>{{ carregando ? 'Cadastrando...' : 'Finalizar Cadastro' }}</span>
        </button>
      </form>

      <div class="auth-rodape">
        <span>Já possui uma conta?</span>
        <router-link :to="{ name: 'login' }" class="link-auth">
          Fazer Login
        </router-link>
      </div>
    </div>
  </main>
</template>