/**
 * Gera um mapa indexado por coordenadas "x,y" com células vazias para inicializar um andar.
 */
export function criarMatrizVazia(largura, altura) {
  const celulas = {}
  for (let y = 0; y < altura; y++) {
    for (let x = 0; x < largura; x++) {
      celulas[`${x},${y}`] = {
        x,
        y,
        tipo: 'VAZIO',
        orientacao: 'NENHUMA',
        setorId: null,
        nomeSetor: null,
        prefixoSetor: null,
        corSetor: null,
        identificador: null,
        livre: true,
        inativa: false,
        macEsp: null,
        idVagaBanco: null,
        usosNoDia: 0
      }
    }
  }
  return celulas
}

/**
 * Converte a estrutura relacional vinda da API FastAPI para a matriz reativa usada no Editor 2D e nos Mapas.
 */
export function hidratarEstabelecimentoDoBanco(estCru) {
  const andaresHidratados = (estCru.andares || []).map((andar) => {
    const gx = Number(andar.grid_x) || 30
    const gy = Number(andar.grid_y) || 20
    const celulas = criarMatrizVazia(gx, gy)

    const mapaSetores = {}
    ;(andar.setores || []).forEach((s) => {
      mapaSetores[s.id_setor] = s
    })

    // Hidrata estradas, entradas, saídas, acessos e fundos de setor
    ;(andar.elementos_mapa || []).forEach((el) => {
      const chave = `${el.coord_x},${el.coord_y}`
      const cel = celulas[chave]
      if (!cel) return

      const setor = el.id_setor ? mapaSetores[el.id_setor] : null
      if (setor) {
        cel.setorId = setor.id_setor
        cel.nomeSetor = setor.nome_setor
        cel.prefixoSetor = setor.prefixo
        cel.corSetor = setor.cor_hex
      }

      if (el.tipo !== 'FUNDO_SETOR') {
        cel.tipo = el.tipo
        cel.orientacao = el.orientacao || 'NENHUMA'
      }
    })

    // Hidrata vagas e vincula seus respectivos equipamentos ESP32
    const equipamentosMap = new Map()
    ;(andar.vagas || []).forEach((v) => {
      const chave = `${v.coord_x},${v.coord_y}`
      const cel = celulas[chave]
      if (!cel) return

      cel.tipo = 'VAGA'
      cel.idVagaBanco = v.id_vaga
      cel.identificador = v.identificador
      cel.livre = Boolean(v.livre)
      cel.inativa = Boolean(v.inativo)
      cel.macEsp = v.mac_esp
      cel.setorId = v.id_setor
      cel.nomeSetor = v.nome_setor
      cel.prefixoSetor = v.prefixo
      cel.corSetor = v.cor_hex

      if (v.mac_esp) {
        if (!equipamentosMap.has(v.mac_esp)) {
          equipamentosMap.set(v.mac_esp, [])
        }
        equipamentosMap.get(v.mac_esp).push(chave)
      }
    })

    const equipamentos = Array.from(equipamentosMap.entries()).map(([mac, coords], idx) => ({
      id: Date.now() + idx,
      mac,
      vagasCoords: coords
    }))

    return {
      id_andar: andar.id_andar,
      nome_andar: andar.nome_andar,
      grid_x: gx,
      grid_y: gy,
      setores: andar.setores || [],
      equipamentos,
      celulas
    }
  })

  return {
    id: estCru.id,
    nome: estCru.nome,
    cidade: estCru.cidade || 'Sorocaba',
    id_usuario: estCru.id_usuario,
    inativo: Boolean(estCru.inativo),
    andares: andaresHidratados
  }
}

/**
 * Retorna preferencialmente o andar que contém a Entrada/Saída principal do estacionamento.
 */
export function obterAndarEntradaSaida(est) {
  if (!est?.andares?.length) return null
  const comEntrada = est.andares.find(andar =>
    Object.values(andar.celulas || {}).some(c => c.tipo === 'ENTRADA' || c.tipo === 'SAIDA')
  )
  return comEntrada || est.andares[0]
}

/**
 * Contabiliza o total de vagas ativas, livres, ocupadas e inativas de um estabelecimento.
 */
export function contarVagasEstabelecimento(est) {
  let total = 0
  let livres = 0
  let ocupadas = 0
  let inativas = 0

  ;(est?.andares || []).forEach((andar) => {
    Object.values(andar.celulas || {}).forEach((c) => {
      if (c.tipo === 'VAGA') {
        if (c.inativa) {
          inativas++
        } else {
          total++
          if (c.livre) livres++
          else ocupadas++
        }
      }
    })
  })

  return { total, livres, ocupadas, inativas }
}