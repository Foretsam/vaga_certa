/**
 * Escurece uma cor hexadecimal aplicando um fator multiplicador (0 a 1) nos canais RGB.
 * Utilizado para diferenciar visualmente vagas vinculadas sobre o fundo pastel do setor.
 */
export function escurecerCorHex(hex, fator = 0.55) {
  if (!hex || typeof hex !== 'string') return '#334155'
  const limpo = hex.replace('#', '')
  if (limpo.length !== 6) return hex

  const r = Math.max(0, Math.floor(parseInt(limpo.substring(0, 2), 16) * fator))
  const g = Math.max(0, Math.floor(parseInt(limpo.substring(2, 4), 16) * fator))
  const b = Math.max(0, Math.floor(parseInt(limpo.substring(4, 6), 16) * fator))

  const toHex = n => n.toString(16).padStart(2, '0')
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}