# Spec — M1: modelo e ordenação

> Decisão que executa: nenhuma decisão nova de negócio. Resolve a divergência entre
> `docs/README.md § Contratos` e `negocio/modelo-de-dados` (decidida pelo operador na entrevista
> de 2026-10-31) e completa P13 no `id`. Item: PENDENCIAS #1 (M1).
> Escrita em 2026-10-31 contra `92c63cc`, branch `ccr-84150143-2b6gxt`.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

`src/vademecum/` não tem `modelo.py`. Toda etapa do pipeline depende dele (Mapa do código em
`docs/README.md`), e o M2 não começa sem ele. O contrato escrito tem lacunas e uma contradição:

- `docs/README.md` (§ Contratos) diz que "campo opcional ausente sai como `null` (esquema
  estável)". O exemplo do art. 121 em `docs/negocio/modelo-de-dados.md` (§4) traz chaves
  diferentes por tipo: `pena` só com `id/tipo/texto`, alínea sem `notas/filhos`, parágrafo sem
  `numero/sufixo/local/parcial`.
- Nenhum documento diz como fica o `id` do artigo com milhar (P13: `Art. 1.091-A`).
- `Nota.data` não tem formato definido (`negocio/vigencia-e-notas`).
- Nenhum documento diz onde fica `ErroFonte`.

Evidência dos formatos de número: H11, H12 e P13 (`negocio/fontes`), e o `arts` de
`claude/topicos-oj2026.json`: `1º a 12`, `1.091-A`, `1.169`, `396-A`. O `359-M-A` vem de H12.

## Estado final

- `src/vademecum/modelo.py` existe, sem dependência interna, e traz: `LinhaFonte`, `Nota`,
  `Local`, `No`, `Norma`, `Metadados`, `Base`, `EntradaRelatorio`, `Relatorio`, `ErroFonte`,
  `chave_ordenacao()`, `chave_de_texto()`, as funções de `id` e `para_json()`.
- `tests/unit/test_modelo.py` prova:
  - `121 < 121-A < 121-B < 122`;
  - `359-M < 359-M-A < 359-M-B < 359-N`;
  - `para_json` da mesma `Base` gera duas vezes os mesmos bytes, com chaves ordenadas,
    `ensure_ascii=False` e `\n` final.
- `negocio/modelo-de-dados` e `docs/README.md § Contratos` descrevem o esquema estável por tipo,
  e o exemplo do art. 121 bate com ele.
- Nenhum chamador ainda: `cli.py` continua levantando `NotImplementedError`.

## Fora do escopo, de propósito

- **Regex de dispositivo** (`Art.`, `§`, inciso, alínea): é do parser, no M3. `chave_de_texto`
  recebe só o fragmento numérico. O prefixo de artigo é vocabulário do perfil (ADR-002).
- **Sintaxe do recorte** (faixas, `;`, `a`): é do M5. Ele usa `chave_de_texto` para cada ponta.
- **Campos específicos** de cada tipo de entrada do relatório (motivo do descarte, de/até da
  faixa): ficam com o marco que gera cada um (M3 e M4).
- **Envelope de `base.relatorio.json`**: é do M4.
- **`id` do item numérico** (`1.`, `2.`): ele só aparece em PDF (M8). Ver "Em aberto".
- **Campos de `Norma` para PDF multi-norma** (número e data por norma, RF13): ficam para o M8.
- `perfil.py` e `Perfil`: ficam para o M3.

## Contrato

Esta é a primeira definição em código; nada existente quebra. Não há base gerada nem snapshot
(`dados/` e `tests/fixtures/snapshots/` só têm `.gitkeep`). `SCHEMA_VERSION` continua `"1.0"`.
Consumidor: a Etapa 2 (um LLM lendo recortes), que ainda não roda contra nada.

**Imutabilidade.** Todas as dataclasses são `frozen=True, slots=True`, e `filhos` e `notas` são
`tuple`, com uma exceção: `Relatorio` é um acumulador mutável (com `slots`, sem `frozen`), com
um único método de escrita, `registrar(entrada)`. As entradas dele são frozen. Assim a assinatura
das etapas no README (dados + `Perfil` + `Relatorio` → dados novos) não muda.

**Esquema estável por tipo.** Cada `tipo` tem um conjunto fixo de chaves. Dentro dele, um
opcional ausente sai como `null` e uma lista vazia sai como `[]`. Chave de outro tipo não aparece.

| `tipo` | Chaves |
|---|---|
| `artigo` | `id tipo rotulo numero sufixo rubrica local texto notas parcial filhos` |
| `paragrafo`, `inciso`, `alinea`, `item` | `id tipo rotulo rubrica texto notas filhos` |
| `pena` | `id tipo texto notas` |
| nota | `tipo norma ano data bruto` |
| `local` | `parte livro titulo capitulo secao subsecao rotulo_livre` |

- O `sufixo` sai como lista no JSON (`[]`, `["M", "A"]`).
- `Nota.data` é `str | None`, em ISO `AAAA-MM-DD`. O texto original fica em `bruto`. Quem
  preenche a data é o `notas.py`, no M4.

**Ordenação.**
- `chave_ordenacao(numero: int, sufixo: tuple[str, ...]) -> tuple[int, tuple[str, ...]]`. A
  tupla vazia ordena antes de qualquer letra.
- `chave_de_texto(s: str)` aceita o número com milhar opcional, um ordinal opcional (`º`, `°`,
  `o`) e sufixos `-X` maiúsculos: `1º`, `121`, `1.091-A`, `359-M-A`. Qualquer outra entrada
  (`Art. 121`, `121-a`, vazio) levanta `ValueError`. Regex com teste, usando os casos reais
  acima.

**`id`** (deriva do rótulo; o número sai normalizado, P13):
- artigo: `art121`, `art121-A`, `art359-M-A`, `art1091-A`;
- parágrafo: `.p2`, `.p2-B`, `.pu` (parágrafo único);
- inciso: `.i7` (romano convertido para inteiro);
- alínea: `.a`;
- pena: `.pena1`, `.pena2`, contando só as penas do mesmo pai, a partir de 1.

O `id` de um filho é o `id` do pai seguido do segmento: `art121.p2.i7.a`, `art121.pena1`.

**Relatório.** `EntradaRelatorio` tem o campo `tipo`, que é um destes: `descarte`, `aviso`,
`nao_classificada`, `nota_outra`, `faixa_revogada`. Os campos comuns são `origem: str` e
`texto: str`.

**Serialização (RNF03).** `para_json(obj) -> str` serve para `Base` e `Relatorio`. Usa
`json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` e acrescenta `\n` no fim. Não faz
I/O; quem grava é a `cli.py`.

**`ErroFonte(Exception)`** fica em `modelo.py`, porque `fontes/*` e `cli.py` já dependem dele.

## Fases

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| 1 | Docs do contrato: esquema estável por tipo, `id` com milhar, `Nota.data` em ISO, `ErroFonte` em `modelo` | `negocio/modelo-de-dados.md`, `docs/README.md` (§ Contratos) | o exemplo do art. 121 tem as chaves da tabela do Contrato; `python scripts/verificar_docs.py` sai 0; portões verdes | Opus | |
| 2 | Chaves de ordenação: `chave_ordenacao` e `chave_de_texto` (H11, H12, P13) | `modelo.py`, `tests/unit/test_modelo.py` | as duas cadeias de ordenação do Estado final; `1º`→`(1, ())`; `1.091-A`→`(1091, ("A",))`; `ValueError` para `Art. 121` e `121-a`; portões verdes | Sonnet | |
| 3 | Dataclasses da árvore e da base: `LinhaFonte`, `Nota`, `Local`, `No`, `Norma`, `Metadados`, `Base`, `ErroFonte` | `modelo.py`, `tests/unit/test_modelo.py` | todas frozen+slots; atribuir campo levanta `FrozenInstanceError`; `filhos`/`notas` são `tuple`; campos de `LinhaFonte` iguais aos de `negocio/pipeline-e-perfis`; portões verdes | Sonnet | |
| 4 | Relatório: `EntradaRelatorio` e `Relatorio.registrar` | `modelo.py`, `tests/unit/test_modelo.py` | tipo fora dos cinco levanta `ValueError`; entradas guardadas na ordem em que foram registradas; portões verdes | Sonnet | |
| 5 | Derivação do `id` | `modelo.py`, `tests/unit/test_modelo.py` | todos os exemplos de `id` do Contrato, inclusive `art1091-A`, `art121.pu` e `art121.pena2`; portões verdes | Sonnet | |
| 6 | `para_json` com esquema estável por tipo (RNF03) | `modelo.py`, `tests/unit/test_modelo.py` | mesmos bytes em duas chamadas; chaves por tipo exatamente as da tabela; `null` e `[]` onde cabem; `ensure_ascii=False` (º e § literais); `\n` final; portões verdes | Sonnet | |
| 7 | Fechamento | `docs/PENDENCIAS.md`, `docs/README.md` (Mapa do código), esta spec | item 1 riscado com data e sha; "Agora" aponta o M2; Mapa cita `ErroFonte` e `chave_de_texto` em `modelo.py`; spec apagada | Sonnet | |

Notas por fase:
- **Fase 1** muda o texto do contrato do JSON (gatilho "Fase pede Opus" nos Parâmetros do
  processo). Trechos a corrigir: `docs/negocio/modelo-de-dados.md:49-77` (exemplo) e
  `docs/README.md:117-120` (Serialização). O exemplo ganha as chaves que faltam, com `null` ou
  `[]` (ex.: `pena` com `"notas": []`).
- **Fase 2**: `chave_de_texto` é regex, e a regra é "regex só muda com teste" (CLAUDE.md). O teste
  cita H11, H12 e P13 e usa as formas reais do `arts` dos tópicos.
- **Fase 3**: a `LinhaFonte` copia os campos de `docs/negocio/pipeline-e-perfis.md:25-34`.
- **Fase 6**: `para_json` escolhe as chaves pelo `tipo` do nó. Os `id` do teste vêm da fase 5.

## Em aberto

- **`id` do item numérico** (`1.`, `2.`; RF08). Responde: o operador, no M8, quando houver PDF
  com item. Parado: nada neste marco. A fase 5 não gera `id` de item.
