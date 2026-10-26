# vade-mecum-extractor — README técnico

Parser genérico que converte legislação bruta (HTML do Planalto, `.mht`, PDF com texto) em base JSON
hierárquica (artigo › parágrafo › inciso › alínea) e gera recortes de artigos. É a Etapa 1 de 2; a
Etapa 2 (material de estudo) está fora de escopo. Quem usa é o operador, pela CLI `python -m vademecum`.

Ordem de leitura: este arquivo → o documento que o problema pede (tabela abaixo) → o código.
Havendo mudança em curso, a spec dela em [../.claude/processo/specs/](../.claude/processo/specs/) vem
antes do código. Em divergência com o código, **vale o código**, e o documento é corrigido.

| Pergunta | Onde |
|---|---|
| O que o sistema **deve** fazer, e por quê? | [Prd.md](Prd.md) (regras H*, P*, RF*, D*, A*) |
| **Como** está construído (módulos, contratos)? | [SPEC_TECNICA.md](SPEC_TECNICA.md) |
| Em que **fase** estamos? | [PENDENCIAS.md](PENDENCIAS.md) ("Agora" e fases 1–7) |
| O que **falta** e o que está em curso? | [PENDENCIAS.md](PENDENCIAS.md) |
| **Como** se faz uma mudança? | [roteiro SPEC](../.claude/processo/SPEC.md) e [roteiro FASE](../.claude/processo/FASE.md) |
| Checklist e log de revisão | [REVISAO.md](../.claude/processo/REVISAO.md) |

## Arquitetura

Pipeline em módulos puros que só se apontam para a direita: fonte (`fontes/`) → `segmentador` →
`normalizador` → `parser` (com `notas` e `perfil`) → `vigencia` → `validador` → JSON; `recorte` lê a
base pronta. Só `cli.py` e `fontes/*` fazem I/O. Diferença entre normas mora em `perfis/*.toml` (D2),
nunca no parser. A tabela de módulos está em SPEC_TECNICA.md §2.

Saída determinística (RNF03): chaves ordenadas, sem timestamp dentro de `artigos`. Nenhum texto some
sem ir para a árvore ou para o relatório, com `origem` (RNF04).

## Stack

Python 3.12, hatchling com layout `src/`, ruff, pytest, `beautifulsoup4` + `lxml`, `pdfplumber`,
`requests`. Versões em `pyproject.toml`. Dependência nova só com registro em SPEC_TECNICA.md §1.

## Ambiente, testes e lint

Windows sem WSL (RNF02): `pathlib` e `encoding="utf-8"` explícito em toda leitura e escrita.

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"   # ambiente
ruff check . && ruff format --check .                 # lint + formato
pytest                                                # a suíte
pytest -m aceite                                      # só A1–A14
```

Marcadores: `aceite`, `regressao`, `rede` (fora do CI padrão). Os tipos de teste estão em SPEC_TECNICA.md §5.

## Commits

Conventional Commits; tipo e escopo em inglês, descrição em português no imperativo, sem ponto final,
com até ~72 caracteres. Quebra de contrato (esquema do JSON, CLI) leva `!` depois do tipo e
`BREAKING CHANGE:` no rodapé.

| Escopo | Área |
|---|---|
| `modelo` | `modelo.py`, serialização e chave de ordenação |
| `fontes` | `fontes/html.py`, `fontes/pdf.py`, cache |
| `parser` | `normalizador`, `notas`, `parser`, `segmentador` |
| `vigencia` | `vigencia.py`, `validador.py`, relatório |
| `recorte` | `recorte.py` |
| `perfil` | `perfil.py`, `perfis/*.toml` |
| `cli` | `cli.py` |
| `docs` | PRD, spec, README, roteiros |

## Mapa do código

| Caminho | Papel |
|---|---|
| `src/vademecum/` | pacote; módulos em SPEC_TECNICA.md §2 |
| `src/vademecum/perfis/` | regras por norma (`padrao.toml`, `cp.toml`, `nscgj.toml`, `lei_sp.toml`) |
| `tests/` | `unit/`, `aceite/`, `regressao/`; `fixtures/` com trechos reais e `snapshots/` |
| `docs/` | PRD, spec técnica, este README e PENDENCIAS |
| `.claude/` | CLAUDE.md, `commands/` (`/spec`, `/fase`), `processo/` (roteiros, revisão e specs) |
| `dados/` | fontes brutas e saídas geradas (não versionado) |

## Parâmetros do processo

Os roteiros de [processo/](../.claude/processo/) leem esta seção. Eles não citam arquivo do projeto,
para continuarem iguais entre projetos.

| Parâmetro | Valor |
|---|---|
| Portões (rodam ao fim de toda fase e na revisão) | na raiz: `ruff check . && ruff format --check . && pytest` |
| Cobertura (revisão; informa, não reprova) | `pytest --cov=vademecum --cov-report=term-missing` |
| Conferência manual quando a suíte não cobre | `python -m vademecum extrair --fonte <fonte> --perfil <perfil> --saida <base.json>` e abrir o relatório |
| Contrato e consumidores | esquema do JSON (SPEC_TECNICA.md §4 e PRD §7); relatório de extração; opções e códigos de saída da CLI (PRD §10); perfil `.toml`; Etapa 2 |
| Repositórios relacionados | nenhum |
| Gatilhos de spec além dos gerais | mudança no esquema do JSON; regex do PRD §8; perfil novo; dependência nova |
| Fase fecha com | PRD §12 atualizado se a fase decidiu algo, e entrada em `REVISAO.md` ao fechar fase do `fase.md` |
| Fase pede Opus quando | contradiz ou completa o PRD; muda o esquema do JSON; semântica de vigência (D1) ou de recorte (D4) |
| Proibido | `if norma == ...` no parser (D2); corrigir ortografia do texto legal; perda silenciosa de texto (RNF04); timestamp dentro de `artigos` (RNF03); I/O sem `encoding="utf-8"`; regravar snapshot sem registro em `REVISAO.md`; teste que acesse a rede sem o marcador `rede`; ler `.env` e arquivos Dynaconf |
| Untracked tolerados | `dados/` |
| Regressão | `pytest -m regressao`, contra `tests/fixtures/snapshots/` |
| Relatório de revisão | log em [REVISAO.md](../.claude/processo/REVISAO.md) |

## Regras de manutenção

1. **Fonte única.** Cada fato mora num lugar; os outros apontam. O PRD é a fonte das regras.
2. **Referência por nome**, de documento, seção, função ou regra (ID do PRD). Nunca por linha ou
   parágrafo. `arquivo:linha` só em spec, que é efêmera.
3. **Vale o código.** Estado se confere no git e no código; não há carimbo de "verificado em".
4. **Obsoleto é apagado**; o git preserva.
5. **Tetos:** este arquivo 300 · PENDENCIAS 200 · spec de mudança 200. Estourou, divida.
6. **Fechou um item de PENDENCIAS?** Risque lá com data e sha, e atualize "Agora".
7. **Contradição com o PRD** vai para `Prd.md` §12 e para o operador; não se decide sozinho.
