import os

# ==========================================================
# CONFIGURAÇÕES DE FILTRO (BLOQUEIOS)
# ==========================================================
# Arquivos com estas extensões serão IGNORADOS
EXTENSOES_INVALIDAS = {
    ".gitattributes",
    ".gitignore",
    ".md",
    ".json",
    ".txt",
    ".png",
    ".svg",
}

# Estas pastas (e tudo dentro delas) serão IGNORADAS
PASTAS_INVALIDAS = {".vscode", "node_modules", "public"}
# ==========================================================


def e_arquivo_texto(extensao):
    """
    Tenta adivinhar se é texto legível baseado na extensão.
    Evita que arquivos binários não previstos quebrem a leitura.
    """
    extensoes_binarias_comuns = {
        ".zip",
        ".exe",
        ".dll",
        ".so",
        ".jpg",
        ".jpeg",
        ".gif",
        ".pdf",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".ico",
    }
    return extensao not in extensoes_binarias_comuns


def obter_extensao(nome_arquivo):
    if nome_arquivo.startswith(".") and nome_arquivo.count(".") == 1:
        return nome_arquivo
    return os.path.splitext(nome_arquivo)[1].lower()


def filtrar_diretorio(caminho_base):
    estrutura_valida = {}

    for root, dirs, files in os.walk(caminho_base):
        # Modifica a lista 'dirs' no próprio loop para IGNORAR as pastas inválidas
        dirs[:] = [d for d in dirs if d not in PASTAS_INVALIDAS]

        arquivos_validos = []
        for f in files:
            ext = obter_extensao(f)
            # O arquivo é válido se a extensão NÃO estiver na lista de inválidas
            if ext not in EXTENSOES_INVALIDAS:
                arquivos_validos.append(f)

        # Só adiciona o diretório ao mapa se houver arquivos válidos nele
        if arquivos_validos:
            estrutura_valida[root] = arquivos_validos

    return estrutura_valida


def mapear_e_consolidar(caminho_base, arquivo_saida):

    estrutura = filtrar_diretorio(caminho_base)

    if not estrutura:
        print("⚠️ Nenhum arquivo válido encontrado (tudo foi bloqueado pelos filtros).")
        return

    with open(arquivo_saida, "w", encoding="utf-8") as file_out:

        # ==========================================================
        # 1. GERAÇÃO DO MAPA DE PASTAS E ARQUIVOS
        # ==========================================================
        file_out.write(
            "=================================================================\n"
        )
        file_out.write("1. MAPA DO DIRETÓRIO (Ignorando arquivos/pastas bloqueados)\n")
        file_out.write(
            "=================================================================\n\n"
        )

        arquivos_para_conteudo = []

        for root in sorted(estrutura.keys()):
            caminho_relativo_root = os.path.relpath(root, caminho_base)
            # Trata a raiz para não somar indentação extra
            if caminho_relativo_root == ".":
                nivel = 0
                nome_pasta = os.path.basename(caminho_base)
            else:
                nivel = caminho_relativo_root.count(os.sep) + 1
                nome_pasta = os.path.basename(root)

            indentacao = "    " * nivel
            file_out.write(f"{indentacao}📂 {nome_pasta}/\n")

            indentacao_sub = "    " * (nivel + 1)
            for f in sorted(estrutura[root]):
                file_out.write(f"{indentacao_sub}📄 {f}\n")

                ext = obter_extensao(f)
                if e_arquivo_texto(ext):
                    arquivos_para_conteudo.append(os.path.join(root, f))

        file_out.write("\n\n")

        # ==========================================================
        # 2. CONTEÚDO DOS ARQUIVOS CONSOLIDADOS
        # ==========================================================
        file_out.write(
            "=================================================================\n"
        )
        file_out.write("2. CONTEÚDO DOS ARQUIVOS\n")
        file_out.write(
            "=================================================================\n\n"
        )

        for caminho_arquivo in arquivos_para_conteudo:
            caminho_relativo = os.path.relpath(caminho_arquivo, caminho_base)

            file_out.write(
                f"// ==================================================================\n"
            )
            file_out.write(f"// 🚀 INÍCIO DO ARQUIVO: {caminho_relativo}\n")
            file_out.write(
                f"// ==================================================================\n\n"
            )

            try:
                # Tenta abrir lendo os primeiros bytes para dupla checagem contra binários
                with open(caminho_arquivo, "tr") as check_file:
                    check_file.read(1024)

                with open(
                    caminho_arquivo, "r", encoding="utf-8", errors="replace"
                ) as f:
                    conteudo = f.read()
                    file_out.write(conteudo)
            except UnicodeDecodeError:
                file_out.write(
                    f"// [Arquivo binário ignorado pelo leitor de segurança]\n"
                )
            except Exception as e:
                file_out.write(f"// [Erro ao tentar ler o arquivo: {e}]\n")

            file_out.write(f"\n\n// 🏁 FIM DO ARQUIVO: {caminho_relativo}\n")
            file_out.write(
                f"// ------------------------------------------------------------------\n\n\n"
            )


if __name__ == "__main__":
    caminho_usuario = input("Digite o caminho (PATH) do diretório: ").strip()
    caminho_usuario = caminho_usuario.strip('"').strip("'")

    if os.path.isdir(caminho_usuario):
        nome_arquivo_saida = "resultado_mapa_e_codigos.txt"
        print(f"\nMapeando o diretório e bloqueando itens indesejados...\n")

        mapear_e_consolidar(caminho_usuario, nome_arquivo_saida)

        print(f"✅ Processo concluído! Resultado salvo em '{nome_arquivo_saida}'")
    else:
        print(
            "❌ O caminho informado não é um diretório válido. Verifique e tente novamente."
        )
