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
        tipo: 'VAZIO',
        orientacao: 'NENHUMA',
        vagaId: null,
        identificador: '',
        livre: true,
        inativa: false,
        semEsp: false,
        usosNoDia: 0,
        horaChegada: null,
        duracaoMinutos: 0,
        macEsp: null
      }
    }
  }
  return celulas
}

export function hidratarEstabelecimentoDoBanco(estBanco) {
  const andaresHidratados = (estBanco.andares || []).map((andar) => {
    const celulas = criarMatrizVazia(andar.grid_x, andar.grid_y)
    const mapaSetores = {}
    ;(andar.setores || []).forEach((s) => {
      mapaSetores[s.id_setor] = s
    })

    ;(andar.elementos_mapa || []).forEach((el) => {
      const chave = `${el.coord_x},${el.coord_y}`
      const c = celulas[chave]
      if (!c) return

      if (el.id_setor && mapaSetores[el.id_setor]) {
        const s = mapaSetores[el.id_setor]
        c.setorId = s.id_setor
        c.nomeSetor = s.nome_setor
        c.prefixoSetor = s.prefixo
        c.corSetor = s.cor_hex
      }

      if (el.tipo !== 'FUNDO_SETOR') {
        c.tipo = el.tipo
        c.orientacao = el.orientacao || 'NENHUMA'
      }
    })

    ;(andar.vagas || []).forEach((v) => {
      const chave = `${v.coord_x},${v.coord_y}`
      const c = celulas[chave]
      if (!c) return

      c.tipo = 'VAGA'
      c.vagaId = v.id_vaga
      c.identificador = v.identificador
      c.livre = Boolean(v.livre)
      c.inativa = Boolean(v.inativo)
      c.macEsp = v.mac_esp
      c.semEsp = !v.mac_esp
      c.setorId = v.id_setor
      c.nomeSetor = v.nome_setor
      c.prefixoSetor = v.prefixo
      c.corSetor = v.cor_hex
    })

    return {
      id_andar: andar.id_andar,
      nome_andar: andar.nome_andar,
      grid_x: andar.grid_x,
      grid_y: andar.grid_y,
      setores: andar.setores || [],
      equipamentos: [],
      celulas
    }
  })

  return {
    id: estBanco.id,
    nome: estBanco.nome,
    id_usuario: estBanco.id_usuario,
    inativo: Boolean(estBanco.inativo),
    andares: andaresHidratados
  }
}

export function obterAndarEntradaSaida(est) {
  if (!est?.andares || est.andares.length === 0) return null
  const andarAmbos = est.andares.find((a) => {
    const cels = Object.values(a.celulas || {})
    return cels.some(c => c.tipo === 'ENTRADA') && cels.some(c => c.tipo === 'SAIDA')
  })
  if (andarAmbos) return andarAmbos

  const andarEntrada = est.andares.find((a) =>
    Object.values(a.celulas || {}).some(c => c.tipo === 'ENTRADA' || c.tipo === 'SAIDA')
  )
  return andarEntrada || est.andares[0]
}

export function contarVagasEstabelecimento(est) {
  let total = 0
  let ocupadas = 0
  let livres = 0
  let inativas = 0
  let somaDuracao = 0
  let qtdComDuracao = 0
  let somaUsosDia = 0

  ;(est.andares || []).forEach((andar) => {
    Object.values(andar.celulas || {}).forEach((c) => {
      if (c.tipo === 'VAGA') {
        total++
        somaUsosDia += c.usosNoDia || 0
        if (c.inativa) {
          inativas++
        } else if (c.livre) {
          livres++
        } else {
          ocupadas++
          if (c.duracaoMinutos > 0) {
            somaDuracao += c.duracaoMinutos
            qtdComDuracao++
          }
        }
      }
    })
  })

  const ativas = Math.max(1, total - inativas)
  const taxaOcupacao = total > 0 ? Math.round((ocupadas / ativas) * 100) : 0
  const tempoMedioMin = qtdComDuracao > 0 ? Math.round(somaDuracao / qtdComDuracao) : (ocupadas > 0 ? 78 : 0)

  return {
    total,
    ocupadas,
    livres,
    inativas,
    taxaOcupacao,
    tempoMedioMin,
    somaUsosDia
  }
}
