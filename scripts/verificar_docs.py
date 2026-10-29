"""
Varredura da documentação e do código contra as regras de manutenção do `docs/README.md`.

Nos `.md` do README raiz, de `docs/` e do `.claude/CLAUDE.md` (quando existe), confere:
    - tetos de linhas por tipo de documento;
    - `arquivo:linha` em documento perene (só spec e relatório podem citar linha);
    - links relativos que apontam para arquivo inexistente.

Nos demais arquivos do repositório (versionados, ou novos e fora do `.gitignore`), confere:
    - ADR citado que não existe em `docs/decisoes/`;
    - seção ou item de documento do projeto citado por número, que se renumera sem ninguém notar.

Nos docs, ADR sem link pode ser de um repositório relacionado; o link quebrado já é achado.

Os "Untracked tolerados" de `docs/README.md § Parâmetros do processo` ficam de fora, e as
exceções de teto declaradas em `§ Regras de manutenção` não têm teto. Os dois são lidos de lá,
que é a fonte única: este script não muda de um projeto para outro.

Uso, na raiz do repositório:
    python scripts/verificar_docs.py

Sai com 0 sem achado e com 1 havendo algum, um por linha no formato `arquivo:linha: mensagem`.
"""

import pathlib
import re
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Primeiro padrão que casa vence; documento sem teto não entra na tabela.
TETOS = [
    ("README.md", 50),
    (".claude/CLAUDE.md", 40),
    ("docs/README.md", 250),
    ("docs/PADRAO_OURO.md", 150),
    ("docs/PENDENCIAS.md", 100),
    ("docs/decisoes/ADR-*.md", 80),
    ("docs/negocio/*.md", 150),
    ("docs/processo/specs/*.md", 200),
]

# Artefatos efêmeros, os únicos que podem citar `arquivo:linha`.
EFEMEROS = ("docs/processo/specs/",)

RE_ARQUIVO_LINHA = re.compile(r"\b[\w./-]+\.(?:py|yml|yaml|md|ini|cfg|txt|sql|json|toml):\d+")
RE_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
RE_CERCA = re.compile(r"^\s*(```|~~~)")
RE_CODIGO = re.compile(r"`([^`]+)`")
RE_EXCECAO = re.compile(r"Exceção declarada:(.*?)(?=^\s*\d+\. |\Z)", re.DOTALL | re.MULTILINE)
RE_ADR = re.compile(r"\bADR-(\d{3})\b")

# Só a citação ancorada num documento do projeto: seção de guia externo tem numeração estável.
RE_SECAO_POR_NUMERO = re.compile(
    r"(?:PADRAO_OURO|PENDENCIAS|README|ADR-\d{3}|\w+\.md)\W{0,3}§\s*\d"
)
RE_ITEM_POR_NUMERO = re.compile(
    r"(?:PENDENCIAS|ADR-\d{3})\W{0,3}item\s+\d|\bitem\s+\d+\s+d[aeo]s?\s+PENDENCIAS"
)


def ler_parametros():
    """Devolve os untracked tolerados e as exceções de teto declarados no `docs/README.md`."""
    readme = RAIZ / "docs" / "README.md"
    texto = readme.read_text(encoding="utf-8") if readme.is_file() else ""

    ignorados = []
    for linha in texto.splitlines():
        if linha.startswith("| Untracked tolerados |"):
            ignorados = [c for c in RE_CODIGO.findall(linha) if "{{" not in c]

    # A exceção é escrita relativa a `docs/` (`negocio/x.md`) ou à raiz (`docs/negocio/x.md`).
    excecoes = set()
    for trecho in RE_EXCECAO.findall(texto):
        for caminho in RE_CODIGO.findall(trecho):
            excecoes.update({caminho, f"docs/{caminho}"})
    return tuple(ignorados), excecoes


def adrs_existentes():
    """Números dos ADRs em `docs/decisoes/`; `None` quando o projeto não tem a pasta."""
    pasta = RAIZ / "docs" / "decisoes"
    if not pasta.is_dir():
        return None
    achados = (RE_ADR.match(arquivo.name) for arquivo in pasta.glob("ADR-*.md"))
    return {achado.group(1) for achado in achados if achado}


def listar_documentos(ignorados):
    candidatos = [RAIZ / "README.md", RAIZ / ".claude" / "CLAUDE.md"]
    candidatos += sorted((RAIZ / "docs").rglob("*.md"))
    for caminho in candidatos:
        relativo = caminho.relative_to(RAIZ).as_posix()
        if caminho.is_file() and not relativo.startswith(ignorados):
            yield caminho, relativo


def listar_codigo(ignorados):
    """Arquivos fora dos `.md` que o git versiona ou versionaria: os novos não ignorados entram."""
    try:
        saida = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=RAIZ, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    nomes = {nome for nome in saida.decode("utf-8").split("\0") if nome}
    return sorted(n for n in nomes if not n.endswith(".md") and not n.startswith(ignorados))


def teto_de(relativo, excecoes):
    if relativo in excecoes:
        return None
    for padrao, teto in TETOS:
        mesmo_nivel = relativo.count("/") == padrao.count("/")
        if mesmo_nivel and pathlib.PurePosixPath(relativo).match(padrao):
            return teto
    return None


def linhas_fora_de_cerca(linhas):
    """Numera as linhas de texto, pulando blocos de código, onde link e exemplo não valem."""
    dentro = False
    for numero, linha in enumerate(linhas, start=1):
        if RE_CERCA.match(linha):
            dentro = not dentro
            continue
        if not dentro:
            yield numero, linha


def verificar(caminho, relativo, excecoes):
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    achados = []

    teto = teto_de(relativo, excecoes)
    if teto is not None and len(linhas) > teto:
        achados.append(f"{relativo}:{len(linhas)}: {len(linhas)} linhas, teto de {teto}")

    efemero = relativo.startswith(EFEMEROS)
    for numero, linha in linhas_fora_de_cerca(linhas):
        if not efemero:
            for citacao in RE_ARQUIVO_LINHA.findall(linha):
                achados.append(f"{relativo}:{numero}: cita linha ({citacao})")
        for alvo in RE_LINK.findall(linha):
            if re.match(r"^[a-z][a-z0-9+.-]*:", alvo, re.IGNORECASE) or alvo.startswith("#"):
                continue
            destino = (caminho.parent / alvo.split("#", 1)[0]).resolve()
            if not destino.exists():
                achados.append(f"{relativo}:{numero}: link quebrado ({alvo})")
    return achados


def verificar_codigo(relativo, existentes):
    try:
        conteudo = (RAIZ / relativo).read_bytes()
    except OSError:
        return []
    if b"\0" in conteudo:  # binário
        return []

    achados = []
    for numero, linha in enumerate(conteudo.decode("utf-8", errors="ignore").splitlines(), start=1):
        if RE_SECAO_POR_NUMERO.search(linha) or RE_ITEM_POR_NUMERO.search(linha):
            achados.append(f"{relativo}:{numero}: cita seção ou item de documento por número")
        if existentes is not None:
            for adr in RE_ADR.findall(linha):
                if adr not in existentes:
                    achados.append(f"{relativo}:{numero}: ADR-{adr} não existe em docs/decisoes/")
    return achados


def main():
    ignorados, excecoes = ler_parametros()
    existentes = adrs_existentes()
    achados = []
    for caminho, relativo in listar_documentos(ignorados):
        achados += verificar(caminho, relativo, excecoes)
    for relativo in listar_codigo(ignorados):
        achados += verificar_codigo(relativo, existentes)
    for achado in achados:
        print(achado)
    print(f"{len(achados)} achado(s)." if achados else "Documentação sem achado.")
    return 1 if achados else 0


if __name__ == "__main__":
    sys.exit(main())
