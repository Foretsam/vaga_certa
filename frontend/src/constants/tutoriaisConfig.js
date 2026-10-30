export const TUTORIAIS_POR_ROTA = {
  // 1. Dashboard Principal — Gerente (GerenteView.vue)
  gerente: [
    {
      seletor: null,
      titulo: 'Bem-vindo ao Dashboard!',
      texto: 'Aqui você acompanha em tempo real os principais indicadores e o resumo operacional das suas unidades.'
    },
    {
      seletor: '.barra-filtros-gerente, .seletor-multi-wrapper',
      titulo: 'Filtros por Unidade e Cidade',
      texto: 'Use estes seletores para filtrar os dados do painel por cidade ou escolher estacionamentos específicos para analisar.'
    },
    {
      seletor: '.gerente-atalhos-topo',
      titulo: 'Navegação Rápida',
      texto: 'Por estes atalhos no topo, você acessa a qualquer momento a planta em tela cheia dos estacionamentos ou a central completa de relatórios.'
    },
    {
      seletor: '.secao-relatorios-dashboard',
      titulo: 'Resumo de Indicadores Diários',
      texto: 'Estes cartões somam o fluxo por hora, a taxa de ocupação atual e o tempo médio de permanência de hoje. Para aprofundar a análise ou baixar planilhas, clique em "Ver relatórios em detalhe" logo abaixo.'
    },
    {
      seletor: '.secao-estacionamentos-dupla-pc',
      seletorTabletMobile: '.secao-seletor-mobile-est',
      titulo: 'Prévia dos Estacionamentos e Tela Cheia',
      texto: 'Aqui ficam as plantas das suas maiores unidades. Clique em "Ver em tela cheia" para abrir e operar o mapa interativo completo.',
      textoTabletMobile: 'Aqui ficam as plantas das suas maiores unidades. Clique em "Escolher Estacionamento" para abrir e operar o mapa interativo completo.'
    }
  ],

  // 2. Relatórios e Exportação — Gerente (GerenteRelatoriosView.vue)
  'gerente-relatorios': [
    {
      seletor: null,
      titulo: 'Central de Relatórios e Exportação BI',
      texto: 'Nesta página você analisa o desempenho detalhado dos seus estacionamentos, compara unidades e exporta relatórios em CSV prontos para Excel ou Power BI.'
    },
    {
      seletor: '.grade-dupla-relatorios .card-relatorio-bloco:first-child',
      titulo: 'Relatórios Individuais e Exportação Rápida',
      texto: 'Cada card exibe um recorte analítico. Clique no botão de download no canto superior de qualquer cartão para exportar os dados daquele relatório'
    },
    {
      seletor: '.seletores-comparador-grid',
      subirParaPai: '.card-relatorio-bloco',
      titulo: 'Comparação Lado a Lado',
      texto: 'Selecione duas unidades diferentes nos campos deste card para comparar diretamente a taxa de ocupação, o total de vagas e o tempo médio de permanência entre elas.'
    },
    {
      seletor: '.tabela-historico-altura-fixa',
      subirParaPai: '.card-relatorio-bloco',
      titulo: 'Histórico de Ocupação por Vaga',
      texto: 'Consulte o registro cronológico de entradas, saídas e permanências. Você pode pesquisar por uma vaga específica no topo da tabela e navegar pelos registros usando a paginação.'
    },
    {
      seletor: '.card-exportacao-completa-bi',
      titulo: 'Exportação Completa por Período',
      texto: 'Precisa consolidar todos os dados de uma vez? Defina uma data inicial e final (ou escolha um dos atalhos de período) e clique no botão verde para baixar o relatório completo.'
    }
  ],

  // 3. Estacionamentos em Tela Cheia — Gerente (GerenteEstacionamentosView.vue)
  'gerente-estacionamentos': [
    {
      seletor: null,
      titulo: 'Visão Operacional em Tela Cheia',
      texto: 'Acompanhe a planta 2D completa de cada andar em tempo real, inspecione vagas e gerencie bloqueios operacionais com facilidade.'
    },
    {
      seletor: '.grupo-filtros-navegacao-gerente',
      abrirTopbarMobile: true,
      titulo: 'Troca de Cidade, Unidade e Andar',
      texto: 'Utilize estes controles para filtrar a cidade, alternar entre seus estacionamentos ou mudar o andar exibido na tela.'
    },
    {
      seletor: '.area-grid-principal',
      titulo: 'Elementos do Estacionamento',
      texto: 'No mapa, cada elemento possui uma cor: Verde (vaga livre), Vermelho (vaga ocupada), Cinza (vaga inativa), Cinza Escuro (estradas de circulação), Azul (entrada), Laranja (saída) e Ícone Verde (acesso de pedestres/elevador).'
    },
    {
      seletor: '.grupo-inativar-reativar-gerente',
      abrirTopbarMobile: true,
      titulo: 'Inativar e Reativar Vagas em Lote',
      texto: 'Precisa interditar vagas para manutenção? Clique em "Inativar Vagas" (ou "Reativar"), selecione uma ou mais vagas diretamente no mapa e confirme a alteração na barra inferior.'
    },
    {
      seletor: '.grupo-calor-simulacao-gerente',
      abrirTopbarMobile: true,
      titulo: 'Mapa de Calor de Rotatividade',
      texto: 'Ao ativar o "Mapa de Calor", as vagas mudam de cor em 5 níveis (do azul ao vermelho intenso) para mostrar quais vagas foram mais utilizadas ao longo do dia.'
    },
    {
      seletor: '.btn-qrcode-gerente',
      abrirTopbarMobile: true,
      titulo: 'QR Code para Motoristas',
      texto: 'Clique neste botão para visualizar e imprimir o QR Code exclusivo deste estacionamento. Com ele na entrada da unidade, os motoristas escaneiam e abrem o mapa de vagas livres direto no celular.'
    }
  ],

  // 4. Lista de Estacionamentos — Admin Dev (AdminListaView.vue)
  'admin-lista': [
    {
      seletor: null,
      titulo: 'Gerenciamento de Estacionamentos',
      texto: 'Bem-vindo ao painel administrativo! Aqui você visualiza e controla todas as unidades cadastradas na plataforma Vaga Certa.'
    },
    {
      seletor: '.barra-pesquisa-admin .input-pesquisa-icone-wrapper',
      titulo: 'Pesquisa e Navegação de Páginas',
      texto: 'Digite o nome do estabelecimento, a cidade ou o #ID na barra de pesquisa para filtrar a lista. Use os botões "Anterior" e "Próxima" no rodapé para alternar entre as páginas.'
    },
    {
      seletor: '.btn-add-est',
      titulo: 'Cadastrar Nova Unidade',
      texto: 'Clique em "Adicionar Estacionamento" para iniciar o cadastro de um novo estabelecimento e construir sua planta 2D do zero.'
    },
    {
      seletor: '.lista-card',
      titulo: 'Editar, Inativar ou Excluir',
      texto: 'Ao lado direito de cada estacionamento, use os três botões de ícone para Editar os dados e o mapa 2D, Inativar/Reativar o acesso à unidade ou Remover o cadastro permanentemente do banco de dados.'
    }
  ],

  // 5. Informações Gerais — Admin Dev (AdminInfoGeraisView.vue)
  'admin-info-gerais': [
    {
      seletor: '.form-card',
      titulo: 'Informações Gerais do Estacionamento',
      texto: 'Nesta primeira etapa de configuração, informe o nome do estabelecimento, a cidade onde ele fica e selecione qual usuário gerente será o responsável pela unidade.'
    },
    {
      seletor: '.linha-andar-dinamica',
      titulo: 'Adicionar ou Remover Andares',
      texto: 'Defina o nome de cada pavimento da unidade (até 10 andares, sem repetir nomes). Clique no botão verde (+) para criar um novo andar ou no botão vermelho (-) para remover um andar existente antes de avançar para o Editor 2D.'
    }
  ],

  // 6. Editor de Mapa 2D — Admin Dev (AdminEditor2DView.vue) — Etapas 2 e 5 invertidas
  'admin-editor-2d': [
    {
      seletor: '.editor-topbar .topbar-esquerda',
      abrirTopbarMobile: true,
      titulo: 'Controles Superiores do Editor',
      texto: 'No menu do topo, você pode voltar para as Informações Gerais, escolher qual Andar está desenhando no momento, alterar o Tamanho do Grid (de 5x5 até 100x100) e usar Desfazer/Refazer a qualquer instante.'
    },
    {
      seletor: '.area-grid-principal',
      titulo: 'Criando Estradas, Setores e Vagas',
      texto: 'Clique e arraste o mouse sobre os quadrados do grid para criar uma seleção. Uma barra flutuante aparecerá na parte inferior permitindo adicionar/remover Estradas, definir Setores, criar Vagas ou limpar tudo com a borracha.'
    },
    {
      seletor: '.sidebar-direita-editor .painel-ferramentas:nth-child(2)',
      abrirSidebarMobile: true,
      titulo: 'Vinculando Equipamentos (ESP32) às Vagas',
      texto: 'Toda vaga criada fica amarela até receber um equipamento. Escolha um formato de cobertura (ex: 1x2, 2x4), clique sobre as vagas amarelas no grid e informe o código MAC do ESP32 para ativá-las.'
    },
    {
      seletor: '.sidebar-direita-editor .painel-ferramentas:nth-child(1)',
      abrirSidebarMobile: true,
      titulo: 'Posicionando Entradas, Saídas e Acessos',
      texto: 'Escolha no painel direito se o acesso/entrada/saída será Horizontal (H) ou Vertical (V), informe a largura em quadrados e clique no mapa para posicionar.'
    },
    {
      seletor: '.area-grid-principal',
      titulo: 'Elementos da Planta 2D',
      texto: 'Cada quadrado no mapa representa parte da estrutura: Cinza Escuro (estradas), Amarelo (vaga não vinculada), Cor Escura do Setor (vaga vinculada), Azul (entrada), Laranja (saída) e Verde (acesso interno).'
    },
    {
      seletor: '.btn-alterar-setores-menu',
      abrirSidebarMobile: true,
      titulo: 'Editar ou Excluir Setores',
      texto: 'Clique em "Alterar Setores" sempre que precisar renomear um setor, trocar seu prefixo de numeração, mudar sua cor ou excluí-lo do andar atual.'
    },
    {
      seletor: '.editor-topbar .topbar-direita',
      seletorTabletMobile: '.hud-coluna-direita-mobile',
      titulo: 'Validação em Tempo Real e Salvamento',
      texto: 'O botão de alerta mostra quantas exigências ainda faltam para liberar a planta (como vincular ESP32 nas vagas amarelas ou incluir entrada e saída). Quando o contador chegar a 0, clique em "Finalizar e Salvar" para gravar tudo no banco de dados!'
    }
  ]
}