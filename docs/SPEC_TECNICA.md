# Especificação técnica — Etapa 1

> Complementa `docs/Prd.md`. O PRD diz **o quê**; este arquivo diz **como**.
> Em conflito, o PRD vence e este arquivo é corrigido.

## 1. Stack

| Item | Escolha | Observação |
|---|---|---|
| Linguagem | Python 3.12 (`requires-python = ">=3.12,<3.13"`) | `tomllib` nativo para perfis. |
| Empacotamento | `pyproject.toml` + hatchling, layout `src/` | Instalação editável: `uv pip install -e ".[dev]"`. |
| Lint/format | ruff (`E,W,F,I,B,UP,SIM,RUF,PTH`), linha 100 | `RUF001-003` desligados: º, °, –, § são do domínio. |
| Testes | pytest (+ pytest-cov) | Marcadores: `aceite`, `regressao`, `rede`. |
| HTML | `beautifulsoup4` + `lxml` | `email` (stdlib) para `.mht`. |
| PDF | `pdfplumber` | Recorte por coluna, mapa de fontes por documento. |
| HTTP | `requests` | Só em `fontes/html.py`, com cache (RF02). |
| CI | GitHub Actions: ruff + pytest em 3.12 (Ubuntu e Windows) | Windows cobre RNF02. |

## 2. Módulos (`src/vademecum/`)

Segue PRD §5.2. Dependências apontam sempre para a direita do pipeline → nunca para trás.

| Módulo | Entrada → Saída | Depende de |
|---|---|---|
| `modelo.py` | dataclasses `LinhaFonte`, `No`, `Nota`, `Local`, `Norma`, `Base`, `Relatorio`; `chave_ordenacao()`; `para_json()` | — |
| `perfil.py` | `carregar_perfil(nome) -> Perfil` (merge `padrao.toml` + específico) | `modelo` |
| `fontes/html.py` | URL/`.htm`/`.mht` → `list[LinhaFonte]` + metadados | `modelo` |
| `fontes/pdf.py` | `.pdf` → `list[LinhaFonte]` | `modelo`, `perfil` |
| `segmentador.py` | `list[LinhaFonte]` → `list[DocumentoFonte]` | `modelo`, `perfil` |
| `normalizador.py` | linhas → linhas normalizadas (ordinal, travessão, junção) | `modelo`, `perfil` |
| `notas.py` | texto → `(texto_limpo, list[Nota])` | `modelo`, `perfil` |
| `parser.py` | linhas → árvore `list[No]` (máquina de estados) | `modelo`, `notas`, `perfil` |
| `vigencia.py` | árvore → árvore vigente + descartes no relatório (D1) | `modelo` |
| `validador.py` | `Base` → avisos V1–V7 no relatório | `modelo`, `perfil` |
| `recorte.py` | `Base` + expressão → `Base` recortada (§9) | `modelo` |
| `cli.py` | argparse → orquestra o pipeline | todos |

## 3. Contratos

- `LinhaFonte` é exatamente o do PRD §5.1 (`frozen=True, slots=True`).
- Funções de etapa são **puras**: recebem dados + `Perfil` + `Relatorio` e devolvem dados novos. Só `cli.py` e `fontes/*` fazem I/O.
- `Relatorio` acumula entradas tipadas: `descarte`, `aviso`, `nao_classificada`, `nota_outra`, `faixa_revogada` — cada uma com `origem`.
- Erros de entrada (arquivo inexistente, PDF sem texto — RF06) levantam `ErroFonte(Exception)` com mensagem para o usuário; a CLI converte em código de saída 2.
- Chave de ordenação (PRD §9.2): `(numero: int, sufixo: tuple[str, ...])`; tupla vazia ordena antes de qualquer letra naturalmente.

## 4. Serialização (RNF03)

- `json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)` + `\n` final, gravado com `encoding="utf-8"` e `newline="\n"`.
- `capturado_em` e `sha256` ficam só em `norma`/`metadados`, nunca em `artigos`.
- Campos opcionais ausentes são serializados como `null` (esquema estável), listas vazias como `[]`.

## 5. Testes

| Tipo | Local | Regra |
|---|---|---|
| Unidade | `tests/unit/test_<modulo>.py` | Um arquivo por módulo; regex com linhas reais. |
| Aceite | `tests/aceite/test_a<NN>_<nome>.py` | Um teste por caso A1–A14, marcador `aceite`. |
| Regressão | `tests/regressao/` + `tests/fixtures/snapshots/` | Marcador `regressao`; regravar snapshot exige registro em `.claude/processo/REVISAO.md`. |
| Rede | qualquer | Marcador `rede`; fora do CI padrão (`-m "not rede"`). |

## 6. Decisões técnicas em aberto

| # | Questão | Proposta |
|---|---|---|
| T1 | Fontes brutas completas (`.mht` do CP, PDF) entram no repositório? A1 e o snapshot precisam delas. | Versionar em `tests/fixtures/` só se o tamanho for aceitável (texto legal é público); senão, teste `regressao` pula quando o arquivo não existe. |
| T2 | Relatório: Markdown, JSON ou ambos? PRD RF17 aceita qualquer um; P4 pede JSON estruturado. | Gerar ambos: `base.relatorio.json` (consumo pela Etapa 2) e `base.relatorio.md` (leitura). |
