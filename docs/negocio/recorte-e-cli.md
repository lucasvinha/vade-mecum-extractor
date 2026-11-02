# Recorte e CLI — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

Como o operador indica os artigos que quer, como eles são ordenados e quais comandos existem.
Usado por `recorte.py`, `modelo.chave_ordenacao` e `cli.py`. A semântica de faixa é o
[ADR-004](../decisoes/ADR-004-faixa-inclui-artigos-com-letra.md). Vizinho:
[modelo-de-dados.md](modelo-de-dados.md) (o recorte tem o mesmo esquema da base).

## §1. Requisito

- **RF18** — Gerar recorte a partir da base, com o mesmo esquema, sem reprocessar a fonte.

## §2. Sintaxe de entrada

Segue a notação do edital, que a CLI recebe como está escrita (confirmado na spec do M5, 2026-11-01):

```
1º a 12; 100-120; 121; 129; 150; 154; 293-305; 307; 308; 311-A; 312-317
994–1.091; 1.091-A
196, inciso XX
```

| Regra | Exemplo |
|---|---|
| Separador de item: `;` ou `,` | `8º; 9º`, `12, 13` |
| Faixa: `-`, `–` ou ` a ` | `1º a 12`, `994–1.091`, `293-305` |
| Ordinal e milhar opcionais, nas duas pontas | `1º–4º`, `1.169 a 1.173` |
| Depois de `-`, letra é sufixo e dígito é fim de faixa | `359-M-A`, `121-A–130`, `994-1.091` |
| Depois de `,` ou `;`, texto que não começa com dígito é qualificador do item anterior (P2) | `196, inciso XX`, `282, § 1º` |
| Qualificador sem item anterior, item vazio, item ilegível ou faixa invertida: erro de entrada | `inciso XX`, `abc`, `121-`, `130-121` |

A expressão também pode vir dos tópicos do edital (`claude/topicos-oj2026.json`): o `recortar`
monta a expressão da matéria com os itens dos grupos da norma da base (ADR-005). O MD do conteúdo
programático a CLI não lê. Uma chamada do `recortar` por norma.

## §3. Semântica e ordenação

- **Chave de ordenação:** `(numero, sufixo)`, com sufixo como tupla e sufixo vazio antes de qualquer letra. Assim: `121 < 121-A < 121-B < 122` e `359-M < 359-M-A < 359-M-B < 359-N`.
- **Faixa `a–b`:** inclui todo artigo com `chave(a) ≤ chave ≤ chave(b)` (ADR-004). Consequência: `121–130` inclui 121-A e 121-B, mas **não** 130-A, que vem depois de `130`. Esse comportamento bate com o edital, que cita `1.091-A` à parte da faixa `994–1.091`.
- **Artigo avulso `121`:** inclui só o art. 121. Artigo com letra entra se for citado (`311-A`) ou se estiver dentro de uma faixa. (P1, confirmada pelo operador em 2026-10-30.)
- **Ordem da saída:** a da base, cada artigo uma vez, mesmo coberto por mais de um item (`120-125; 121`).
- Item ou faixa que **não alcança** artigo nenhum, nem na base nem nos descartes, gera aviso, não erro.
- Granularidade sub-artigo (`196, inciso XX`; `282, § 1º`) **não** é recortada pelo `recortar`: o artigo inteiro entra, com aviso do trecho ignorado. (P2, confirmada pelo operador em 2026-10-30.)

## §4. Interface de linha de comando

```bash
python -m vademecum extrair --fonte "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm" --perfil cp --saida dados/cp/base.json
```
`extrair` lê a fonte e gera a base completa.
- `--fonte` aceita URL, `.htm`, `.mht` ou `.pdf`.
- `--perfil` escolhe as regras da norma ([pipeline-e-perfis.md](pipeline-e-perfis.md)); se omitido, usa `padrao`.
- `--saida` é o caminho do JSON.
- O relatório é gravado ao lado, como `base.relatorio.json`. Não há versão em Markdown: quem lê
  é um LLM (Etapa 3), e o JSON guarda os descartes de forma estruturada (ADR-001).

```bash
python -m vademecum extrair --fonte LEI_SECA_OJ26.pdf --perfil-auto --saida-dir dados/legislacao_especial/
```
- Em PDF multi-norma, `--perfil-auto` escolhe o perfil de cada norma segmentada pelo título.
- `--saida-dir` recebe um JSON por norma.

```bash
python -m vademecum recortar --base dados/cp/base.json --artigos "1-12; 100-120; 121; 129; 150; 154; 293-305" --saida dados/cp/recorte_oj26.json
```
`recortar` filtra uma base existente sem reler a fonte.
- `--base` é o JSON gravado pelo `extrair`; o relatório dele (`<base>.relatorio.json`) tem de
  estar ao lado.
- `--artigos` recebe a expressão da sintaxe de entrada acima.
- `--saida` recebe o JSON do recorte, com o mesmo esquema da base; `norma` e `metadados` vêm da
  base, e `recorte` guarda a expressão e o nome do arquivo da base, sem a pasta
  ([modelo-de-dados.md](modelo-de-dados.md)).
- O relatório do recorte vai ao lado (`<saida>.relatorio.json`), no esquema do relatório da base.
  Traz um `aviso` por item que não alcança artigo e por qualificador ignorado, com `origem` igual
  ao item escrito, e os `descarte` da base cujo artigo cai no recorte, copiados sem mudança (P4).
  Item que só existe nos descartes (`189` no CP) não gera aviso: o descarte já diz que ele saiu.
- Erro de entrada: base ou relatório da base ausente, `schema_version` diferente do atual e
  expressão inválida. A mensagem cita o arquivo ou o item.

`python -m vademecum` executa o pacote `vademecum` como programa: roda o `__main__.py` dele, que despacha os subcomandos.

Erro de entrada sai com código 2 ([docs/README.md § Contratos](../README.md#contratos)).

## §5. Armadilhas e limites conhecidos

- `121–130` não traz 130-A (ADR-004); quem quiser 130-A cita à parte.
- `196, incisos XX, XXI` funciona, mas `282, §§ 1º, 2º` não: o `2º` começa com dígito e vira o
  art. 2º. Quem chama escreve `282, § 1º; 282, § 2º`.
- O descarte sem `id` (linha tachada do HTML) não se liga a artigo e fica só no relatório da base.
