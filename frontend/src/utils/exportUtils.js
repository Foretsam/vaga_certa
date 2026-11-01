/**
 * Gera e dispara o download de um arquivo CSV com BOM UTF-8 (compatível com Excel e Power BI).
 */
export function baixarArquivoCsv(nomeArquivo, cabecalhos, linhas) {
  const escaparCelulaCsv = (valor) => {
    const texto = valor === null || valor === undefined ? '' : String(valor)
    const escapado = texto.replace(/"/g, '""')
    return /[";,\n]/.test(escapado) ? `"${escapado}"` : escapado
  }

  const conteudo = [
    cabecalhos.map(escaparCelulaCsv).join(';'),
    ...linhas.map(linha => linha.map(escaparCelulaCsv).join(';'))
  ].join('\r\n')

  // Prefixo \uFEFF garante leitura correta de acentos no Microsoft Excel
  const blob = new Blob(['\uFEFF' + conteudo], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', nomeArquivo)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}