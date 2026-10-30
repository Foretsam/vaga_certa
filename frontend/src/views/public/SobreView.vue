<script setup>
import { useRouter } from 'vue-router'
import {
  IconInfoCircle,
  IconParking,
  IconCpu,
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
        <p class="subtitulo">Mobilidade inteligente e gestão de estacionamentos em tempo real</p>
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
      <!-- PARTE 1: INTUITO DO PROJETO (SEM TECNICIDADES) -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge azul">
            <IconParking :size="24" />
          </div>
          <h2>1. O Propósito do Projeto</h2>
        </div>
        <p class="texto-sobre">
          Procurar uma vaga disponível em horários de pico costuma gerar filas, perda de tempo e frustração. O <strong>Vaga Certa</strong> foi criado para eliminar essa incerteza: ao chegar ao local (ou antes mesmo de sair de casa), o motorista escaneia um QR Code ou pesquisa o estacionamento pelo celular e visualiza no mapa exatamente onde estão as vagas livres.
        </p>
        <p class="texto-sobre">
          Para os administradores e gestores, o sistema substitui o controle visual por um painel inteligente, permitindo acompanhar a lotação ao vivo, identificar os horários de maior movimento e interditar vagas com poucos cliques.
        </p>
      </section>

      <!-- PARTE 2: TECNOLOGIAS UTILIZADAS E O PORQUÊ -->
      <section class="card-sobre-bloco">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge roxo">
            <IconCpu :size="24" />
          </div>
          <h2>2. Tecnologias Utilizadas e Por Quê</h2>
        </div>
        <p class="texto-sobre">
          A arquitetura foi planejada para unir resposta em tempo real, facilidade de manutenção e baixo custo de implantação:
        </p>
        <ul class="lista-tecnologias-sobre">
          <li>
            <strong>IoT com ESP32, Sensores HC-SR04 e LEDs:</strong> O microcontrolador ESP32 oferece conectividade Wi-Fi nativa de baixo consumo, enquanto os sensores ultrassônicos detectam a distância física dos veículos com precisão e acionam a sinalização luminosa local a um custo acessível.
          </li>
          <li>
            <strong>Backend em Python (FastAPI) + MySQL:</strong> O FastAPI foi escolhido pela altíssima performance assíncrona na comunicação entre hardware e web. Já o MySQL garante a integridade relacional das plantas 2D, setores, equipamentos e histórico de ocupação.
          </li>
          <li>
            <strong>Frontend em Vue 3 e Vite:</strong> A reatividade leve do Vue 3 permitiu criar um Editor 2D gamificado, mapas interativos com suporte a gestos de pinça no celular e relatórios dinâmicos com exportação direta para BI.
          </li>
        </ul>
      </section>

      <!-- PARTE 3: PLANOS FUTUROS E CONCLUSÃO -->
      <section class="card-sobre-bloco destaque-futuro">
        <div class="cabecalho-sobre-bloco">
          <div class="icone-sobre-badge verde">
            <IconEye :size="24" />
          </div>
          <h2>3. Planos Futuros e Conclusão</h2>
        </div>
        <p class="texto-sobre">
          A evolução do <strong>Vaga Certa</strong> prevê duas frentes principais para adaptar o sistema a diferentes infraestruturas:
        </p>
        <div class="grade-planos-futuros">
          <div class="item-plano-futuro">
            <strong>Câmeras em Estacionamentos Cobertos</strong>
            <span>Uso de visão computacional para monitorar dezenas de vagas simultaneamente através de câmeras já instaladas nos corredores, reduzindo a necessidade de sensores individuais.</span>
          </div>
          <div class="item-plano-futuro">
            <strong>Sistema de Cancelas em Áreas Abertas</strong>
            <span>Integração direta com cancelas eletrônicas de entrada e saída para automatizar a contagem de fluxo em pátios abertos, onde a instalação de sensores de teto não é viável.</span>
          </div>
        </div>
        <p class="texto-sobre conclusao-sobre">
          <IconInfoCircle :size="18" class="icone-conclusao" />
          <span>
            Mais do que um monitor de estacionamento, o <strong>Vaga Certa</strong> demonstra na prática como a integração entre hardware embarcado e desenvolvimento web moderno pode transformar espaços urbanos em ambientes mais ágeis, organizados e inteligentes.
          </span>
        </p>
      </section>
    </div>
  </main>
</template>