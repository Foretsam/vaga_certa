<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { estabelecimentos } from '../store/estacionamentoStore'

const route = useRoute()
const router = useRouter()

const vagaFavorita = ref(null)
const filtrarOcupadas = ref(false)
const modoSimuladorSensor = ref(false)
const andarSelecionadoId = ref(null)

const estacionamentoAtual = computed(() => {
  const id = parseInt(route.params.id, 10)
  return estabelecimentos.value.find(e => e.id === id && !e.inativo) || null
})

const andarMotorista = computed(() => {
  if (!estacionamentoAtual.value) return null
  return (
    estacionamentoAtual.value.andares.find(a => a.id_andar === andarSelecionadoId.value) ||
    estacionamentoAtual.value.andares[0]
  )
})

watch(
  estacionamentoAtual,
  (novo) => {
    if (novo && novo.andares.length > 0) {
      andarSelecionadoId.value = novo.andares[0].id_andar
      vagaFavorita.value = null
    }
  },
  { immediate: true }
)

function clicarCelulaMotorista(celula) {
  if (!celula || celula.tipo !== 'VAGA') return
  if (modoSimuladorSensor.value) {
    celula.livre = !celula.livre
    if (!celula.livre && vagaFavorita.value === `${celula.x},${celula.y}`) {
      vagaFavorita.value = null
    }
    return
  }
  if (!celula.livre) return
  const chave = `${celula.x},${celula.y}`
  vagaFavorita.value = vagaFavorita.value === chave ? null : chave
}
</script>

<template>
  <div v-if="estacionamentoAtual && andarMotorista" class="painel-estacionamento">
    <header class="painel-header">
      <div>
        <h1>{{ estacionamentoAtual.nome }}</h1>
        <p class="subtitulo">Toque em uma vaga livre (verde) para marcá-la em roxo</p>
      </div>
      <button class="btn-secundario" @click="router.push({ name: 'motorista-home' })">
        📷 Ler outro QR Code
      </button>
    </header>

    <div class="abas-andares">
      <button
        v-for="andar in estacionamentoAtual.andares"
        :key="andar.id_andar"
        class="aba-btn"
        :class="{ 'aba-ativa': andarMotorista.id_andar === andar.id_andar }"
        @click="andarSelecionadoId = andar.id_andar"
      >
        {{ andar.nome_andar }}
      </button>
    </div>

    <div class="barra-controles">
      <div class="controles-esquerda">
        <label class="filtro-toggle">
          <input type="checkbox" v-model="filtrarOcupadas" />
          Deixar vagas ocupadas cinzas
        </label>
        <label class="filtro-toggle">
          <input type="checkbox" v-model="modoSimuladorSensor" />
          🔄 Clique simula Sensor HC-SR04 (Carro Entrando/Saindo)
        </label>
      </div>

      <div class="legenda">
        <span class="badge" style="background:#2563eb">Entrada</span>
        <span class="badge" style="background:#ea580c">Saída</span>
        <span class="badge" style="background:#16a34a">Vaga Livre</span>
        <span class="badge" style="background:#9333ea">Sua Vaga</span>
        <span class="badge" style="background:#dc2626">Ocupada</span>
      </div>
    </div>

    <div class="grid-scroll-wrapper">
      <div
        class="grid-tabuleiro"
        :style="{ gridTemplateColumns: `repeat(${andarMotorista.grid_x}, 42px)` }"
      >
        <template v-for="y in andarMotorista.grid_y" :key="`mot-row-${y}`">
          <div
            v-for="x in andarMotorista.grid_x"
            :key="`mot-cell-${x}-${y}`"
            class="celula-fundo-setor"
            :style="{
              backgroundColor: andarMotorista.celulas[`${x},${y}`]?.corSetor || 'transparent'
            }"
            @click="clicarCelulaMotorista(andarMotorista.celulas[`${x},${y}`])"
          >
            <div
              class="quadrado-interno"
              :class="{
                'q-invisivel': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAZIO',
                'q-estrada': andarMotorista.celulas[`${x},${y}`]?.tipo === 'ESTRADA',
                'q-entrada': andarMotorista.celulas[`${x},${y}`]?.tipo === 'ENTRADA',
                'q-saida': andarMotorista.celulas[`${x},${y}`]?.tipo === 'SAIDA',
                'q-acesso': andarMotorista.celulas[`${x},${y}`]?.tipo === 'ACESSO',
                'q-vaga-livre': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && andarMotorista.celulas[`${x},${y}`]?.livre && vagaFavorita !== `${x},${y}`,
                'q-vaga-roxa': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && andarMotorista.celulas[`${x},${y}`]?.livre && vagaFavorita === `${x},${y}`,
                'q-vaga-ocupada': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarMotorista.celulas[`${x},${y}`]?.livre && !filtrarOcupadas,
                'q-vaga-cinza': andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA' && !andarMotorista.celulas[`${x},${y}`]?.livre && filtrarOcupadas
              }"
            >
              <span v-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'VAGA'">
                {{ andarMotorista.celulas[`${x},${y}`]?.identificador }}
              </span>
              <span v-else-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'ENTRADA'">ENT</span>
              <span v-else-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'SAIDA'">SAI</span>
              <span v-else-if="andarMotorista.celulas[`${x},${y}`]?.tipo === 'ACESSO'">🚶</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>

  <div v-else class="admin-container">
    <div class="lista-card" style="text-align: center">
      <h2>Estacionamento não encontrado ou inativo</h2>
      <button class="btn-primario" style="margin-top: 16px" @click="router.push({ name: 'motorista-home' })">
        Voltar ao Início
      </button>
    </div>
  </div>
</template>