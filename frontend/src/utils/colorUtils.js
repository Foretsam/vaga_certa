import { paletaSetores } from '@/constants/paletaSetores'

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
