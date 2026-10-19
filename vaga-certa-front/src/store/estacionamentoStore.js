import { ref } from 'vue'

export const paletaSetores = [
  { nome: 'Ciano Vivo', hex: '#00b4d8', vagaHex: '#005066' },
  { nome: 'Azul Royal', hex: '#3b82f6', vagaHex: '#1d3b8b' },
  { nome: 'Coral Vibrante', hex: '#fb7185', vagaHex: '#881337' },
  { nome: 'Turquesa Intenso', hex: '#14b8a6', vagaHex: '#115e59' },
  { nome: 'Âmbar Dourado', hex: '#f59e0b', vagaHex: '#78350f' },
  { nome: 'Índigo Vivo', hex: '#6366f1', vagaHex: '#312e81' }
]

export function escurecerCorHex(hex) {
  if (!hex) return '#334155'
  const encontrada = paletaSetores.find(p => p.hex.toLowerCase() === hex.toLowerCase())
  if (encontrada) return encontrada.vagaHex

  const limpo = hex.replace('#', '')
  const num = parseInt(limpo, 16)
  const fator = 0.45
  const r = Math.max(0, Math.floor(((num >> 16) & 255) * fator))
  const g = Math.max(0, Math.floor(((num >> 8) & 255) * fator))
  const b = Math.max(0, Math.floor((num & 255) * fator))
  return `rgb(${r}, ${g}, ${b})`
}

export function criarMatrizVazia(largura, altura) {
  const celulas = {}
  for (let y = 1; y <= altura; y++) {
    for (let x = 1; x <= largura; x++) {
      celulas[`${x},${y}`] = {
        x,
        y,
        setorId: null,
        corSetor: null,
        nomeSetor: null,
        prefixoSetor: null,
        tipo: 'VAZIO', // 'VAZIO' | 'ESTRADA' | 'VAGA' | 'ENTRADA' | 'SAIDA' | 'ACESSO'
        orientacao: 'NENHUMA',
        vagaId: null,
        identificador: '',
        livre: true,
        macEsp: null
      }
    }
  }
  return celulas
}

function gerarEstabelecimentoMaquete() {
  const celulas = criarMatrizVazia(12, 8)
  celulas['1,4'].tipo = 'ENTRADA'
  celulas['1,5'].tipo = 'ENTRADA'
  for (let x = 2; x <= 10; x++) {
    celulas[`${x},4`].tipo = 'ESTRADA'
    celulas[`${x},5`].tipo = 'ESTRADA'
  }
  celulas['11,4'].tipo = 'SAIDA'
  celulas['11,5'].tipo = 'SAIDA'

  ;[4, 5].forEach((x, idx) => {
    celulas[`${x},3`] = {
      x,
      y: 3,
      setorId: 100,
      nomeSetor: 'Setor A (Maquete)',
      prefixoSetor: 'A',
      corSetor: '#00b4d8',
      tipo: 'VAGA',
      orientacao: 'NENHUMA',
      vagaId: idx + 1,
      identificador: `A${idx + 1}`,
      livre: idx === 0,
      macEsp: 'AA:BB:CC:DD:EE:01'
    }
  })

  celulas['8,2'].tipo = 'ACESSO'

  return {
    id: 1,
    nome: 'Shopping Central (Maquete 2 Vagas)',
    id_usuario: 1,
    inativo: false,
    andares: [
      {
        id_andar: 10,
        nome_andar: 'Subsolo 1',
        grid_x: 12,
        grid_y: 8,
        setores: [
          {
            id_setor: 100,
            nome_setor: 'Setor A (Maquete)',
            prefixo: 'A',
            cor_hex: '#00b4d8',
            inativo_offline: false
          }
        ],
        equipamentos: [{ id_equipamento: 1, codigo_mac: 'AA:BB:CC:DD:EE:01', id_setor: 100 }],
        celulas
      }
    ]
  }
}

export const usuariosCadastrados = ref([
  { id_usuario: 1, nome: 'Carlos Tanaka', email: 'tanaka@estacionamento.com' },
  { id_usuario: 2, nome: 'Marcos Almeida', email: 'marcos@megashopping.com' },
  { id_usuario: 3, nome: 'Ana Clara Silva', email: 'ana@redeestacionar.com' }
])

export const estabelecimentos = ref([gerarEstabelecimentoMaquete()])

// Estado temporário usado durante a criação ou edição de um estacionamento no Nível 3
export const modoEdicaoId = ref(null)
export const formEstabelecimento = ref({
  nome: '',
  id_usuario: 1,
  andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
})

export function iniciarNovoFormulario() {
  modoEdicaoId.value = null
  formEstabelecimento.value = {
    nome: '',
    id_usuario: usuariosCadastrados.value[0].id_usuario,
    andares: [{ id_andar: Date.now(), nome_andar: 'Subsolo 1', grid_x: 30, grid_y: 20 }]
  }
}

export function carregarFormularioEdicao(est) {
  modoEdicaoId.value = est.id
  formEstabelecimento.value = JSON.parse(JSON.stringify(est))
}