# Vade mecum (Etapa 3) — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

O HTML do vade mecum é gerado por uma LLM a partir dos recortes, dos relatórios e dos tópicos do
edital ([ADR-005](../decisoes/ADR-005-vade-mecum-em-tres-etapas.md)). Este documento é o
contrato entre esse HTML e o `conferir`, que garante que o texto legal dele é o dos recortes.
Usado por `conferencia.py` e `cli.py`. Vizinhos: [modelo-de-dados.md](modelo-de-dados.md) (os
nós e os `id`) e [recorte-e-cli.md](recorte-e-cli.md) (o recorte).

## Contrato do HTML

- Cada norma fica num elemento `[data-norma="<norma.id>"]`. A mesma norma pode aparecer em mais
  de um elemento, porque a ordem do HTML é a dos tópicos do edital, não a da norma.
- Cada nó do recorte (artigo, parágrafo, inciso, alínea, item, pena) é um `[data-id="<id>"]`
  dentro da sua norma, com o `id` do JSON.
- Os campos do nó ficam em `[data-campo="rotulo"|"rubrica"|"texto"]`. Conta só o campo cujo
  `[data-id]` mais próximo é o próprio nó: o filho pode ficar aninhado no pai.
- O texto do campo é comparado com espaços colapsados (inclusive o `&nbsp;`) e sem os das
  pontas. Fora isso, a comparação é **literal**: grafia antiga, pontuação e acento contam.
  Marcação dentro do campo (`<mark>`, `<strong>`) não muda o texto e é livre.
- Campo que o nó não tem (rubrica nula, rótulo da pena) não aparece no HTML.
- Anotações e quadros (realces, pontos de atenção, comparativos, capa, rodapé) não levam
  `data-id` nem `data-campo` e não são conferidos.

## Divergências

O `conferir` imprime uma linha por divergência, `<norma>:<id>: <motivo>`:

| Motivo | Quando |
|---|---|
| `nó ausente` | nó do recorte sem `[data-id]` na sua norma |
| `campo <c> divergente` | o texto do campo difere do recorte; a linha traz os dois |
| `campo <c> ausente`, `a mais`, `repetido` ou `desconhecido` | o nó não tem o campo, tem um que o recorte não tem, tem o campo duas vezes ou um `data-campo` fora da lista |
| `data-id desconhecido` | `data-id` que não está no recorte da norma; fora de `[data-norma]`, a norma sai `-` |
| `data-id repetido` | o mesmo nó duas vezes na mesma norma |

## Interface de linha de comando

```bash
python -m vademecum conferir --recorte dados/recortes/oj26/penal/cp.json --html dados/vade-mecum/oj26/penal.html
```
- `--recorte` é repetível: um por norma da matéria.
- `--html` é o vade mecum gerado.
- Sai 0 sem divergência e 1 com divergência. Erro de entrada (recorte ou HTML ausente,
  `schema_version` diferente do atual) sai 2.

## Armadilhas e limites conhecidos

- O `conferir` não confere as anotações: um realce errado ou um quadro com pena trocada passa.
  Quem garante o conteúdo delas é o operador.
- Tirar o `data-id` de um nó faz os campos dele contarem para o pai, e a divergência aparece no
  pai (`campo texto repetido`).
