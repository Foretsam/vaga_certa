<script setup>
import { useRouter } from 'vue-router'
import {
  IconInfoCircle,
  IconChartBar,
  IconLayoutBoard,
  IconEye,
  IconSquareRoundedArrowLeft
} from '@/constants/icons'

const router = useRouter()
</script>

<template>
  <main class="admin-container sobre-container">
    <header class="topbar-titulo-central com-botao-direita">
      <div class="bloco-titulo-centro">
        <h1>Sobre o Vaga Certa</h1>
        <p class="subtitulo">Gestão de fluxo para estacionamentos e localização de vagas em tempo real</p>
      </div>
      <button
        class="btn-secundario btn-voltar-topo item-icone-texto"
        @click="router.back()"
      >
        <IconSquareRoundedArrowLeft :size="18" />
        <span>Voltar</span>
      </button>
    </header>

    <div class="grade-sobre-secoes">
      <!-- PARTE 1: PROPOSTA DO PROJETO -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge azul">
            <IconChartBar :size="24" />
          </div>
          <h2>1. O Propósito do Projeto</h2>
        </div>
        <p class="texto-sobre">
          Muitos estacionamentos operam sem dados claros de rotina: o gestor até sabe quantos veículos entraram no mês, mas não consegue acompanhar como o <strong>fluxo</strong> se comporta ao longo do dia. O <strong>Vaga Certa</strong> resolve esse problema registrando em tempo real a ocupação das vagas para entregar métricas diretas de horários de pico, tempo médio de permanência e setores mais procurados.
        </p>
        <p class="texto-sobre">
          Para o motorista, o funcionamento é direto: basta ler o QR Code na entrada do local ou buscar o estacionamento pelo site para abrir o mapa do andar e ir direto até uma vaga livre, sem precisar rodar pelos corredores.
        </p>
      </section>

      <!-- PARTE 2: STACK E DECISÕES TÉCNICAS -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge roxo">
            <IconLayoutBoard :size="24" />
          </div>
          <h2>2. Tecnologias e Decisões de Projeto</h2>
        </div>
        <p class="texto-sobre">
          O foco principal do desenvolvimento foi construir uma aplicação web completa (Frontend e Backend) que funcione de forma independente do tipo de sensor usado na ponta:
        </p>
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

      <!-- PARTE 3: PRÓXIMOS PASSOS E CONCLUSÃO -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge verde">
            <IconEye :size="24" />
          </div>
          <h2>3. Próximos Passos</h2>
        </div>
        <p class="texto-sobre">
          Com a base de software já estruturada para receber leituras de diferentes origens, a evolução natural do projeto é substituir os sensores do protótipo por duas soluções de mercado:
        </p>
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
        <p class="texto-sobre conclusao-sobre">
          <IconInfoCircle :size="19" class="icone-conclusao" />
          <span>
            O <strong>Vaga Certa</strong> nasceu como um projeto acadêmico de engenharia, mas foi estruturado como um produto real: código modular, dados claros para quem administra o espaço e rapidez para quem só quer estacionar.
          </span>
        </p>
      </section>
    </div>

    <!-- FOOTER COM LINK DO GITHUB -->
    <footer class="sobre-footer">
      <a
        href="https://github.com/Foretsam/vaga_certa"
        target="_blank"
        rel="noopener noreferrer"
        class="link-github-footer item-icone-texto"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M9 19c-4.3 1.4 -4.3 -2.5 -6 -3m12 5v-3.5c0 -1 .1 -1.4 -.5 -2c2.8 -.3 5.5 -1.4 5.5 -6a4.6 4.6 0 0 0 -1.3 -3.2a4.2 4.2 0 0 0 -.1 -3.2s-1.1 -.3 -3.5 1.3a12.3 12.3 0 0 0 -6.2 0c-2.4 -1.6 -3.5 -1.3 -3.5 -1.3a4.2 4.2 0 0 0 -.1 3.2a4.6 4.6 0 0 0 -1.3 3.2c0 4.6 2.7 5.7 5.5 6c-.6 .6 -.6 1.2 -.5 2v3.5" />
        </svg>
        <span>Ver código-fonte no GitHub</span>
      </a>
    </footer>
  </main>
</template>