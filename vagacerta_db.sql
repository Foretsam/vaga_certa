SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;


CREATE TABLE `andares` (
  `id_andar` int(11) NOT NULL,
  `id_estabelecimento` int(11) NOT NULL,
  `nome_andar` varchar(25) NOT NULL,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `equipamentos` (
  `id_equipamento` int(11) NOT NULL,
  `id_setor` int(11) NOT NULL,
  `codigo_mac` varchar(17) NOT NULL,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `estabelecimentos` (
  `id_estabelecimento` int(11) NOT NULL,
  `nome` varchar(50) NOT NULL,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `historico_ocupacao` (
  `id_historico` int(11) NOT NULL,
  `id_vaga` int(11) NOT NULL,
  `data_entrada` datetime NOT NULL DEFAULT current_timestamp(),
  `data_saida` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `setores` (
  `id_setor` int(11) NOT NULL,
  `id_andar` int(11) NOT NULL,
  `nome_setor` varchar(25) NOT NULL,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL,
  `nome` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `senha_hash` varchar(255) NOT NULL,
  `nivel_acesso` enum('admin_dev','admin_estabelecimento') NOT NULL,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `usuario_estabelecimento` (
  `id_usuario` int(11) NOT NULL,
  `id_estabelecimento` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `vagas` (
  `id_vaga` int(11) NOT NULL,
  `id_equipamento` int(11) NOT NULL,
  `identificador` varchar(10) NOT NULL,
  `livre_para_estacionar` tinyint(1) DEFAULT 1,
  `inativo` tinyint(1) DEFAULT 0,
  `data_cadastro` datetime DEFAULT current_timestamp(),
  `data_ultima_modificacao` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `data_inativacao` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


ALTER TABLE `andares`
  ADD PRIMARY KEY (`id_andar`),
  ADD KEY `id_estabelecimento` (`id_estabelecimento`);

ALTER TABLE `equipamentos`
  ADD PRIMARY KEY (`id_equipamento`),
  ADD UNIQUE KEY `codigo_mac` (`codigo_mac`),
  ADD KEY `id_setor` (`id_setor`);

ALTER TABLE `estabelecimentos`
  ADD PRIMARY KEY (`id_estabelecimento`),
  ADD UNIQUE KEY `nome` (`nome`);

ALTER TABLE `historico_ocupacao`
  ADD PRIMARY KEY (`id_historico`),
  ADD KEY `id_vaga` (`id_vaga`);

ALTER TABLE `setores`
  ADD PRIMARY KEY (`id_setor`),
  ADD KEY `fk_setores_andares` (`id_andar`);

ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `email` (`email`);

ALTER TABLE `usuario_estabelecimento`
  ADD PRIMARY KEY (`id_usuario`,`id_estabelecimento`),
  ADD KEY `id_estabelecimento` (`id_estabelecimento`);

ALTER TABLE `vagas`
  ADD PRIMARY KEY (`id_vaga`),
  ADD KEY `id_equipamento` (`id_equipamento`);


ALTER TABLE `andares`
  MODIFY `id_andar` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `equipamentos`
  MODIFY `id_equipamento` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `estabelecimentos`
  MODIFY `id_estabelecimento` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `historico_ocupacao`
  MODIFY `id_historico` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `setores`
  MODIFY `id_setor` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `usuarios`
  MODIFY `id_usuario` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `vagas`
  MODIFY `id_vaga` int(11) NOT NULL AUTO_INCREMENT;


ALTER TABLE `andares`
  ADD CONSTRAINT `andares_ibfk_1` FOREIGN KEY (`id_estabelecimento`) REFERENCES `estabelecimentos` (`id_estabelecimento`) ON DELETE CASCADE;

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

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
