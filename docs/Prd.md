# PRD — Etapa 1: Extração estruturada de legislação

| Campo | Valor |
|---|---|
| Projeto | Vade mecum de estudo — TJSP Oficial de Justiça 2026 |
| Repositório | `vade-mecum-extractor` · pacote Python `vademecum` |
| Etapa | 1 de 2 — fonte bruta → base estruturada (+ recorte) |
| Versão | 0.2 — 26/10/2026 (0.1 de 25/10/2026: levantamento inicial) |
| Status | Direção aprovada para implementação; pendências na §12 |
| Fontes analisadas | `DEL2848compilado_2.mht` (Planalto, salvo em 26/10/2026) · `LEI_SECA_OJ26_Legislacao_Especial.17.10.pdf` (18 p.) |

**Legenda de evidência:** **[Verificado]** = conferido nas fontes anexadas · **[Inferido]** = dedução a partir das amostras, a confirmar na implementação · **[Decisão]** = definido pelo usuário.

---

## 1. Objetivo

Construir um **parser genérico** em Python que receba o texto bruto de uma norma — página HTML do Planalto ou PDF — e produza uma **base estruturada** (artigo › parágrafo › inciso › alínea, com rubricas, penas e notas legislativas). Sobre essa base, um segundo comando gera o **recorte** de artigos indicado pelo usuário, no mesmo formato.

A Etapa 2 (material de estudo: realces, quadros comparativos, pontos de atenção) consome essa base e **está fora do escopo deste documento**. Mas a Etapa 1 deve preservar os dados que a Etapa 2 vai precisar (ver §7, campos de notas e penas).

## 2. Escopo

**Dentro**
- Leitura de HTML do Planalto: URL, `.htm`/`.html` salvo ou `.mht` salvo pelo navegador.
- Leitura de PDF com texto (não escaneado), inclusive PDF montado com várias normas.
- Normalização, parsing hierárquico, classificação de notas, filtro de vigência.
- Exportação da base completa e do recorte em JSON.
- Relatório de extração (avisos, descartes, inconsistências).

**Fora**
- OCR de PDF escaneado.
- Material de estudo, realces e quadros (Etapa 2).
- Reconstrução de redações anteriores ou históricas.
- Resolução automática da data exata de leis alteradoras (ver §12, P3).

## 3. Decisões já tomadas

| ID | Decisão | Origem |
|---|---|---|
| D1 | A base contém **somente texto vigente**. Dispositivos revogados ou vetados são descartados da base e listados no relatório de extração. | [Decisão] |
| D2 | O parser é **genérico**, sem lógica fixa do Código Penal. Particularidades de cada norma ficam em **perfis de configuração** (§5.3). | [Decisão] |
| D3 | A extração da fonte bruta traz **todos** os artigos da norma. | [Decisão] |
| D4 | No recorte, uma **faixa** `a–b` inclui os artigos com letra que estão dentro dela (ex.: `121–130` inclui 121-A e 121-B). | [Decisão] |
| D5 | Formato canônico de saída: **JSON hierárquico**, UTF-8. CSV é rejeitado porque achata a árvore de dispositivos. | [Decisão] |
| D6 | O PDF é tratado como fonte **já estruturada**: montado no Word, com texto selecionável. | [Decisão] |

## 4. Características observadas nas fontes

### 4.1 HTML do Planalto (Código Penal)

| # | Característica | Evidência | Consequência |
|---|---|---|---|
| H1 | Codificação **windows-1252** declarada em `<meta>`. | [Verificado] | Decodificar pelo charset declarado e emitir UTF-8. |
| H2 | **Sem marcação semântica.** Só `<p>`, `<b>`/`<strong>`, `<font>`, `<a>`, `<span>`. Só existem 8 âncoras `name="art…"` em todo o documento. | [Verificado] | O parse é **por texto + regex**, não por DOM ou âncoras. |
| H3 | O código-fonte tem quebras de linha **no meio das frases** (ex.: `§` numa linha e `1º Se o agente…` na seguinte). As quebras reais são `<p>` e `<br>`. | [Verificado] | Colapsar espaços em branco **antes** de quebrar em blocos; quebrar só em `<p>`/`<br>`/`<div>`/`<blockquote>`. |
| H4 | Um mesmo `<p>` pode conter **vários artigos** separados por `<br>` (ex.: arts. 187, 189 e 191). | [Verificado] | A unidade de parse é a **linha lógica**, não o parágrafo HTML. |
| H5 | Títulos estruturais ficam em `<p align="CENTER"><strong>` (ex.: `TÍTULO I<br>DOS CRIMES CONTRA A PESSOA`). | [Verificado] | Centralizado + negrito + palavra-chave identifica um nível hierárquico. A linha seguinte é o nome do nível. |
| H6 | Rubricas ("Homicídio simples", "Caso de diminuição de pena") ficam em `<p align="left"><b>`, isoladas. Também aparecem **antes de parágrafos e incisos**, não só antes de artigos (ex.: "Homicídio contra menor de 14 anos" antes do inciso IX do art. 121, § 2º). | [Verificado] | Rubrica = bloco 100% negrito, não centralizado, sem padrão de dispositivo. Ela se liga ao **próximo dispositivo de qualquer nível**. |
| H7 | Rubricas podem carregar nota: `Feminicídio (Incluído pela Lei nº 14.994, de 2024)`. | [Verificado] | Separar a nota do texto da rubrica. |
| H8 | **`<strike>` não marca texto revogado.** As 6 ocorrências estão vazias (só envolvem `<br>` ou espaço). | [Verificado] | Ignorar `<strike>`. A revogação é identificada pela **nota**, não pela formatação. |
| H9 | Notas aparecem inline, entre parênteses, em geral como link: Incluído (610), Redação dada (480), Vigência (74), Revogado (47), Vide (34), Vetado (17). | [Verificado] | Extrair todas e classificar por tipo (§7.3). |
| H10 | "Vigência" aparece **com e sem parênteses** (25 linhas terminam em `) Vigência`). | [Verificado] | O regex de notas deve aceitar as duas formas. |
| H11 | Variações de numeração: `Art. 1º -`, `Art. 10 -`, `Art. 121.`, `Art 187.` (sem ponto), `§ 2°` (grau), `§ 4o` (letra "o"), `§ 2o-A`, `§ 2º-B.` | [Verificado] | Normalizar `º`/`°`/`o` como ordinal; aceitar `Art` com ou sem ponto e `-`, `–` ou `.` como separador. |
| H12 | Sufixos de **dois níveis**: `Art. 359-M-A`, `Art. 359-M-B`. | [Verificado] | O identificador e a ordenação suportam sufixo composto (§9.2). |
| H13 | Travessão (`–`) e hífen (`-`) se alternam: `VII – contra:` / `I - mediante…` / `Pena – reclusão`. | [Verificado] | Tratar os dois como o mesmo separador. |
| H14 | A linha `Pena -` **não fecha** o dispositivo. No art. 121, § 2º, há uma pena depois do inciso V, os incisos VII–X continuam no mesmo § 2º e a pena se repete no final. | [Verificado] | A pena é um nó **posicional** dentro do pai. O parser não deve encerrar o § ao encontrar `Pena`. |
| H15 | Falso positivo de revogação: `Art. 88 - Revogado o livramento, não poderá ser novamente concedido…` é texto **vigente**. | [Verificado] | Só é revogado o dispositivo cujo conteúdo, tirando as notas, está **vazio** ou é exatamente `Revogado.`/`Revogados.`. |
| H16 | Rubrica que fica **órfã** quando o dispositivo seguinte é revogado (ex.: "Feminicídio" antes do inciso VI revogado do art. 121, § 2º). | [Verificado] | Descartar a rubrica junto com o dispositivo revogado. |
| H17 | Cabeçalho da página (Presidência, "Vide" gerais, ementa, preâmbulo) e rodapé (local/data, assinaturas, "Este texto não substitui o publicado no DOU…"). | [Verificado] | Guardar preâmbulo e rodapé em `metadados`, fora da árvore de artigos. |
| H18 | Títulos estruturais com nota: `TÍTULO I / DA APLICAÇÃO DA LEI PENAL / (Redação dada…)`; `CAPÍTULO IV / (Incluído…) / DOS CRIMES…` (a nota pode vir **antes** do nome). | [Verificado] | O nome do nível é a próxima linha que não é nota. |
| H19 | Numeração-base do CP sem lacunas (1 a 361) e último artigo `Art. 361 - Este Código entrará em vigor…`. | [Verificado] | Usar como critério de aceite (§11). |

### 4.2 PDF montado (Legislação Especial)

| # | Característica | Evidência | Consequência |
|---|---|---|---|
| P1 | Gerado por "Microsoft: Print To PDF" a partir do Word. Texto selecionável. | [Verificado] | `pdfplumber` resolve; não precisa de OCR. |
| P2 | **Duas colunas.** A extração padrão intercala as colunas. | [Verificado] | Recortar cada página em duas colunas (esquerda, depois direita) antes de extrair linhas. Detectar a divisória ou usar a metade da largura, configurável. |
| P3 | Cabeçalho de página `LEGISLAÇÃO ESPECIAL` e número de página (fonte F1, 12 pt). | [Verificado] | Remover por fonte/tamanho/posição. |
| P4 | Rótulos em **negrito** (`Art. 1º`, `§ 1º`, `I -`, `a)`, `Parágrafo único`); corpo em fonte regular. Os nomes de fonte são genéricos (`CIDFont+F3` = negrito, `CIDFont+F4` = regular). | [Verificado] | O negrito vem do **mapeamento de fonte por documento**, não do nome. Rótulo em negrito no início da linha é sinal forte de novo dispositivo. |
| P5 | **Várias normas num só PDF**: NSCGJ Tomo I, Lei 6.830/80, Res. CNJ 354/2020, Lei SP 11.608/03. Cada norma começa com título em azul-escuro sublinhado, ementa em vermelho-escuro e preâmbulo. | [Verificado] | Segmentar o PDF em **documentos** antes do parse. A saída tem uma base por norma (ou uma base com várias normas, ver §7.1). |
| P6 | O PDF já é um **recorte**: a numeração tem lacunas (NSCGJ pula de 4 para 33, 49, 105…). | [Verificado] | Não acusar lacuna no modo PDF; acusar só **numeração fora de ordem**. |
| P7 | Artigos **parciais**: o edital pede "196, inciso XX", e o PDF traz só o inciso XX do art. 196. | [Verificado] | Modelo aceita artigo sem caput ou com incisos esparsos (`parcial: true`). |
| P8 | Hierarquia **incompleta**: o bloco dos arts. 994 e seguintes aparece sob "DOS OFICIAIS DE JUSTIÇA / Seção I", sem a linha "CAPÍTULO VII". | [Verificado] | Campos de hierarquia são opcionais. Título sem palavra-chave vira `rotulo_livre`. |
| P9 | Lei estadual usa `Artigo 1° -` em vez de `Art. 1º`. | [Verificado] | O perfil define os prefixos aceitos (`Art.`, `Artigo`). |
| P10 | Notas da NSCGJ usam outro vocabulário e cor azul: `(Alterado pelo Provimento CG Nº 33/2024)`, `(Acrescentado pelo…)`, `(Revogado pelo…)`. | [Verificado] | O vocabulário de notas é configurável por perfil. A cor serve como sinal auxiliar. |
| P11 | Revogação em faixa: `Art. 1.054 a Art. 1091. Revogados.` | [Verificado] | Reconhecer e registrar a faixa como revogada (relatório), sem gerar artigos. |
| P12 | Revogação sem parênteses: `Artigo 10 - Revogado.`; `I – Revogado. (Revogado pelo Provimento CG Nº 03/2026)`. | [Verificado] | Mesma regra do H15. |
| P13 | Números com separador de milhar: `Art. 1.247`, `1.091-A`. | [Verificado] | Normalizar `1.091` → 1091 no número; manter o rótulo original para exibição. |
| P14 | Linhas terminadas em hífen são palavras compostas (`apresentar-`/`se`, `e-`/`mail`, `devolvê-`/`lo`), não hifenização tipográfica. | [Inferido, 6 amostras] | Ao juntar linhas, manter o hífen e não inserir espaço. |
| P15 | `Parágrafo único.` **no meio da linha**, colado ao caput (Res. CNJ 354, art. 8º). | [Verificado] | Não quebrar automaticamente. Gerar **aviso** no relatório para revisão manual. |
| P16 | Marcador `(NR)` (nova redação). | [Verificado, 1 ocorrência] | Tratar como nota do tipo `redacao`. |

## 5. Arquitetura

### 5.1 Pipeline

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

### 5.2 Módulos

Caminhos relativos a `src/vademecum/`. Contratos e dependências entre módulos: `docs/README.md § Mapa do código`.

| Módulo | Responsabilidade |
|---|---|
| `fontes/html.py` | URL, `.htm` e `.mht` → `LinhaFonte` (decodificação, colapso de espaços, quebra por bloco, flags de negrito e centralizado). |
| `fontes/pdf.py` | PDF → `LinhaFonte` (colunas, remoção de cabeçalho e rodapé, negrito pelo mapa de fontes, cor). |
| `segmentador.py` | Divide o fluxo em normas (P5). |
| `normalizador.py` | Ordinais, travessões, junção de linhas quebradas, separação de notas. |
| `parser.py` | Máquina de estados: hierarquia, dispositivos, rubricas, penas. |
| `notas.py` | Classificação de notas (§7.3). |
| `vigencia.py` | Aplica D1 e alimenta o relatório. |
| `validador.py` | Regras de consistência (§11). |
| `recorte.py` | Sintaxe e semântica do recorte (§9). |
| `modelo.py` | Dataclasses + serialização JSON. |
| `cli.py` | Comandos `extrair` e `recortar` (§10). |
| `perfil.py` | Carrega e mescla `padrao.toml` com o perfil específico. |
| `perfis/*.toml` | Configuração por norma (§5.3), distribuída dentro do pacote. |

### 5.3 Perfis por norma (D2)

O parser é um só. O que varia fica num arquivo de perfil, por exemplo `perfis/cp.toml`, `perfis/nscgj.toml`, `perfis/lei_sp.toml`:

- prefixos de artigo (`Art.`, `Artigo`);
- vocabulário de notas (`Redação dada`/`Incluído` × `Alterado`/`Acrescentado`);
- níveis hierárquicos reconhecidos (`PARTE`, `LIVRO`, `TÍTULO`, `CAPÍTULO`, `Seção`, `Subseção`);
- se existe rubrica e se existe linha de pena;
- validação de lacunas: ligada para norma integral, desligada para PDF-recorte.

Um perfil `padrao` cobre os casos comuns. Os perfis específicos só sobrescrevem diferenças.

## 6. Requisitos funcionais

### Leitura
- **RF01** — Aceitar como fonte: URL HTTP(S), arquivo `.htm`/`.html`, `.mht`/`.mhtml` e `.pdf`. O tipo é detectado pela extensão ou pelo conteúdo.
- **RF02** — Ao baixar por URL, salvar o HTML bruto em cache local com data e SHA-256, para reprodutibilidade.
- **RF03** — Em `.mht`, extrair a parte `text/html` principal (MIME `multipart/related`) e decodificar pelo charset declarado (H1).
- **RF04** — No HTML, colapsar espaços em branco e só então quebrar linhas em `<p>`, `<br>`, `<div>`, `<blockquote>`, `<tr>` (H3, H4).
- **RF05** — No PDF, extrair por coluna (P2), remover cabeçalho e número de página (P3) e mapear negrito e cor por caractere (P4).
- **RF06** — Rejeitar com mensagem clara um PDF sem camada de texto (OCR está fora de escopo).

### Parsing
- **RF07** — Reconhecer níveis hierárquicos configuráveis, com nome na linha seguinte e nota antes ou depois do nome (H5, H18). Hierarquia ausente não é erro (P8).
- **RF08** — Reconhecer dispositivos: artigo (inclusive sufixos simples e compostos e milhar: H11, H12, P13), `§ n` e `Parágrafo único`, inciso romano, alínea `a)`, item numérico (`1.`, `2.`; reservado para outras normas).
- **RF09** — Reconhecer a linha `Pena –` como nó posicional do dispositivo corrente (H14).
- **RF10** — Reconhecer rubrica (bloco em negrito no HTML; heurística no PDF) e ligá-la ao próximo dispositivo de qualquer nível (H6).
- **RF11** — Juntar continuação de linha ao dispositivo corrente: linha que não abre dispositivo, título, rubrica nem nota é continuação. No PDF, aplicar a regra do hífen (P14).
- **RF12** — Extrair notas entre parênteses (e "Vigência" sem parênteses) do texto, guardá-las no nó e deixar o `texto` limpo (H9, H10, P10, P16).
- **RF13** — Segmentar PDF multi-norma e identificar cada norma por título, número e data (P5).

### Vigência (D1)
- **RF14** — Descartar dispositivo cujo conteúdo, sem notas, é vazio, `Revogado(s).` ou `(VETADO)`. Descartar junto a rubrica órfã (H15, H16, P12).
- **RF15** — Revogação em faixa (`Art. X a Art. Y. Revogados.`) não gera artigo; vai para o relatório (P11).
- **RF16** — Todo descarte é registrado no relatório com rótulo, motivo e nota de origem.

### Saída
- **RF17** — Gerar base completa em JSON (§7) e relatório de extração em JSON ou Markdown.
- **RF18** — Gerar recorte a partir da base, com o mesmo esquema, sem reprocessar a fonte (§9).
- **RF19** — Cada nó guarda `origem` (§5.1), para depurar o parser.

## 7. Modelo de dados

### 7.1 Envelope

```json
{
  "schema_version": "1.0",
  "norma": {
    "id": "cp",
    "titulo": "DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940",
    "ementa": "Código Penal.",
    "tipo_fonte": "html",
    "fonte": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm",
    "capturado_em": "2026-10-26T02:03:12Z",
    "sha256": "…",
    "perfil": "cp"
  },
  "metadados": {"preambulo": "…", "rodape": "…"},
  "recorte": null,
  "artigos": [ ]
}
```

- `metadados` guarda o que fica fora da árvore de artigos (H17). É a única parte que pode diferir entre leituras da mesma página por `.mht` e por URL (A14).
- PDF multi-norma: o comando gera **um arquivo por norma**, com o mesmo envelope.
- No recorte, `"recorte": {"expressao": "121-130; 311-A", "origem": "base_cp.json"}`.

### 7.2 Nós (exemplo real — art. 121, trecho)

```json
{
  "id": "art121",
  "tipo": "artigo",
  "rotulo": "Art. 121",
  "numero": 121,
  "sufixo": [],
  "rubrica": "Homicídio simples",
  "local": {"parte": "PARTE ESPECIAL", "livro": null,
            "titulo": "TÍTULO I — DOS CRIMES CONTRA A PESSOA",
            "capitulo": "CAPÍTULO I — DOS CRIMES CONTRA A VIDA",
            "secao": null, "subsecao": null, "rotulo_livre": null},
  "texto": "Matar alguem:",
  "notas": [],
  "parcial": false,
  "filhos": [
    {"id": "art121.pena1", "tipo": "pena", "texto": "reclusão, de seis a vinte anos."},
    {"id": "art121.p2", "tipo": "paragrafo", "rotulo": "§ 2º",
     "rubrica": "Homicídio qualificado",
     "texto": "Se o homicídio é cometido:", "notas": [],
     "filhos": [
       {"id": "art121.p2.i7", "tipo": "inciso", "rotulo": "VII", "texto": "contra:",
        "notas": [{"tipo": "redacao", "norma": "Lei nº 15.134", "ano": 2025, "data": null,
                   "bruto": "(Redação dada pela Lei nº 15.134, de 2025)"}],
        "filhos": [{"id": "art121.p2.i7.a", "tipo": "alinea", "rotulo": "a", "texto": "autoridade ou agente…"}]}
     ]}
  ]
}
```

- `id` é estável e derivado do rótulo: `art121`, `art121-A`, `art359-M-A`, `art121.p2-B`, `art121.pu` (parágrafo único), `.i7`, `.a`.
- `filhos` preserva a **ordem do texto**. Penas e dispositivos ficam intercalados, como na lei (H14).
- O texto vem **literal**, inclusive grafias antigas ("alguem", "conseqüências"). Normalizar ortografia é decisão da Etapa 2.

### 7.3 Notas

| `tipo` | Gatilhos (perfil padrão + NSCGJ) |
|---|---|
| `redacao` | Redação dada, Alterado, (NR) |
| `inclusao` | Incluído/Incluída, Acrescentado |
| `revogacao` | Revogado/Revogada/Revogados |
| `veto` | VETADO, Vetado |
| `vigencia` | Vigência (com ou sem parênteses) |
| `remissao` | Vide |
| `outra` | qualquer parêntese com "Lei nº"/"Provimento" não classificado (vai para o relatório) |

Campos: `norma` (ex.: "Lei nº 15.134", "Provimento CG Nº 48"), `ano`, `data` (quando o texto trouxer a data completa), `bruto`.

## 8. Regras de reconhecimento (ponto de partida)

Os regex abaixo são o **ponto de partida** e devem ser cobertos por testes com as linhas reais do §11. São aplicados **depois** da normalização (ordinal → `º`, travessão → `-`). Na tabela, `\|` é só o escape do Markdown: no código, use `|`. Os padrões de artigo e parágrafo já foram testados contra linhas reais das duas fontes (`Art 187.`, `Art. 359-M-A.`, `Artigo 1°`, `Art. 1.091-A`, `§ 2o-A`, `§ 2°`).

| Elemento | Padrão |
|---|---|
| Artigo | `^(Art\.?\|Artigo)\s*(\d{1,3}(?:\.\d{3})*)\s*º?((?:-[A-Z])*)\s*[-.]?\s*(.*)$` |
| Parágrafo | `^§\s*(\d+)\s*º?((?:-[A-Z])*)\s*[-.]?\s*(.*)$` |
| Parágrafo único | `^Parágrafo\s+único\s*[-.:]?\s*(.*)$` (sem diferenciar maiúsculas) |
| Inciso | `^([IVXLCDM]+)\s*-\s*(.*)$` (no PDF, exigir rótulo em negrito para evitar falso positivo) |
| Alínea | `^([a-z])\)\s*(.*)$` |
| Pena | `^Pena\s*-\s*(.*)$` |
| Nível | `^(PARTE\|LIVRO\|TÍTULO\|CAPÍTULO\|Seção\|Subseção)\b\s*([IVXLC\d]*)` (centralizado) |
| Nota | `\((?:Redação dada\|Incluíd[oa]\|Revogad[oa]s?\|Vide\|Vigência\|VETADO\|Alterad[oa]\|Acrescentad[oa]\|NR)[^)]*\)` + `\bVigência\s*$` |

## 9. Recorte

### 9.1 Sintaxe de entrada
Segue a notação do edital: itens separados por `;` ou `,`; faixa com `-`, `–` ou `a`; milhar opcional.

```
1-12; 100-120; 121; 129; 150; 154; 293-305; 307; 308; 311-A; 312-317
994-1.091; 1.091-A
```

### 9.2 Semântica e ordenação
- **Chave de ordenação:** `(numero, sufixo)`, com sufixo como tupla e sufixo vazio antes de qualquer letra. Assim: `121 < 121-A < 121-B < 122` e `359-M < 359-M-A < 359-M-B < 359-N`.
- **Faixa `a–b`:** inclui todo artigo com `chave(a) ≤ chave ≤ chave(b)` (D4). Consequência: `121–130` inclui 121-A e 121-B, mas **não** 130-A, que vem depois de `130`. Esse comportamento bate com o edital, que cita `1.091-A` à parte da faixa `994–1.091`.
- **Artigo avulso `121`:** inclui só o art. 121. Artigo com letra entra se for citado (`311-A`) ou se estiver dentro de uma faixa. (Ver pendência P1.)
- Item do recorte que **não existe** na base gera aviso, não erro.
- Granularidade sub-artigo (`196, inciso XX`; `282, § 1º`) **não** é recortada na Etapa 1: o artigo inteiro entra. Ver pendência P2.

## 10. Interface de linha de comando (proposta)

```bash
python -m vademecum extrair --fonte "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm" --perfil cp --saida dados/cp/base.json
```
`extrair` lê a fonte e gera a base completa.
- `--fonte` aceita URL, `.htm`, `.mht` ou `.pdf`.
- `--perfil` escolhe as regras da norma (§5.3); se omitido, usa `padrao`.
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
- `--artigos` recebe a expressão do §9.1.
- `--saida` recebe o JSON do recorte.

`python -m vademecum` executa o pacote `vademecum` como programa: roda o `__main__.py` dele, que despacha os subcomandos.

## 11. Validação e critérios de aceite

### 11.1 Regras do validador
- **V1** — Numeração em ordem crescente pela chave do §9.2 (sempre).
- **V2** — Sem lacunas na numeração-base (só em perfil de norma integral).
- **V3** — Nenhum `id` duplicado.
- **V4** — Nenhum filho fora de ordem lógica (inciso depois de inciso maior no mesmo pai gera aviso).
- **V5** — Nenhum texto vazio em dispositivo vigente.
- **V6** — Nenhuma nota `outra` sem registro no relatório.
- **V7** — Linhas não classificadas (nem dispositivo, nem continuação reconhecida) aparecem no relatório com `origem`.

### 11.2 Casos de aceite (com as fontes anexadas)

| # | Entrada | Resultado esperado |
|---|---|---|
| A1 | CP, base completa | Artigos 1 a 361 sem lacuna de numeração-base; último = art. 361; rodapé fora da árvore. |
| A2 | CP, art. 121, § 2º | Incisos I–V e VII–X; **VI ausente** (revogado); rubrica "Feminicídio" do VI descartada; VII com alíneas a e b; duas penas posicionais. |
| A3 | CP, art. 121 | § 2º-A e § 7º ausentes; § 2º-B, § 2º-C e § 2º-D presentes; § 2º-D com pena própria. |
| A4 | CP, art. 88 | **Presente** ("Revogado o livramento…" é texto vigente). |
| A5 | CP, arts. 187–196 | Ausentes (revogados); registrados no relatório. |
| A6 | CP, art. 359-M-A e 359-M-B | Presentes, ordenados após 359-M e antes de 359-N. |
| A7 | CP, art. 2º | Parágrafo único reconhecido (`Parágrafo único -`). |
| A8 | CP, `§ 4o` e `§ 2°` | Rotulados como `§ 4º` e `§ 2º`. |
| A9 | PDF | 4 normas segmentadas: NSCGJ Tomo I, Lei 6.830/1980, Res. CNJ 354/2020, Lei 11.608/2003. |
| A10 | PDF, NSCGJ | Nenhum aviso de lacuna; art. 196 com `parcial: true` contendo só o inciso XX; arts. 1.054–1.091 registrados como faixa revogada. |
| A11 | PDF, Lei 11.608 | `Artigo 1°` reconhecido; artigos 10 e 11 ausentes (revogados). |
| A12 | PDF, Res. CNJ 354, art. 8º | Aviso de "Parágrafo único" no meio da linha (P15). |
| A13 | Recorte `121-130` | Contém 121, 121-A, 121-B, 122…130 vigentes; não contém 130-A. |
| A14 | Leitura de `.mht` e da URL da mesma página | Bases idênticas, exceto `metadados`. |

### 11.3 Testes
- `pytest` com fixtures de **trechos reais** das fontes (não o arquivo inteiro), um teste por caso do §11.2.
- Teste de regressão: base completa do CP gerada e comparada com um snapshot JSON versionado. Qualquer mudança no parser que altere o snapshot precisa ser revisada.

## 12. Pendências e riscos

| # | Item | Tipo | Proposta |
|---|---|---|---|
| P1 | Artigo avulso (`121`) inclui só ele ou também `121-X`? A decisão D4 cobre faixas. | Pendência | Assumido: **só ele** (§9.2). Confirmar. |
| P2 | Recorte sub-artigo (`196, inciso XX`; `282, § 1º`), que o edital usa na NSCGJ. | Pendência | Na Etapa 1 entra o artigo inteiro. Avaliar suporte a `art.inciso` na sintaxe. |
| P3 | **Regra temporal do edital (vigência até 19/10/2026)** × captura do HTML (26/10/2026). Há alterações "de 2026" no CP (Leis 15.358, 15.384, 15.402, 15.425) e as notas trazem só o ano, não a data. | Risco | A Etapa 1 guarda número e ano de cada nota. A conferência de data contra o corte do edital fica como ponto de atenção da Etapa 2, ou como lista manual de leis posteriores ao corte no perfil. |
| P4 | Ao descartar revogados (D1), perde-se a informação "este inciso foi revogado/deslocado", que é útil como ponto de atenção (ex.: feminicídio saiu do art. 121, § 2º, VI e virou o art. 121-A). | Risco | O relatório de extração guarda os descartes de forma estruturada (JSON), para a Etapa 2 poder consultar sem que eles entrem na base. |
| P5 | Detecção de rubrica no PDF (sem rubricas na amostra atual; normas penais em PDF terão). | Risco | Heurística: linha curta, sem pontuação final, imediatamente antes de dispositivo. Validar quando houver PDF de norma penal. |
| P6 | Mudança de layout do Planalto (HTML antigo do FrontPage convive com trechos novos em `<p style="text-align: justify">`). | Risco | Os testes de regressão (§11.3) detectam a quebra. O leitor não deve depender de atributos de estilo, só de negrito e alinhamento. |
| P7 | PDFs de outras origens (Senado, editoras) com layout diferente. | Risco | O leitor PDF expõe parâmetros (colunas, zonas de cabeçalho e rodapé, mapa de fontes) no perfil. |

## 13. Requisitos não funcionais

- **RNF01** — Python 3.12. Dependências: `requests`, `beautifulsoup4`, `lxml`, `pdfplumber`. Desenvolvimento: `pytest`, `pytest-cov`, `ruff` (lint e formatação; configuração em `pyproject.toml`).
- **RNF02** — Rodar em Windows sem WSL (caminhos via `pathlib`, saída UTF-8 explícita).
- **RNF03** — Determinismo: mesma fonte e mesmo perfil geram JSON idêntico, byte a byte (chaves ordenadas, sem timestamp dentro de `artigos`).
- **RNF04** — Nenhuma perda silenciosa: todo texto da fonte entra na árvore ou aparece no relatório.
- **RNF05** — Desempenho: base do CP em menos de 10 s numa máquina comum. É meta, não requisito rígido.

## 14. Sequência de implementação

Acompanhamento da execução: `docs/PENDENCIAS.md` (fase 0 = setup do projeto).

1. `modelo.py` + chave de ordenação + `recorte.py`, com testes de unidade e sem depender de fonte.
2. `fontes/html.py` (`.mht` e arquivo local) + `normalizador.py`.
3. `parser.py` com perfil `cp`, guiado pelos casos A1–A8 e A13.
4. `notas.py` + `vigencia.py` + relatório.
5. `fontes/pdf.py` + `segmentador.py` + perfis `nscgj` e `lei_sp`, guiados pelos casos A9–A12.
6. Download por URL com cache (RF02) e teste A14.
7. CLI.
