<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  estabelecimentos,
  usuariosCadastrados,
  iniciarNovoFormulario,
  carregarFormularioEdicao,
  carregarDadosDoBanco,
  alternarInativoNoBanco,
  removerEstabelecimentoNoBanco
} from '@/stores/estacionamentoStore'
import {
  IconSearch,
  IconSquareRoundedPlus,
  IconPencil,
  IconBan,
  IconSquareRoundedCheck,
  IconTrash,
  IconSquareRoundedChevronLeft,
  IconSquareRoundedChevronRight
} from '@/constants/icons'

const router = useRouter()
const termoPesquisaAdmin = ref('')
const paginaAtualAdmin = ref(1)
const itensPorPagina = ref(6)

// Ajusta a quantidade de itens exibidos por página conforme a altura da janela
function calcularItensPorAlturaTela() {
  const alturaTela = window.innerHeight
  const larguraTela = window.innerWidth
  const espacoReservadoSeguranca = larguraTela <= 768 ? 320 : larguraTela <= 1024 ? 330 : 345
  const alturaPorLinha = larguraTela <= 768 ? 64 : 70
  const disponivel = Math.max(200, alturaTela - espacoReservadoSeguranca)
  const calculado = Math.floor(disponivel / alturaPorLinha)
  itensPorPagina.value = Math.max(3, Math.min(11, calculado))
}

onMounted(() => {
  carregarDadosDoBanco()
  calcularItensPorAlturaTela()
  window.addEventListener('resize', calcularItensPorAlturaTela)
})

onUnmounted(() => {
  window.removeEventListener('resize', calcularItensPorAlturaTela)
})

function obterNomeEmailUsuario(idUsuario) {
  const usuario = usuariosCadastrados.value.find(u => u.id_usuario === idUsuario)
  if (usuario) {
    return `${usuario.nome} - ${usuario.email}`
  }
  return `Usuário #${idUsuario}`
}

const estabelecimentosFiltrados = computed(() => {
  const termo = termoPesquisaAdmin.value.trim().toLowerCase()
  if (!termo) return estabelecimentos.value
  return estabelecimentos.value.filter(
    e =>
      e.nome.toLowerCase().includes(termo) ||
      (e.cidade || '').toLowerCase().includes(termo) ||
      String(e.id) === termo
  )
})

const totalPaginasAdmin = computed(() =>
  Math.max(1, Math.ceil(estabelecimentosFiltrados.value.length / itensPorPagina.value))
)

watch(totalPaginasAdmin, (novoTotal) => {
  if (paginaAtualAdmin.value > novoTotal) {
    paginaAtualAdmin.value = novoTotal
  }
})

const estabelecimentosPaginados = computed(() => {
  const inicio = (paginaAtualAdmin.value - 1) * itensPorPagina.value
  return estabelecimentosFiltrados.value.slice(inicio, inicio + itensPorPagina.value)
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
  const confirmou = confirm(
    `Tem certeza que deseja REMOVER permanentemente "${est.nome}" e todos os seus andares e vagas do banco de dados?`
  )
  if (confirmou) {
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
    <header class="topbar-titulo-central topbar-abaixo-tablet-mobile">
      <div class="bloco-titulo-centro">
        <h1>Gerenciamento de Estacionamentos</h1>
        <p class="subtitulo ocultar-subtitulo-mobile">
          Pesquise, adicione, edite, inative ou remova estabelecimentos
        </p>
      </div>
    </header>

    <div class="barra-pesquisa-admin">
      <div class="input-pesquisa-icone-wrapper">
        <IconSearch :size="18" class="icone-input-pesquisa" />
        <input
          v-model="termoPesquisaAdmin"
          type="text"
          placeholder="Pesquisar por nome, cidade ou ID..."
          class="input-pesquisa-grande com-icone"
          @input="paginaAtualAdmin = 1"
        />
      </div>
      <button class="btn-primario btn-add-est item-icone-texto" @click="criarNovo">
        <IconSquareRoundedPlus :size="20" />
        <span>Adicionar Estacionamento</span>
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
            <h3 :title="est.nome">
              <span class="nome-est-lista">{{ est.nome }}</span>
              <span class="badge-cidade-inline">{{ est.cidade || 'Sorocaba' }}</span>
              <span v-if="est.inativo" class="tag-inativo">INATIVO</span>
            </h3>
            <p class="meta-est">
              {{ obterNomeEmailUsuario(est.id_usuario) }}
            </p>
          </div>
        </div>

        <div class="acoes-direita">
          <button
            class="btn-icone editar"
            title="Editar Estacionamento"
            @click="editarEstabelecimento(est)"
          >
            <IconPencil :size="18" />
          </button>
          <button
            class="btn-icone inativar"
            :title="est.inativo ? 'Reativar Estacionamento' : 'Inativar Estacionamento'"
            @click="alternarInativoEstabelecimento(est)"
          >
            <IconSquareRoundedCheck v-if="est.inativo" :size="18" />
            <IconBan v-else :size="18" />
          </button>
          <button
            class="btn-icone remover"
            title="Remover Permanentemente"
            @click="removerEstabelecimento(est)"
          >
            <IconTrash :size="18" />
          </button>
        </div>
      </div>

      <div v-if="estabelecimentosFiltrados.length === 0" class="lista-vazia">
        Nenhum estacionamento encontrado.
      </div>
    </div>

    <div v-if="totalPaginasAdmin > 1" class="paginacao-rodape">
      <button
        class="btn-secundario item-icone-texto"
        :disabled="paginaAtualAdmin <= 1"
        @click="paginaAtualAdmin--"
      >
        <IconSquareRoundedChevronLeft :size="18" />
        <span>Anterior</span>
      </button>
      <span class="info-paginacao">
        Página {{ paginaAtualAdmin }} de {{ totalPaginasAdmin }}
      </span>
      <button
        class="btn-secundario item-icone-texto"
        :disabled="paginaAtualAdmin >= totalPaginasAdmin"
        @click="paginaAtualAdmin++"
      >
        <span>Próxima</span>
        <IconSquareRoundedChevronRight :size="18" />
      </button>
    </div>
  </div>
</template>