# Fontes — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

O que se observou nas fontes reais e como cada leitor as transforma em `LinhaFonte`. Usado por
`fontes/html.py`, `fontes/pdf.py` e `segmentador.py`. Vizinhos: [parsing.md](parsing.md) (o que se
faz com as linhas) e [pipeline-e-perfis.md](pipeline-e-perfis.md).

Fontes analisadas: `DEL2848compilado_2.mht` (Planalto, salvo em 26/10/2026),
`LEI_SECA_OJ26_Legislacao_Especial.17.10.pdf` (18 p.) e, para H1 e H8, os `.htm` do CP, CPP,
CPC, CC, LINDB, CF e Leis 9.099, 8.429, 6.830 e 13.146 (baixados em 31/10/2026).

**Legenda de evidência:** **[Verificado]** = conferido nas fontes anexadas · **[Inferido]** =
dedução a partir das amostras, a confirmar na implementação.

## §1. O PDF é fonte já estruturada (D6)

O PDF é tratado como fonte **já estruturada**: montado no Word, com texto selecionável.

## §2. Leitura

- **RF01** — Aceitar como fonte: URL HTTP(S), arquivo `.htm`/`.html`, `.mht`/`.mhtml` e `.pdf`. O tipo é detectado pela extensão ou pelo conteúdo.
- **RF02** — Ao baixar por URL, salvar o HTML bruto em cache local com data e SHA-256, para reprodutibilidade.
- **RF03** — Em `.mht`, extrair a parte `text/html` principal (MIME `multipart/related`) e decodificar pelo charset declarado (H1).
- **RF04** — No HTML, colapsar espaços em branco e só então quebrar linhas em `<p>`, `<br>`, `<div>`, `<blockquote>`, `<tr>`, `<center>`, `<li>` e `<h1>`–`<h6>` (H3, H4). O HTML é lido pela regra do HTML5, como o navegador o mostra.
- **RF05** — No PDF, extrair por coluna (P2), remover cabeçalho e número de página (P3) e mapear negrito e cor por caractere (P4).
- **RF06** — Rejeitar com mensagem clara um PDF sem camada de texto (OCR está fora de escopo).

## §3. HTML do Planalto (Código Penal)

| # | Característica | Evidência | Consequência |
|---|---|---|---|
| H1 | Codificação **windows-1252**. O `.htm` não declara charset nem no `<meta>` nem no HTTP (`Content-Type: text/html`); o `<meta>` do `.mht` foi o navegador que pôs. Há bytes 0x80–0x9F (81 no CP, 104 no CPP), que o latin-1 não cobre. | [Verificado] | Decodificar pelo charset declarado; sem declaração, windows-1252, sempre estrito. Emitir UTF-8. |
| H2 | **Sem marcação semântica.** Só `<p>`, `<b>`/`<strong>`, `<font>`, `<a>`, `<span>`. Só existem 8 âncoras `name="art…"` em todo o documento. | [Verificado] | O parse é **por texto + regex**, não por DOM ou âncoras. |
| H3 | O código-fonte tem quebras de linha **no meio das frases** (ex.: `§` numa linha e `1º Se o agente…` na seguinte). As quebras reais são `<p>` e `<br>`. | [Verificado] | Colapsar espaços em branco **antes** de quebrar em blocos; quebrar só em `<p>`/`<br>`/`<div>`/`<blockquote>`. |
| H4 | Um mesmo `<p>` pode conter **vários artigos** separados por `<br>` (ex.: arts. 187, 189 e 191). | [Verificado] | A unidade de parse é a **linha lógica**, não o parágrafo HTML. |
| H5 | Títulos estruturais ficam em `<p align="CENTER"><strong>` (ex.: `TÍTULO I<br>DOS CRIMES CONTRA A PESSOA`). Alguns centralizam só pelo `style` (`text-align:center`, CAPÍTULO V do Título X). | [Verificado] | Nível = linha centralizada que começa por palavra-chave do perfil, sem diferenciar maiúsculas (`SEÇÃO I`); o negrito não é exigido (`CAPÍTULO IV` do Título XII não tem). O nome são as linhas centralizadas seguintes que não são nota, nível nem rubrica (forma (d) da H6), unidas por espaço (nome em duas linhas no CP). Linha centralizada em negrito sem palavra-chave, depois do primeiro artigo, é `rotulo_livre` (`DISPOSIÇÕES FINAIS`, P8) e fecha os níveis abaixo da `parte`: as disposições finais do CP não são do Título XII. O `local` guarda `"<rótulo> — <nome>"`; nível novo zera os de baixo. Operador, 2026-11-01. |
| H6 | Rubricas ("Homicídio simples", "Caso de diminuição de pena") ficam em `<p align="left"><b>`, isoladas. O negrito também vem só pelo `style` (`font-weight: 700`, rubrica do art. 311-A) e sai dentro do `<b>` com `font-weight: normal` (art. 298, parágrafo único); no `.htm`, `<b><i><p></i>…</b></p>` é negrito, porque o navegador reabre o `<b>` pela regra do HTML5. Também aparecem **antes de parágrafos e incisos**, não só antes de artigos (ex.: "Homicídio contra menor de 14 anos" antes do inciso IX do art. 121, § 2º). | [Verificado] | Rubrica é a linha sem padrão de dispositivo que, não centralizada, é (a) 100% negrito; ou (b) só com o início em negrito (`rotulo_negrito`: `Lugar do crime (Redação dada…)`, nota fora do `<b>`) e seguida de dispositivo; ou (c), se o perfil ligar `rubrica.sem_negrito`, sem negrito, com o resto sem notas não terminado em `.`, `;`, `:` ou `,`, e seguida de dispositivo (`Sabotagem`, `Golpe de Estado`); ou, centralizada, é (d) em caixa mista e seguida de dispositivo (`Registro não autorizado da intimidade sexual`, CP, art. 216-B; nome de nível vem em maiúsculas ou todo em minúsculas). Ela se liga ao **próximo dispositivo de qualquer nível**. Operador, 2026-11-01. |
| H7 | Rubricas podem carregar nota: `Feminicídio (Incluído pela Lei nº 14.994, de 2024)`. | [Verificado] | Separar a nota do texto da rubrica; ela vai para `notas` do dispositivo a que a rubrica se liga, antes das notas dele. Rubrica sem dispositivo seguinte (vem nível ou fim) → `aviso`. |
| H8 | **Texto tachado (`<strike>`, `<s>`, `<del>` ou `text-decoration` com `line-through` no `style` de qualquer ancestral, inclusive `none line-through`) é redação que não vale mais.** Só pelo CSS há 55 tachados (CPC 35, Lei 8.429 16, Lei 13.146 4). No CP e na LINDB ele está vazio (só `<br>` ou espaço). Nas demais normas, a redação antiga vem tachada, inclusive o rótulo: `<strike>Art. 4° Os agentes…</strike> (Revogado pela Lei nº 14.230, de 2021)` (Lei 8.429). Há um tachado no meio de uma frase vigente: `condenatória (<strike>art. 110 do Código Penal</strike>).` (CPP, art. 336, parágrafo único). | [Verificado] | Linha cujo texto fora do tachado é vazio ou só nota sai inteira e vai como `descarte` para o relatório (ADR-001, RNF04). Tachado parcial fica na linha e gera `aviso`. Tachado vazio é ignorado. Operador, 2026-10-31; o CSS, 2026-11-01. |
| H9 | Notas aparecem inline, entre parênteses, em geral como link: Incluído (610), Redação dada (480), Vigência (74), Revogado (47), Vide (34), Vetado (17). | [Verificado] | Extrair todas e classificar por tipo ([vigencia-e-notas.md](vigencia-e-notas.md)). |
| H10 | "Vigência" aparece **com e sem parênteses** (25 linhas terminam em `) Vigência`). | [Verificado] | O regex de notas deve aceitar as duas formas. |
| H11 | Variações de numeração: `Art. 1º -`, `Art. 10 -`, `Art. 121.`, `Art 187.` (sem ponto), `§ 2°` (grau), `§ 4o` (letra "o"), `§ 2o-A`, `§ 2º-B.` | [Verificado] | Normalizar `º`/`°`/`o` como ordinal; aceitar `Art` com ou sem ponto e `-`, `–` ou `.` como separador. |
| H12 | Sufixos de **dois níveis**: `Art. 359-M-A`, `Art. 359-M-B`. | [Verificado] | O identificador e a ordenação suportam sufixo composto ([recorte-e-cli.md](recorte-e-cli.md)). |
| H13 | Travessão (`–`) e hífen (`-`) se alternam: `VII – contra:` / `I - mediante…` / `Pena – reclusão`. | [Verificado] | Tratar os dois como o mesmo separador. |
| H14 | A linha `Pena -` **não fecha** o dispositivo. No art. 121, § 2º, há uma pena depois do inciso V, os incisos VII–X continuam no mesmo § 2º e a pena se repete no final. | [Verificado] | A pena é um nó **posicional** dentro do pai. O parser não deve encerrar o § ao encontrar `Pena`. |
| H15 | Falso positivo de revogação: `Art. 88 - Revogado o livramento, não poderá ser novamente concedido…` é texto **vigente**. | [Verificado] | Só é revogado o dispositivo cujo conteúdo, tirando as notas, está **vazio** ou é exatamente `Revogado.`/`Revogados.`. |
| H16 | Rubrica que fica **órfã** quando o dispositivo seguinte é revogado (ex.: "Feminicídio" antes do inciso VI revogado do art. 121, § 2º). | [Verificado] | Descartar a rubrica junto com o dispositivo revogado. |
| H17 | Cabeçalho da página (Presidência, "Vide" gerais, ementa, preâmbulo) e rodapé (local/data, assinaturas, "Este texto não substitui o publicado no DOU…"). | [Verificado] | Cabeçalho = linhas antes do primeiro nível ou artigo → `metadados.preambulo`. `norma.titulo` = 1ª linha centralizada do cabeçalho que começa por tipo de norma (`DECRETO-LEI`, `LEI`…); `norma.ementa` = linha logo antes da fórmula `O PRESIDENTE DA REPÚBLICA`. O rodapé começa na linha que casa `rodape.inicio` do perfil (`Rio de Janeiro, 7 de dezembro de 1940;`, `Brasília, …`) → `metadados.rodape`. Operador, 2026-11-01. |
| H18 | Títulos estruturais com nota: `TÍTULO I / DA APLICAÇÃO DA LEI PENAL / (Redação dada…)`; `CAPÍTULO IV / (Incluído…) / DOS CRIMES…` (a nota pode vir **antes** do nome). | [Verificado] | O nome do nível são as linhas seguintes que não são nota (H5). A nota do nível não tem nó onde ficar e vai para o relatório como `aviso`, com a `origem`. |
| H19 | Numeração-base do CP sem lacunas (1 a 361) e último artigo `Art. 361 - Este Código entrará em vigor…`. | [Verificado] | Usar como critério de aceite (A1, no [PADRAO_OURO](../PADRAO_OURO.md)). |

## §4. PDF montado (Legislação Especial)

| # | Característica | Evidência | Consequência |
|---|---|---|---|
| P1 | Gerado por "Microsoft: Print To PDF" a partir do Word. Texto selecionável. | [Verificado] | `pdfplumber` resolve; não precisa de OCR. |
| P2 | **Duas colunas.** A extração padrão intercala as colunas. | [Verificado] | Recortar cada página em duas colunas (esquerda, depois direita) antes de extrair linhas. Detectar a divisória ou usar a metade da largura, configurável. |
| P3 | Cabeçalho de página `LEGISLAÇÃO ESPECIAL` e número de página (fonte F1, 12 pt). | [Verificado] | Remover por fonte/tamanho/posição. |
| P4 | Rótulos em **negrito** (`Art. 1º`, `§ 1º`, `I -`, `a)`, `Parágrafo único`); corpo em fonte regular. Os nomes de fonte são genéricos (`CIDFont+F3` = negrito, `CIDFont+F4` = regular). | [Verificado] | O negrito vem do **mapeamento de fonte por documento**, não do nome. Rótulo em negrito no início da linha é sinal forte de novo dispositivo. |
| P5 | **Várias normas num só PDF**: NSCGJ Tomo I, Lei 6.830/80, Res. CNJ 354/2020, Lei SP 11.608/03. Cada norma começa com título em azul-escuro sublinhado, ementa em vermelho-escuro e preâmbulo. | [Verificado] | Segmentar o PDF em **documentos** antes do parse. A saída tem uma base por norma ([modelo-de-dados.md](modelo-de-dados.md)). |
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

Os IDs P1–P16 desta tabela são características do PDF; as pendências P1–P7 de
[PENDENCIAS.md](../PENDENCIAS.md) são outra série.

## §5. Armadilhas e limites conhecidos

- Fora o tachado (H8, por tag ou por CSS), atributos de estilo não dizem nada sobre vigência. O leitor depende só
  de negrito, alinhamento e tachado.
- O tachado também erra: no CPP, art. 336, o Planalto tachou parte de uma frase vigente. Por
  isso o tachado parcial não é apagado (H8).
- O layout do Planalto muda: HTML antigo do FrontPage convive com trechos novos em
  `<p style="text-align: justify">`.
