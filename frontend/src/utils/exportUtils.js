export function formatarMinutos(mins) {
  if (!mins || mins <= 0) return '0min'
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h > 0 ? `${h}h ${m}min` : `${m}min`
}

export function formatarLinhasParaCsvBrasil(linhas) {
  return linhas
    .map(row => row.map(val => `"${String(val ?? '').replace(/"/g, '""')}"`).join(';'))
    .join('\r\n')
}

export function dispararDownloadArquivo(conteudo, nomeArquivo, mimeType = 'text/csv;charset=utf-8;') {
  const blob = new Blob([conteudo], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = nomeArquivo
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
