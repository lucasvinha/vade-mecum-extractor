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

Segue a notação do edital: itens separados por `;` ou `,`; faixa com `-`, `–` ou `a`; milhar opcional.

```
1-12; 100-120; 121; 129; 150; 154; 293-305; 307; 308; 311-A; 312-317
994-1.091; 1.091-A
```

## §3. Semântica e ordenação

- **Chave de ordenação:** `(numero, sufixo)`, com sufixo como tupla e sufixo vazio antes de qualquer letra. Assim: `121 < 121-A < 121-B < 122` e `359-M < 359-M-A < 359-M-B < 359-N`.
- **Faixa `a–b`:** inclui todo artigo com `chave(a) ≤ chave ≤ chave(b)` (ADR-004). Consequência: `121–130` inclui 121-A e 121-B, mas **não** 130-A, que vem depois de `130`. Esse comportamento bate com o edital, que cita `1.091-A` à parte da faixa `994–1.091`.
- **Artigo avulso `121`:** inclui só o art. 121. Artigo com letra entra se for citado (`311-A`) ou se estiver dentro de uma faixa. (Ver pendência P1 em [PENDENCIAS.md](../PENDENCIAS.md).)
- Item do recorte que **não existe** na base gera aviso, não erro.
- Granularidade sub-artigo (`196, inciso XX`; `282, § 1º`) **não** é recortada na Etapa 1: o artigo inteiro entra. Ver pendência P2.

## §4. Interface de linha de comando (proposta)

```bash
python -m vademecum extrair --fonte "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm" --perfil cp --saida dados/cp/base.json
```
`extrair` lê a fonte e gera a base completa.
- `--fonte` aceita URL, `.htm`, `.mht` ou `.pdf`.
- `--perfil` escolhe as regras da norma ([pipeline-e-perfis.md](pipeline-e-perfis.md)); se omitido, usa `padrao`.
- `--saida` é o caminho do JSON.
- O relatório é gravado ao lado, como `base.relatorio.md`.

```bash
python -m vademecum extrair --fonte LEI_SECA_OJ26.pdf --perfil-auto --saida-dir dados/legislacao_especial/
```
- Em PDF multi-norma, `--perfil-auto` escolhe o perfil de cada norma segmentada pelo título.
- `--saida-dir` recebe um JSON por norma.

```bash
python -m vademecum recortar --base dados/cp/base.json --artigos "1-12; 100-120; 121; 129; 150; 154; 293-305" --saida dados/cp/recorte_oj26.json
```
`recortar` filtra uma base existente sem reler a fonte.
- `--artigos` recebe a expressão da sintaxe de entrada acima.
- `--saida` recebe o JSON do recorte.

`python -m vademecum` executa o pacote `vademecum` como programa: roda o `__main__.py` dele, que despacha os subcomandos.

Erro de entrada sai com código 2 ([docs/README.md § Contratos](../README.md#contratos)).

## §5. Armadilhas e limites conhecidos

- `121–130` não traz 130-A (ADR-004); quem quiser 130-A cita à parte.
