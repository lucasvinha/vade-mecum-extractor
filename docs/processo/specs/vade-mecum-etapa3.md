# Spec — Vade mecum em 3 etapas, com dados versionados (piloto: Direito Penal)

> Decisão que executa: ADR-005, escrito na fase 1 (decidido pelo operador na entrevista de
> 2026-11-02). Item: PENDENCIAS #19, novo, que entra como M6 (os marcos M6–M9 sobem um).
> Escrita em 2026-11-02 contra `271ad1d`, branch `main`.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

O vade mecum (antes "Etapa 2") é montado fora do repositório: o operador sobe os recortes num
projeto do Claude.ai, que não tem o extrator, os tópicos nem os relatórios. Evidências:
- O recorte do CP precisou de um script avulso para virar expressão a partir de
  `claude/topicos-oj2026.json`. A CLI não lê os tópicos (`docs/negocio/recorte-e-cli.md:35`).
- Os tópicos não dizem a norma de cada grupo: `proc-penal` mistura CPP e Lei 9.099, `civil`
  mistura CC e LINDB.
- `dados/` está fora do git (`.gitignore:20`) e desatualizado em silêncio:
  `dados/cp/base.relatorio.json` tem 3 KB e é anterior ao M4. A base atual gera 39 KB.
- Nada impede uma LLM de alterar o texto legal ao montar o HTML.

## Estado final

- Três etapas delimitadas. **1** `extrair` e **2** `recortar` são determinísticas e versionadas.
  **3** é a LLM gerando o HTML a partir de instruções neutras (qualquer LLM), conferida pelo
  `conferir`, que também é determinístico.
- `dados/` versionado:
  ```
  dados/fontes/<norma>/<arquivo original>          (.htm, .mht, .pdf)
  dados/bases/<norma>/base.json (+ .relatorio.json)
  dados/recortes/oj26/<materia>/<norma>.json (+ .relatorio.json)
  dados/vade-mecum/oj26/<materia>.html (+ .pdf)
  ```
- `python -m vademecum recortar --base dados/bases/cp/base.json --topicos claude/topicos-oj2026.json
  --materia penal --saida dados/recortes/oj26/penal/cp.json` gera o recorte sem expressão manual.
- `python -m vademecum conferir --recorte dados/recortes/oj26/penal/cp.json --html
  dados/vade-mecum/oj26/penal.html` sai 0.
- `dados/vade-mecum/oj26/penal.html` e `.pdf` versionados: organizados pelos tópicos do edital, com
  capa e rodapé assinados "Lucas Vinha Teixeira · github.com/lucasvinha" (no rodapé, o link do
  repositório e a página).
- Teste de sincronia: reextrair e recortar de novo dá bytes idênticos aos versionados.

## Fora do escopo, de propósito

- Perfis das outras normas (agora M7). O piloto é só o CP. As fontes das outras normas entram
  versionadas na fase 2, mas sem base.
- `renderizar` em Python: o operador escolheu a LLM para o estilo e a verificação do produto.
  A guarda do texto literal é o `conferir`.
- Gerar o PDF por código (weasyprint etc.): o PDF sai do navegador (Ctrl+P), sem dependência nova.
- Itens `integral` e o grupo "Demais normas" de `leg-especial` (M9, PDF).
- Conferir o conteúdo das anotações (realces, quadros): o `conferir` só garante o texto legal.

## Contrato

- **CLI `recortar`** (aditivo): `--topicos <json> --materia <id>`, mutuamente exclusivos com
  `--artigos`. A expressão é a junção, com `"; "`, dos `arts` dos itens dos grupos da matéria cujo
  `norma` é igual a `base.norma.id`, na ordem do arquivo. Itens sem `arts` ficam de fora.
  `recorte.expressao` grava essa junção. O código de saída é 2 quando a matéria não existe ou
  nenhum grupo dela é da norma da base.
- **Tópicos `topicos-oj/2`**: campo `norma` (id do perfil, igual ao nome da pasta em
  `dados/fontes/`) em cada grupo de matéria `tipo: "lei"`. É o primeiro esquema documentado do
  arquivo. `docs/schema-questoes-json.md` passa a citar `/2`.
- **CLI `conferir`** (novo): `--recorte <json>` (repetível, uma por norma) e `--html <arquivo>`.
  Sai 0 sem divergência e 1 com divergência, imprimindo uma linha por divergência
  (`<norma>:<id>: <motivo>`). Erro de entrada sai 2.
- **Contrato do HTML** (novo, `docs/negocio/vade-mecum.md`):
  - Cada norma fica num elemento `[data-norma="<norma.id>"]`.
  - Cada nó do recorte (artigo, parágrafo, inciso, alínea, item, pena) é um `[data-id="<id>"]`
    dentro da sua norma.
  - Os campos do nó ficam em `[data-campo="rotulo"|"rubrica"|"texto"]`. Conta só o campo cujo
    `[data-id]` mais próximo é o próprio nó.
  - Compara com espaços colapsados e sem os das pontas. Fora isso, a comparação é literal.
  - Divergências: nó ausente, campo divergente, `data-id` desconhecido e `data-id` repetido.
  - Anotações e quadros não levam `data-id`.
- **Esquema da base e do relatório:** sem mudança. **Etapa 2 antiga:** deixa de existir com esse
  nome. Vira a Etapa 3, dentro do projeto.

## Fases

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| 1 | **Decisão.** ADR-005 (três etapas; LLM gera o HTML e o `conferir` guarda o texto; `dados/` versionado num repositório público, porque texto de lei não tem direito autoral, Lei 9.610/98, art. 8º, IV; assinatura; ordem pelos tópicos). README técnico: escopo "Etapa 1 de 2" → três etapas. PADRAO_OURO §6: regra de enxertos e `dados/` fora do git. `negocio/recorte-e-cli` §2: a CLI passa a ler os tópicos. PENDENCIAS: item 19 como M6, renumeração M6–M9 → M7–M10 (13 menções: `docs/README.md`, `PENDENCIAS.md`, `negocio/modelo-de-dados.md`, `tests/unit/test_normalizador.py`) e "Agora". | ~6 docs + 1 comentário de teste | portões verdes; `python scripts/verificar_docs.py` sai 0 | Opus | |
| 2 | **`dados/` versionado.** Tira `dados/*` do `.gitignore`. Move as fontes para `dados/fontes/<norma>/`. Gera `dados/bases/cp/` a partir do `.mht` (traz URL e data da captura). Apaga a base velha. Ajusta `tests/aceite/conftest.py:11` e os comentários com `dados/cp/...` (`test_parser.py:8`, `test_vigencia.py:9`, `test_normalizador.py:77`, `test_a05_arts_187_196.py:5`). Os cabeçalhos das fixtures ficam como estão, porque registram a procedência. Atualiza os caminhos em `.claude/CLAUDE.md:25`, `negocio/recorte-e-cli` §4, `tests/fixtures/README.md:4`, README técnico (Infra, Mapa, "Untracked tolerados") e PADRAO_OURO (A1 não é mais pulado). Teste novo `tests/regressao/test_dados_versionados.py`: reextrai cada `dados/bases/<norma>` e compara byte a byte. | exceção declarada: ~8 MB de fontes + ~10 arquivos | portões verdes; A1 roda sem pular; teste de sincronia verde | Sonnet | |
| 3 | **Tópicos `topicos-oj/2`.** Campo `norma` nos grupos de matéria `lei` (`cp`, `cpp`, `lei9099`, `cpc`, `cf`, `cc`, `lindb`, `lei8429`, `lei13146`, `lei6830`; NSCGJ e Lei SP 10.261 com o id que o M9 usar, ver Em aberto). Documenta o esquema em `negocio/recorte-e-cli`. `schema-questoes-json.md:6` e `docs/README.md:16` passam a citar `/2`. | 3–4 arquivos | portões verdes; todo grupo de matéria `lei` tem `norma` (teste pequeno sobre o arquivo) | Sonnet | |
| 4 | **`recortar --topicos --materia`.** Função pura em `recorte.py` (tópicos já lidos, matéria e id da norma → expressão) e opção na CLI (`cli.py`, `_recortar`). Testes de unidade e de CLI: matéria inexistente, matéria sem grupo da norma, item sem `arts` e a junção da matéria `penal`, cuja expressão é a usada no piloto. Gera `dados/recortes/oj26/penal/cp.json` (90 artigos). O teste de sincronia passa a cobrir os recortes. Doc: `negocio/recorte-e-cli` §4. | ~6 arquivos | portões verdes; recorte do CP igual ao versionado | Sonnet | |
| 5 | **`conferir`.** Módulo puro `conferencia.py` (recortes + texto do HTML → divergências; usa `beautifulsoup4`, já dependência). Subcomando na CLI. `docs/negocio/vade-mecum.md` com o contrato do HTML (seção Contrato acima). Fixture: HTML pequeno com art. 121 do recorte dos enxertos, um caso por divergência e o caso limpo. README técnico: Mapa do código e escopo `conferencia` em Commits. | ~6 arquivos | portões verdes; `conferir` sai 0 no HTML correto e 1 em cada um dos quatro tipos de divergência | Opus | |
| 6 | **Instruções da Etapa 3 + skill.** `docs/etapa3/INSTRUCOES.md`, neutro de LLM: entradas (recortes + relatórios + tópicos); ordem pelos tópicos, com a rubrica do edital como título e a `nota` do edital como aviso; contrato `data-*`; realces, quadros comparativos e pontos de atenção; notas de vigência e descartes do relatório; capa e rodapé assinados; CSS de impressão com `@page` (margem e número de página); rodar o `conferir` até sair 0. `.claude/skills/vade-mecum/SKILL.md` fino: `/vade-mecum <materia>` roda 1 e 2 se faltar arquivo, carrega as instruções, gera o HTML, roda o `conferir` e pede o PDF ao operador. `.claude/CLAUDE.md`: `skills/` também é versionado. | 3–4 arquivos | portões verdes; `verificar_docs.py` sai 0 | Opus | |
| 7 | **Piloto: Direito Penal.** `/vade-mecum penal` → `dados/vade-mecum/oj26/penal.html`. O operador abre no navegador, salva `penal.pdf` ao lado e confere capa e rodapé. O que o piloto revelar sobre as instruções entra nesta fase. Falta no contrato vira item em PENDENCIAS. | 2 arquivos de dados + ajustes nas instruções | `conferir` sai 0; PDF presente; operador aprova | Opus | |
| 8 | **Fechamento.** Risca o item 19 em PENDENCIAS, atualiza "Agora" (próximo: M7), ajusta o ADR-005 se o piloto mudou algo e apaga esta spec. | docs | — | Sonnet | |

## Em aberto

- **Id de norma em perfil `padrao`:** `base.norma.id` vem do perfil, e lei sem perfil próprio sai
  `padrao`, o que não casa com `norma: "lei9099"` dos tópicos. Quem responde: a spec do M7
  (perfis), que decide se cada lei ganha perfil, mesmo mínimo, ou se o id vem de outro lugar.
  Não bloqueia o piloto (o CP tem perfil `cp`).
- **Ids de NSCGJ e Lei SP 10.261** nos tópicos: só se fixam no M9 (PDF). A fase 3 usa o
  provisório `nscgj` e `lei_sp10261` e registra o ponto no ADR-005.
- **Roteiro `docs/processo/REGRESSAO.md`** (vem do molde do dotfiles) diz que as fontes de
  `dados/` ficam fora do git. O ajuste é no molde, decisão do operador. Não bloqueia fase.
