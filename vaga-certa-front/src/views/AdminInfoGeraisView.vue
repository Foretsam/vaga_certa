<script setup>
import { useRouter } from 'vue-router'
import {
  usuariosCadastrados,
  formEstabelecimento,
  criarMatrizVazia
} from '../store/estacionamentoStore'

const router = useRouter()

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

  const nomesAndares = formEstabelecimento.value.andares.map(a => a.nome_andar.trim().toLowerCase())
  if (nomesAndares.some(n => !n)) {
    alert('Preencha o nome de todos os andares.')
    return
  }

  // Regra: Nomes de andares não podem repetir-se no mesmo estacionamento
  const nomesUnicos = new Set(nomesAndares)
  if (nomesUnicos.size !== nomesAndares.length) {
    alert('Os nomes dos andares não se podem repetir no mesmo estacionamento!')
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
    <header class="painel-header">
      <div>
        <h1>Editar estacionamento - Informações Gerais</h1>
        <p class="subtitulo">Defina os dados gerais e a lista de andares sem nomes repetidos (máx. 10 andares)</p>
      </div>
      <button class="btn-secundario" @click="router.push({ name: 'admin-lista' })">⬅️ Voltar à Lista</button>
    </header>

    <div class="form-card">
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
        <label>Vincular Utilizador Responsável (Dono do Estacionamento)</label>
        <select v-model="formEstabelecimento.id_usuario" class="select-padrao">
          <option v-for="u in usuariosCadastrados" :key="u.id_usuario" :value="u.id_usuario">
            #{{ u.id_usuario }} - {{ u.nome }} ({{ u.email }})
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
            −
          </button>

          <button
            v-if="idx === formEstabelecimento.andares.length - 1 && formEstabelecimento.andares.length < 10"
            class="btn-mais-menos btn-mais"
            title="Adicionar novo andar abaixo"
            @click="adicionarAndarForm"
          >
            +
          </button>
        </div>
      </div>

      <div class="rodape-form">
        <button class="btn-primario btn-grande" @click="avancarParaEditorP2">
          🎮 Avançar para o Editor de Mapa 2D ➡️
        </button>
      </div>
    </div>
  </div>
</template>