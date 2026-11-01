-- ============================================================================
-- VAGA CERTA - SCHEMA OFICIAL DO BANCO DE DADOS (MySQL / MariaDB)
-- ============================================================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

-- Tabela de pavimentos/andares vinculados a um estabelecimento
CREATE TABLE `andares` (
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

-- Elementos estruturais da planta 2D (estradas, entradas, saídas, acessos e fundo de setor)
CREATE TABLE `elementos_mapa` (
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

-- Microcontroladores ESP32 vinculados aos setores
CREATE TABLE `equipamentos` (
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

-- Unidades de estacionamento cadastradas
CREATE TABLE `estabelecimentos` (
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

-- Registro histórico de entradas e saídas por vaga
CREATE TABLE `historico_ocupacao` (
  `id_historico` int(11) NOT NULL AUTO_INCREMENT,
  `id_vaga` int(11) NOT NULL,
  `data_entrada` datetime NOT NULL DEFAULT current_timestamp(),
  `data_saida` datetime DEFAULT NULL,
  PRIMARY KEY (`id_historico`),
  KEY `id_vaga` (`id_vaga`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Setores de cada andar (com prefixo e cor de identificação)
CREATE TABLE `setores` (
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

-- Usuários do sistema (Desenvolvedor, Gerente de Estabelecimento e Motorista)
CREATE TABLE `usuarios` (
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

-- Relação N:N entre usuários responsáveis e estabelecimentos
CREATE TABLE `usuario_estabelecimento` (
  `id_usuario` int(11) NOT NULL,
  `id_estabelecimento` int(11) NOT NULL,
  PRIMARY KEY (`id_usuario`,`id_estabelecimento`),
  KEY `id_estabelecimento` (`id_estabelecimento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Vagas monitoradas pelos equipamentos ESP32
CREATE TABLE `vagas` (
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

-- Chaves Estrangeiras com deleção em cascata
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

COMMIT;
