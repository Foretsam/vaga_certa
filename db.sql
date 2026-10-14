-- Criação do Banco de Dados
CREATE DATABASE IF NOT EXISTS vagacerta_db;
USE vagacerta_db;

-- Tabela de Estabelecimentos
CREATE TABLE estabelecimentos (
    id_estabelecimento INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    inativo BOOLEAN DEFAULT FALSE,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_ultima_modificacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_inativacao DATETIME DEFAULT NULL
);

-- Tabela de Usuários (Clientes não precisam logar)
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
-- Acesso para devenvolvedor e para donos/gerentes
    nivel_acesso ENUM('admin_dev', 'admin_estabelecimento') NOT NULL, 
    inativo BOOLEAN DEFAULT FALSE,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_ultima_modificacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_inativacao DATETIME DEFAULT NULL
);

-- Tabela de Relacionamento (Muitos-para-Muitos entre Usuários e Estabelecimentos; 
-- link entre usuários e estabelecimentos)
CREATE TABLE usuario_estabelecimento (
    id_usuario INT NOT NULL,
    id_estabelecimento INT NOT NULL,
    PRIMARY KEY (id_usuario, id_estabelecimento),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_estabelecimento) REFERENCES estabelecimentos(id_estabelecimento) ON DELETE CASCADE
);

-- Tabela de Setores
CREATE TABLE setores (
    id_setor INT AUTO_INCREMENT PRIMARY KEY,
    id_estabelecimento INT NOT NULL,
    nome_setor VARCHAR(25) NOT NULL,
    inativo BOOLEAN DEFAULT FALSE,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_ultima_modificacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_inativacao DATETIME DEFAULT NULL,
    FOREIGN KEY (id_estabelecimento) REFERENCES estabelecimentos(id_estabelecimento) ON DELETE CASCADE
);

-- Tabela de Equipamentos
CREATE TABLE equipamentos (
    id_equipamento INT AUTO_INCREMENT PRIMARY KEY,
    id_setor INT NOT NULL,
    codigo_mac VARCHAR(17) NOT NULL UNIQUE, -- Endereço MAC de cada equipamento
    inativo BOOLEAN DEFAULT FALSE,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_ultima_modificacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_inativacao DATETIME DEFAULT NULL,
    FOREIGN KEY (id_setor) REFERENCES setores(id_setor) ON DELETE CASCADE
);

-- Tabela de Vagas
CREATE TABLE vagas (
    id_vaga INT AUTO_INCREMENT PRIMARY KEY,
    id_equipamento INT NOT NULL,
    identificador VARCHAR(10) NOT NULL,
    livre_para_estacionar BOOLEAN DEFAULT TRUE,
    inativo BOOLEAN DEFAULT FALSE,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_ultima_modificacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_inativacao DATETIME DEFAULT NULL,
    FOREIGN KEY (id_equipamento) REFERENCES equipamentos(id_equipamento) ON DELETE CASCADE
);

-- Tabela de Histórico de Ocupação (Para os Relatórios de BI)
CREATE TABLE historico_ocupacao (
    id_historico INT AUTO_INCREMENT PRIMARY KEY,
    id_vaga INT NOT NULL,
    data_entrada DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_saida DATETIME DEFAULT NULL,
    FOREIGN KEY (id_vaga) REFERENCES vagas(id_vaga) ON DELETE CASCADE
);