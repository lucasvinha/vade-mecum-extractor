# Spec — M4: vigência e validação

> Decisão que executa: ADR-001 e negocio/vigencia-e-notas (RF14, RF16); V1–V7 do PADRAO_OURO.
> Item: PENDENCIAS #8 (M4) e pergunta #5 (P3).
> Escrita em 2026-11-01 contra `ef00e9b`, branch `m4-vigencia-validacao`.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

A base ainda traz o que caiu. Na base do CP inteiro gerada em `ef00e9b`, 58 nós têm texto vazio,
e todos têm nota `revogacao` ou `veto`. Entre eles estão 31 artigos inteiros (185, 187–196, 214,
216, 217, 219–224, 231, 231-A, 232, 240, 279, 281, 350, 359-O, 359-Q, 359-U, 234-C), o
`art121.p2.i6` com a rubrica "Feminicídio" (H16) e o `art171.p5` com os quatro incisos.
`tests/aceite/test_a02_art121_paragrafo2.py:6` e `test_a03_art121_paragrafos.py:5` registram
que a ausência deles depende do filtro de vigência. O descarte no relatório é só
`{tipo, origem, texto}` (`modelo.py:195`), sem o rótulo, o motivo e a nota que o RF16 pede.
Não existe validador: V1–V6 não rodam.

## Estado final

- A2, A3 e A5 completos e A1 com a contagem nova, todos passando. A4, A6, A7 e A8 seguem verdes.
- No CP inteiro: nenhum dos 58 nós na base, 58 + 4 descartes estruturados no relatório e nenhum
  aviso V1–V6.
- Snapshot da base e do relatório de `cp_enxertos.mht`, com `pytest -m regressao` verde.
- Pergunta 5 (P3) fechada em PENDENCIAS, com a decisão registrada em negocio/vigencia-e-notas.

Regras que as fases executam, decididas na entrevista de 2026-11-01:

- **Descarte (RF14, H15, H16).** Um nó não pena é descartado quando o texto sem notas é vazio,
  ou é exatamente um gatilho `notas.revogacao` do perfil seguido de `.` (P12:
  `Artigo 10 - Revogado.`), e todos os filhos também são descartados. `Revogado o livramento…`
  (H15, A4) não casa. A rubrica sai junto com o nó (H16), registrada no descarte. Nó vazio com
  filho vigente fica na base e cai na V5 (ADR-001: não se descarta texto vigente). A pena nunca
  é descartada.
- **Motivo:** `vetado` quando há nota `veto`, `revogado` quando há nota `revogacao` ou o texto é
  `Revogado.`, `vazio` nos outros casos. Com veto e revogação no mesmo nó, vale a primeira nota.
- **Descarte estruturado (RF16, P4).** Só a entrada `descarte` ganha as chaves `id`, `rotulo`,
  `rubrica`, `motivo` e `notas` (objeto nota completo). As outras entradas seguem
  `{tipo, origem, texto}`, com esquema estável por tipo, como na base. O `texto` é o rótulo,
  seguido do texto e dos `bruto` das notas, separados por espaço. Há uma entrada por nó
  descartado, em pré-ordem. Os 4 `(VETADO)` sem rótulo do parser (`parser.py:430`) usam o mesmo
  formato, com `id`, `rotulo` e `rubrica` `null` e `motivo` `vetado`. A linha tachada que o
  leitor HTML descarta (H8, `fontes/html.py:201`; nenhuma no CP) também: `motivo` `vazio` e
  `notas` vazio, porque o leitor não tem perfil para classificar a nota, que segue no `texto`
  (achado da fase 1).
- **V2 × A1 (H19, ADR-003).** Lacuna é o número da numeração-base que não está nem na base nem
  num `descarte` de artigo. A A1 passa a conferir `base ∪ descartes de artigo = 1..361`.
- **Aviso do validador:** `aviso` comum, com o ID no início do texto (`V2: …`) e a `origem` do
  nó mais próximo. Não ganha chave nova.
- **V7** já é cumprida pelo parser (`nao_classificada`, `parser.py:434`; A1). O validador não a
  repete.
- **P3:** a base guarda norma e ano de cada nota, e a conferência contra o corte do edital
  (19/10/2026) é da Etapa 2. Não há código no M4.

## Fora do escopo, de propósito

- **RF15** (faixa `Art. X a Art. Y. Revogados.`): o CP não tem caso. O real (P11) é do NSCGJ em
  PDF e vai para o M8.
- **H18:** a nota de nível continua `aviso` de texto livre (20 no CP).
- **Chave `regra` nos avisos:** não entra. O ID vai no texto.
- **Snapshot de `cp_parser.htm`:** o `capturado_em` do `.htm` é o `mtime` (`fontes/html.py:110`)
  e muda a cada checkout. Só o `.mht`, que traz o `Date`, é estável.
- Lista de leis posteriores ao corte no perfil (P3, opção recusada).

## Contrato

- **Base JSON:** o esquema não muda, mas o conteúdo perde os nós descartados. Nenhum consumidor
  existe ainda (a Etapa 2 não está implementada), e a `dados/cp/base.json` local é regerada.
  Não é quebra de esquema, então não leva `!`.
- **Relatório JSON:** o `descarte` ganha `id`, `rotulo`, `rubrica`, `motivo` e `notas`, uma
  mudança aditiva. Novos `aviso` com `V1:`…`V6:`.
- **CLI:** opções e códigos de saída não mudam. Aviso não muda o código de saída.
- **Perfil:** nenhuma chave nova. A V2 já lê `validacao.lacunas`, e o `Revogado.` textual lê
  `notas.revogacao`.
- **Etapa 2:** recebe só o vigente (ADR-001). Os descartes ficam consultáveis no relatório.

## Fases

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| 1 | Descarte estruturado no relatório | 8 arquivos | portões verdes; `para_json(Relatorio)` sai com esquema por tipo; os 4 `(VETADO)` com `motivo` `vetado` e `notas` | Opus | |
| 2 | `vigencia.py`: filtro RF14 | 2 arquivos | portões verdes; unidade com linhas reais; nenhum chamador ainda | Opus | |
| 3 | `extrair` aplica a vigência | 6 arquivos | portões verdes; A2, A3 e A5 completos; A1 com descartes | Sonnet | |
| 4 | `validador.py`: V1–V6 | 2 arquivos | portões verdes; unidade com base sintética; nenhum chamador ainda | Sonnet | |
| 5 | `extrair` roda o validador | 3 arquivos | portões verdes; CP inteiro sem aviso `V*` | Sonnet | |
| 6 | Snapshot dos enxertos do CP | 3 arquivos | `pytest -m regressao` verde | Sonnet | |
| 7 | Fechamento | docs | `scripts/verificar_docs.py` sai 0 | Sonnet | |

**1. Descarte estruturado.** Em `modelo.py`, o descarte ganha os campos `id`, `rotulo`,
`rubrica`, `motivo` e `notas` (fase escolhe: subclasse ou campos opcionais com chaves por tipo
em `_para_dict`, como `_CHAVES_POR_TIPO`, `modelo.py:233`). `motivo` aceita `revogado`, `vetado`
ou `vazio`; valor fora disso é `ValueError`, como o `tipo` (`modelo.py:207`). Em `parser.py:430`,
o `(VETADO)` sem rótulo registra `motivo` `vetado` e as `notas` já extraídas. Testes:
`test_modelo.py` (esquema por tipo no JSON do relatório) e `test_parser.py:492` (estrutura).
Docs: RF16 em negocio/vigencia-e-notas (as chaves) e a linha `Relatorio` de docs/README.md
§ Contratos.

**2. `vigencia.py`.** `filtrar_vigentes(artigos, perfil, relatorio) -> tuple[No, ...]`,
função pura de `modelo` e `perfil`, que aplica as regras de descarte e motivo acima. Casos em
`tests/unit/test_vigencia.py`, montados com `analisar` sobre linhas reais:
`art121.p2.i6` com a rubrica "Feminicídio" (H16), o art. 88 vigente (H15), o `art171.p5` com
os quatro incisos revogados (descarte em cascata, 5 entradas), `Artigo 10 - Revogado.` (P12,
perfil `padrao`), `(VETADO) (Incluído…)` no art. 359-O e nó vazio com filho vigente (fica).
Os ids e penas restantes não são renumerados.

**3. Ligar a vigência.** `cli.py:76`: `filtrar_vigentes` sobre `analise.artigos` antes de
montar a `Base`. Aceite: a A2 sem o VI, com a rubrica no descarte; a A3 sem o § 2º-A e o § 7º;
`tests/aceite/test_a05_arts_187_196.py` novo (ausentes e com descarte `revogado` cada um, no
`cp_enxertos`); a A1 (`test_a01_cp_completo.py:6`) conta `base ∪ descartes de artigo`. Saem os
comentários de "ainda estão na árvore" da A2 e da A3. Docs: a linha A1 do PADRAO_OURO e a H19
em negocio/fontes passam a dizer "na base ou nos descartes".

**4. `validador.py`.** `validar(base, perfil, relatorio) -> None`, que só registra avisos.
- V1: artigos em ordem pela `chave_ordenacao`.
- V2: com `perfil.lacunas`, lacunas de 1 até o maior número, descontados os descartes de
  artigo do `relatorio`.
- V3: `id` duplicado na árvore inteira.
- V4: entre irmãos do mesmo tipo (parágrafo numerado, inciso, alínea), rótulo menor depois de um
  maior.
- V5: dispositivo não pena com texto vazio e sem filhos com texto.
- V6: nota `outra` na árvore sem `nota_outra` de mesmo `bruto` no relatório.

O comentário no módulo diz que a V7 é do parser. Testes em `tests/unit/test_validador.py`, com
`Base` sintética, um caso positivo e um negativo por regra.

**5. Ligar o validador.** `cli.py`: `validar` depois de montar a `Base`, antes de gravar.
Aceite: em `test_a01_cp_completo.py`, nenhum `aviso` com texto que comece por `V` no CP
inteiro. Em `test_cli.py`, aviso não muda o código de saída. Se a V2 ou a V4 acusarem algo no
CP, a fase para e relata (`depuracao-sistematica`): não se afrouxa a regra.

**6. Snapshot.** `tests/regressao/test_snapshot_cp_enxertos.py` (marcador `regressao`) roda o
`extrair` sobre `tests/fixtures/html/cp_enxertos.mht`, passado como caminho relativo à raiz
(`monkeypatch.chdir`), para o `norma.fonte` não variar. Compara os bytes com
`tests/fixtures/snapshots/cp_enxertos.json` e `cp_enxertos.relatorio.json`. Primeira gravação,
com a justificativa no corpo do commit.

**7. Fechamento.** PENDENCIAS: risca o M4 com data e sha, fecha a pergunta 5 e atualiza
"Agora" (próximo: M5); P4 e P6 apontam para o que ficou. Em negocio/vigencia-e-notas, a
armadilha P3 registra a decisão (Etapa 2 confere, operador 2026-11-01). Em docs/README.md
§ Mapa do código, as assinaturas de `vigencia.py` e `validador.py`. Apaga esta spec.

## Em aberto

- **As 4 leis de 2026 no CP** (15.358, 15.384, 15.402, 15.425): o operador confere à mão se
  alguma é posterior a 19/10/2026. Não bloqueia fase nenhuma: a decisão P3 já tira isso do M4.
