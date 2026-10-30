import { ref, computed } from 'vue'
import { TUTORIAIS_POR_ROTA } from '@/constants/tutoriaisConfig'
import { usuarioLogado, salvarSessaoUsuario } from './authStore'
import { registrarTutorialVistoApi } from '@/services/authService'

export const rotaTutorialAtivo = ref(null)
export const indiceEtapaTutorial = ref(0)

export const etapasTutorialAtual = computed(() => {
  if (!rotaTutorialAtivo.value) return []
  return TUTORIAIS_POR_ROTA[rotaTutorialAtivo.value] || []
})

export const etapaTutorialAtual = computed(() => {
  return etapasTutorialAtual.value[indiceEtapaTutorial.value] || null
})

function chaveLocalStorageUsuario(idUsuario) {
  return `vagacerta_tutoriais_vistos_${idUsuario}`
}

export function obterTutoriaisVistosUsuario() {
  if (!usuarioLogado.value) return []
  const doUsuario = Array.isArray(usuarioLogado.value.tutoriais_vistos)
    ? usuarioLogado.value.tutoriais_vistos
    : []
  const doStorage = JSON.parse(
    localStorage.getItem(chaveLocalStorageUsuario(usuarioLogado.value.id_usuario)) || '[]'
  )
  return Array.from(new Set([...doUsuario, ...doStorage]))
}

export function verificarPrimeiroAcessoTutorial(nomeRota) {
  if (!nomeRota || !TUTORIAIS_POR_ROTA[nomeRota] || !usuarioLogado.value) return
  const vistos = obterTutoriaisVistosUsuario()
  if (!vistos.includes(nomeRota)) {
    iniciarTutorial(nomeRota)
  }
}

export function iniciarTutorial(nomeRota) {
  if (!TUTORIAIS_POR_ROTA[nomeRota]) return
  indiceEtapaTutorial.value = 0
  rotaTutorialAtivo.value = nomeRota
}

export function avancarEtapaTutorial() {
  if (indiceEtapaTutorial.value < etapasTutorialAtual.value.length - 1) {
    indiceEtapaTutorial.value++
  } else {
    concluirTutorialAtual()
  }
}

export function voltarEtapaTutorial() {
  if (indiceEtapaTutorial.value > 0) {
    indiceEtapaTutorial.value--
  }
}

export async function concluirTutorialAtual() {
  const rotaConcluida = rotaTutorialAtivo.value
  rotaTutorialAtivo.value = null
  indiceEtapaTutorial.value = 0

  if (!rotaConcluida || !usuarioLogado.value) return

  const idUsuario = usuarioLogado.value.id_usuario
  const atualizados = Array.from(new Set([...obterTutoriaisVistosUsuario(), rotaConcluida]))

  // Salva imediatamente na sessão local para não reabrir
  localStorage.setItem(chaveLocalStorageUsuario(idUsuario), JSON.stringify(atualizados))
  salvarSessaoUsuario({
    ...usuarioLogado.value,
    tutoriais_vistos: atualizados
  })

  // Persiste no banco de dados MySQL
  try {
    const resp = await registrarTutorialVistoApi(idUsuario, rotaConcluida)
    if (resp?.tutoriais_vistos) {
      salvarSessaoUsuario({
        ...usuarioLogado.value,
        tutoriais_vistos: resp.tutoriais_vistos
      })
    }
  } catch (err) {
    console.warn('Tutorial salvo localmente (sincronização com banco pendente):', err)
  }
}