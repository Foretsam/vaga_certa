<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  usuariosCadastrados,
  formEstabelecimento,
  criarMatrizVazia
} from '@/stores/estacionamentoStore'
import {
  IconSquareRoundedArrowLeft,
  IconSquareRoundedArrowRight,
  IconSquareRoundedPlus,
  IconSquareRoundedMinus,
  IconLayoutGrid
} from '@/constants/icons'

const router = useRouter()

// Filtra para exibir apenas motoristas ('usuario') e gerentes ('admin_estabelecimento')
const usuariosResponsaveisDisponiveis = computed(() => {
  return usuariosCadastrados.value.filter(u => u.nivel_acesso !== 'admin_dev')
})

onMounted(() => {
  const disponiveis = usuariosResponsaveisDisponiveis.value
  if (
    disponiveis.length > 0 &&
    !disponiveis.some(u => u.id_usuario === formEstabelecimento.value.id_usuario)
  ) {
    formEstabelecimento.value.id_usuario = disponiveis[0].id_usuario
  }
})

function rotuloNivelUsuario(nivel) {
  return nivel === 'admin_estabelecimento' ? 'Gerente' : 'Motorista'
}

function adicionarAndarForm() {
  if (formEstabelecimento.value.andares.length >= 10) return
  const numero = formEstabelecimento.value.andares.length + 1
  formEstabelecimento.value.andares.push({
    id_andar: Date.now() + numero,
    nome_andar: `Andar ${numero}`,
    grid_x: 30,
    grid_y: 20
  })
}

function removerAndarForm(index) {
  if (index === 0) return
  formEstabelecimento.value.andares.splice(index, 1)
}

function avancarParaEditorP2() {
  if (!formEstabelecimento.value.nome.trim()) {
    alert('Digite o nome do estabelecimento antes de continuar.')
    return
  }

  if (!formEstabelecimento.value.cidade || !formEstabelecimento.value.cidade.trim()) {
    alert('Digite a cidade do estabelecimento antes de continuar.')
    return
  }

  const nomesAndares = formEstabelecimento.value.andares.map(a => a.nome_andar.trim().toLowerCase())
  if (nomesAndares.some(n => !n)) {
    alert('Preencha o nome de todos os andares.')
    return
  }

  const nomesUnicos = new Set(nomesAndares)
  if (nomesUnicos.size !== nomesAndares.length) {
    alert('Os nomes dos andares não podem se repetir no mesmo estacionamento!')
    return
  }

  formEstabelecimento.value.andares.forEach((andar) => {
    if (!andar.celulas) {
      andar.grid_x = andar.grid_x || 30
      andar.grid_y = andar.grid_y || 20
      andar.setores = andar.setores || []
      andar.equipamentos = andar.equipamentos || []
      andar.celulas = criarMatrizVazia(andar.grid_x, andar.grid_y)
    }
  })

  router.push({ name: 'admin-editor-2d' })
}
</script>

<template>
  <div class="admin-container">
    <header class="topbar-titulo-central com-botao-direita">
      <div class="bloco-titulo-centro">
        <h1>Informações Gerais</h1>
      </div>
      <button class="btn-secundario btn-voltar-topo item-icone-texto" @click="router.push({ name: 'admin-lista' })">
        <IconSquareRoundedArrowLeft :size="18" />
        <span>Voltar</span>
      </button>
    </header>

    <div class="form-card">
      <div class="grade-campos-dupla">
        <div class="campo-grupo">
          <label>Nome do Estabelecimento (máx. 50 caracteres)</label>
          <input
            v-model="formEstabelecimento.nome"
            type="text"
            maxlength="50"
            placeholder="Ex: Shopping Sorocaba Center"
          />
        </div>

        <div class="campo-grupo">
          <label>Cidade (máx. 60 caracteres)</label>
          <input
            v-model="formEstabelecimento.cidade"
            type="text"
            maxlength="60"
            placeholder="Ex: Sorocaba"
          />
        </div>
      </div>

      <div class="campo-grupo">
        <label>Vincular Usuário Responsável (Motorista vinculado torna-se Gerente automaticamente)</label>
        <select v-model="formEstabelecimento.id_usuario" class="select-padrao">
          <option
            v-for="u in usuariosResponsaveisDisponiveis"
            :key="u.id_usuario"
            :value="u.id_usuario"
          >
            #{{ u.id_usuario }} - {{ u.nome }} ({{ u.email }}) — [{{ rotuloNivelUsuario(u.nivel_acesso) }}]
          </option>
        </select>
      </div>

      <div class="campo-grupo">
        <label>Andares do Estacionamento ({{ formEstabelecimento.andares.length }}/10)</label>
        <div
          v-for="(andar, idx) in formEstabelecimento.andares"
          :key="andar.id_andar"
          class="linha-andar-dinamica"
        >
          <input
            v-model="andar.nome_andar"
            type="text"
            maxlength="25"
            :placeholder="`Nome do Andar ${idx + 1}`"
          />

          <button
            v-if="idx >= 1"
            class="btn-mais-menos btn-menos"
            title="Remover este andar"
            @click="removerAndarForm(idx)"
          >
            <IconSquareRoundedMinus :size="20" />
          </button>

          <button
            v-if="idx === formEstabelecimento.andares.length - 1 && formEstabelecimento.andares.length < 10"
            class="btn-mais-menos btn-mais"
            title="Adicionar novo andar abaixo"
            @click="adicionarAndarForm"
          >
            <IconSquareRoundedPlus :size="20" />
          </button>
        </div>
      </div>

      <div class="rodape-form">
        <button class="btn-primario btn-grande item-icone-texto" @click="avancarParaEditorP2">
          <IconLayoutGrid :size="20" />
          <span>Avançar para o Editor de Mapa 2D</span>
          <IconSquareRoundedArrowRight :size="20" />
        </button>
      </div>
    </div>
  </div>
</template>