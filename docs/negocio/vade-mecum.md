# Vade mecum (Etapa 3) — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

O HTML do vade mecum é gerado pelo `renderizar` a partir dos recortes, dos relatórios, dos
tópicos do edital e da curadoria, que uma LLM escreve
([ADR-005](../decisoes/ADR-005-vade-mecum-em-tres-etapas.md),
[ADR-006](../decisoes/ADR-006-curadoria-em-json-e-render-deterministico.md)). Este documento
traz o esquema da curadoria e o contrato entre o HTML e o `conferir`, que garante que o texto
legal dele é o dos recortes. Usado por `curadoria.py`, `render.py`, `conferencia.py` e `cli.py`.
Vizinhos: [modelo-de-dados.md](modelo-de-dados.md) (os nós e os `id`) e
[recorte-e-cli.md](recorte-e-cli.md) (o recorte).

## Curadoria

`dados/curadoria/<edital>/<materia>.json`, esquema `curadoria-vm/1`. Só anotação de estudo:
texto legal nunca entra aqui.

```json
{"schema": "curadoria-vm/1", "edital": "oj26", "materia": "penal", "gerado_em": "2026-11-02",
 "avisos_capa": ["..."],
 "dispositivos": {"cp:art312": {"marcas": [{"trecho": "Apropriar-se", "cat": "verbo"}],
                                "atencao": ["..."]}},
 "quadros": [{"depois_de": "cp:art314", "titulo": "Peculato e figuras próximas",
              "colunas": ["Dispositivo", "Verbo nuclear", "Elemento distintivo", "Pena"],
              "linhas": [["Art. 312 — Peculato", "apropriar-se", "tem a posse",
                          {"pena": "cp:art312.pena1", "texto": "reclusão, 2 a 12 anos, e multa"}],
                         ["Art. 304 — Uso de documento falso", "fazer uso", "não falsifica",
                          {"pena": "cp:art304.pena1"}]],
              "nota": "..."}]}
```

- **Chave** `<norma>:<id>`, com o `norma.id` e o `id` do nó no recorte: a matéria pode ter mais
  de uma norma.
- **`cat`** da marca: `verbo` (conduta nuclear), `sujeito` (quem pode praticar),
  `especializante` (o que separa o tipo do vizinho), `quantidade` (prazos, frações) e `condicao`
  (subsidiariedade e procedibilidade). A pena não é categoria: tem caixa própria.
- **Marca:** o `trecho` é procurado no `texto` do nó, os dois em NFC. Tem de aparecer uma vez
  só e não pode sobrepor outra marca do nó. Vira `<mark class="hl-<cat>">` dentro do
  `data-campo="texto"`, o que não muda o texto conferido.
- **Atenção:** cada texto vira um aside depois do dispositivo, como material de apoio.
- **Quadro:** sai em largura total logo depois do nó `depois_de`. Célula é texto ou pena.
- **Pena no quadro:** `{"pena": "<id da pena>", "texto": "..."}` declara uma pena por célula.
  Espécie, mínimo, máximo, unidade e multa do `texto` têm de bater com as da pena do recorte.
  "dois", "2" e "2 (dois)" valem o mesmo. A multa é ausente, cumulativa ("e multa", "além da
  multa") ou alternativa ("ou multa"), e "e" × "ou" conta.
- **Pena literal:** `{"pena": "<id>"}`, sem `texto`, sai com o texto da pena do recorte, sem
  conferência. É a saída para a pena com duas faixas ou por remissão: com `texto`, ela é erro.
- **`gerado_em`** é a data da capa e vem da curadoria, nunca do relógio (RNF03).

| Resultado | Quando |
|---|---|
| **Erro** (sai 1, sem gravar) | id inexistente no recorte; trecho não encontrado, ambíguo ou sobreposto; `cat` fora da lista; pena divergente ou, com `texto`, não interpretável |
| **Aviso** (sai 0) | marcas acima de ~15% dos caracteres do artigo, sem contar a pena |

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
python -m vademecum renderizar --topicos claude/topicos-oj2026.json --materia penal \
  --recorte dados/recortes/oj26/penal/cp.json --curadoria dados/curadoria/oj26/penal.json \
  --saida dados/vade-mecum/oj26/penal.html
```
- `--recorte` é repetível: um por norma da matéria. O relatório de cada um é lido ao lado
  (`<recorte>.relatorio.json`), de onde saem os revogados e os avisos.
- `--curadoria` é opcional: sem ela, sai só o texto legal.
- Sai 0 e grava o HTML; o aviso de teto vai para o stderr (`aviso: <norma>:<id>: <motivo>`) e
  não muda o código. Erro de curadoria sai 1, uma linha por erro na saída padrão, **sem gravar
  o HTML**. Erro de entrada sai 2: tópicos, recorte, relatório ou curadoria ausentes ou com JSON
  inválido, curadoria sem o esquema ou com forma errada, matéria inexistente, norma de grupo sem
  recorte e artigo do recorte que nenhum item cobre.

```bash
python -m vademecum conferir --recorte dados/recortes/oj26/penal/cp.json --html dados/vade-mecum/oj26/penal.html
```
- `--recorte` é repetível: um por norma da matéria.
- `--html` é o vade mecum gerado.
- Sai 0 sem divergência e 1 com divergência. Erro de entrada (recorte ou HTML ausente,
  `schema_version` diferente do atual) sai 2.

## Armadilhas e limites conhecidos

- O `conferir` não confere as anotações. A pena do quadro é conferida pelo `renderizar`, mas a
  escolha do trecho marcado, o texto das atenções e as demais células são do operador.
- Tirar o `data-id` de um nó faz os campos dele contarem para o pai, e a divergência aparece no
  pai (`campo texto repetido`).
