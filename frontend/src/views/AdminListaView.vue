<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  estabelecimentos,
  iniciarNovoFormulario,
  carregarFormularioEdicao,
  carregarDadosDoBanco,
  alternarInativoNoBanco,
  removerEstabelecimentoNoBanco
} from '../store/estacionamentoStore'

const router = useRouter()
const termoPesquisaAdmin = ref('')
const paginaAtualAdmin = ref(1)
const itensPorPagina = 5

onMounted(() => {
  carregarDadosDoBanco()
})

const estabelecimentosFiltrados = computed(() => {
  const termo = termoPesquisaAdmin.value.trim().toLowerCase()
  if (!termo) return estabelecimentos.value
  return estabelecimentos.value.filter(
    e => e.nome.toLowerCase().includes(termo) || String(e.id) === termo
  )
})

const totalPaginasAdmin = computed(() =>
  Math.max(1, Math.ceil(estabelecimentosFiltrados.value.length / itensPorPagina))
)

const estabelecimentosPaginados = computed(() => {
  const inicio = (paginaAtualAdmin.value - 1) * itensPorPagina
  return estabelecimentosFiltrados.value.slice(inicio, inicio + itensPorPagina)
})

function criarNovo() {
  iniciarNovoFormulario()
  router.push({ name: 'admin-info-gerais' })
}

function editarEstabelecimento(est) {
  carregarFormularioEdicao(est)
  router.push({ name: 'admin-info-gerais' })
}

async function alternarInativoEstabelecimento(est) {
  try {
    await alternarInativoNoBanco(est)
  } catch (err) {
    alert(err.message)
  }
}

async function removerEstabelecimento(est) {
  if (confirm(`Tem certeza que deseja REMOVER permanentemente "${est.nome}" e todos os seus andares e vagas do banco de dados?`)) {
    try {
      await removerEstabelecimentoNoBanco(est)
    } catch (err) {
      alert(err.message)
    }
  }
}
</script>

<template>
  <div class="admin-container">
    <!-- Cabeçalho no topo, centralizado à direita do menu hambúrguer -->
    <header class="topbar-titulo-central">
      <h1>Gerenciamento de Estacionamentos</h1>
      <p class="subtitulo">Pesquise, adicione, edite, inative ou remova estabelecimentos</p>
    </header>

    <div class="barra-pesquisa-admin">
      <input
        v-model="termoPesquisaAdmin"
        type="text"
        placeholder="🔍 Pesquisar por nome ou ID..."
        class="input-pesquisa-grande"
        @input="paginaAtualAdmin = 1"
      />
      <button class="btn-primario btn-add-est" @click="criarNovo">
        ➕ Adicionar Estacionamento
      </button>
    </div>

    <div class="lista-card">
      <div
        v-for="est in estabelecimentosPaginados"
        :key="est.id"
        class="linha-estabelecimento"
        :class="{ 'linha-inativa': est.inativo }"
      >
        <div class="info-est">
          <span class="id-badge">#{{ est.id }}</span>
          <div class="textos-est">
            <h3>
              {{ est.nome }}
              <span v-if="est.inativo" class="tag-inativo">INATIVO</span>
            </h3>
            <p class="meta-est">
              Andares: {{ est.andares.length }} | Resp. ID: #{{ est.id_usuario }}
            </p>
          </div>
        </div>

        <!-- Apenas Editar, Inativar e Remover alinhados à direita -->
        <div class="acoes-direita">
          <button class="btn-icone editar" title="Editar Estacionamento" @click="editarEstabelecimento(est)">
            ✏️
          </button>
          <button
            class="btn-icone inativar"
            :title="est.inativo ? 'Reativar' : 'Inativar'"
            @click="alternarInativoEstabelecimento(est)"
          >
            {{ est.inativo ? '✅' : '🚫' }}
          </button>
          <button class="btn-icone remover" title="Remover Permanentemente" @click="removerEstabelecimento(est)">
            🗑️
          </button>
        </div>
      </div>

      <div v-if="estabelecimentosPaginados.length === 0" class="lista-vazia">
        Nenhum estacionamento encontrado.
      </div>
    </div>

    <div class="paginacao-admin">
      <button :disabled="paginaAtualAdmin <= 1" @click="paginaAtualAdmin--">⬅️ Anterior</button>
      <span>Página {{ paginaAtualAdmin }} de {{ totalPaginasAdmin }}</span>
      <button :disabled="paginaAtualAdmin >= totalPaginasAdmin" @click="paginaAtualAdmin++">Próxima ➡️</button>
    </div>
  </div>
</template>