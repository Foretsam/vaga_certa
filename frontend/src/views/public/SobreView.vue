<script setup>
import { useRouter } from 'vue-router'
import { usuarioLogado } from '@/stores/authStore'
import {
  IconSquareRoundedArrowLeft,
  IconSquareRoundedArrowRight,
  IconParking,
  IconCpu,
  IconChartBar,
  IconSquareRoundedCheck
} from '@/constants/icons'

const router = useRouter()

function voltarPaginaInicial() {
  const nivel = usuarioLogado.value?.nivel_acesso
  if (nivel === 'admin_dev') {
    router.push({ name: 'admin-lista' })
  } else if (nivel === 'admin_estabelecimento') {
    router.push({ name: 'gerente' })
  } else {
    router.push({ name: 'motorista-home' })
  }
}
</script>

<template>
  <main class="admin-container sobre-container">
    <!-- Botão Voltar fixo na direita na mesma altura dos botões da esquerda -->
    <button
      class="btn-secundario btn-voltar-fixo-topo item-icone-texto"
      @click="voltarPaginaInicial"
    >
      <IconSquareRoundedArrowLeft :size="18" />
      <span>Voltar</span>
    </button>

    <!-- Título sempre abaixo da barra superior em todas as resoluções -->
    <header class="topbar-titulo-central topbar-sobre-abaixo-sempre">
      <div class="bloco-titulo-centro">
        <h1>Sobre o Vaga Certa</h1>
        <p class="subtitulo">
          Gestão de fluxo para estacionamentos e localização de vagas em tempo real
        </p>
      </div>
    </header>

    <div class="grade-sobre-secoes">
      <!-- Seção 1: Propósito -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge azul">
            <IconParking :size="24" />
          </div>
          <h2>O Problema e a Nossa Solução</h2>
        </div>

        <p class="texto-sobre">
          Muitos estacionamentos operam sem dados claros de rotina: o gestor até sabe quantos veículos entraram no mês, mas não consegue acompanhar como o <strong>fluxo</strong> se comporta ao longo do dia. O <strong>Vaga Certa</strong> resolve esse problema registrando em tempo real a ocupação das vagas para entregar métricas diretas de horários de pico, tempo médio de permanência e setores mais procurados.
        </p>
        <p class="texto-sobre">
          Para o motorista, o funcionamento é direto: basta ler o QR Code na entrada do local ou buscar o estacionamento pelo site para abrir o mapa do andar e ir direto até uma vaga livre, sem precisar rodar pelos corredores.
        </p>
      </section>

      <!-- Seção 2: Arquitetura -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge roxo">
            <IconCpu :size="24" />
          </div>
          <h2>Arquitetura Tecnológica e Funcionalidades</h2>
        </div>

        <ul class="lista-tecnologias-sobre">
          <li>
            <strong>Frontend (Vue 3 e Vite):</strong> Escolhidos pela facilidade em lidar com atualizações constantes na tela sem recarregar a página. O painel conta com um editor 2D para desenhar a planta dos andares, mapas de calor de uso das vagas, comparador entre unidades e exportação em CSV para Excel e Power BI.
          </li>
          <li>
            <strong>Backend (Python com FastAPI e MySQL):</strong> O FastAPI recebe as leituras de ocupação e responde ao painel de forma assíncrona, mantendo o sistema leve. O MySQL organiza a estrutura de andares, coordenadas do mapa, setores, usuários e o histórico de movimentação.
          </li>
          <li>
            <strong>Protótipo de Hardware (ESP32 e HC-SR04):</strong> Em uma implantação comercial real, a leitura das vagas seria feita por equipamentos industriais. Neste projeto, usamos o microcontrolador ESP32 com sensores ultrassônicos por uma questão de orçamento, que não permitia opções superiores. O conjunto cumpriu bem o papel de simular a operação física e validar a integração em tempo real com a API.
          </li>
        </ul>
      </section>

      <!-- Seção 3: Expansão -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge verde">
            <IconChartBar :size="24" />
          </div>
          <h2>Visão de Futuro e Escalabilidade</h2>
        </div>

        <div class="grade-planos-futuros">
          <div class="item-plano-futuro">
            <strong>Câmeras em Locais Cobertos</strong>
            <span>Uso de visão computacional para identificar várias vagas livres e ocupadas de uma só vez pelas câmeras dos corredores, dispensando sensores individuais por vaga.</span>
          </div>
          <div class="item-plano-futuro">
            <strong>Cancelas em Pátios Abertos</strong>
            <span>Integração direta com o sistema de cancelas na entrada e na saída para controlar a lotação e o fluxo em áreas descobertas.</span>
          </div>
        </div>

        <div class="conclusao-sobre">
          <IconSquareRoundedCheck :size="20" class="icone-conclusao" />
          <span>
            O <strong>Vaga Certa</strong> nasceu como um projeto acadêmico de engenharia, mas foi estruturado como um produto real: código modular, dados claros para quem administra o espaço e rapidez para quem só quer estacionar.
          </span>
        </div>
      </section>
    </div>

    <footer class="sobre-footer">
      <a
        href="https://github.com/Foretsam/vaga_certa"
        target="_blank"
        rel="noopener noreferrer"
        class="link-github-footer item-icone-texto"
      >
        <span>Ver Repositório Oficial no GitHub</span>
        <IconSquareRoundedArrowRight :size="18" />
      </a>
    </footer>
  </main>
</template>