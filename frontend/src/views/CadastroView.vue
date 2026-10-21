<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { carregarDadosDoBanco } from '../store/estacionamentoStore'
import {
  IconUserPlus,
  IconUser,
  IconMail,
  IconLock,
  IconEye,
  IconEyeOff,
  IconSquareRoundedCheck,
  IconAlertSquareRounded
} from '../icons'

const API_URL = 'http://127.0.0.1:8000'
const router = useRouter()

const nome = ref('')
const email = ref('')
const senha = ref('')
const confirmarSenha = ref('')

const mostrarSenha = ref(false)
const mostrarConfirmarSenha = ref(false)
const carregando = ref(false)
const erroMensagem = ref('')
const cadastroConcluido = ref(false)

// Aviso dinâmico em tempo real estilo Gmail (mostra apenas o que falta na senha)
const avisoFaltandoSenha = computed(() => {
  const s = senha.value
  if (!s) return ''

  if (/\s/.test(s)) {
    return 'A senha não pode conter espaços em branco.'
  }

  const faltando = []
  if (s.length < 8) faltando.push('mínimo de 8 caracteres')
  if (!/[A-Z]/.test(s)) faltando.push('1 letra maiúscula')
  if (!/[a-z]/.test(s)) faltando.push('1 letra minúscula')
  if (!/\d/.test(s)) faltando.push('1 número')
  if (!/[^A-Za-z0-9\s]/.test(s)) faltando.push('1 símbolo (!@#$...)')

  if (faltando.length === 0) return ''
  return `Falta na senha: ${faltando.join(', ')}.`
})

const avisoConfirmacaoSenha = computed(() => {
  if (!confirmarSenha.value) return ''
  if (senha.value !== confirmarSenha.value) {
    return 'As senhas não coincidem.'
  }
  return ''
})

// Permite clicar no botão assim que os campos básicos e a força da senha estiverem preenchidos
const formularioValido = computed(() => {
  return (
    nome.value.trim().length >= 3 &&
    /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value.trim()) &&
    senha.value.length >= 8 &&
    avisoFaltandoSenha.value === '' &&
    senha.value === confirmarSenha.value
  )
})

function senhaParecidaComEmail(senhaStr, emailStr) {
  const e = emailStr.trim().toLowerCase()
  const prefixoEmail = e.includes('@') ? e.split('@')[0] : e
  const sLower = senhaStr.toLowerCase()
  return sLower === e || (prefixoEmail.length >= 3 && sLower.includes(prefixoEmail))
}

async function realizarCadastro() {
  if (carregando.value || !formularioValido.value) return
  erroMensagem.value = ''

  // Regra estilo Gmail: só verifica semelhança com o e-mail após clicar em "Criar Conta"
  if (senhaParecidaComEmail(senha.value, email.value)) {
    erroMensagem.value = 'Por segurança, a senha não pode conter nem ser parecida com o seu e-mail.'
    return
  }

  carregando.value = true
  try {
    const resposta = await fetch(`${API_URL}/auth/cadastro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nome: nome.value.trim(),
        email: email.value.trim(),
        senha: senha.value
      })
    })

    const dados = await resposta.json().catch(() => ({}))
    if (!resposta.ok) {
      throw new Error(dados.detail || 'Não foi possível concluir o cadastro.')
    }

    await carregarDadosDoBanco()
    cadastroConcluido.value = true
  } catch (err) {
    erroMensagem.value = err.message
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <main class="tela-inicial">
    <div class="auth-card auth-card-cadastro">
      <!-- Oculta o cabeçalho após concluir o cadastro -->
      <div v-if="!cadastroConcluido" class="auth-cabecalho">
        <div class="auth-icone-topo">
          <IconUserPlus :size="32" />
        </div>
        <h1>Criar nova conta</h1>
        <p class="subtitulo">Preencha seus dados para acessar o sistema Vaga Certa</p>
      </div>

      <Transition name="fade-pop">
        <div v-if="erroMensagem" class="alerta-auth erro item-icone-texto">
          <IconAlertSquareRounded :size="18" />
          <span>{{ erroMensagem }}</span>
        </div>
      </Transition>

      <div v-if="cadastroConcluido" class="sucesso-cadastro-box">
        <div class="icone-sucesso-modal" style="color: #16a34a">
          <IconSquareRoundedCheck :size="48" />
        </div>
        <h3>Conta criada com sucesso!</h3>
        <p class="subtitulo">Seu cadastro foi registrado com segurança no banco de dados.</p>
        <button
          type="button"
          class="btn-primario btn-auth-submit item-icone-texto"
          style="margin-top: 18px"
          @click="router.push({ name: 'login' })"
        >
          <IconSquareRoundedCheck :size="20" />
          <span>Ir para o Login</span>
        </button>
      </div>

      <form v-else class="auth-form" @submit.prevent="realizarCadastro">
        <div class="campo-grupo">
          <label for="cad-nome">Nome completo</label>
          <div class="input-icone-container">
            <IconUser :size="18" class="icone-interno-esquerda" />
            <input
              id="cad-nome"
              v-model="nome"
              type="text"
              maxlength="100"
              placeholder="Ex: Lucas Oliveira"
              autocomplete="name"
              :disabled="carregando"
              required
            />
          </div>
        </div>

        <div class="campo-grupo">
          <label for="cad-email">E-mail</label>
          <div class="input-icone-container">
            <IconMail :size="18" class="icone-interno-esquerda" />
            <input
              id="cad-email"
              v-model="email"
              type="email"
              maxlength="150"
              placeholder="seu@email.com"
              autocomplete="email"
              :disabled="carregando"
              required
            />
          </div>
        </div>

        <div class="campo-grupo">
          <label for="cad-senha">Senha</label>
          <div class="input-icone-container">
            <IconLock :size="18" class="icone-interno-esquerda" />
            <input
              id="cad-senha"
              v-model="senha"
              :type="mostrarSenha ? 'text' : 'password'"
              placeholder="Crie uma senha forte"
              autocomplete="new-password"
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
          <Transition name="fade-pop">
            <p v-if="avisoFaltandoSenha" class="aviso-inline-senha">
              {{ avisoFaltandoSenha }}
            </p>
          </Transition>
        </div>

        <div class="campo-grupo">
          <label for="cad-confirma-senha">Confirmar senha</label>
          <div class="input-icone-container">
            <IconLock :size="18" class="icone-interno-esquerda" />
            <input
              id="cad-confirma-senha"
              v-model="confirmarSenha"
              :type="mostrarConfirmarSenha ? 'text' : 'password'"
              placeholder="Repita a senha criada"
              autocomplete="new-password"
              :disabled="carregando"
              required
            />
            <button
              type="button"
              class="btn-toggle-senha"
              :title="mostrarConfirmarSenha ? 'Ocultar senha' : 'Mostrar senha'"
              @click="mostrarConfirmarSenha = !mostrarConfirmarSenha"
            >
              <IconEyeOff v-if="mostrarConfirmarSenha" :size="19" />
              <IconEye v-else :size="19" />
            </button>
          </div>
          <Transition name="fade-pop">
            <p v-if="avisoConfirmacaoSenha" class="aviso-inline-senha">
              {{ avisoConfirmacaoSenha }}
            </p>
          </Transition>
        </div>

        <button
          type="submit"
          class="btn-primario btn-auth-submit item-icone-texto"
          :disabled="carregando || !formularioValido"
        >
          <span v-if="carregando" class="spinner-btn"></span>
          <IconUserPlus v-else :size="20" />
          <span>{{ carregando ? 'Cadastrando...' : 'Criar Conta' }}</span>
        </button>
      </form>

      <!-- Oculta o rodapé após concluir o cadastro -->
      <div v-if="!cadastroConcluido" class="auth-rodape">
        <span>Já possui uma conta?</span>
        <router-link :to="{ name: 'login' }" class="link-auth">
          Fazer login
        </router-link>
      </div>
    </div>
  </main>
</template>