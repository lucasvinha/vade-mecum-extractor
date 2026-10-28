# Spec — Estrutura da documentação no molde padrão

> Decisão que executa: nenhuma decisão nova (D1–D4 do PRD são formalizadas como ADR na fase 3). Item: nenhum ainda; a fase 6 cria o #12 em PENDENCIAS.
> Escrita em 2026-10-27 contra `ce6a861`, branch `main` (sugerida para a migração: `docs/estrutura`, a partir da `main`).
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

A documentação tem 1.023 linhas em 11 arquivos, e o `Prd.md` sozinho tem 381 (o teto é 150 por assunto).
Os roteiros `/spec` e `/fase` vivem em `.claude/processo/`, e não em `docs/processo/`. Faltam `/revisao`,
`/auditoria`, `/regressao`, `PADRAO_OURO.md`, ADRs e `negocio/`. O `CLAUDE.md` tem 60 linhas (teto 40) e
repete regras do README técnico. O `SPEC_TECNICA.md` repete a tabela de módulos do PRD §5.2.

## Estado final

```
README.md                          ≤ 50
.claude/CLAUDE.md                  ≤ 40   (versionado; settings.local.json segue fora do git)
.claude/commands/                  spec fase revisao auditoria regressao
docs/README.md                     ≤ 250  (absorve SPEC_TECNICA e PRD §1–2)
docs/PADRAO_OURO.md                ≤ 150  (unidade: módulo do pipeline)
docs/PENDENCIAS.md                 ≤ 100
docs/decisoes/ADR-001..004-*.md    ≤ 80
docs/negocio/                      ≤ 150 cada: fontes, pipeline-e-perfis, parsing,
                                   vigencia-e-notas, modelo-de-dados, recorte-e-cli
docs/processo/                     README SPEC FASE REVISAO AUDITORIA REGRESSAO
docs/processo/relatorios/          fora do git
scripts/verificar_docs.py          do molde, sem edição
```

Somem: `docs/Prd.md`, `docs/SPEC_TECNICA.md`, `.claude/processo/` e o log de revisões.

## Fora do escopo, de propósito

- Nenhuma linha de `src/` ou de teste muda de comportamento. Só comentários e docstrings que citam
  `Prd.md §N` ou `SPEC_TECNICA.md §N` (fase 7).
- `docs/schema-questoes-json.md` (commit `ce6a861`) e `tests/fixtures/README.md` não são tocados.
- Texto legal, regex, perfis `.toml` e snapshots não mudam. O conteúdo do PRD é **movido**, não reescrito.
- `docs/Prd.md` §3 D1–D4 viram ADR sem mudar a decisão. D5 e D6 não viram ADR (ver "Em aberto").

## Contrato

O que muda para quem lê ou usa o repositório (não há contrato de JSON, CLI ou perfil afetado):

- Caminho dos roteiros: `.claude/processo/*.md` → `docs/processo/*.md`. Carregadores em `.claude/commands/`
  são atualizados na mesma fase, para nenhum slash command ficar quebrado entre commits.
- Referência a regra: continua o **ID** do PRD (`H15`, `RF07`, `D2`, `A2`). O `Prd.md` deixa de existir,
  então "ver Prd.md §N" vira `negocio/<assunto>` ou `ADR-00N`.
- Regra de snapshot: "só regravar com justificativa registrada em `REVISAO.md`" passa a ser "justificativa
  no corpo da mensagem do commit que regrava o snapshot". Reescrita em `docs/README.md § Parâmetros do
  processo` (fase 2) e em `.claude/CLAUDE.md` (fase 8). Decisão do operador: o log de revisões é abandonado.
- Ordem de deploy e rollback: não há deploy. Cada fase é um commit; desfaz com `git revert`.
- Ambiente: nada depende de rede, credencial ou HML. Fases de doc também rodam `ruff` e `pytest`, para
  provar que nenhum código se mexeu.

Tabela de destino por seção (a de cada fase detalha o trecho que ela move):

| Origem | Destino |
|---|---|
| `Prd.md` §1–2 (objetivo, escopo) | `docs/README.md` (abertura) |
| `Prd.md` §3 D1, D2, D3, D4 | `decisoes/ADR-001..004` |
| `Prd.md` §3 D5, D6 | `negocio/modelo-de-dados`, `negocio/fontes` |
| `Prd.md` §4 (fontes) e §6 Leitura | `negocio/fontes` |
| `Prd.md` §5 (arquitetura, perfis) | `negocio/pipeline-e-perfis` |
| `Prd.md` §6 Parsing e §8 (regex) | `negocio/parsing` |
| `Prd.md` §6 Vigência e §7.3 (notas) | `negocio/vigencia-e-notas` |
| `Prd.md` §6 Saída, §7.1–7.2 (envelope, nós) | `negocio/modelo-de-dados` |
| `Prd.md` §9 (recorte) e §10 (CLI) | `negocio/recorte-e-cli` |
| `Prd.md` §11 (validação, aceite), §13 (RNF) | `docs/PADRAO_OURO.md` |
| `Prd.md` §12 (pendências P1–P7), §14 (sequência) | `docs/PENDENCIAS.md` |
| `Prd.md` cabeçalho (campos, legenda) | apagar: versão e fontes analisadas estão no git |
| `SPEC_TECNICA.md` §1–5 | `docs/README.md` (Stack, Mapa do código, Testes e lint, Contratos) |
| `SPEC_TECNICA.md` §6 (T1, T2) | apagar: já são os itens 2 e 3 de `PENDENCIAS.md` |
| `.claude/processo/SPEC.md`, `FASE.md` | `docs/processo/` (adaptados ao molde, não sobrescritos) |
| `.claude/processo/REVISAO.md` checklist | `docs/PADRAO_OURO.md` |
| `.claude/processo/REVISAO.md` log | apagar (decisão do operador) |

## Fases

Cada fase roda `ruff check . && ruff format --check . && pytest` ao fim.

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| ~~1~~ | ~~Processo~~: mover `SPEC.md`/`FASE.md` para `docs/processo/` com `git mv`; instalar `README`, `REVISAO`, `AUDITORIA`, `REGRESSAO` do molde; criar os 3 carregadores novos e apontar `spec.md`/`fase.md` para o novo caminho; `docs/processo/relatorios/` no `.gitignore`; mover esta spec para o lugar certo se ainda não estiver | ~12 arquivos (renomeação e cópia mecânicas, exceção declarada) | `/spec` e `/fase` leem o roteiro no novo caminho; `.claude/processo/` não existe mais; portões verdes | Sonnet | **2026-10-28 `737edcb`** |
| ~~2~~ | ~~README técnico~~: `docs/README.md` absorve `SPEC_TECNICA.md` §1–5 e `Prd.md` §1–2; atualiza os caminhos, as linhas novas dos Parâmetros do processo e a regra de snapshot; apaga `SPEC_TECNICA.md`. Antes de apagar, `grep` por `SPEC_TECNICA` e corrija o que for doc | `docs/README.md`, `docs/SPEC_TECNICA.md`, docs que o citam | `docs/README.md` ≤ 250 e com as seções fixas do molde; nenhuma menção a `SPEC_TECNICA` fora de `src/` e `tests/` (esses ficam para a fase 7) | Opus (mexe em regra de snapshot e nos Parâmetros) | **2026-10-28 `db8de40`** |
| 3 | ADRs: `ADR-001` (D1 vigência), `ADR-002` (D2 parser genérico e perfis), `ADR-003` (D3 todos os artigos), `ADR-004` (D4 faixa inclui letras) no molde, sem mudar a decisão; listar para o operador o que mudou em cada um | 4 arquivos novos em `docs/decisoes/` | cada ADR ≤ 80 linhas, com Problema · Opções · Decisão e porquê · Consequências · Status · Histórico; texto da decisão idêntico ao PRD §3 | Sonnet | |
| 4a | negocio, parte 1: `fontes`, `pipeline-e-perfis`, `parsing` movidos do PRD (§4, §5, §6 Leitura e Parsing, §8), mantendo os IDs H*, RF*, regex literais | 3 arquivos novos (~130–150 linhas de diff cada, exceção declarada: mover texto) | cada arquivo ≤ 150; todo ID `H*`/`RF03–RF11` do PRD aparece em exatamente um; regex idênticas ao PRD | Sonnet | |
| 4b | negocio, parte 2: `vigencia-e-notas` (§6 Vigência, §7.3, D1 por ponteiro para o ADR-001), `modelo-de-dados` (§6 Saída, §7.1–7.2, D5), `recorte-e-cli` (§9, §10, D4 por ponteiro) | 3 arquivos novos | cada arquivo ≤ 150; exemplos de JSON do PRD preservados byte a byte; IDs `RF12–RF17` presentes | Sonnet | |
| 5 | PADRAO_OURO: unidade "módulo do pipeline". Checklist do `REVISAO.md` antigo + PRD §11 (V1–V7, casos A1–A14, tipos de teste) + §13 (RNF01–RNF0N) | `docs/PADRAO_OURO.md` | ≤ 150 linhas; cada RNF e cada caso A1–A14 aparece uma vez; se não couber, ver "Em aberto" | Opus (organiza critérios) | |
| 6 | PENDENCIAS: absorve `Prd.md` §12 (P1–P7) e §14 (sequência) sem duplicar os itens 4 e 5; cria o #12 "Estrutura da documentação" apontando esta spec; ajusta "Agora" | `docs/PENDENCIAS.md` | ≤ 100 linhas; todo P1–P7 está na fila ou marcado como já resolvido por item; "Agora" cita o #12 | Sonnet | |
| 7 | Apagar `docs/Prd.md` e corrigir referências: `grep` em `src/`, `tests/`, `docs/`, `README.md` e `.claude/` por `Prd.md`, `SPEC_TECNICA`, `REVISAO.md` e `PRD §`; trocar por `negocio/<assunto>` ou ADR, citando por nome e nunca por número de seção | `docs/Prd.md`, comentários e docstrings afetados (lista exata sai do `grep` e vai para a mensagem de commit) | `grep -rn "Prd.md\|SPEC_TECNICA" . --include=*.py --include=*.md --include=*.toml` sem resultado; só comentário/docstring mudou no código; testes inalterados e verdes | Sonnet | |
| 8 | Porta de entrada: `README.md` raiz no molde (≤ 50, com "quero fazer X → Y") e `.claude/CLAUDE.md` ≤ 40. Regras de estilo repetidas vão para `docs/README.md`; fica "Específico do Claude" e a regra de snapshot no novo formato | 2 arquivos | `wc -l`: README ≤ 50 e CLAUDE ≤ 40; o `CLAUDE.md` começa por "comece pelo `docs/README.md`" e preserva as regras invioláveis (D2, RNF02–RNF04, texto legal literal) | Opus (decide o que é inviolável) | |
| 9 | Fechamento: copiar `scripts/verificar_docs.py` sem edição; citá-lo em `docs/README.md § Testes e lint`; rodar até zero achado; riscar o #12 em `PENDENCIAS.md`; atualizar "Agora"; **apagar esta spec** | `scripts/verificar_docs.py`, `docs/README.md`, `docs/PENDENCIAS.md`, esta spec | `python scripts/verificar_docs.py` sai 0; `git ls-files '*.md'` bate com o "Estado final" | Sonnet | |

Ordem: a fase 1 vem primeiro porque o `/fase` precisa ler o roteiro no caminho novo. As fases 4a, 4b e 5
vêm antes da 7, que apaga o `Prd.md`. Nenhum conteúdo sai do PRD sem destino declarado na tabela acima.

Cada commit usa o tipo `docs`. O corpo cita "Fase N de docs/processo/specs/estrutura-docs.md".

## Em aberto

- **D5 e D6 sem ADR.** D5 (JSON hierárquico, CSV rejeitado) e D6 (PDF como fonte já estruturada) ficam em
  `negocio/modelo-de-dados` e `negocio/fontes`, porque a entrevista pediu ADR só para D1–D4. Quem decide:
  operador. Bloqueia: nada; se quiser ADR, é fase extra depois da 3.
- **PADRAO_OURO pode estourar 150.** §11.2 tem 14 casos de aceite (A1–A14) e a lista de V1–V7. Se a fase 5
  não couber no teto, a fase decide entre mover os casos de aceite para `negocio/criterios-de-aceite.md`
  ou declarar exceção de teto, e avisa o operador. Bloqueia: só a fase 5.
- **Onde registrar a justificativa de snapshot regravado.** A spec assume o corpo da mensagem do commit.
  Se o operador preferir outro lugar, avisar antes da fase 2. Bloqueia: fases 2 e 8.
- **Untracked tolerados:** `dados/` (já gitignored). Nenhum outro.
