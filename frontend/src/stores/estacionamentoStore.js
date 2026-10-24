import { ref } from 'vue'
import { paletaSetores } from '@/constants/paletaSetores'
import { escurecerCorHex } from '@/utils/colorUtils'
import {
  criarMatrizVazia,
  hidratarEstabelecimentoDoBanco,
  obterAndarEntradaSaida,
  contarVagasEstabelecimento
} from '@/utils/gridUtils'
import { listarUsuariosApi } from '@/services/authService'
import {
  listarEstabelecimentosApi,
  salvarEstabelecimentoApi,
  alternarStatusEstabelecimentoApi,
  removerEstabelecimentoApi
} from '@/services/estacionamentoService'
import { usuarioLogado } from './authStore'
import {
  idsSelecionadosGerente,
  simulacao1Ativa,
  estabelecimentosDoGerente,
  estabelecimentosFiltradosGerente,
  alternarSimulacao1Frontend
} from './gerenteStore'

export {
  paletaSetores,
  escurecerCorHex,
  criarMatrizVazia,
  obterAndarEntradaSaida,
  contarVagasEstabelecimento,
  usuarioLogado,
  idsSelecionadosGerente,
  simulacao1Ativa,
  estabelecimentosDoGerente,
  estabelecimentosFiltradosGerente,
  alternarSimulacao1Frontend
}

export const usuariosCadastrados = ref([])
export const estabelecimentos = ref([])
export const carregandoDados = ref(false)

export const modoEdicaoId = ref(null)
export const formEstabelecimento = ref({
  nome: '',
  id_usuario: 1,
  andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
})

export async function carregarDadosDoBanco() {
  carregandoDados.value = true
  try {
    const [usuarios, listaCrua] = await Promise.all([
      listarUsuariosApi(),
      listarEstabelecimentosApi()
    ])

    usuariosCadastrados.value = usuarios || []
    estabelecimentos.value = (listaCrua || []).map(hidratarEstabelecimentoDoBanco)

    if (simulacao1Ativa.value) {
      simulacao1Ativa.value = false
      alternarSimulacao1Frontend()
    }
  } catch (err) {
    console.error('Erro ao conectar com a API FastAPI:', err)
  } finally {
    carregandoDados.value = false
  }
}

export async function salvarEstacionamentoNoBanco() {
  const payload = {
    nome: formEstabelecimento.value.nome,
    id_usuario: formEstabelecimento.value.id_usuario,
    andares: formEstabelecimento.value.andares.map((andar) => {
      const celulasPreenchidas = []

      Object.values(andar.celulas || {}).forEach((c) => {
        if (c.tipo === 'VAZIO' && !c.setorId) return
        celulasPreenchidas.push({
          x: c.x,
          y: c.y,
          tipo: c.tipo === 'VAZIO' && c.setorId ? 'FUNDO_SETOR' : c.tipo,
          orientacao: c.orientacao || 'NENHUMA',
          setor_id_temp: c.setorId || null,
          identificador: c.identificador || null,
          livre: c.livre !== false,
          mac_esp: c.macEsp || null
        })
      })

      return {
        nome_andar: andar.nome_andar,
        grid_x: andar.grid_x,
        grid_y: andar.grid_y,
        setores: (andar.setores || []).map(s => ({
          id_temp: s.id_setor,
          nome_setor: s.nome_setor,
          prefixo: s.prefixo,
          cor_hex: s.cor_hex
        })),
        celulas_preenchidas: celulasPreenchidas
      }
    })
  }

  await salvarEstabelecimentoApi(payload, modoEdicaoId.value)
  await carregarDadosDoBanco()
}

export async function alternarInativoNoBanco(est) {
  await alternarStatusEstabelecimentoApi(est.id)
  await carregarDadosDoBanco()
}

export async function removerEstabelecimentoNoBanco(est) {
  await removerEstabelecimentoApi(est.id)
  await carregarDadosDoBanco()
}

export function iniciarNovoFormulario() {
  modoEdicaoId.value = null
  const idPadrao = usuariosCadastrados.value[0]?.id_usuario || 1
  formEstabelecimento.value = {
    nome: '',
    id_usuario: idPadrao,
    andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
  }
}

export function carregarFormularioEdicao(est) {
  modoEdicaoId.value = est.id
  formEstabelecimento.value = JSON.parse(JSON.stringify(est))
}
