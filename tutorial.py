import tkinter as tk
from tkinter import ttk
import webbrowser

# ==============================================================================
# SCRIPTS PARA CÓPIA (BANCO DE DADOS SQL E DEPENDÊNCIAS DO TERMINAL)
# ==============================================================================

SQL_SCRIPT = """-- Criação automática do banco Vaga Certa
CREATE DATABASE IF NOT EXISTS `vagacerta_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `vagacerta_db`;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE TABLE IF NOT EXISTS `andares` (
  `id_andar` int(11) NOT NULL AUTO_INCREMENT,
  `id_estabelecimento` int(11) NOT NULL,
  `nome_andar` varchar(25) NOT NULL,
  `grid_x` int(11) NOT NULL DEFAULT 30,
  `grid_y` int(11) NOT NULL DEFAULT 20,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL,
  PRIMARY KEY (`id_andar`),
  KEY `id_estabelecimento` (`id_estabelecimento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `elementos_mapa` (
  `id_elemento` int(11) NOT NULL AUTO_INCREMENT,
  `id_andar` int(11) NOT NULL,
  `id_setor` int(11) DEFAULT NULL,
  `tipo` enum('ESTRADA','ENTRADA','SAIDA','ACESSO','FUNDO_SETOR') NOT NULL,
  `orientacao` enum('H','V','NENHUMA') NOT NULL DEFAULT 'NENHUMA',
  `coord_x` int(11) NOT NULL,
  `coord_y` int(11) NOT NULL,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_elemento`),
  UNIQUE KEY `uk_andar_coordenada_elemento` (`id_andar`,`coord_x`,`coord_y`),
  KEY `fk_elementos_setor` (`id_setor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `equipamentos` (
  `id_equipamento` int(11) NOT NULL AUTO_INCREMENT,
  `id_setor` int(11) NOT NULL,
  `codigo_mac` varchar(17) NOT NULL,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL,
  PRIMARY KEY (`id_equipamento`),
  UNIQUE KEY `uk_setor_mac` (`id_setor`,`codigo_mac`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `estabelecimentos` (
  `id_estabelecimento` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(50) NOT NULL,
  `cidade` varchar(60) NOT NULL DEFAULT 'Sorocaba',
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL,
  PRIMARY KEY (`id_estabelecimento`),
  UNIQUE KEY `nome` (`nome`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `historico_ocupacao` (
  `id_historico` int(11) NOT NULL AUTO_INCREMENT,
  `id_vaga` int(11) NOT NULL,
  `data_entrada` datetime NOT NULL DEFAULT current_timestamp(),
  `data_saida` datetime DEFAULT NULL,
  PRIMARY KEY (`id_historico`),
  KEY `id_vaga` (`id_vaga`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `setores` (
  `id_setor` int(11) NOT NULL AUTO_INCREMENT,
  `id_andar` int(11) NOT NULL,
  `nome_setor` varchar(25) NOT NULL,
  `prefixo` varchar(3) NOT NULL DEFAULT 'A',
  `cor_hex` varchar(7) NOT NULL DEFAULT '#bae6fd',
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL,
  PRIMARY KEY (`id_setor`),
  KEY `fk_setores_andares` (`id_andar`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `senha_hash` varchar(255) NOT NULL,
  `nivel_acesso` enum('admin_dev','admin_estabelecimento','usuario') NOT NULL DEFAULT 'usuario',
  `tutoriais_vistos` text DEFAULT NULL,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `usuario_estabelecimento` (
  `id_usuario` int(11) NOT NULL,
  `id_estabelecimento` int(11) NOT NULL,
  PRIMARY KEY (`id_usuario`,`id_estabelecimento`),
  KEY `id_estabelecimento` (`id_estabelecimento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `vagas` (
  `id_vaga` int(11) NOT NULL AUTO_INCREMENT,
  `id_equipamento` int(11) NOT NULL,
  `identificador` varchar(10) NOT NULL,
  `coord_x` int(11) NOT NULL,
  `coord_y` int(11) NOT NULL,
  `livre_para_estacionar` tinyint(1) DEFAULT 1,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL,
  PRIMARY KEY (`id_vaga`),
  KEY `id_equipamento` (`id_equipamento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

ALTER TABLE `andares`
  ADD CONSTRAINT `andares_ibfk_1` FOREIGN KEY (`id_estabelecimento`) REFERENCES `estabelecimentos` (`id_estabelecimento`) ON DELETE CASCADE;

ALTER TABLE `elementos_mapa`
  ADD CONSTRAINT `fk_elementos_andar` FOREIGN KEY (`id_andar`) REFERENCES `andares` (`id_andar`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_elementos_setor` FOREIGN KEY (`id_setor`) REFERENCES `setores` (`id_setor`) ON DELETE SET NULL;

ALTER TABLE `equipamentos`
  ADD CONSTRAINT `equipamentos_ibfk_1` FOREIGN KEY (`id_setor`) REFERENCES `setores` (`id_setor`) ON DELETE CASCADE;

ALTER TABLE `historico_ocupacao`
  ADD CONSTRAINT `historico_ocupacao_ibfk_1` FOREIGN KEY (`id_vaga`) REFERENCES `vagas` (`id_vaga`) ON DELETE CASCADE;

ALTER TABLE `setores`
  ADD CONSTRAINT `fk_setores_andares` FOREIGN KEY (`id_andar`) REFERENCES `andares` (`id_andar`) ON DELETE CASCADE;

ALTER TABLE `usuario_estabelecimento`
  ADD CONSTRAINT `usuario_estabelecimento_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE,
  ADD CONSTRAINT `usuario_estabelecimento_ibfk_2` FOREIGN KEY (`id_estabelecimento`) REFERENCES `estabelecimentos` (`id_estabelecimento`) ON DELETE CASCADE;

ALTER TABLE `vagas`
  ADD CONSTRAINT `vagas_ibfk_1` FOREIGN KEY (`id_equipamento`) REFERENCES `equipamentos` (`id_equipamento`) ON DELETE CASCADE;

COMMIT;"""

COMANDOS_DEPENDENCIAS = """# 1. Instalar dependências do Backend (Python / FastAPI / MySQL)
pip install fastapi uvicorn aiomysql pydantic cryptography

# 2. Entrar na pasta do Frontend e instalar pacotes (Vue 3 / Vite / Ícones)
cd frontend
npm install
npm install @tabler/icons-vue vue-router
cd .."""

COMANDOS_EXECUCAO = """# Terminal 1 (Rodar o Backend FastAPI):
cd backend
python -m uvicorn main:app --reload

# Terminal 2 (Rodar o Frontend Vue + Vite):
cd frontend
npm run dev"""


# ==============================================================================
# INTERFACE GRÁFICA (TKINTER)
# ==============================================================================


class TutorialVagaCertaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vaga Certa — Assistente de Configuração e Instalação")
        self.geometry("760x600")
        self.minsize(680, 540)
        self.configure(bg="#0f172a")

        # Paleta de cores
        self.cor_fundo = "#0f172a"
        self.cor_card = "#1e293b"
        self.cor_borda = "#334155"
        self.cor_texto = "#f8fafc"
        self.cor_subtexto = "#94a3b8"
        self.cor_azul = "#2563eb"
        self.cor_azul_hover = "#1d4ed8"
        self.cor_verde = "#16a34a"
        self.cor_codigo_bg = "#090d16"

        self.tela_atual = 1

        # Container principal de conteúdo
        self.container_conteudo = tk.Frame(self, bg=self.cor_fundo)
        self.container_conteudo.pack(fill="both", expand=True, padx=24, pady=(20, 10))

        # Rodapé fixo para os botões Anterior / Próximo / Concluir
        self.rodape = tk.Frame(
            self,
            bg=self.cor_card,
            height=64,
            highlightthickness=1,
            highlightbackground=self.cor_borda,
        )
        self.rodape.pack(fill="x", side="bottom")
        self.rodape.pack_propagate(False)

        self.btn_anterior = tk.Button(
            self.rodape,
            text="⬅  Anterior",
            font=("Segoe UI", 10, "bold"),
            bg="#334155",
            fg=self.cor_texto,
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.ir_tela_anterior,
        )

        self.lbl_passo = tk.Label(
            self.rodape,
            text="Tela 1 de 3",
            font=("Segoe UI", 10, "bold"),
            bg=self.cor_card,
            fg=self.cor_subtexto,
        )
        self.lbl_passo.place(relx=0.5, rely=0.5, anchor="center")

        self.btn_proximo = tk.Button(
            self.rodape,
            text="Próximo  ➡",
            font=("Segoe UI", 10, "bold"),
            bg=self.cor_azul,
            fg="#ffffff",
            activebackground=self.cor_azul_hover,
            activeforeground="#ffffff",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.ir_proxima_tela,
        )

        self.renderizar_tela()

    def limpar_conteudo(self):
        for widget in self.container_conteudo.winfo_children():
            widget.destroy()

    def copiar_para_clipboard(self, texto, botao, texto_original):
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.update()
        botao.configure(
            text="✔  Copiado para a área de transferência!", bg=self.cor_verde
        )
        self.after(
            2200,
            lambda: (
                botao.exists()
                if hasattr(botao, "exists")
                else self._restaurar_botao(botao, texto_original)
            ),
        )

    def _restaurar_botao(self, botao, texto_original):
        if botao.winfo_exists():
            botao.configure(text=texto_original, bg=self.cor_azul)

    def criar_caixa_codigo(self, parent, codigo, altura=10):
        frame_cod = tk.Frame(
            parent,
            bg=self.cor_codigo_bg,
            highlightthickness=1,
            highlightbackground=self.cor_borda,
        )
        frame_cod.pack(fill="both", expand=True, pady=(4, 6))

        scrollbar = ttk.Scrollbar(frame_cod, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        txt = tk.Text(
            frame_cod,
            height=altura,
            bg=self.cor_codigo_bg,
            fg="#38bdf8",
            insertbackground="#ffffff",
            font=("Consolas", 9),
            bd=0,
            padx=10,
            pady=8,
            wrap="none",
            yscrollcommand=scrollbar.set,
        )
        txt.insert("1.0", codigo)
        txt.configure(state="disabled")
        txt.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=txt.yview)

    def atualizar_botoes_rodape(self):
        self.lbl_passo.configure(text=f"Passo {self.tela_atual} de 3")

        # Botão Anterior (Canto Inferior Esquerdo - apenas nas telas 2 e 3)
        if self.tela_atual > 1:
            self.btn_anterior.pack(side="left", padx=20, pady=12)
        else:
            self.btn_anterior.pack_forget()

        # Botão Próximo / Concluir (Canto Inferior Direito)
        self.btn_proximo.pack_forget()
        if self.tela_atual < 3:
            self.btn_proximo.configure(
                text="Próximo  ➡",
                bg=self.cor_azul,
                activebackground=self.cor_azul_hover,
                command=self.ir_proxima_tela,
            )
        else:
            self.btn_proximo.configure(
                text="Concluir  ✔",
                bg=self.cor_verde,
                activebackground="#15803d",
                command=self.destroy,
            )
        self.btn_proximo.pack(side="right", padx=20, pady=12)

    def ir_proxima_tela(self):
        if self.tela_atual < 3:
            self.tela_atual += 1
            self.renderizar_tela()

    def ir_tela_anterior(self):
        if self.tela_atual > 1:
            self.tela_atual -= 1
            self.renderizar_tela()

    def renderizar_tela(self):
        self.limpar_conteudo()
        self.atualizar_botoes_rodape()

        if self.tela_atual == 1:
            self.montar_tela_1()
        elif self.tela_atual == 2:
            self.montar_tela_2()
        elif self.tela_atual == 3:
            self.montar_tela_3()

    # --------------------------------------------------------------------------
    # TELA 1: DOWNLOADS EXTERNOS (PYTHON, NODE.JS)
    # --------------------------------------------------------------------------
    def montar_tela_1(self):
        tk.Label(
            self.container_conteudo,
            text="1. Ferramentas Essenciais (Downloads Externos)",
            font=("Segoe UI", 16, "bold"),
            bg=self.cor_fundo,
            fg=self.cor_texto,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            self.container_conteudo,
            text="Antes de iniciar o projeto Vaga Certa, instale as ferramentas abaixo clicando nos links:",
            font=("Segoe UI", 10),
            bg=self.cor_fundo,
            fg=self.cor_subtexto,
            anchor="w",
        ).pack(fill="x", pady=(4, 16))

        ferramentas = [
            (
                "Python (3.10 ou superior)",
                "Necessário para rodar a API Backend (FastAPI). IMPORTANTE: Marque a opção 'Add Python to PATH' no instalador!",
                "https://www.python.org/downloads/",
            ),
            (
                "Node.js (Versão LTS recomendada)",
                "Necessário para instalar os pacotes e rodar o Frontend (Vue 3 + Vite).",
                "https://nodejs.org/pt-br",
            ),
        ]

        for titulo, desc, url in ferramentas:
            card = tk.Frame(
                self.container_conteudo,
                bg=self.cor_card,
                padx=14,
                pady=12,
                highlightthickness=1,
                highlightbackground=self.cor_borda,
            )
            card.pack(fill="x", pady=6)

            topo_card = tk.Frame(card, bg=self.cor_card)
            topo_card.pack(fill="x")

            tk.Label(
                topo_card,
                text=titulo,
                font=("Segoe UI", 11, "bold"),
                bg=self.cor_card,
                fg="#ffffff",
            ).pack(side="left")

            btn_link = tk.Button(
                topo_card,
                text="🌐 Abrir Site de Download",
                font=("Segoe UI", 9, "bold"),
                bg=self.cor_azul,
                fg="#ffffff",
                activebackground=self.cor_azul_hover,
                activeforeground="#ffffff",
                bd=0,
                padx=12,
                pady=4,
                cursor="hand2",
                command=lambda link=url: webbrowser.open(link),
            )
            btn_link.pack(side="right")

            tk.Label(
                card,
                text=desc,
                font=("Segoe UI", 9),
                bg=self.cor_card,
                fg=self.cor_subtexto,
                anchor="w",
                justify="left",
                wraplength=660,
            ).pack(fill="x", pady=(6, 0))

    # --------------------------------------------------------------------------
    # TELA 2: XAMPP + BANCO DE DADOS SQL (COM BOTÃO DE COPIAR)
    # --------------------------------------------------------------------------
    def montar_tela_2(self):
        tk.Label(
            self.container_conteudo,
            text="2. Banco de Dados MySQL (XAMPP e phpMyAdmin)",
            font=("Segoe UI", 16, "bold"),
            bg=self.cor_fundo,
            fg=self.cor_texto,
            anchor="w",
        ).pack(fill="x")

        # Card do Mini Tutorial do XAMPP
        card_xampp = tk.Frame(
            self.container_conteudo,
            bg=self.cor_card,
            padx=14,
            pady=10,
            highlightthickness=1,
            highlightbackground=self.cor_borda,
        )
        card_xampp.pack(fill="x", pady=(10, 12))

        passos_texto = (
            "Passo a passo do XAMPP:\n"
            "1. Baixe e instale o XAMPP clicando no botão ao lado.\n"
            "2. Abra o XAMPP Control Panel e clique em 'Start' nos módulos Apache e MySQL.\n"
            "3. Abra o phpMyAdmin no navegador (http://localhost/phpmyadmin)."
        )
        tk.Label(
            card_xampp,
            text=passos_texto,
            font=("Segoe UI", 9),
            bg=self.cor_card,
            fg=self.cor_texto,
            justify="left",
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        frame_links_xampp = tk.Frame(card_xampp, bg=self.cor_card)
        frame_links_xampp.pack(side="right", padx=(10, 0))

        tk.Button(
            frame_links_xampp,
            text="🌐 Baixar XAMPP",
            font=("Segoe UI", 9, "bold"),
            bg=self.cor_azul,
            fg="#ffffff",
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            command=lambda: webbrowser.open(
                "https://www.apachefriends.org/pt_br/index.html"
            ),
        ).pack(fill="x", pady=(0, 6))

        tk.Button(
            frame_links_xampp,
            text="🔗 Abrir phpMyAdmin",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="#ffffff",
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            command=lambda: webbrowser.open("http://localhost/phpmyadmin"),
        ).pack(fill="x")

        # Informação acima do botão de copiar
        tk.Label(
            self.container_conteudo,
            text="ℹ No phpMyAdmin, clique na aba 'SQL' no topo da página, copie o código no botão abaixo, cole na área de texto do SQL e clique em 'Executar':",
            font=("Segoe UI", 9, "bold"),
            bg=self.cor_fundo,
            fg="#fbbf24",
            anchor="w",
            justify="left",
            wraplength=700,
        ).pack(fill="x", pady=(2, 6))

        # Botão de copiar acima do código SQL
        txt_btn_sql = "📋  Copiar Código SQL Completo"
        btn_copiar_sql = tk.Button(
            self.container_conteudo,
            text=txt_btn_sql,
            font=("Segoe UI", 10, "bold"),
            bg=self.cor_azul,
            fg="#ffffff",
            activebackground=self.cor_azul_hover,
            activeforeground="#ffffff",
            bd=0,
            padx=16,
            pady=7,
            cursor="hand2",
        )
        btn_copiar_sql.configure(
            command=lambda: self.copiar_para_clipboard(
                SQL_SCRIPT, btn_copiar_sql, txt_btn_sql
            )
        )
        btn_copiar_sql.pack(anchor="w", pady=(0, 4))

        # Caixa com o código SQL
        self.criar_caixa_codigo(self.container_conteudo, SQL_SCRIPT, altura=12)

    # --------------------------------------------------------------------------
    # TELA 3: INSTALAÇÃO DE DEPENDÊNCIAS NO TERMINAL
    # --------------------------------------------------------------------------
    def montar_tela_3(self):
        tk.Label(
            self.container_conteudo,
            text="3. Instalação das Dependências do Projeto",
            font=("Segoe UI", 16, "bold"),
            bg=self.cor_fundo,
            fg=self.cor_texto,
            anchor="w",
        ).pack(fill="x")

        # Informação acima do botão de copiar
        tk.Label(
            self.container_conteudo,
            text="ℹ Abra o terminal (PowerShell ou CMD) dentro da pasta raiz do projeto (vaga_certa), clique no botão abaixo para copiar os comandos, cole no terminal e pressione Enter:",
            font=("Segoe UI", 9, "bold"),
            bg=self.cor_fundo,
            fg="#fbbf24",
            anchor="w",
            justify="left",
            wraplength=700,
        ).pack(fill="x", pady=(10, 6))

        # Botão de copiar em cima do código
        txt_btn_dep = "📋  Copiar Comandos de Instalação"
        btn_copiar_dep = tk.Button(
            self.container_conteudo,
            text=txt_btn_dep,
            font=("Segoe UI", 10, "bold"),
            bg=self.cor_azul,
            fg="#ffffff",
            activebackground=self.cor_azul_hover,
            activeforeground="#ffffff",
            bd=0,
            padx=16,
            pady=7,
            cursor="hand2",
        )
        btn_copiar_dep.configure(
            command=lambda: self.copiar_para_clipboard(
                COMANDOS_DEPENDENCIAS, btn_copiar_dep, txt_btn_dep
            )
        )
        btn_copiar_dep.pack(anchor="w", pady=(0, 4))

        # Caixa de código das dependências
        self.criar_caixa_codigo(
            self.container_conteudo, COMANDOS_DEPENDENCIAS, altura=7
        )

        # Seção bônus: Como iniciar os servidores após instalar
        tk.Label(
            self.container_conteudo,
            text="Como iniciar o projeto após instalar tudo (em 2 terminais):",
            font=("Segoe UI", 10, "bold"),
            bg=self.cor_fundo,
            fg=self.cor_texto,
            anchor="w",
        ).pack(fill="x", pady=(10, 4))

        txt_btn_run = "📋  Copiar Comandos para Rodar o Projeto"
        btn_copiar_run = tk.Button(
            self.container_conteudo,
            text=txt_btn_run,
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="#ffffff",
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
        )
        btn_copiar_run.configure(
            command=lambda: self.copiar_para_clipboard(
                COMANDOS_EXECUCAO, btn_copiar_run, txt_btn_run
            )
        )
        btn_copiar_run.pack(anchor="w", pady=(0, 4))

        self.criar_caixa_codigo(self.container_conteudo, COMANDOS_EXECUCAO, altura=6)


if __name__ == "__main__":
    app = TutorialVagaCertaApp()
    app.mainloop()
