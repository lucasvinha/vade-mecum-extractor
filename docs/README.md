# vade-mecum-extractor — README técnico

Parser **genérico** em Python que recebe o texto bruto de uma norma (página HTML do Planalto,
`.mht` salvo ou PDF com texto) e produz uma **base estruturada**: artigo › parágrafo › inciso ›
alínea, com rubricas, penas e notas legislativas. Sobre essa base, um segundo comando gera o
**recorte** de artigos indicado pelo usuário, no mesmo formato. Quem usa é o operador, pela CLI
`python -m vademecum`; o contrato é o JSON da base, descrito em
[negocio/modelo-de-dados.md](negocio/modelo-de-dados.md).

Este projeto é a **Etapa 1 de 2**. A Etapa 2 (material de estudo: realces, quadros comparativos,
pontos de atenção) consome a base e está fora de escopo, mas a Etapa 1 preserva o que ela vai
precisar (notas, penas e o relatório de descartes). A Etapa 2 roda no Claude (Opus): o `recortar`
separa os artigos do edital, o operador sobe só os recortes JSON num projeto do Claude.ai, e o
modelo monta o vade mecum em HTML, convertido depois em PDF. O consumidor do JSON é, portanto, um
LLM. Os artigos de cada tópico do edital estão em
[claude/topicos-oj2026.json](../claude/topicos-oj2026.json) (schema `topicos-oj/1`).

- **Dentro:** leitura de HTML do Planalto (URL, `.htm`/`.html` ou `.mht`) e de PDF com texto,
  inclusive PDF com várias normas; normalização, parsing hierárquico, classificação de notas,
  filtro de vigência; exportação da base e do recorte em JSON; relatório de extração (avisos,
  descartes, inconsistências).
- **Fora:** OCR de PDF escaneado; material de estudo (Etapa 2); reconstrução de redações
  anteriores; resolução automática da data exata de leis alteradoras (ver PENDENCIAS); por ora, o
  extrator de questões de concurso (marco M9 em PENDENCIAS; contrato em
  [schema-questoes-json.md](schema-questoes-json.md)).

Ordem de leitura: este arquivo → o documento que o problema pede (tabela abaixo) → o código.
Em divergência com o código, **vale o código**, e o documento é corrigido.

| Pergunta | Onde |
|---|---|
| Como o código **deve** ser? | [PADRAO_OURO.md](PADRAO_OURO.md) |
| O que o sistema **decide**? (regras H*, P*, RF*) | [negocio/](negocio/) |
| **Por que** é assim? (D1–D4) | [decisoes/](decisoes/) |
| O que **falta** e o que está em curso? | [PENDENCIAS.md](PENDENCIAS.md) |
| **Como** se faz uma mudança? | [processo/README.md](processo/README.md) |

Regras e casos são citados pelo **ID** (`H15`, `RF07`, `A2`), nunca pelo número da seção.

## Arquitetura

Pipeline em módulos puros, cujas dependências só apontam para a direita: fonte (`fontes/`) →
`segmentador` → `normalizador` → `parser` (com `notas` e `perfil`) → `vigencia` → `validador` →
JSON; `recorte` lê a base pronta. O contrato central é `LinhaFonte`: tudo à direita dele
independe da fonte. Diferença entre normas mora em `perfis/*.toml`, nunca no parser (ADR-002).
O detalhe do pipeline e dos perfis está em
[negocio/pipeline-e-perfis.md](negocio/pipeline-e-perfis.md).

Saída determinística (RNF03) e nenhuma perda silenciosa (RNF04): ver
[PADRAO_OURO.md](PADRAO_OURO.md).

## Stack

| Item | Escolha | Observação |
|---|---|---|
| Linguagem | Python 3.12 (`requires-python = ">=3.12,<3.13"`) | `tomllib` nativo para perfis |
| Empacotamento | `pyproject.toml` + hatchling, layout `src/` | instalação editável: `uv pip install -e ".[dev]"` |
| Lint/format | ruff (`E,W,F,I,B,UP,SIM,RUF,PTH`), linha 100 | `RUF001-003` desligados: º, °, –, § são do domínio |
| Testes | pytest (+ pytest-cov) | marcadores `aceite`, `regressao`, `rede` |
| HTML | `beautifulsoup4` + `lxml` | `email` (stdlib) para `.mht` |
| PDF | `pdfplumber` | recorte por coluna, mapa de fontes por documento |
| HTTP | `requests` | só em `fontes/html.py`, com cache (RF02) |
| CI | GitHub Actions: ruff + pytest em 3.12 (Ubuntu e Windows) | Windows cobre RNF02 |

Versões em `pyproject.toml`. **Dependência nova só com registro nesta tabela.**

## Infra e deploy

Não há deploy: é uma CLI local. Roda em Windows sem WSL (RNF02): `pathlib` e `encoding="utf-8"`
explícito em toda leitura e escrita. Fontes brutas e saídas geradas ficam em `dados/`, fora do git.

## Configuração

Não há variável de ambiente. A configuração por norma é o perfil `.toml` em
`src/vademecum/perfis/`: `padrao.toml` cobre os casos comuns e o perfil específico sobrescreve só
as chaves que mudam (ver [negocio/pipeline-e-perfis.md](negocio/pipeline-e-perfis.md)).

## Testes e lint

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"   # ambiente
ruff check . && ruff format --check .                 # lint + formato
pytest                                                # a suíte
pytest -m aceite                                      # só os casos de aceite A1–A14
```

| Tipo | Local | Regra |
|---|---|---|
| Unidade | `tests/unit/test_<modulo>.py` | um arquivo por módulo; regex com linhas reais |
| Aceite | `tests/aceite/test_a<NN>_<nome>.py` | um teste por caso A1–A14, marcador `aceite` |
| Regressão | `tests/regressao/` + `tests/fixtures/snapshots/` | marcador `regressao`; regravar snapshot exige justificativa no corpo do commit |
| Rede | qualquer | marcador `rede`; fora do CI padrão (`-m "not rede"`) |

Config do ruff e dos marcadores em `pyproject.toml`; linha de 100 colunas.

```bash
python scripts/verificar_docs.py   # sai 0 sem achado; 1 com a lista em arquivo:linha: mensagem
```

`scripts/verificar_docs.py` confere os docs contra as Regras de manutenção (tetos, `arquivo:linha`
fora de spec, links relativos) e o código versionado (ADR citado que não existe, seção ou item
de documento citado por número). Vem do molde e é recopiado sem edição, por isso fica fora do
`ruff format`.

## Contratos

- `LinhaFonte` é `frozen=True, slots=True`, com os campos descritos em
  [negocio/pipeline-e-perfis.md](negocio/pipeline-e-perfis.md).
- Funções de etapa são **puras**: recebem dados + `Perfil` + `Relatorio` e devolvem dados novos.
  Só `cli.py` e `fontes/*` fazem I/O.
- `Relatorio` acumula entradas tipadas: `descarte`, `aviso`, `nao_classificada`, `nota_outra`,
  `faixa_revogada`, cada uma com `origem`.
- Erros de entrada (arquivo inexistente, PDF sem texto — RF06) levantam `ErroFonte(Exception)`,
  definido em `modelo.py`, com mensagem para o usuário; a CLI converte em código de saída 2.
- Chave de ordenação: `(numero: int, sufixo: tuple[str, ...])`; tupla vazia ordena antes de
  qualquer letra (ver [negocio/recorte-e-cli.md](negocio/recorte-e-cli.md)).
- Serialização (RNF03): `json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)` + `\n`
  final, gravado com `encoding="utf-8"` e `newline="\n"`. `capturado_em` e `sha256` ficam só em
  `norma`/`metadados`, nunca em `artigos`.
- Esquema estável **por tipo**: cada `tipo` de nó tem um conjunto fixo de chaves, listado em
  [negocio/modelo-de-dados.md](negocio/modelo-de-dados.md). Dentro dele, opcional ausente sai
  como `null` e lista vazia como `[]`; chave de outro tipo não aparece.

## Commits

Conventional Commits; tipo e escopo em inglês, descrição em português no imperativo, sem ponto final,
com até ~72 caracteres. Quebra de contrato (esquema do JSON, CLI) leva `!` depois do tipo e
`BREAKING CHANGE:` no rodapé. Commit que regrava snapshot traz a justificativa no corpo.

| Escopo | Área |
|---|---|
| `modelo` | `modelo.py`, serialização e chave de ordenação |
| `fontes` | `fontes/html.py`, `fontes/pdf.py`, cache |
| `parser` | `normalizador`, `notas`, `parser`, `segmentador` |
| `vigencia` | `vigencia.py`, `validador.py`, relatório |
| `recorte` | `recorte.py` |
| `perfil` | `perfil.py`, `perfis/*.toml` |
| `cli` | `cli.py` |
| `docs` | documentação e roteiros |

## Mapa do código

Caminhos dos módulos relativos a `src/vademecum/`.

| Módulo | Entrada → Saída | Depende de |
|---|---|---|
| `modelo.py` | dataclasses `LinhaFonte`, `No`, `Nota`, `Local`, `Norma`, `Base`, `Relatorio`; `chave_ordenacao()`; `para_json()` | — |
| `perfil.py` | `carregar_perfil(nome) -> Perfil` (merge `padrao.toml` + específico) | `modelo` |
| `fontes/html.py` | URL/`.htm`/`.mht` → `list[LinhaFonte]` + metadados | `modelo` |
| `fontes/pdf.py` | `.pdf` → `list[LinhaFonte]` | `modelo`, `perfil` |
| `segmentador.py` | `list[LinhaFonte]` → `list[DocumentoFonte]` (P5) | `modelo`, `perfil` |
| `normalizador.py` | linhas → linhas normalizadas (ordinal, travessão, junção) | `modelo`, `perfil` |
| `notas.py` | texto → `(texto_limpo, list[Nota])` | `modelo`, `perfil` |
| `parser.py` | linhas → árvore `list[No]` (máquina de estados) | `modelo`, `notas`, `perfil` |
| `vigencia.py` | árvore → árvore vigente + descartes no relatório (ADR-001) | `modelo` |
| `validador.py` | `Base` → avisos V1–V7 no relatório | `modelo`, `perfil` |
| `recorte.py` | `Base` + expressão → `Base` recortada | `modelo` |
| `cli.py` | argparse → orquestra o pipeline | todos |
| `perfis/*.toml` | regras por norma (`padrao`, `cp`, `nscgj`, `lei_sp`) | — |

| Caminho | Papel |
|---|---|
| `tests/` | `unit/`, `aceite/`, `regressao/`; `fixtures/` com trechos reais e `snapshots/` |
| `docs/` | este README, PADRAO_OURO, PENDENCIAS, `decisoes/`, `negocio/`, `processo/` |
| `.claude/` | `CLAUDE.md` e `commands/` (carregadores dos roteiros de `docs/processo/`) |
| `scripts/` | utilitários fora da suíte |
| `dados/` | fontes brutas e saídas geradas (não versionado) |

## Parâmetros do processo

Os roteiros de [processo/](processo/) leem esta seção. Eles não citam arquivo do projeto, para
continuarem iguais entre projetos.

| Parâmetro | Valor |
|---|---|
| Portões (rodam ao fim de toda fase e na revisão) | na raiz: `ruff check . && ruff format --check . && pytest` |
| Cobertura (revisão e auditoria; informa, não reprova) | `pytest --cov=vademecum --cov-report=term-missing`; diff: `coverage xml` e `diff-cover coverage.xml --compare-branch=main --include-untracked` |
| Conferência manual quando a suíte não cobre | `python -m vademecum extrair --fonte <fonte> --perfil <perfil> --saida <base.json>` e abrir o relatório |
| Contrato e consumidores | esquema do JSON ([negocio/modelo-de-dados.md](negocio/modelo-de-dados.md) e § Contratos acima); relatório de extração; opções e códigos de saída da CLI ([negocio/recorte-e-cli.md](negocio/recorte-e-cli.md)); perfil `.toml`; Etapa 2 |
| Repositórios relacionados | nenhum |
| Gatilhos de spec além dos gerais | mudança no esquema do JSON; regex de [negocio/parsing.md](negocio/parsing.md); perfil novo; dependência nova |
| Fase pede Opus quando | contradiz ou completa uma regra de negócio ou ADR; muda o esquema do JSON; semântica de vigência (ADR-001) ou de recorte (ADR-004) |
| Proibido | `if norma == ...` no parser (ADR-002); corrigir ortografia do texto legal; perda silenciosa de texto (RNF04); timestamp dentro de `artigos` (RNF03); I/O sem `encoding="utf-8"`; regravar snapshot sem justificativa no corpo do commit; teste que acesse a rede sem o marcador `rede`; ler `.env` e arquivos Dynaconf |
| Untracked tolerados | `dados/` |
| Regressão | `pytest -m regressao` contra `tests/fixtures/snapshots/`, mais antes/depois da base (ver [processo/REGRESSAO.md](processo/REGRESSAO.md)); relatórios em `docs/processo/relatorios/` (gitignored) |
| Relatório de revisão | `docs/processo/relatorios/` (gitignored) |
| Relatório de auditoria | `docs/processo/relatorios/` (gitignored) |

## Regras de manutenção

1. **Fonte única.** Cada fato mora num lugar; os outros apontam.
2. **Referência por nome**, de documento, seção, função ou regra (ID: `H15`, `RF07`, `ADR-002`).
   Nunca por linha, parágrafo ou número de seção. `arquivo:linha` só em spec e relatório, que são
   efêmeros.
3. **Vale o código.** Estado se confere no git e no código; não há carimbo de "verificado em".
4. **Obsoleto é apagado**; o git preserva.
5. **ADR se edita** quando está errado ou desatualizado, com uma linha em "Histórico".
6. **Tetos:** README raiz 50 · este 250 · CLAUDE.md 40 · PADRAO_OURO 150 · PENDENCIAS 100 ·
   ADR 80 · negócio 150 por assunto · spec 200. Estourou, divida.
7. **Fechou um item de PENDENCIAS?** Risque lá com data e sha, e atualize "Agora".
8. **Contradição com uma regra de negócio ou ADR** vai para PENDENCIAS e para o operador; não se
   decide sozinho.
