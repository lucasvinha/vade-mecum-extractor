# Pipeline e perfis — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

Por quais etapas a fonte passa até virar base, qual o contrato entre elas e o que cada perfil de
norma pode mudar (ADR-002). Entrada e saída de cada módulo e as dependências entre eles estão em
[docs/README.md § Mapa do código](../README.md#mapa-do-código). Vizinhos: [fontes.md](fontes.md)
e [parsing.md](parsing.md).

## §1. Pipeline

```
 Leitor HTML ─┐                    ┌─► Segmentador de normas (PDF multi-norma)
 Leitor PDF  ─┴─► list[LinhaFonte] ┴─► Normalizador ─► Parser (máquina de estados)
                                                          │
                                       Filtro de vigência ◄┘
                                                │
                       Validador ─► Base (JSON) + Relatório ─► Recorte (JSON)
```

O contrato central é `LinhaFonte`. Tudo à direita dele independe da fonte, e isso é o que torna o parser genérico.

```python
@dataclass
class LinhaFonte:
    texto: str              # texto já com espaços colapsados
    negrito: bool           # linha inteiramente em negrito
    rotulo_negrito: bool    # só o início da linha em negrito (padrão do PDF)
    centralizado: bool
    cor: str | None         # útil para notas e títulos no PDF
    origem: str             # "html:p#123" | "pdf:p3:col2:l14"  (rastreabilidade)
```

## §2. Responsabilidade de cada etapa

Caminhos relativos a `src/vademecum/`.

| Módulo | Responsabilidade |
|---|---|
| `fontes/html.py` | URL, `.htm` e `.mht` → `LinhaFonte` (decodificação, colapso de espaços, quebra por bloco, flags de negrito e centralizado). |
| `fontes/pdf.py` | PDF → `LinhaFonte` (colunas, remoção de cabeçalho e rodapé, negrito pelo mapa de fontes, cor). |
| `segmentador.py` | Divide o fluxo em normas (P5). |
| `normalizador.py` | Ordinais, travessões, junção de linhas quebradas, separação de notas. |
| `parser.py` | Máquina de estados: hierarquia, dispositivos, rubricas, penas. |
| `notas.py` | Classificação de notas ([vigencia-e-notas.md](vigencia-e-notas.md)). |
| `vigencia.py` | Aplica ADR-001 e alimenta o relatório. |
| `validador.py` | Regras de consistência V1–V7 ([PADRAO_OURO](../PADRAO_OURO.md)). |
| `recorte.py` | Sintaxe e semântica do recorte ([recorte-e-cli.md](recorte-e-cli.md)). |
| `modelo.py` | Dataclasses + serialização JSON. |
| `cli.py` | Comandos `extrair` e `recortar` ([recorte-e-cli.md](recorte-e-cli.md)). |
| `perfil.py` | Carrega e mescla `padrao.toml` com o perfil específico. |
| `perfis/*.toml` | Configuração por norma (seção seguinte), distribuída dentro do pacote. |

## §3. Perfis por norma (ADR-002)

O parser é um só. O que varia fica num arquivo de perfil, por exemplo `perfis/cp.toml`, `perfis/nscgj.toml`, `perfis/lei_sp.toml`:

- prefixos de artigo (`Art.`, `Artigo`);
- vocabulário de notas (`Redação dada`/`Incluído` × `Alterado`/`Acrescentado`);
- níveis hierárquicos reconhecidos (`PARTE`, `LIVRO`, `TÍTULO`, `CAPÍTULO`, `Seção`, `Subseção`);
- se existe rubrica e se existe linha de pena;
- validação de lacunas: ligada para norma integral, desligada para PDF-recorte.

Um perfil `padrao` cobre os casos comuns. Os perfis específicos só sobrescrevem diferenças.

O leitor PDF expõe no perfil os parâmetros que mudam com a origem do arquivo (colunas, zonas de
cabeçalho e rodapé, mapa de fontes), para PDFs de outras origens (Senado, editoras).

## §4. Armadilhas e limites conhecidos

- Se uma fase precisa de `if norma == ...` no parser, falta uma chave no perfil.
- Só `cli.py` e `fontes/*` fazem I/O; as etapas do meio são funções puras.
