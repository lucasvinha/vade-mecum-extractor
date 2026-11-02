# ADR-005 — Vade mecum em três etapas, com `dados/` versionado

**Status:** aceito em 2026-11-02 (decidido pelo operador na entrevista da spec do M6); a Etapa 3
foi emendada pelo [ADR-006](ADR-006-curadoria-em-json-e-render-deterministico.md)

## Problema

O vade mecum era montado fora do repositório: o operador subia os recortes num projeto do
Claude.ai, que não tem o extrator, os tópicos do edital nem os relatórios. O recorte do CP
precisou de um script avulso para virar expressão a partir dos tópicos, `dados/` ficava fora do
git e desatualizado em silêncio, e nada impedia a LLM de alterar o texto legal ao montar o HTML.

## Opções discutidas

| Opção | A favor | Contra |
|---|---|---|
| Etapa 2 fora do projeto (como era) | Nada a construir | Sem tópicos nem relatórios; texto legal sem guarda; `dados/` sem versão |
| `renderizar` em Python | Determinístico | Estilo e anotações de estudo ficam pobres; muito código de layout |
| LLM gera o HTML no projeto, `conferir` guarda o texto | Estilo e anotações da LLM; texto legal verificado | A LLM pode errar a marcação, e o `conferir` aponta para refazer |

## Decisão

O vade mecum sai em **três etapas**, todas dentro deste repositório:

1. **`extrair`** (determinística): fonte → base JSON.
2. **`recortar`** (determinística): base + tópicos do edital → recorte por matéria e norma.
3. **Vade mecum** (LLM): recortes + relatórios + tópicos → HTML, por instruções neutras de LLM
   (qualquer modelo serve). O PDF sai do navegador.

O **`conferir`** (determinístico) compara o texto legal do HTML com o dos recortes, pelo contrato
`data-*` do HTML ([negocio/vade-mecum.md](../negocio/vade-mecum.md)). Só o texto legal é guardado; as anotações são
da LLM.

`dados/` passa a ser **versionado**: fontes originais, bases, recortes e o vade mecum. O
repositório é público, e texto de lei não tem direito autoral (Lei 9.610/98, art. 8º, IV). Um
teste de sincronia reextrai e recorta de novo, e os bytes têm de bater com os versionados.

O HTML segue a **ordem dos tópicos do edital**, não a da norma, e leva capa e rodapé assinados
"Lucas Vinha Teixeira · github.com/lucasvinha".

## Consequências

- A antiga "Etapa 2" deixa de existir com esse nome: o material de estudo é a Etapa 3.
- Os tópicos ganham o esquema `topicos-oj/2`, com a `norma` de cada grupo
  ([negocio/recorte-e-cli.md](../negocio/recorte-e-cli.md)).
- Um grupo dos tópicos tem uma norma só: o antigo "Demais normas" virou um grupo por norma, e
  o "Atualidades", que não é lei, tem `norma: null`.
- Os ids `nscgj`, `lei_sp10261`, `lei_sp11608` e `res_cnj354` nos tópicos são provisórios até o
  marco do PDF.
- Fixtures de teste continuam sendo enxertos; a fonte inteira mora em `dados/fontes/`.

## Histórico

- 2026-11-02: grupo dos tópicos com uma norma só e `null` no "Atualidades" (operador, na fase 3).
- 2026-11-02: a LLM deixa de escrever o HTML e passa a escrever a curadoria em JSON, que o
  `renderizar` transforma em HTML ([ADR-006](ADR-006-curadoria-em-json-e-render-deterministico.md)).
