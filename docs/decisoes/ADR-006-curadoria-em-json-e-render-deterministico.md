# ADR-006 — Vade mecum por curadoria em JSON e `renderizar` determinístico

**Status:** aceito em 2026-11-02 (decidido pelo operador na entrevista da spec do render; emenda
o [ADR-005](ADR-005-vade-mecum-em-tres-etapas.md))

## Problema

No ADR-005, a LLM escrevia o HTML inteiro do vade mecum: texto legal, layout e anotações. O
piloto de Direito Penal (`dados/vade-mecum/oj26/penal.html`) passou no `conferir`, mas ficou
aquém da amostra de estilo (`docs/etapa3/estilo.md` e `referencia-visual.pdf`): grifos de uma
cor só, pena sem a caixa da referência, uma coluna, quadros com pena digitada sem conferência.
O script que gerou o piloto não ficou no repositório, e cada geração reinventaria o estilo.

## Opções discutidas

| Opção | A favor | Contra |
|---|---|---|
| LLM gera o HTML (ADR-005) | Nada a construir | Layout reinventado a cada geração; anotações sem guarda; pena do quadro não conferida |
| LLM gera o HTML com um CSS fixo | Estilo estável | A LLM continua montando a marcação e copiando penas à mão |
| LLM escreve a curadoria em JSON, `renderizar` gera o HTML | Layout determinístico e versionado; marcas e penas validadas | Código de layout em Python; a curadoria tem esquema próprio |

## Decisão

A Etapa 3 se divide em duas partes:

1. **Curadoria** (LLM): `dados/curadoria/<edital>/<materia>.json`, esquema `curadoria-vm/1`
   ([negocio/vade-mecum.md](../negocio/vade-mecum.md)). Traz só o que é de estudo: marcas por
   categoria, pontos de atenção, quadros comparativos e avisos de capa, ancorados pelo id
   `<norma>:<id>` dos recortes. Nunca traz texto legal.
2. **`renderizar`** (determinístico): tópicos + recortes + relatórios + curadoria → HTML, com o
   CSS de `src/vademecum/estilo/vade-mecum.css` embutido. A marca é casada por substring no
   texto do nó, e a pena citada num quadro é ancorada e conferida contra a do recorte.

O `conferir` continua valendo sobre o HTML e o contrato `data-*` não muda: o `renderizar`
produz o mesmo contrato que a LLM produzia. A ordem dos tópicos, a capa assinada e o PDF salvo
do navegador seguem o ADR-005.

## Consequências

- A LLM não escreve HTML: `docs/etapa3/INSTRUCOES.md` passa a pedir a curadoria e a rodar o
  `renderizar` e o `conferir`.
- O erro de curadoria (trecho não encontrado, ambíguo, pena divergente) sai 1, sem gravar o
  HTML. O excesso de grifo (~15% do artigo) só avisa.
- Se a lei for capturada de novo, a curadoria se religa pelos ids. Trecho que sumiu do texto
  vira erro, não marca perdida em silêncio.
- Diagramas em SVG, flashcards e as correções de extração do `estilo.md` ficam fora, como itens
  próprios em [PENDENCIAS](../PENDENCIAS.md).
